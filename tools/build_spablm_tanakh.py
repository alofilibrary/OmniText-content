#!/usr/bin/env python3
"""Build the CC0 SpaBLM Hebrew-Bible corpus as one validated Spanish Tanakh pack."""
from __future__ import annotations

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
SOURCE = ROOT / ".work" / "spablm.zip"
OUTPUT = ROOT / "packs" / "judaism-tanakh-spablm-es-v1.otpack"
PACK_ID = "judaism-tanakh-spablm-es"
WORK_SLUG = "tanakh-spablm-es"
ATTRIBUTION = (
    "Santa Biblia libre para el mundo, David Williams & Michael Paul Johnson, "
    "CC0 1.0. Hebrew Bible corpus extracted from the complete edition."
)
VERSE = re.compile(r"^\\v\s+(\d+)(?:[a-z-]+)?(?:\s+(.*))?$")
CHAPTER = re.compile(r"^\\c\s+(\d+)")
CONTINUATION = re.compile(r"^\\(?:q\d*|p|m|pi\d*|li\d*|mi|nb|b)\s*(.*)$")
MARKER = re.compile(r"\\[A-Za-z0-9*+.-]+")


def digest(path: Path) -> str:
    hash_ = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hash_.update(chunk)
    return hash_.hexdigest()


def parse_usfm(name: str, text: str) -> tuple[str, list[tuple[int, int, str]]]:
    if "\ufffd" in text:
        raise ValueError(f"Replacement character in {name}")
    title = next((line[3:].strip() for line in text.splitlines() if line.startswith("\\h ")), None)
    if not title:
        raise ValueError(f"No title in {name}")
    rows: list[tuple[int, int, str]] = []
    chapter: int | None = None
    verse: int | None = None
    parts: list[str] = []

    def flush() -> None:
        if chapter is None or verse is None:
            return
        body = re.sub(r"\s+", " ", MARKER.sub("", " ".join(parts))).strip()
        if not body:
            raise ValueError(f"Empty verse in {name}: {chapter}:{verse}")
        rows.append((chapter, verse, body))

    for line in text.splitlines():
        if match := CHAPTER.match(line):
            flush()
            chapter, verse, parts = int(match.group(1)), None, []
        elif match := VERSE.match(line):
            flush()
            if chapter is None:
                raise ValueError(f"Verse before chapter in {name}")
            verse, parts = int(match.group(1)), [match.group(2) or ""]
        elif match := CONTINUATION.match(line):
            if verse is not None:
                parts.append(match.group(1))
        elif verse is not None and line and not line.startswith("\\"):
            parts.append(line)
    flush()
    return title, rows


def source_books() -> list[tuple[str, list[tuple[int, int, str]]]]:
    with zipfile.ZipFile(SOURCE) as archive:
        paths = [f"{number:02d}-{code}spablm.usfm" for number, code in (
            (2, "GEN"), (3, "EXO"), (4, "LEV"), (5, "NUM"), (6, "DEU"),
            (7, "JOS"), (8, "JDG"), (9, "RUT"), (10, "1SA"), (11, "2SA"),
            (12, "1KI"), (13, "2KI"), (14, "1CH"), (15, "2CH"), (16, "EZR"),
            (17, "NEH"), (18, "EST"), (19, "JOB"), (20, "PSA"), (21, "PRO"),
            (22, "ECC"), (23, "SNG"), (24, "ISA"), (25, "JER"), (26, "LAM"),
            (27, "EZK"), (28, "DAN"), (29, "HOS"), (30, "JOL"), (31, "AMO"),
            (32, "OBA"), (33, "JON"), (34, "MIC"), (35, "NAM"), (36, "HAB"),
            (37, "ZEP"), (38, "HAG"), (39, "ZEC"), (40, "MAL"),
        )]
        return [parse_usfm(path, archive.read(path).decode("utf-8")) for path in paths]


def build_database(path: Path, books: list[tuple[str, list[tuple[int, int, str]]]]) -> int:
    database = sqlite3.connect(path)
    database.executescript(SCHEMA.read_text(encoding="utf-8"))
    cursor = database.cursor()
    cursor.executemany("INSERT INTO pack_meta VALUES (?, ?)", (
        ("schemaVersion", "1"), ("packId", PACK_ID), ("packVersion", "1"),
    ))
    cursor.execute("INSERT INTO religion VALUES (1, 'Judaism', 'judaism', '#315f72', 0)")
    cursor.execute(
        "INSERT INTO work VALUES (1, 1, ?, 'Tanakh', 'es', 'ltr', ?, 'CC0 1.0', ?, 0)",
        (WORK_SLUG, "Santa Biblia libre para el mundo", ATTRIBUTION),
    )
    verse_id = chapter_id = 0
    for book_id, (title, rows) in enumerate(books, start=1):
        cursor.execute("INSERT INTO book VALUES (?, 1, NULL, ?, ?, ?)", (book_id, title, title[:8], book_id - 1))
        by_chapter: dict[int, list[tuple[int, str]]] = {}
        for chapter, verse, text in rows:
            by_chapter.setdefault(chapter, []).append((verse, text))
        for chapter_order, (number, verses) in enumerate(by_chapter.items()):
            chapter_id += 1
            cursor.execute("INSERT INTO chapter VALUES (?, ?, ?, NULL, ?)", (chapter_id, book_id, number, chapter_order))
            for verse_order, (number, text) in enumerate(verses):
                verse_id += 1
                cursor.execute("INSERT INTO verse VALUES (?, ?, ?, ?, ?)", (verse_id, chapter_id, number, text, verse_order))
    database.commit()
    indexed = cursor.execute("SELECT COUNT(*) FROM verse_fts").fetchone()[0]
    if verse_id != indexed:
        raise ValueError(f"FTS mismatch: {indexed} indexed / {verse_id} verses")
    database.close()
    return verse_id


def main() -> None:
    books = source_books()
    if len(books) != 39:
        raise ValueError(f"Expected 39 Tanakh books, got {len(books)}")
    OUTPUT.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        database = work / "content.db"
        verse_count = build_database(database, books)
        manifest = {
            "formatVersion": 1, "id": PACK_ID, "version": 1,
            "createdAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "contentDb": {"path": "content.db", "sha256": digest(database)},
            "source": {"repository": "https://github.com/kahunapule/spablm", "commit": "a741e2b6de48f8c08bab9e003bc4ae8f291bf99f", "path": "spablm_usfm.zip", "sha256": digest(SOURCE)},
            "works": [{"slug": WORK_SLUG, "title": "Tanakh", "language": "es", "translation": "Santa Biblia libre para el mundo", "license": "CC0 1.0", "attribution": ATTRIBUTION, "verseCount": verse_count}],
        }
        (work / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as pack:
            pack.write(database, "content.db")
            pack.write(work / "manifest.json", "manifest.json")
    print(json.dumps({"pack": str(OUTPUT), "sha256": digest(OUTPUT), "sizeBytes": OUTPUT.stat().st_size, "verseCount": verse_count}, indent=2))


if __name__ == "__main__":
    main()
