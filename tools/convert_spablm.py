#!/usr/bin/env python3
"""Convert the pinned chapter-USFM SpaBLM repository into Omni Text's flat source JSON."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

BOOKS = (
    ("Genesis", "Génesis"), ("Exodus", "Éxodo"), ("Leviticus", "Levítico"), ("Numbers", "Números"), ("Deuteronomy", "Deuteronomio"),
    ("Joshua", "Josué"), ("Judges", "Jueces"), ("Ruth", "Rut"), ("1 Samuel", "1 Samuel"), ("2 Samuel", "2 Samuel"),
    ("1 Kings", "1 Reyes"), ("2 Kings", "2 Reyes"), ("1 Chronicles", "1 Crónicas"), ("2 Chronicles", "2 Crónicas"), ("Ezra", "Esdras"),
    ("Nehemiah", "Nehemías"), ("Esther", "Ester"), ("Job", "Job"), ("Psalms", "Salmos"), ("Proverbs", "Proverbios"),
    ("Ecclesiastes", "Eclesiastés"), ("Song of Solomon", "Cantares"), ("Isaiah", "Isaías"), ("Jeremiah", "Jeremías"), ("Lamentations", "Lamentaciones"),
    ("Ezekiel", "Ezequiel"), ("Daniel", "Daniel"), ("Hosea", "Oseas"), ("Joel", "Joel"), ("Amos", "Amós"), ("Obadiah", "Abdías"),
    ("Jonah", "Jonás"), ("Micah", "Miqueas"), ("Nahum", "Nahúm"), ("Habakkuk", "Habacuc"), ("Zephaniah", "Sofonías"),
    ("Haggai", "Hageo"), ("Zechariah", "Zacarías"), ("Malachi", "Malaquías"), ("Matthew", "Mateo"), ("Mark", "Marcos"),
    ("Luke", "Lucas"), ("John", "Juan"), ("Acts", "Hechos"), ("Romans", "Romanos"), ("1 Corinthians", "1 Corintios"),
    ("2 Corinthians", "2 Corintios"), ("Galatians", "Gálatas"), ("Ephesians", "Efesios"), ("Philippians", "Filipenses"), ("Colossians", "Colosenses"),
    ("1 Thessalonians", "1 Tesalonicenses"), ("2 Thessalonians", "2 Tesalonicenses"), ("1 Timothy", "1 Timoteo"), ("2 Timothy", "2 Timoteo"),
    ("Titus", "Tito"), ("Philemon", "Filemón"), ("Hebrews", "Hebreos"), ("James", "Santiago"), ("1 Peter", "1 Pedro"),
    ("2 Peter", "2 Pedro"), ("1 John", "1 Juan"), ("2 John", "2 Juan"), ("3 John", "3 Juan"), ("Jude", "Judas"), ("Revelation", "Apocalipsis"),
)
VERSE = re.compile(r"^\\v\s+(\d+)(?:[a-z-]+)?(?:\s+(.*))?$")
CHAPTER = re.compile(r"^\\c\s+(\d+)")
FOOTNOTE = re.compile(r"\\(?:f|x)\b.*?\\(?:f|x)\*", re.DOTALL)
MARKER = re.compile(r"\\[A-Za-z0-9*+.-]+")


def chapter_rows(path: Path, book: str) -> list[dict[str, object]]:
    text = FOOTNOTE.sub("", path.read_text(encoding="utf-8"))
    chapter_match = CHAPTER.search(text)
    if chapter_match is None:
        raise ValueError(f"No chapter marker in {path}")
    chapter = int(chapter_match.group(1))
    rows: list[dict[str, object]] = []
    verse: int | None = None
    parts: list[str] = []

    def flush() -> None:
        if verse is None:
            return
        body = re.sub(r"\s+", " ", MARKER.sub("", " ".join(parts))).strip()
        # This source keeps markers for a small number of verses omitted by its
        # critical edition. Omit those markers rather than inventing content.
        if not body:
            return
        if "\ufffd" in body:
            raise ValueError(f"Replacement character in {path}: {chapter}:{verse}")
        rows.append({"book": book, "chapter": chapter, "verse": verse, "text": body})

    for line in text.splitlines():
        match = VERSE.match(line)
        if match:
            flush()
            verse, parts = int(match.group(1)), [match.group(2) or ""]
        elif verse is not None and line and not line.startswith("\\"):
            parts.append(line)
    flush()
    return rows


def convert(source: Path, output: Path) -> int:
    rows: list[dict[str, object]] = []
    for folder, title in BOOKS:
        chapter_paths = sorted(
            (path for path in (source / folder).glob("*/data") if path.parent.name.isdigit() and path.parent.name != "0"),
            key=lambda path: int(path.parent.name),
        )
        if not chapter_paths:
            raise ValueError(f"Missing canonical book: {folder}")
        for path in chapter_paths:
            rows.extend(chapter_rows(path, title))
    keys = {(row["book"], row["chapter"], row["verse"]) for row in rows}
    if len(keys) != len(rows) or len(rows) < 31_000:
        raise ValueError(f"Expected at least 31,000 unique verses, got {len(rows)}")
    output.write_text(json.dumps(rows, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(f"Converted {convert(args.source, args.output)} verses.")
