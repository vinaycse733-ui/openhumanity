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

### Independent SDK and source excerpt utility
- Implemented trust_sdk.verify_report to validate signed envelopes, expected claim IDs, evidence relationships, duplicate entries and caller-controlled trust, recomputing all report summaries. Completeness and truth remain undetermined.
- Implemented detached check_excerpt for exact UTF-8 quotations, SHA-256 and optional expected digest, bounded to 8 MiB. No URL retrieval, source authenticity check or signed snapshot linkage yet.
- Linux Python environment with cryptography 46.0.4: ran the complete 52-test suite successfully. Built a wheel without dependency downloads using available build tools, installed it to a separate target, and reran all 52 tests outside the source directory successfully. New SDK, test and packaging Git blob hashes matched committed versions: 13393ac23892799f6b361dbad9b9c17c89698168, 3f46ce6106d214186a763dd2a4873702f16582fa and 5181c7cdd825e2a9afde4a2283f22248d5da75b3. Existing Python files matched prior fetched hashes. Clean dependency resolution, actual browser compatibility and cross-platform CI remain unverified.
- Next: signed source-snapshot linkage, evidence authoring UI, reference AI integration. No public deployment or paid services.

### Signed snapshot binding
- Added v3 evidence with one source and signed SHA-256 source digest; retained v1/v2 compatibility in upgraded nodes. Local CLI verifies exact UTF-8 excerpts before signing snapshot evidence. SDK independently verifies signatures, digest and excerpt; reports carry the digest. Source bytes are not stored or exchanged.
- Ran all 60 tests locally (cryptography 46.0.4), including eight snapshot tests. All six modified/new Python blob hashes matched committed files. Built wheel with existing tools and no dependency download; all 60 tests also passed against installed wheel in a separate directory. Manual CLI round trip with test passphrase input patched succeeded: encrypted identity, claim, snapshot evidence, JSON report, independent snapshot verification.
- Remaining: browser evidence authoring, reference AI integration, independent source authentication, clean dependencies, cross-platform CI and browser checks. No public deployment.

### Browser authoring and verified local client
- Added browser-based v2 evidence submission with existing signing key, validated target/relation and CSRF protection; reject duplicate form fields and ambiguous request framing. Source-file fingerprint evidence remains a CLI workflow.
- Added trust_client.fetch_verified_report and openhumanity-client entry point. Local-only fixed URL shape, no proxy/redirect, bounded response, independently verified report. No model-provider calls, and no source URL retrieval.
- Re-ran 60 baseline tests, 63 tests after browser changes, and all 66 tests after client changes in the Linux environment with cryptography 46.0.4. Built and installed wheel with existing build tools and dependencies; all 66 tests passed outside the source tree. Client help entry point module smoke check passed. All five changed/new code and packaging blob hashes matched the committed versions. New tests use actual local HTTP servers and signed SQLite records.
- Remaining: reference integration with an actual model, independent source authentication, browser rendering, fresh dependency installation, cross-platform CI and public-release review. Private repo retained; no external services or paid infrastructure.

### Optional local model adapter
- Added trust_model.ask_local and openhumanity-ask command, targeting a caller-selected model name and fixed loopback Ollama-compatible endpoint. Fetches verified evidence, sends bounded JSON context without tools, validates completion and evidence citation IDs, labels model output not fact-checked. No actual source entailment or prompt-injection immunity is claimed.
- Executed baseline 66 tests, then all 71 tests with five new model-adapter tests on Linux Python 3.13.5, cryptography 46.0.4. Built wheel offline with existing build tools, installed to a separate target and ran all 71 tests outside the source tree; module help smoke test passed. All three changed/new package and code blob hashes matched GitHub: 589d054f7d988b190e05987cbe10896d97977c0e, 2cb5e76b2c7db5e343856e2af6b437afde8f6cfb, 245956fb7997342b557e42160eed24893b6f8efb.
- Model tests use actual local HTTP transport and signed SQLite evidence, but a deterministic response fixture for the model endpoint. Ollama executable/model weights were not present; real inference and model behavior evaluation remain unverified. No downloads or cloud model calls were made. A loopback runtime could itself forward data externally; use only a trusted local-only runtime. Other outstanding blockers: independent source authentication, cross-platform CI, browser compatibility and licensing/security review.

### Optional model adapter
- Added ai_adapter.py with fixed loopback Ollama chat endpoint, no redirects or proxies, bounded JSON request/response, citation ID validation and explicit unverified model output. The caller must configure a trusted local-only runtime; forwarding by that runtime is outside the adapter's control.
- Executed seven new adapter tests using Python 3.13.5 and a real loopback HTTP test server that returns predetermined responses (not AI inference). All seven passed. Git blob hashes exactly matched committed adapter and test files: 3eb3c8e802f4ccf9122d44069252ce3b8a26ee97 and e8e4dc76e958f24a5ed3dbd731c9552f23b0c2ee.
- No Ollama executable or model weights found in the execution environment. Real model inference, model-specific context limits and injection resistance remain unverified. Full regression suite and package installation were not rerun in this iteration. Earlier full-suite counts are recorded historical results, not fresh verification. Updated packaging and CI smoke-check configuration; CI status not verified. No public deployment or paid services.

### Model response evidence coverage
- Model adapter now preserves the entire independently verified evidence index, marks cited and uncited evidence by relation, and reports whether both supporting and contradicting records exist. The generated answer cannot suppress those separate fields. No entailment or factual verdict is inferred.
- Full source and separately installed wheel suites each passed 73 tests on Linux Python 3.13.5 with cryptography 46.0.4. Both modified Python blob hashes match tested copies: 384f6f3d38911f12818b933f745f46caf729ee1e and 9916a352ed23332833b0c81b35fc2d723691fc41. Wheel built offline using existing dependencies. Two added tests check omitted and cited disagreement. Actual model inference remains unverified; no Ollama runtime or weights available. Cross-platform CI, source authenticity and browser compatibility remain outstanding.

### Reconciled local model adapters and packaging
- Inspected the latest main branch, which already contained two optional Ollama-compatible adapters and a packaging mismatch: openhumanity-ai was declared but ai_adapter was absent from py-modules. Fixed the missing module without removing either CLI.
- Hardened trust_model to reject truncated completions, wrong message roles, tool calls and unexpected answer fields. Preserved explicit visibility of uncited conflicting evidence. Added three regression tests.
- Actually executed `python -m unittest discover -s tests -v` with Python 3.13.5 and cryptography 46.0.4: 83 tests passed. Built wheel using `pip wheel . --no-deps --no-build-isolation`, installed to a separate target, ran all 83 tests from outside the source tree, and executed both installed AI CLI help commands successfully. Changed local file Git hashes exactly matched returned committed blobs: 074727d7a802521a29fe2005e314b3c9a581dae1 (pyproject), f48949258ea923744fa6868cfff70cd00d35a17e (trust_model), 65473fbf6aef2699b4a04ddeee3c2d35d0223941 (model tests).
- Ollama executable and downloaded model weights were not present in this environment; these tests use controlled HTTP fixtures, not real model inference. No external model was downloaded or invoked. Fresh dependency resolution, cross-platform CI, browser rendering, factual/source authentication and public-release licensing/security checks remain pending.

### Consistent evidence visibility across both model adapters
- Updated the alternate ai_adapter command to reject empty citations when evidence exists and preserve cited/uncited evidence and conflict indicators separately from model prose. Added two tests.
- Executed all 85 source and separately installed wheel tests on Linux Python 3.13.5 with cryptography 46.0.4; all seven installed CLI help checks passed. Wheel built with existing build tools, no dependency downloads. Changed tested Git blob hashes matched committed files: 4c7a227e3796f80dc3d33656d3f9583babe71790 and f62aacbb50b22c24ad7f02f5a15931d949855672.
- Actual model inference remains unverified: no Ollama executable or model weights. HTTP fixtures are not model inference. No public deployment or paid services.
