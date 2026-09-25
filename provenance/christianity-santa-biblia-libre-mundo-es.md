# Santa Biblia libre para el mundo (Spanish) — approved source record

- **Pack id:** `christianity-santa-biblia-libre-mundo-es`
- **Pack version:** `1`
- **Review date:** 2026-09-25

## Rights and attribution

- **License:** CC0 1.0
- **Displayed attribution:** `Santa Biblia libre para el mundo, CC0 1.0. Source: eBible.org and kahunapule/spablm.`
- **License evidence:** the pinned upstream
  [LICENSE](https://github.com/kahunapule/spablm/blob/a741e2b6de48f8c08bab9e003bc4ae8f291bf99f/LICENSE)
  is CC0-1.0. eBible.org also labels this edition (`spablm`) **Public Domain**
  at <https://ebible.org/Scriptures/details.php?id=spablm>.

## Immutable source

- **Repository:** <https://github.com/kahunapule/spablm>
- **Commit:** `a741e2b6de48f8c08bab9e003bc4ae8f291bf99f`
- **Source format:** chapter-level USFM data files
- **Source archive SHA-256:** `cedcbfaa7fb1830cd21da8b70cf40890e4a6844a7aeeb78285d44fa62f8ffe99`
- **Normalized source SHA-256:** `8fff1a644104df848f1d0612052673c6b5cd65018d8716869828e649d4546cd1`

`tools/convert_spablm.py` deterministically selects the canonical 66 books,
removes USFM footnotes, and preserves the source text. It discards only blank
verse markers used by this critical edition for omitted verses; it never invents
text. The generated source is then passed through the normal pack validator.

## Validation

- 66 canonical books;
- 31,087 unique, non-empty verses;
- no Unicode replacement characters;
- FTS4 row count matches verse count;
- all previously failed references from the rejected SpaRV candidate are present
  in this source where this edition includes them.

## Generated artifact

- **Format:** Omni Text pack v1 (`content.db` + `manifest.json` ZIP)
- **Pack SHA-256:** `0d42d2d17ed1abb60482bb5dc80442cbf19eccf6b7382d0048b91f87d7acee78`
- **Pack size:** 4,985,759 bytes
- **Release URL:** GitHub Releases only; never a mutable branch URL.
