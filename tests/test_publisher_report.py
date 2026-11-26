import unittest
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from node_store import Store, sign
from openhumanity import create, create_evidence, create_snapshot_evidence
from trust import report
from source_auth import attest
from publisher_policy import PublisherPolicy, SCHEMA
from publisher_report import verify_with_publishers


class PublisherReportTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(':memory:')
        key = Ed25519PrivateKey.generate()
        self.source = 'https://example.org/report'
        self.snapshot = b'An excerpt.'
        claim = sign(create('Claim', [self.source]), key)
        self.id = claim['record']['id']
        support = sign(create_snapshot_evidence(self.id, 'supports', 'excerpt', self.source,
                       sha256(self.snapshot).hexdigest()), key)
        conflict = sign(create_evidence(self.id, 'contradicts', 'Contrary account', [self.source]), key)
        self.store.ingest([claim, support, conflict])
        self.support = support['record']['id']
        self.conflict = conflict['record']['id']
        self.att = attest(self.source, self.snapshot, Ed25519PrivateKey.generate())
        self.policy = PublisherPolicy({'schema': SCHEMA, 'pins': {self.source: [self.att['public_key']]}, 'revoked_keys': []})
        self.payload = report(self.store, self.id)
    def tearDown(self):
        self.store.close()
    def run_report(self, proofs):
        return verify_with_publishers(self.payload, self.id, self.policy, proofs)
    def test_mixed_evidence_retained(self):
        result = self.run_report({self.support: (self.snapshot, self.att)})
        self.assertEqual(result['counts'], {'supports': 1, 'contradicts': 1, 'context': 0})
        self.assertEqual(result['publisher_verified_counts'], {'supports': 1, 'contradicts': 0, 'context': 0})
        self.assertEqual(result['evidence']['contradicts'][0]['publisher_status'], 'proof_not_supplied')
        self.assertEqual(result['truth_status'], 'not_determined')
    def test_unsigned_status_ignored(self):
        self.payload['evidence']['supports'][0]['publisher_status'] = 'verified_against_local_policy'
        self.assertEqual(self.run_report({})['evidence']['supports'][0]['publisher_status'], 'proof_not_supplied')
    def test_invalid_bytes(self):
        with self.assertRaises(ValueError):
            self.run_report({self.support: (b'changed', self.att)})
    def test_unrelated_proof(self):
        with self.assertRaises(ValueError):
            self.run_report({'0'*64: (self.snapshot, self.att)})
    def test_unbound_proof(self):
        with self.assertRaises(ValueError):
            self.run_report({self.conflict: (self.snapshot, self.att)})
    def test_revoked_key(self):
        self.policy = PublisherPolicy({'schema': SCHEMA, 'pins': {self.source: [self.att['public_key']]}, 'revoked_keys': [self.att['public_key']]})
        with self.assertRaisesRegex(ValueError, 'revoked'):
            self.run_report({self.support: (self.snapshot, self.att)})
    def test_oversize(self):
        with self.assertRaisesRegex(ValueError, 'budget'):
            self.run_report({self.support: (b'x'*(8*1024*1024+1), self.att)})
