import json
import tempfile
import unittest
from pathlib import Path
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from node_store import sign
from openhumanity import create, create_snapshot_evidence
from source_auth import attest
from publisher_policy import PublisherPolicy, SCHEMA


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.source = 'https://example.org/report'
        self.snapshot = b'An excerpt.'
        self.first = attest(self.source, self.snapshot, Ed25519PrivateKey.generate())
        self.second = attest(self.source, self.snapshot, Ed25519PrivateKey.generate())
        target = create('Claim', [self.source])['id']
        self.envelope = sign(create_snapshot_evidence(target, 'supports', 'excerpt', self.source,
                             sha256(self.snapshot).hexdigest()), Ed25519PrivateKey.generate())
    def policy(self, keys=(), revoked=(), source=None):
        return PublisherPolicy({'schema': SCHEMA, 'pins': {source or self.source: list(keys)} if keys else {},
                                'revoked_keys': list(revoked)})
    def verify(self, policy, attestation=None):
        return policy.verify(self.envelope, self.snapshot, attestation or self.first, self.source)
    def test_pinned(self):
        self.assertEqual(self.verify(self.policy([self.first['public_key']]))['policy_status'], 'allowed_by_local_policy')
    def test_unknown_source(self):
        with self.assertRaises(ValueError):
            self.verify(self.policy([self.first['public_key']], source=self.source + '/other'))
    def test_unknown_key(self):
        with self.assertRaises(ValueError):
            self.verify(self.policy([self.second['public_key']]))
    def test_revocation_overrides_pin(self):
        with self.assertRaisesRegex(ValueError, 'revoked'):
            self.verify(self.policy([self.first['public_key']], [self.first['public_key']]))
    def test_rotation(self):
        policy = self.policy([self.first['public_key'], self.second['public_key']], [self.first['public_key']])
        with self.assertRaises(ValueError):
            self.verify(policy)
        self.assertTrue(self.verify(policy, self.second)['publisher']['publisher_signature_valid'])
    def test_invalid_policy(self):
        for doc in ({}, {'schema': SCHEMA, 'pins': {}, 'revoked_keys': ['bad']},
                    {'schema': SCHEMA, 'pins': {self.source: []}, 'revoked_keys': []}):
            with self.assertRaises(ValueError):
                PublisherPolicy(doc)
    def test_load_and_duplicate_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'policy.json'
            path.write_text(json.dumps({'schema': SCHEMA, 'pins': {self.source: [self.first['public_key']]}, 'revoked_keys': []}), encoding='utf-8')
            self.assertTrue(self.verify(PublisherPolicy.load(path))['publisher']['publisher_signature_valid'])
            path.write_text('{"schema":"' + SCHEMA + '","pins":{},"pins":{},"revoked_keys":[]}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                PublisherPolicy.load(path)
    def test_policy_input_mutation(self):
        doc = {'schema': SCHEMA, 'pins': {self.source: [self.first['public_key']]}, 'revoked_keys': []}
        policy = PublisherPolicy(doc)
        doc['pins'][self.source].append(self.second['public_key'])
        with self.assertRaises(ValueError):
            self.verify(policy, self.second)
