"""Detached publisher attestations verified against an explicitly pinned key."""
import re
from urllib.parse import urlsplit
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey, Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from hashlib import sha256
from openhumanity import canonical
from trust_sdk import verify_snapshot, MAX_SNAPSHOT_BYTES

DOMAIN = b'OpenHumanity source attestation v1\x00'


def _body(source, snapshot):
    if not isinstance(source, str) or not 0 < len(source) <= 2048 or any(ord(c) <= 32 or ord(c) == 127 for c in source):
        raise ValueError('invalid source URL')
    url = urlsplit(source)
    if url.scheme != 'https' or not url.hostname or url.username is not None or url.password is not None or url.fragment:
        raise ValueError('expected an HTTPS source URL without credentials or fragment')
    if not isinstance(snapshot, bytes) or len(snapshot) > MAX_SNAPSHOT_BYTES:
        raise ValueError('snapshot must be bytes, at most 8 MiB')
    snapshot.decode('utf-8', errors='strict')
    return {'schema': 'openhumanity.publisher-attestation.v1', 'source': source,
            'sha256': sha256(snapshot).hexdigest()}


def attest(source, snapshot, key):
    """Publishers sign exact bytes; no network request or key discovery."""
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError('expected an Ed25519 private key')
    body = _body(source, snapshot)
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    return {'body': body, 'public_key': public, 'signature': key.sign(DOMAIN + canonical(body)).hex()}


def verify_publisher(attestation, snapshot, expected_source, pinned_key):
    """Check exact source/digest and signature using a caller-pinned publisher key."""
    expected = _body(expected_source, snapshot)
    if not isinstance(pinned_key, str) or not re.fullmatch(r'[0-9a-f]{64}', pinned_key):
        raise ValueError('invalid pinned publisher key')
    if not isinstance(attestation, dict) or set(attestation) != {'body', 'public_key', 'signature'}:
        raise ValueError('invalid publisher attestation')
    sig = attestation['signature']
    if attestation['body'] != expected or attestation['public_key'] != pinned_key or not isinstance(sig, str) or not re.fullmatch(r'[0-9a-f]{128}', sig):
        raise ValueError('publisher attestation does not match source, bytes or pinned key')
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(pinned_key)).verify(bytes.fromhex(sig), DOMAIN + canonical(expected))
    except InvalidSignature as exc:
        raise ValueError('invalid publisher signature') from exc
    return {'source': expected_source, 'sha256': expected['sha256'], 'publisher_key': pinned_key,
            'publisher_signature_valid': True, 'identity_status': 'caller_pinned_key_only',
            'truth_status': 'not_determined', 'freshness': 'not_determined'}


def verify_published_evidence(envelope, snapshot, attestation, expected_source, pinned_key):
    """Verify both the contributor quotation and publisher's detached attestation."""
    evidence = verify_snapshot(envelope, snapshot)
    if evidence['source'] != expected_source:
        raise ValueError('evidence source does not match expected source')
    publisher = verify_publisher(attestation, snapshot, expected_source, pinned_key)
    return {'evidence': evidence, 'publisher': publisher, 'truth_status': 'not_determined'}
