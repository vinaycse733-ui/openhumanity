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
- [x] Add evidence authoring UI and signed source snapshot/quotation provenance checks (publisher proofs via CLI).
- [x] Implement report-verifying developer SDK and local AI adapters; treat supplied text as untrusted data. Real inference remains a separate unverified gate.
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

### Model integration packaging and live smoke check
- Fixed wheel manifest to include both AI adapters and the new live_model_smoke module. Both adapters preserve cited/uncited evidence separately from generated answers and require citations when evidence is present. Removed redundant coverage logic and duplicate tests after inspecting fetched files.
- Executed `python -m unittest discover -s tests` in Linux Python 3.13.5 with cryptography 46.0.4: 85 tests passed. Built wheel offline with existing build tools and installed it to a separate target; 85 tests passed against the installed package. Installed `openhumanity-ai --help` and `openhumanity-model-smoke --help` succeeded. Changed source/test/packaging hashes matched GitHub: ai_adapter.py 4e6b38632ab86a80846d81009cea47cb6f4a8c9a; tests/test_ai_adapter.py 671bb626a949607832cfcd2c04d876d102e46c66; live_model_smoke.py 05f246e9b32679dc36e31307bf474b8f12365a5b; pyproject.toml 7e08e82d7cdba00e9248517978be1814f14f279a.
- Actual smoke command attempted on loopback port 11434: signed synthetic evidence HTTP retrieval returned 200; model connection failed explicitly with Errno 111 Connection refused. Ollama executable and local model weights not found. No real inference, model download or cloud calls. CI smoke checks configured, not verified. Remaining: real model inference/evaluation, browser and cross-platform verification, source authenticity and public release review.

### Model integration packaging correction and smoke verification
- Latest repository metadata exposed openhumanity-model-smoke without including its Python module in the wheel. Corrected the module list and removed duplicated evidence-coverage computation in ai_adapter. Added a synthetic smoke workflow test and CI help check.
- Actual Linux container run: Python 3.13.5, cryptography 46.0.4, `python -m unittest discover -s tests`: 86 tests passed (7.676 s). Built wheel with --no-deps --no-build-isolation, installed separately, reran 86 tests outside the source tree (7.808 s), and executed the installed smoke entry point --help successfully. Changed code/package/test blob hashes match committed versions 4e6b38632ab86a80846d81009cea47cb6f4a8c9a, 7e08e82d7cdba00e9248517978be1814f14f279a and 07840399a8e4bd95faece645e0ad9c99033339e7. Controlled HTTP fixture is not an AI model.
- Actual smoke invocation reached the synthetic knowledge node (HTTP 200) but failed connecting to local model port 11434 with connection refused. Ollama executable not found. No real inference, source authenticity, fresh dependency resolution, browser rendering or cross-platform CI is claimed. No model downloaded or cloud provider called.

### Pinned publisher attestation
- Added source_auth SDK with domain-separated Ed25519 attestations for exact HTTPS source identifiers and UTF-8 source fingerprints. Combined verification checks both contributor evidence and independently pinned publisher key. No automatic source retrieval, key discovery, identity verification, revocation or freshness guarantees.
- Actual container tests: Python 3.13.5, cryptography 46.0.4; 94 tests passed from source (7.868 s) and against separately installed wheel (7.893 s). Built without dependency download or isolated build dependency resolution. Existing 26 source/test/package files were checked against fetched repository blob hashes before changes. New source, test and package blob hashes match committed versions 66a40a13be6316d4bc7da61989f8b8c6e4fd6b61, 7753d4395c9702fa5810461bfe836819e29fa61c and 98a1651df4a9c5be746b52a9d433a0b5fe2d7cb4. Combined commit status returned no status entries; CI still unverified.
- Remaining: actual model inference, publisher integration with real cooperating sources, publisher trust policy and revocation, browser and cross-platform verification, fresh dependencies and public-release review. No public deployment or paid infrastructure.

### Local publisher trust policy
- Added bounded local JSON publisher policy, exact source-specific key pins, fail-closed defaults, revocation overriding pins and manual rotation. Input mutations cannot change loaded policy collections. Duplicate JSON fields rejected. Policy is not a distributed revocation registry and must be protected against unauthorized modification or rollback.
- Local Python 3.13.5 / cryptography 46.0.4: 102 tests passed (7.400 s); built wheel with existing dependencies and no dependency downloads, installed separately and ran all 102 tests outside source tree (7.107 s). New policy, tests and pyproject blob hashes match committed files e2016b1766cc3b5d2f344a2252f330076141d047, 06eff999bc701d222b509dfc78b73e95a0821197 and b67734c722bbd900f8cafbd70d243ab6d4e14d69.
- Actual publisher integration, real model inference, browser compatibility, clean dependency resolution and cross-platform CI remain unverified. No public deployment or paid services.

### Publisher-enriched evidence reports
- Added independent publisher_report SDK with caller-supplied proofs, explicit local publisher policy, bounded snapshot bytes, fail-closed invalid proof handling and preservation of all relationships when proofs are missing. Recomputes publisher-authenticated record counts and ignores unsigned producer status.
- Actual local container execution: Python 3.13.5 / cryptography 46.0.4; 109 tests passed from source (6.733 s). Built with --no-deps --no-build-isolation, installed wheel into separate directory and reran all 109 tests outside source (5.769 s). Changed source, test and packaging blob hashes matched repository c81169e0b25a1ad138126798f80cbcc3fccf459d, 62952ea724603eb04581ceb8119fb6fdb171c062 and f75bced13638465ad7a860150138c9683cab3fda. Used previous local baseline; did not re-fetch every unchanged source file in this iteration.
- Remaining: automatic model adapter integration with explicitly provided proofs, actual model inference and cooperating publisher integration, browser and cross-platform testing, dependency resolution and release review. No public deployment.

### Model proof integration and evidence review UI
- Connected optional explicitly selected publisher policies and proof files to both local model adapters and the verified report client. Proof validation occurs before model requests, with bounded files and duplicate-ID rejection. Existing behavior is preserved without proofs; output distinguishes publisher-authenticated evidence and preserves disagreements.
- Added local HTML evidence review with grouped relationships, disagreement notice, escaped text, source fingerprints and keyboard-focus styles. Browser does not claim publisher verification.
- Executed actual Linux tests: 113 passed after proof integration (7.859 s), 114 passed after review UI (6.700 s); built wheel without fresh dependency resolution, installed separately and reran 114 tests outside source directory (7.718 s). Verified changed code/test Git blob hashes match committed files. Installed ask CLI help exposes proof options. Model tests use fixtures, not actual inference. Real browser rendering and accessibility audit, cross-platform CI, fresh dependency installation and real publisher onboarding remain unverified. Ollama executable still unavailable.
- Freeze expansion until release verification. Prioritize clean supported install, independently verified CI, permitted browser interaction and actual local model smoke test. Do not publish, spend money or claim production readiness without evidence.

### Publisher-aware model integration and evidence review reconciliation
- Inspected current main: both model adapters and local client already accept explicit publisher policy and proof files; an evidence review page groups supporting, contradictory and contextual evidence. Reconciled local working copies with latest fetched changed-file Git hashes, including the alternate adapter, browser page, publisher model tests and packaging. Re-ran 114 tests (8.419 s), then applied consistent origin/fetch-site restrictions to all local GET routes, including root; new regression exercises all three routes. Actual local Python 3.13.5 / cryptography 46.0.4 execution: 115 tests passed (6.038 s); built and installed wheel without dependency downloads and ran 115 tests outside source (8.279 s). All eight installed entry-point help checks succeeded. New tested hashes match GitHub blobs c10428d35eca34aac2608293f0b33c586d0f514b and 53b021ebfe7bf907527167ddf0ec484fa53ada56. Reused existing baseline for unchanged files, not a complete fresh clone. Model tests are HTTP fixtures, not actual inference.
- Remaining release gates: actual local-model inference, cooperating publisher with independently obtained pins, real browser interaction, clean supported dependency resolution, cross-platform CI evidence, security/licensing review. No public release, spend or model download.

### Release audit: packaging, licensing and external verification
- Existing repository LICENSE is MIT (blob 2524249dc9e3da0884479dae956fb29c3b94a9d1); retained its exact bytes and copyright notice. Updated packaging description and declared the existing license. Built a wheel and verified the embedded LICENSE exactly matched the repository and metadata identified it. Tested pyproject blob 5c1b2bdc8f0c11cd955522564f133d0c59a31b37 matches committed file. Installed dependency metadata: cryptography 46.0.4 Apache-2.0 OR BSD-3-Clause, cffi 2.0.0 MIT, pycparser 3.0 BSD-3-Clause. This is a preliminary metadata inventory, not a complete third-party binary/license or legal audit.
- Local Python 3.13.5 with existing dependencies: 115 tests passed from source (7.085 s), and 115 passed against separately installed wheel (7.411 s). Wheel built with --no-deps --no-build-isolation. Reused prior verified local source tree. Fresh venv installation actually attempted; build dependency resolution failed because the package index could not be resolved (temporary failure in name resolution; setuptools>=68 unavailable). No successful fresh dependency install claimed.
- GitHub combined status contained no entries and the available PR-filtered workflow runs query returned no runs for d28b47aa085650c8ee7872ac36395cb42fe62c3d. These results cannot verify push-triggered cross-platform CI. Removed redundant CLI smoke check in workflow; updated SECURITY.md for model and publisher trust boundaries. Actual model inference, external publisher onboarding, browser rendering, clean dependencies and full independent release security/licensing review remain open. No public deployment or spend.

### Manual development: signed request framing and form validation
- Reproduced a concrete defect in the local browser server: a truncated request body, invalid UTF-8 percent-encoded form data, malformed percent escapes and unexpected fields could receive HTTP 303 and persist signed records. Added two regression tests; the pre-fix run failed in five assertions.
- Fixed exact body-length checks, strict percent and UTF-8 decoding, strict form parsing and route-specific field allowlists. Full source suite: 117 tests passed in 8.400 s. Built and separately installed wheel without dependency downloads; installed-package suite outside source tree: 117 tests passed in 5.356 s. Tested blob hashes match committed node_web.py a773c88c59689dd542f168f5f84371fc25ade438 and tests/test_node_web.py 0688aa47ce6ec54e0e447a877a54ad8591635d00. Used existing Linux Python 3.13.5 environment and previous audited source baseline.
- Hourly automation disabled at owner's request. Development is manual. Previous external release gates remain unresolved; no public deployment or spend.

### Manual development: CLI export privacy and missing-database protection
- Reproduced three failing assertions in two new regression tests: missing database search/export created empty databases, and an exported JSON bundle had mode 0666 under a permissive POSIX umask. Read-only search/export now reject missing database paths; exports use exclusive file creation requesting mode 0600. Existing files are not overwritten. Windows ACL protection is not established by the POSIX test.
- Local source suite: 119 tests passed in 6.364 s. Built a wheel using --no-deps --no-build-isolation, installed in a separate target, and ran all 119 tests outside the source tree in 6.522 s. Used previously verified local source baseline. Changed source and test blobs match committed Git hashes ce844c450289baf7d4973096fbf80fe39b464078 and 0680d7983332674ee225530fb99cb0ed7067267f.
- External release gates remain open: actual AI inference, fresh dependency resolution, browser compatibility, cross-platform CI and independent security review. Scheduled development remains disabled; no public deployment or spending.

### Manual development: database file privacy and canonical integrity
- Reproduced three failing regression tests: new SQLite databases used mode 0644 under permissive POSIX umask; noncanonical stored envelopes and oversized signed records bypassed read validation. New databases now request exclusive creation with mode 0600, without changing existing file permissions. Reads enforce canonical serialization and 65536-byte envelope limit. SQLite connection closes on schema initialization failure.
- Actual Linux Python 3.13.5 source run: 122 tests passed (7.846 s). Built wheel using --no-deps --no-build-isolation, installed separately, and ran all 122 tests outside source tree (7.938 s). Used previous tested baseline. New file hashes matched committed Git blobs cced5c61f6f029f1060c116ef3d4273af0441d6e and c4f71ef0e13efc92f65e3c69443a6ad5e7fa36a0.
- Existing databases still need independently restricted permissions; Windows ACLs are not established by POSIX tests. Database contents remain unencrypted. Noncanonical stored rows manually modified outside the application now fail validation. Remaining external gates unchanged: real model inference, clean dependency installation, browser and cross-platform checks, independent review. Scheduled task remains disabled; no public deployment or spend.

### Manual development: read-only diagnostics and backup validation
- Reproduced acceptance and mutation of empty or unrelated SQLite files by doctor/search/export/backup. Added read-only Store mode with encoded file URI and expected records-table schema checks. CLI read commands and verification of the backup copy now use that mode; write commands retain existing initialization behavior.
- Actual local execution using prior verified baseline: 124 source tests passed (7.279 s), rebuilt wheel and installed separately without dependency downloads, 124 installed-package tests passed (6.873 s). New source and test file hashes match GitHub blobs 8f25b55e312e28e99a6c65a83dc56b75f84c86f3, 0817efc5530fa7f1b0cc8dd9f8fb799cc3f98931, bfcf60985ffa62938214471626fd586c721ef33f and 12b0ed5b44ce5b70db086bde418a0506d7dfdca1. Schema checking is not full tamper-proofing; existing signed record integrity checks remain necessary.
- Real model inference, clean dependency resolution, browser and cross-platform verification and independent security review remain open. Scheduled automation remains disabled; no deployment or spend.
