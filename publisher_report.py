"""Combine independently verified evidence with caller-supplied publisher proofs."""
import json
import re
from openhumanity import RELATIONS
from trust_sdk import verify_report, MAX_SNAPSHOT_BYTES
from publisher_policy import PublisherPolicy, _unique_object

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


def add_proof_arguments(parser):
    parser.add_argument("--publisher-policy", help="Trusted local policy JSON file")
    parser.add_argument("--publisher-proof", nargs=3, action="append", default=[],
                        metavar=("EVIDENCE_ID", "SNAPSHOT", "ATTESTATION"),
                        help="Explicit local proof files; repeat for additional evidence")


def load_proof_arguments(args):
    """Read only explicitly chosen files, never paths from evidence or model output."""
    if not args.publisher_policy:
        if args.publisher_proof:
            raise ValueError("publisher proofs require a trusted policy")
        return None, None
    policy = PublisherPolicy.load(args.publisher_policy)
    if len(args.publisher_proof) > 100:
        raise ValueError("too many publisher proofs")
    proofs = {}
    remaining = MAX_TOTAL_SNAPSHOT_BYTES
    for evidence_id, snapshot_file, attestation_file in args.publisher_proof:
        if not re.fullmatch(r"[0-9a-f]{64}", evidence_id) or evidence_id in proofs:
            raise ValueError("invalid or duplicate proof identifier")
        with open(snapshot_file, "rb") as handle:
            limit = min(MAX_SNAPSHOT_BYTES, remaining)
            snapshot = handle.read(limit + 1)
        if len(snapshot) > limit:
            raise ValueError("publisher proof exceeds snapshot budget")
        remaining -= len(snapshot)
        with open(attestation_file, "rb") as handle:
            raw = handle.read(16385)
        if len(raw) > 16384:
            raise ValueError("publisher attestation exceeds size limit")
        attestation = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        proofs[evidence_id] = (snapshot, attestation)
    return policy, proofs
