# v0.1 release gate

Goal: a local-first, installable knowledge commons prototype, with manually configured peer replication. Not a claim of internet-scale decentralization or authoritative truth.

- [x] Content-addressed records, signing, SQLite and explicit bundle exchange implemented.
- [x] Loopback peer server and explicit pulls implemented.
- [x] Implement signed browser integration and protected write actions (verification pending).
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
