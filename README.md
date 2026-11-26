# OpenHumanity

Knowledge belongs to everyone.

An experimental knowledge commons with portable, source-backed claims and content-addressed revisions.

## Run locally

Clone this repository, then run `python -m http.server 8000 --bind 127.0.0.1` from its root. Open http://localhost:8000 in a browser. Python 3.11+ recommended. No third-party runtime dependencies.

## Features
- Create claims with sources and revision references.
- Search local records, export and import JSON.
- Verify SHA-256 fingerprints. Browser data stays in local storage; export backups regularly.

## Tests
`python -m unittest discover -s tests -v`

## Limitations
This is a local prototype, not a distributed network. Hashes detect changes relative to trusted identifiers, not truth or authorship. Do not enter sensitive personal information. Browser storage is not encrypted by this application. Browser compatibility and interoperability need further testing.

## Roadmap
1. Signed records and persistence
2. Peer replication and conflict handling
3. Source assessment and moderation
4. Accessibility and multilingual support

Private development repository; public release and licensing pending review.
