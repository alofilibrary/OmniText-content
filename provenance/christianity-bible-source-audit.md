# Christianity Bible source audit — 2026-09-25

## Scrollmapper BSB — rejected for this pinned snapshot

- **Repository:** <https://github.com/scrollmapper/bible_databases>
- **Commit:** `e1b254cef86d0e65b1a5d1a94b8b112d0f296a2c`
- **Candidate:** `sources/en/BSB/BSB.json` / `formats/sqlite/BSB.db`
- **Stated license:** CC0, recorded in `sources/en/BSB/README.md`

### Result

Do not build or publish an Omni Text pack from this snapshot.

The SQLite export contains 217,714 rows for 31,102 canonical references.
Some duplicate references differ in whitespace. More seriously, the canonical
JSON contains Unicode replacement characters (`U+FFFD`) in scripture text,
including Genesis 1:5. That means characters were already lost upstream.

A license-compatible source that has lost text fidelity is still unsuitable.

## Official Open English Bible — rejected as a full-Bible source at this pin

- **Repository:** <https://github.com/openenglishbible/Open-English-Bible>
- **Commit:** `1965127de5c3c103af3fdbc9288c1abec5f39994`
- **Stated license:** CC0-1.0

The official USFM release artifact contains 44 books; its development artifact
contains 59 books. Both fail Omni Text's complete 66-book / 31,102-verse Bible
validator. Keep OEB as a candidate only after an official complete release is
available or the maintainers identify the intended complete canonical export.
