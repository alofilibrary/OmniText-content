# Tanakh — Santa Biblia libre para el mundo (Spanish)

- **Pack ID:** `judaism-tanakh-spablm-es`
- **Version:** 1
- **Status:** published
- **Language:** Spanish (`es`)
- **Source edition:** *Santa Biblia libre para el mundo*, Hebrew-Bible corpus only
- **Source repository:** <https://github.com/kahunapule/spablm>
- **Pinned source commit:** `a741e2b6de48f8c08bab9e003bc4ae8f291bf99f`
- **Acquisition format:** eBible USFM ZIP: <https://eBible.org/Scriptures/spablm_usfm.zip>
- **License evidence:** the source repository's [`LICENSE`](https://github.com/kahunapule/spablm/blob/main/LICENSE) is CC0 1.0; eBible lists the edition as Public Domain.
- **Attribution:** Santa Biblia libre para el mundo, David Williams & Michael Paul Johnson, CC0 1.0.
- **Scope:** the 39 Hebrew-Bible books (USFM files 02–40). New Testament and deuterocanonical books are deliberately excluded.

## Validation

`tools/build_spablm_tanakh.py` rejects replacement characters and empty verses,
requires all 39 intended books, builds the FTS index, and requires its count to
match the inserted verse count.

- **Verse count:** 23,145
- **Pack SHA-256:** `3096e8f0278d0bdc1c5de756d3643e2b7216f1be38c7bdfae671505f6b618ce6`
- **Pack size:** 4,806,507 bytes

The pack is published as the immutable GitHub Release asset
[`judaism-tanakh-spablm-es-v1.otpack`](https://github.com/alofilibrary/OmniText-content/releases/download/tanakh-spablm-es-v1/judaism-tanakh-spablm-es-v1.otpack).
GitHub reports the same SHA-256 digest shown above for the uploaded asset.
