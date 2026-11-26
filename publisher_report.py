"""Combine independently verified evidence with caller-supplied publisher proofs."""
from openhumanity import RELATIONS
from trust_sdk import verify_report, MAX_SNAPSHOT_BYTES
from publisher_policy import PublisherPolicy

MAX_TOTAL_SNAPSHOT_BYTES = 32 * 1024 * 1024


def verify_with_publishers(payload, expected_claim_id, policy, proofs, trusted_keys=()):
    """Rebuild report and annotate publisher proof status without dropping evidence.

    proofs maps evidence IDs to (snapshot bytes, detached publisher attestation).
    The policy and proofs are supplied explicitly by the caller, never by the
    report producer. Invalid supplied proofs reject the entire request.
    """
    if not isinstance(policy, PublisherPolicy):
        raise ValueError('expected a local publisher policy')
    if not isinstance(proofs, dict) or len(proofs) > 100:
        raise ValueError('expected at most 100 publisher proofs')
    verified = verify_report(payload, expected_claim_id, trusted_keys)
    ids = {entry['id'] for group in verified['evidence'].values() for entry in group}
    if not set(proofs).issubset(ids):
        raise ValueError('publisher proof does not belong to this report')
    total = 0
    for proof in proofs.values():
        if not isinstance(proof, tuple) or len(proof) != 2 or not isinstance(proof[0], bytes):
            raise ValueError('expected snapshot bytes and attestation tuple')
        total += len(proof[0])
        if len(proof[0]) > MAX_SNAPSHOT_BYTES or total > MAX_TOTAL_SNAPSHOT_BYTES:
            raise ValueError('publisher proof exceeds snapshot budget')
    envelopes = {(entry['envelope']['record']['id'], entry['envelope']['public_key']): entry['envelope']
                 for group in payload['evidence'].values() for entry in group}
    counts = {}
    for relation in RELATIONS:
        authenticated = set()
        for entry in verified['evidence'][relation]:
            evidence_id = entry['id']
            if evidence_id not in proofs:
                entry['publisher_status'] = 'proof_not_supplied'
                continue
            snapshot, attestation = proofs[evidence_id]
            if entry['snapshot_sha256'] is None:
                raise ValueError('publisher proof requires signed snapshot evidence')
            result = policy.verify(envelopes[(evidence_id, entry['signer'])], snapshot,
                                   attestation, entry['sources'][0])
            entry['publisher_status'] = 'verified_against_local_policy'
            entry['publisher_verification'] = result['publisher']
            authenticated.add(evidence_id)
        counts[relation] = len(authenticated)
    verified['publisher_verified_counts'] = counts
    verified['publisher_verification_scope'] = 'caller_supplied_proofs_and_local_policy_only'
    return verified
