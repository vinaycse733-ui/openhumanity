"""Local, caller-controlled publisher pins and global key revocation."""
import json
import re
from pathlib import Path
from types import MappingProxyType
from source_auth import _body, verify_published_evidence

MAX_POLICY_BYTES = 1024 * 1024
SCHEMA = 'openhumanity.publisher-policy.v1'


def _key(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
        raise ValueError('invalid publisher key')
    return value


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate policy field')
        result[key] = value
    return result


class PublisherPolicy:
    """Immutable snapshot of local trust configuration. Unknown sources fail closed."""
    def __init__(self, document):
        if not isinstance(document, dict) or set(document) != {'schema', 'pins', 'revoked_keys'} or document['schema'] != SCHEMA:
            raise ValueError('invalid publisher policy schema')
        pins, revoked = document['pins'], document['revoked_keys']
        if not isinstance(pins, dict) or len(pins) > 1000 or not isinstance(revoked, list) or len(revoked) > 1000:
            raise ValueError('invalid publisher policy size or structure')
        checked = {}
        for source, keys in pins.items():
            _body(source, b'')  # Use the attestation protocol's exact URL rules.
            if not isinstance(keys, list) or not 1 <= len(keys) <= 20:
                raise ValueError('invalid source key list')
            unique = frozenset(_key(key) for key in keys)
            if len(unique) != len(keys):
                raise ValueError('duplicate publisher key')
            checked[source] = unique
        self._pins = MappingProxyType(checked)
        self._revoked = frozenset(_key(key) for key in revoked)
        if len(self._revoked) != len(revoked):
            raise ValueError('duplicate revoked key')

    @classmethod
    def load(cls, path):
        with Path(path).open('rb') as handle:
            raw = handle.read(MAX_POLICY_BYTES + 1)
        if len(raw) > MAX_POLICY_BYTES:
            raise ValueError('publisher policy exceeds size limit')
        try:
            return cls(json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object))
        except RecursionError as exc:
            raise ValueError('invalid publisher policy nesting') from exc

    def verify(self, envelope, snapshot, attestation, expected_source):
        """Verify against an exact caller-selected source; revocation overrides pins."""
        _body(expected_source, b'')
        if not isinstance(attestation, dict):
            raise ValueError('invalid publisher attestation')
        key = _key(attestation.get('public_key'))
        if key in self._revoked:
            raise ValueError('publisher key revoked by local policy')
        if key not in self._pins.get(expected_source, ()):
            raise ValueError('publisher key not pinned for expected source')
        verified = verify_published_evidence(envelope, snapshot, attestation, expected_source, key)
        return dict(verified, policy_status='allowed_by_local_policy', revocation_scope='local_policy_snapshot')
