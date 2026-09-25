#!/usr/bin/env python3
"""Build one validated Omni Text Bible pack from a pinned Scrollmapper JSON source."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema" / "content-v1.sql"
SOURCE_REPOSITORY = "https://github.com/scrollmapper/bible_databases"
SOURCE_COMMIT = "e1b254cef86d0e65b1a5d1a94b8b112d0f296a2c"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_flat_bible(payload: list[object], expected_verses: int) -> tuple[list[tuple[int, str]], list[tuple[int, int, int, str]]]:
    book_ids: dict[str, int] = {}
    verses: list[tuple[int, int, int, str]] = []
    seen: set[tuple[int, int, int]] = set()
    for row in payload:
        if not isinstance(row, dict):
            raise ValueError("Flat Bible rows must be objects")
        name, chapter, verse, text = row.get("book"), row.get("chapter"), row.get("verse"), row.get("text")
        if not isinstance(name, str) or not isinstance(chapter, int) or not isinstance(verse, int):
            raise ValueError(f"Invalid flat Bible reference: {row!r}")
        if not isinstance(text, str) or not text.strip() or "\ufffd" in text:
            raise ValueError(f"Invalid flat Bible text: {name} {chapter}:{verse}")
        book_id = book_ids.setdefault(name, len(book_ids) + 1)
        key = (book_id, chapter, verse)
        if key in seen:
            raise ValueError(f"Duplicate flat Bible reference: {name} {chapter}:{verse}")
        seen.add(key)
        verses.append((book_id, chapter, verse, text.strip()))
    if len(book_ids) != 66 or len(verses) != expected_verses:
        raise ValueError(f"Expected 66 books / {expected_verses} verses, got {len(book_ids)} / {len(verses)}")
    return [(book_id, name) for name, book_id in book_ids.items()], verses


def load_bible(source: Path, expected_verses: int) -> tuple[list[tuple[int, str]], list[tuple[int, int, int, str]]]:
    payload = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return load_flat_bible(payload, expected_verses)
    books = payload.get("books")
    if not isinstance(books, list) or len(books) != 66:
        raise ValueError("Expected exactly 66 books in a Scrollmapper Bible JSON source")

    verses: list[tuple[int, int, int, str]] = []
    seen: set[tuple[int, int, int]] = set()
    named_books: list[tuple[int, str]] = []
    for book_id, book in enumerate(books, start=1):
        name = book.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Book {book_id} has no name")
        named_books.append((book_id, name.strip()))
        for chapter in book.get("chapters", []):
            chapter_number = chapter.get("chapter")
            for verse in chapter.get("verses", []):
                number, text = verse.get("verse"), verse.get("text")
                key = (book_id, chapter_number, number)
                if not isinstance(number, int) or not isinstance(text, str) or not text.strip():
                    raise ValueError(f"Invalid verse at {key!r}")
                if chapter_number != verse.get("chapter") or key in seen:
                    raise ValueError(f"Inconsistent or duplicate reference: {key!r}")
                if "\ufffd" in text:
                    raise ValueError(f"Replacement character in source verse: {key!r}")
                seen.add(key)
                verses.append((book_id, chapter_number, number, text.strip()))
    if len(verses) != expected_verses:
        raise ValueError(f"Expected {expected_verses} verses, got {len(verses)}")
    return named_books, verses


def load_usfm_bible(source: Path, expected_verses: int) -> tuple[list[tuple[int, str]], list[tuple[int, int, int, str]]]:
    files = sorted(path for path in source.glob("[0-9][0-9]-*.usfm") if not path.name.startswith("00-"))
    if len(files) != 66:
        raise ValueError(f"Expected 66 USFM book files, got {len(files)}")

    books: list[tuple[int, str]] = []
    verses: list[tuple[int, int, int, str]] = []
    verse_pattern = re.compile(r"^\\v\s+(\d+)(?:[a-z-]+)?(?:\s+(.*))?$")
    chapter_pattern = re.compile(r"^\\c\s+(\d+)")
    continuation_pattern = re.compile(r"^\\(?:q\d*|p|m|pi\d*|li\d*|mi|nb|b)\s*(.*)$")

    for book_id, path in enumerate(files, start=1):
        text = path.read_text(encoding="utf-8")
        if "\ufffd" in text:
            raise ValueError(f"Replacement character in {path.name}")
        title = next((line[3:].strip() for line in text.splitlines() if line.startswith("\\\\h ")), None)
        if not title:
            raise ValueError(f"No book title in {path.name}")
        books.append((book_id, title))
        chapter: int | None = None
        verse: int | None = None
        parts: list[str] = []

        def flush() -> None:
            if chapter is None or verse is None:
                return
            body = re.sub(r"\s+", " ", " ".join(parts)).strip()
            body = re.sub(r"\\[A-Za-z0-9*+.-]+", "", body).strip()
            if not body:
                raise ValueError(f"Empty verse in {path.name}: {chapter}:{verse}")
            verses.append((book_id, chapter, verse, body))

        for line in text.splitlines():
            chapter_match = chapter_pattern.match(line)
            if chapter_match:
                flush()
                chapter, verse, parts = int(chapter_match.group(1)), None, []
                continue
            verse_match = verse_pattern.match(line)
            if verse_match:
                flush()
                if chapter is None:
                    raise ValueError(f"Verse before chapter in {path.name}")
                verse, parts = int(verse_match.group(1)), [verse_match.group(2) or ""]
                continue
            continuation = continuation_pattern.match(line)
            if continuation and verse is not None:
                parts.append(continuation.group(1))
            elif verse is not None and line and not line.startswith("\\\\"):
                parts.append(line)
        flush()

    references = {(book, chapter, verse) for book, chapter, verse, _ in verses}
    if len(references) != len(verses):
        raise ValueError("Duplicate verse reference in USFM source")
    if len(verses) != expected_verses:
        raise ValueError(f"Expected {expected_verses} verses, got {len(verses)}")
    return books, verses


def source_sha256(source: Path) -> str:
    if source.is_file():
        return sha256(source)
    digest = hashlib.sha256()
    for path in sorted(source.rglob("*.usfm")):
        digest.update(path.relative_to(source).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def build_db(target: Path, source: Path, args: argparse.Namespace) -> dict[str, object]:
    books, verses = (
        load_usfm_bible(source, args.expected_verses)
        if args.source_format == "usfm"
        else load_bible(source, args.expected_verses)
    )
    db = sqlite3.connect(target)
    try:
        db.executescript(SCHEMA.read_text(encoding="utf-8"))
        db.execute("INSERT INTO religion VALUES(1, ?, ?, ?, 1)", (
            "Christianity", "christianity", "#6E3B3B",
        ))
        db.execute("INSERT INTO work VALUES(1, 1, ?, ?, ?, 'ltr', ?, ?, ?, 1)", (
            args.work_slug, "Bible", args.language, args.translation, args.license, args.attribution,
        ))
        db.executemany("INSERT INTO division VALUES(?, 1, ?, 'testament', ?)", (
            (1, "Old Testament", 1), (2, "New Testament", 2),
        ))
        for book_id, name in books:
            db.execute("INSERT INTO book VALUES(?, 1, ?, ?, NULL, ?)", (
                book_id, 1 if book_id <= 39 else 2, name, book_id,
            ))

        chapter_ids: dict[tuple[int, int], int] = {}
        for chapter_id, (book_id, chapter) in enumerate(
            sorted({(book, chapter) for book, chapter, _, _ in verses}), start=1,
        ):
            chapter_ids[(book_id, chapter)] = chapter_id
            db.execute("INSERT INTO chapter VALUES(?, ?, ?, NULL, ?)", (
                chapter_id, book_id, chapter, chapter,
            ))
        for verse_id, (book, chapter, verse, text) in enumerate(verses, start=1):
            db.execute("INSERT INTO verse VALUES(?, ?, ?, ?, ?)", (
                verse_id, chapter_ids[(book, chapter)], verse, text, verse,
            ))
        db.execute("INSERT INTO verse_fts(verse_fts) VALUES('optimize')")
        db.executemany("INSERT INTO pack_meta VALUES(?, ?)", {
            "packId": args.pack_id,
            "packVersion": str(args.version),
            "schemaVersion": "1",
            "sourceRepository": args.source_repository,
            "sourceCommit": args.source_commit,
            "sourcePath": args.source_path,
            "sourceSha256": source_sha256(source),
            "workCount": "1",
            "verseCount": str(len(verses)),
        }.items())
        db.commit()
    finally:
        db.close()
    return {"bookCount": len(books), "verseCount": len(verses), "sourceSha256": source_sha256(source)}


def build_pack(source: Path, output: Path, args: argparse.Namespace) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        content_db = work / "content.db"
        summary = build_db(content_db, source, args)
        manifest = {
            "formatVersion": 1, "id": args.pack_id, "version": args.version,
            "createdAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "contentDb": {"path": "content.db", "sha256": sha256(content_db)},
            "source": {"repository": args.source_repository, "commit": args.source_commit,
                       "path": args.source_path, "sha256": summary["sourceSha256"]},
            "works": [{"slug": args.work_slug, "title": "Bible", "language": args.language,
                       "translation": args.translation, "license": args.license,
                       "attribution": args.attribution, "verseCount": summary["verseCount"]}],
        }
        manifest_path = work / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as pack:
            pack.write(content_db, "content.db")
            pack.write(manifest_path, "manifest.json")
    return {**summary, "packSha256": sha256(output), "packSize": output.stat().st_size}


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-format", choices=("json", "usfm"), default="json")
    parser.add_argument("--source-path", required=True)
    parser.add_argument("--source-repository", default=SOURCE_REPOSITORY)
    parser.add_argument("--source-commit", default=SOURCE_COMMIT)
    parser.add_argument("--expected-verses", type=int, required=True)
    parser.add_argument("--pack-id", required=True)
    parser.add_argument("--work-slug", required=True)
    parser.add_argument("--translation", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--license", required=True)
    parser.add_argument("--attribution", required=True)
    parser.add_argument("--version", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = arguments()
    print(json.dumps({"output": str(args.output), **build_pack(args.source, args.output, args)}, indent=2))
