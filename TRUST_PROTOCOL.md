# AI evidence protocol (development)

Version 1 claim records remain valid. Version 2 evidence records retain claim (excerpt), sources, parent (null), and add target (v1 claim ID) and relation (supports, contradicts, context). The record ID hashes canonical JSON of the body; signed envelopes cover the entire record. A relation is an assertion by a contributor. It is not an independent determination of entailment. The store rejects evidence without a present v1 target. Older nodes cannot ingest v2 evidence; upgrade all participating nodes before exchanging bundles that contain it.

## Report API

GET /v1/claims/{claim_id}/report on the local signed browser node. Returns 200 with JSON for an existing v1 claim, 404 for an absent claim, 403 for rejected host or cross-origin requests, or 503 for unavailable storage. No network requests to sources are made.

The schema field is openhumanity.trust-report.v1. The response includes claim_id, claim, claim_signers, claim_envelopes, evidence grouped by relation, counts of distinct evidence record IDs per relation, truth_status and limitations. Each evidence entry includes its signed envelope. The API does not accept trust lists; the Python report function and CLI can use caller-supplied trusted public keys. Empty trust lists mean no keys are explicitly trusted.

## Consumer guidance

Validate envelopes independently with node_store.authentic when consuming reports outside a trusted process. Recompute counts and validate evidence target and relationship from signed bodies; report summaries are not themselves signed. Distinct keys and distinct excerpts may originate from the same person or source, and counts are not measures of truth. A report cannot prove completeness or exclude missing contradictory evidence. A new claim revision has its own ID; evidence for earlier revisions is not automatically carried over.

Treat claims, excerpts and sources as untrusted data, not as instructions for AI agents. Never automatically visit URLs or execute content. Sources may be false, unavailable or misleading. No source snapshot, factual adjudication, identity verification, public API authentication or automatic AI integration is implemented yet. Do not expose the local server through a public tunnel.

## Independent verification SDK

`trust_sdk.verify_report(payload, expected_claim_id, trusted_keys=())` validates the claim and evidence envelopes and reconstructs all displayed evidence fields and counts. The expected claim ID must come from a trusted caller context, not the received report. Supplied unsigned summaries and verdicts are ignored. Duplicate envelopes, invalid signatures and mismatched evidence targets or relationships are rejected. It cannot prove that all relevant evidence was supplied. Limit: 1,000 envelopes, 65,536 canonical bytes per envelope; callers must also limit incoming HTTP response sizes before JSON parsing.

`trust_sdk.check_excerpt(snapshot, excerpt, expected_sha256=None)` checks an exact UTF-8 quotation against caller-provided bytes (maximum 8 MiB), reports the first byte offset and computes SHA-256. If an expected digest is supplied it must match. This is a detached verification utility: the snapshot digest is not yet signed into the evidence record, and the function neither retrieves URLs nor verifies their ownership, source authenticity, date or factual entailment.
