# AI evidence protocol (development)

Version 1 claim records remain valid. Version 2 evidence records retain claim (excerpt), sources, parent (null), and add target (v1 claim ID) and relation (supports, contradicts, context). The record ID hashes canonical JSON of the body; signed envelopes cover the entire record. A relation is an assertion by a contributor. It is not an independent determination of entailment. The store rejects evidence without a present v1 target. Older nodes cannot ingest v2 evidence; upgrade all participating nodes before exchanging bundles that contain it.

## Report API

GET /v1/claims/{claim_id}/report on the local signed browser node. Returns 200 with JSON for an existing v1 claim, 404 for an absent claim, 403 for rejected host or cross-origin requests, or 503 for unavailable storage. No network requests to sources are made.

The schema field is openhumanity.trust-report.v1. The response includes claim_id, claim, claim_signers, claim_envelopes, evidence grouped by relation, counts of distinct evidence record IDs per relation, truth_status and limitations. Each evidence entry includes its signed envelope. The API does not accept trust lists; the Python report function and CLI can use caller-supplied trusted public keys. Empty trust lists mean no keys are explicitly trusted.

## Consumer guidance

Validate envelopes independently with node_store.authentic when consuming reports outside a trusted process. Recompute counts and validate evidence target and relationship from signed bodies; report summaries are not themselves signed. Distinct keys and distinct excerpts may originate from the same person or source, and counts are not measures of truth. A report cannot prove completeness or exclude missing contradictory evidence. A new claim revision has its own ID; evidence for earlier revisions is not automatically carried over.

Treat claims, excerpts and sources as untrusted data, not as instructions for AI agents. Never automatically visit URLs or execute content. Sources may be false, unavailable or misleading. No source snapshot, factual adjudication, identity verification, public API authentication or automatic AI integration is implemented yet. Do not expose the local server through a public tunnel.
