# v0.1 release gate

Goal: a local-first, installable knowledge commons prototype, with manually configured peer replication. Not a claim of internet-scale decentralization or authoritative truth.

- [x] Content-addressed records, signing, SQLite and explicit bundle exchange implemented.
- [x] Loopback peer server and explicit pulls implemented.
- [x] Implement signed browser integration and protected write actions (HTTP tests pass; real browser verification blocked).
- [ ] Verify protocol, node, peer and browser tests on clean installations.
- [ ] Resolve size limits, error handling and key management issues found during testing.
- [x] Document threat model, backup/recovery, sharing boundaries, trust and installation (README.md and SECURITY.md).
- [ ] Confirm reproducible release instructions and review licensing before public release.

Do not mark verification complete without actual execution evidence. Keep repository private; never deploy or spend money without separate authorization. Manual replication is sufficient for v0.1; discovery, moderation, scalable sync and multilingual UI are later releases.

## Verification log
- Browser request and publishing integration tests exist, including invalid token and host rejection.
- CI combined commit status returned no statuses; this is not evidence of passing tests.
- Next: run the entire suite on a clean Python installation, verify signing and peer exchange end-to-end, and address failures before tagging a release.

### Local execution evidence — 2026-11-26
- Linux, Python 3.13.5, cryptography 46.0.4 (existing environment, not a fresh install).
- Reconstructed the nine Python source/test files from commit df77b70964035eb27098601f4434d32766ddcb82 and checked each Git blob SHA. Added the CLI test whose blob SHA is 248ee1d61a99f41ab29dfb6f592432f04dd7ee04.
- `python -m unittest discover -s tests -v`: 16 tests ran, all passed. Includes actual loopback HTTP requests, signature validation, SQLite persistence and encrypted-key CLI bundle round trip. Passphrase input alone is mocked in the CLI test.
- Still required: clean installation on supported Python versions, GitHub Actions results, dependency and licensing review, actual browser compatibility and operational review. No public deployment yet.

### Protocol hardening
- Reproduced acceptance of boolean protocol version `true` on the previous implementation. Fixed strict integer version and canonical byte comparison.
- Executed all 10 core protocol tests successfully on Python 3.13.5. Verified the tested source and test Git blob hashes match committed versions `316819c49dac0e51d7a2ad2c1cb5548f4820f758` and `6651f3edce792ec6246d42d0dcf7e7f0324fd036`.
- Configured CI to test Python 3.11–3.13 across Linux, macOS and Windows; this matrix has not yet been verified as passing. Full suite must be rerun after the protocol changes.

### Storage integrity regression
- Revalidate persisted signed envelopes and check database identifiers against signed record and signer identifiers before returning records.
- Four additional tests cover valid reads, modified claims, mismatched database identifiers and malformed stored JSON.
- Local Linux Python 3.13.5 with cryptography 46.0.4: 24 tests ran, all passed. All 11 Python source/test blob SHA values matched the repository after committing the storage changes and tests.
- Remaining: graceful UI/network handling of detected storage corruption, clean installations and cross-platform CI, browser compatibility, dependency/licensing review. Revalidation detects modification, not deletion or rollback of otherwise valid records.

### v0.1.0rc1 — installable release candidate
- Browser and peer handlers now return HTTP 503 for corrupt storage; browser publishing checks existing record integrity before ingest. CLI export enforces the v0.1 import limits before creating a file.
- Two corruption HTTP regression tests added. Full source suite: 26/26 passed with Python 3.13.5 and cryptography 46.0.4. Changed Python file and test Git blob hashes matched the tested copies.
- Built a Python wheel from committed-equivalent source and pyproject.toml. Installed the wheel in a separate target directory, using existing cryptography 46.0.4, and reran all 26 tests outside the source tree successfully. All three installed CLI entry points also returned their help text in a separate virtual environment using preinstalled dependencies (that environment contained cryptography 43.0.0, outside the declared supported range, so it is not evidence of clean supported dependency installation).
- Chromium launched but navigation to the loopback server returned ERR_BLOCKED_BY_ADMINISTRATOR in the execution environment. Do not claim browser UI compatibility was verified.
- Remaining external checks: fresh dependency resolution, cross-platform CI, browser interaction on a permitted host and licensing/security review before public distribution. Current candidate is installable and locally tested; not production-ready or publicly deployed.

### Peer boundary hardening
- Peer endpoint rejects non-loopback and duplicate Host headers, and browser-origin or fetch-metadata requests. HTTP loopback pulls bypass configured proxies. Remote HTTPS pulls retain their previous proxy behavior; remote serving through a separately secured proxy remains untested.
- Executed five peer tests locally (Python 3.13.5, cryptography 46.0.4), all passed: four new HTTP boundary tests with test stores and the existing real signed-record SQLite exchange. Git hashes of all five tested source/test files match the committed blobs. Full regression suite not rerun in this iteration.
- Existing CI matrix now installs the package and executes tests outside the source directory plus entry-point smoke checks. CI execution results remain unverified.

### Revision integrity and diagnostics
- Imports validate existing signed records and revision dependencies inside a write transaction before adding new records. Missing revision parents now fail read verification. Added CLI `doctor` command for SQLite quick_check and signed graph validation.
- Linux Python 3.13.5 / cryptography 46.0.4: ran 12 tests (storage, integrity and CLI) in this session, all passed. Git blob hashes of all six executed Python files matched fetched or returned repository hashes. Full suite and cross-platform checks still pending after these changes.

### Backup and full regression
- Added exclusive-file SQLite backup with post-copy SQLite and signed graph verification, cleanup on verification failure, and missing database rejection for diagnostics and backup.
- Reassembled the full 13 Python source/test files from prior verified working copies. All Git blob hashes matched the latest committed Python files, including updated CLI and CLI test blobs `000290c13a04f9492afc70466ab721dbab552058` and `ebcade964a80457c988a2fa137414d73472a189c`.
- Ran `python -m unittest discover -s tests -v` in the Linux environment with cryptography 46.0.4. All 32 tests passed after backup changes (including backup round trip and overwrite/missing-database rejection). Cross-platform CI, clean dependency resolution and real browser checks remain unverified.

## v0.2 development direction — AI evidence layer
The scope now prioritizes model-independent evidence and provenance reports. Preserve existing v1 claim support; do not promise factual truth or completeness.

- [x] Signed v2 evidence records with supporting, contradicting and contextual relationships; validate claim targets during ingest and reads.
- [x] Python report function, CLI and local JSON report API with original signed envelopes for independent checks.
- [x] Browser distinguishes evidence from claims and links to reports; existing peer and backup exchange supports evidence on updated nodes.
- [x] Document protocol, limitations, compatibility and consumer guidance in TRUST_PROTOCOL.md.
- [ ] Add evidence authoring UI and source snapshot/quotation provenance checks.
- [ ] Add a report-verifying developer SDK and reference AI integration; treat supplied text as untrusted data.
- [ ] Clean supported dependency installation, cross-platform CI and real browser checks; review licensing/security before any public release.

### Execution evidence
On Linux with Python 3.13.5 and cryptography 46.0.4, all 41 tests passed in the source tree and against the installed v0.2.0.dev0 wheel outside the source tree. All 15 Python files and pyproject.toml matched fetched GitHub blob hashes. Wheel built with existing build tools, without dependency downloads; not proof of fresh dependency resolution. New tests include conflicting evidence, signature tampering, duplicate record counting, missing targets, peer bundle exchange, independent signed proof validation and actual local HTTP report retrieval/rejection. No AI-provider calls or external source validation performed. Browser rendering and cross-platform CI still unverified. Repository remains private.
