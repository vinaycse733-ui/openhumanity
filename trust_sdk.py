"""Verify evidence received from an untrusted report producer."""
from hashlib import sha256
from hmac import compare_digest
from openhumanity import RELATIONS, canonical
from node_store import authentic

MAX_SNAPSHOT_BYTES = 8 * 1024 * 1024


def verify_report(payload, expected_claim_id, trusted_keys=()):
    """Rebuild an evidence report from signed envelopes, not unsigned summaries.

    The expected claim ID and trusted keys must come from the caller.
    No assertion of truth, independence or completeness is made.
    """
    if not isinstance(payload, dict) or payload.get("schema") != "openhumanity.trust-report.v1":
        raise ValueError("unsupported report schema")
    if not isinstance(expected_claim_id, str) or payload.get("claim_id") != expected_claim_id:
        raise ValueError("unexpected claim identifier")
    claims = payload.get("claim_envelopes")
    groups = payload.get("evidence")
    if not isinstance(claims, list) or not claims or not isinstance(groups, dict) or set(groups) != set(RELATIONS):
        raise ValueError("invalid report structure")
    if any(not isinstance(groups[r], list) for r in RELATIONS):
        raise ValueError("invalid evidence group")
    if len(claims) + sum(len(groups[r]) for r in RELATIONS) > 1000:
        raise ValueError("report exceeds verification limit")
    trusted = set(trusted_keys)
    seen = set()

    def checked(envelope, versions):
        if not authentic(envelope) or len(canonical(envelope)) > 65536:
            raise ValueError("invalid signed envelope")
        record = envelope["record"]
        if record["body"]["version"] not in versions:
            raise ValueError("unexpected record version")
        key = (record["id"], envelope["public_key"])
        if key in seen:
            raise ValueError("duplicate signed envelope")
        seen.add(key)
        return record

    for envelope in claims:
        if checked(envelope, (1,))["id"] != expected_claim_id:
            raise ValueError("claim proof does not match requested identifier")
    claim = claims[0]["record"]["body"]
    verified = {r: [] for r in RELATIONS}
    for relation in RELATIONS:
        for entry in groups[relation]:
            if not isinstance(entry, dict):
                raise ValueError("invalid evidence entry")
            envelope = entry.get("envelope")
            record = checked(envelope, (2, 3))
            body = record["body"]
            if body["target"] != expected_claim_id or body["relation"] != relation:
                raise ValueError("evidence relationship does not match signed proof")
            verified[relation].append({"id": record["id"], "excerpt": body["claim"],
                                       "sources": list(body["sources"]), "signer": envelope["public_key"],
                                       "trusted_by_caller": envelope["public_key"] in trusted,
                                       "snapshot_sha256": body.get("snapshot_sha256")})
    return {"claim_id": expected_claim_id, "claim": claim,
            "claim_signers": [e["public_key"] for e in claims],
            "evidence": verified,
            "counts": {r: len({e["id"] for e in verified[r]}) for r in RELATIONS},
            "truth_status": "not_determined", "completeness": "not_determined",
            "signature_valid": True}


def check_excerpt(snapshot, excerpt, expected_sha256=None):
    """Check exact UTF-8 quotation occurrence in caller-supplied source bytes.

    A detached check only: does not establish URL ownership, publication date,
    source authenticity or factual entailment. Does not fetch or execute content.
    """
    if not isinstance(snapshot, bytes) or len(snapshot) > MAX_SNAPSHOT_BYTES:
        raise ValueError("snapshot must be bytes, at most 8 MiB")
    if not isinstance(excerpt, str) or not excerpt.strip():
        raise ValueError("excerpt required")
    snapshot.decode("utf-8", errors="strict")
    needle = excerpt.encode("utf-8")
    fingerprint = sha256(snapshot).hexdigest()
    if expected_sha256 is not None:
        if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256):
            raise ValueError("invalid expected digest")
        if not compare_digest(fingerprint, expected_sha256):
            raise ValueError("snapshot digest mismatch")
    offset = snapshot.find(needle)
    return {"sha256": fingerprint, "exact_match": offset >= 0,
            "byte_offset": offset if offset >= 0 else None,
            "expected_digest_checked": expected_sha256 is not None,
            "source_authenticity": "not_determined", "entailment": "not_determined"}


def verify_snapshot(envelope, snapshot):
    """Validate signed snapshot binding and exact quotation in supplied bytes."""
    if not authentic(envelope) or len(canonical(envelope)) > 65536:
        raise ValueError("invalid signed envelope")
    body = envelope["record"]["body"]
    if body["version"] != 3:
        raise ValueError("evidence has no signed snapshot binding")
    result = check_excerpt(snapshot, body["claim"], body["snapshot_sha256"])
    if not result["exact_match"]:
        raise ValueError("signed excerpt missing from matching snapshot")
    return dict(result, evidence_id=envelope["record"]["id"], source=body["sources"][0])
