-- Omni Text downloadable content-pack schema v1.
-- Packs contain one or more immutable works. User notes/bookmarks stay in the app DB.
PRAGMA foreign_keys = ON;

CREATE TABLE pack_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE religion (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    accent_color TEXT NOT NULL,
    sort_order INTEGER NOT NULL
);

CREATE TABLE work (
    id INTEGER PRIMARY KEY,
    religion_id INTEGER NOT NULL REFERENCES religion(id),
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    language TEXT NOT NULL,
    script_dir TEXT NOT NULL DEFAULT 'ltr',
    translation_name TEXT,
    license TEXT NOT NULL,
    attribution TEXT,
    sort_order INTEGER NOT NULL
);

CREATE TABLE division (
    id INTEGER PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES work(id),
    name TEXT NOT NULL,
    kind TEXT,
    sort_order INTEGER NOT NULL
);

CREATE TABLE book (
    id INTEGER PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES work(id),
    division_id INTEGER REFERENCES division(id),
    name TEXT NOT NULL,
    abbrev TEXT,
    sort_order INTEGER NOT NULL
);

CREATE TABLE chapter (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES book(id),
    number INTEGER NOT NULL,
    title TEXT,
    sort_order INTEGER NOT NULL,
    UNIQUE(book_id, number)
);

CREATE TABLE verse (
    id INTEGER PRIMARY KEY,
    chapter_id INTEGER NOT NULL REFERENCES chapter(id),
    number INTEGER NOT NULL,
    text TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    UNIQUE(chapter_id, number)
);

CREATE INDEX idx_work_religion ON work(religion_id);
CREATE INDEX idx_book_work ON book(work_id);
CREATE INDEX idx_chapter_book ON chapter(book_id);
CREATE INDEX idx_verse_chapter ON verse(chapter_id);

CREATE VIRTUAL TABLE verse_fts USING fts4(
    text,
    content='verse',
    tokenize=porter
);

CREATE TRIGGER verse_ai AFTER INSERT ON verse BEGIN
    INSERT INTO verse_fts(rowid, text) VALUES (new.id, new.text);
END;
