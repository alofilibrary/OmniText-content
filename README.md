# Omni Text Content

Curated, versioned text packs for the [Omni Text](../OmniText) Android reader.

The Android app is useful without a network connection. On first run, a reader
chooses starter editions to download; every installed pack then works offline.
The catalog stays visible even without a connection, while downloading and
checking for updates are deliberate network actions.

## What belongs here

- `catalog/catalog.json` — the reviewed catalogue metadata embedded in the app
  and published with each catalog release.
- `packs/` — release-ready Omni Text SQLite packs, published only through GitHub
  Releases; never mutable branch URLs.
- `provenance/` — review records that establish a pack's rights, exact upstream
  commit/source, attribution, checksum, and reviewer decision.

## Non-negotiable content policy

A repository license for a converter or dataset collection does **not**
automatically license every text inside it. A pack may be published only when
its exact edition has a documented commercial redistribution grant, required
attribution, immutable upstream reference, and independently verified SHA-256.

Texts are free to download. Omni Text may charge only for its separate study
tools; it never sells access to sacred texts.

## Release contract

The app accepts only catalog entries whose `status` is `published` and whose
pack URL, SHA-256, schema version, license, and attribution are present. Draft
records exist for review only and must never be offered to readers.
