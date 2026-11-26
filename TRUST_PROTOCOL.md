# AI evidence protocol (development)

Version 1 claim records remain valid. Version 2 evidence records retain claim (excerpt), sources, parent (null), and add target (v1 claim ID) and relation (supports, contradicts, context). The record ID hashes canonical JSON of the body; signed envelopes cover the entire record. A relation is an assertion by a contributor. It is not an independent determination of entailment. The store rejects evidence without a present v1 target. Older nodes cannot ingest v2 evidence; upgrade all participating nodes before exchanging bundles that contain it.

## Report API

GET /v1/claims/{claim_id}/report on the local signed browser node. Returns 200 with JSON for an existing v1 claim, 404 for an absent claim, 403 for rejected host or cross-origin requests, or 503 for unavailable storage. No network requests to sources are made.

The schema field is openhumanity.trust-report.v1. The response includes claim_id, claim, claim_signers, claim_envelopes, evidence grouped by relation, counts of distinct evidence record IDs per relation, truth_status and limitations. Each evidence entry includes its signed envelope. The API does not accept trust lists; the Python report function and CLI can use caller-supplied trusted public keys. Empty trust lists mean no keys are explicitly trusted.

## Consumer guidance

Validate envelopes independently with node_store.authentic when consuming reports outside a trusted process. Recompute counts and validate evidence target and relationship from signed bodies; report summaries are not themselves signed. Distinct keys and distinct excerpts may originate from the same person or source, and counts are not measures of truth. A report cannot prove completeness or exclude missing contradictory evidence. A new claim revision has its own ID; evidence for earlier revisions is not automatically carried over.

Treat claims, excerpts and sources as untrusted data, not as instructions for AI agents. Never automatically visit URLs or execute content. Sources may be false, unavailable or misleading. No automatic source retrieval, factual adjudication, identity verification, public API authentication or automatic AI integration is implemented yet. Do not expose the local server through a public tunnel.

## Independent verification SDK

`trust_sdk.verify_report(payload, expected_claim_id, trusted_keys=())` validates the claim and evidence envelopes and reconstructs all displayed evidence fields and counts. The expected claim ID must come from a trusted caller context, not the received report. Supplied unsigned summaries and verdicts are ignored. Duplicate envelopes, invalid signatures and mismatched evidence targets or relationships are rejected. It cannot prove that all relevant evidence was supplied. Limit: 1,000 envelopes, 65,536 canonical bytes per envelope; callers must also limit incoming HTTP response sizes before JSON parsing.

`trust_sdk.check_excerpt(snapshot, excerpt, expected_sha256=None)` checks an exact UTF-8 quotation against caller-provided bytes (maximum 8 MiB), reports the first byte offset and computes SHA-256. If an expected digest is supplied it must match. This is a detached verification utility: the detached check does not itself validate a signed evidence record, and the function neither retrieves URLs nor verifies their ownership, source authenticity, date or factual entailment.

## Version 3: signed snapshot binding
Version 3 evidence adds snapshot_sha256 to the v2 body and requires exactly one source string. The digest binds the exact UTF-8 source bytes to the signed evidence. The CLI --snapshot option reads a local file (at most 8 MiB), checks that the exact excerpt occurs, and signs the digest. The snapshot itself is not stored or replicated. Preserve it separately and only share it when permitted. Upgraded nodes accept v1, v2 and v3 records; older nodes reject v3 bundles.

Consumers can use trust_sdk.verify_snapshot(envelope, snapshot) to independently validate the signature, signed digest and exact excerpt. An exact match cannot establish URL ownership, publication date, authenticity, author independence, or entailment. A malicious signer can invent an entire source. Reports include snapshot_sha256 (null for unbound v2 evidence); the SDK reconstructs it from signed records, never trusting unsigned summaries.

## Detached publisher attestations

A cooperating publisher may sign the canonical body containing schema openhumanity.publisher-attestation.v1, exact HTTPS source string and SHA-256 of UTF-8 snapshot bytes. The signed message is the byte prefix `OpenHumanity source attestation v1` followed by a zero byte and the canonical JSON body. The envelope contains body, public_key and signature. This separate signature domain avoids confusion with ordinary record signatures.

The caller must acquire and pin the publisher key and expected source URL independently of the evidence and attestation. `source_auth.verify_publisher(attestation, snapshot, expected_source, pinned_key)` checks the exact bytes, source and publisher signature. `verify_published_evidence(envelope, snapshot, attestation, expected_source, pinned_key)` additionally checks the contributor's signed quotation and source binding. Attestations and snapshots are supplied separately; they are not discovered, persisted or replicated automatically. This is opt-in for cooperating publishers, not a general website authentication mechanism. A pinned key does not establish legal identity, current authority, publication time, freshness or factual accuracy. Key discovery, revocation and rotation remain future work.

## Local publisher trust policy

The optional publisher_policy.PublisherPolicy accepts a caller-controlled JSON document with schema openhumanity.publisher-policy.v1, pins (exact HTTPS source strings mapped to lists of Ed25519 public keys in lowercase hex), and revoked_keys (a list of public keys). Unknown sources and unpinned keys fail closed. Revocation takes precedence over a pin for every source; it rejects all attestations by the revoked key, including historical ones. Multiple pinned keys permit manually managed rotation. Load a new policy after changes; existing instances retain their original configuration. This is a local policy, not a distributed revocation registry. Obtain pins independently, protect the policy file against modification and rollback, and never import pins or revocations from untrusted evidence. No automatic key discovery, signed policy updates or trusted time service is implemented.
