import unittest
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from openhumanity import create, create_evidence, create_snapshot_evidence, verify
from node_store import Store, sign
from trust import report
from trust_sdk import verify_report, verify_snapshot

class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.store = Store(':memory:')
        claim = sign(create('Claim', ['source']), self.key)
        self.id = claim['record']['id']
        self.store.ingest([claim])
        self.snapshot = 'An excerpt: café'.encode()
        self.hash = sha256(self.snapshot).hexdigest()
    def tearDown(self):
        self.store.close()
    def item(self, excerpt='café'):
        return sign(create_snapshot_evidence(self.id, 'supports', excerpt, 'source', self.hash), self.key)
    def test_match(self):
        self.assertTrue(verify_snapshot(self.item(), self.snapshot)['exact_match'])
    def test_changed_bytes(self):
        with self.assertRaises(ValueError):
            verify_snapshot(self.item(), self.snapshot + b'!')
    def test_missing_quote(self):
        with self.assertRaises(ValueError):
            verify_snapshot(self.item('wrong'), self.snapshot)
    def test_tampered_digest(self):
        item = self.item()
        item['record']['body']['snapshot_sha256'] = '0' * 64
        self.assertFalse(verify(item['record']))
        with self.assertRaises(ValueError):
            verify_snapshot(item, self.snapshot)
    def test_unbound_evidence(self):
        with self.assertRaises(ValueError):
            verify_snapshot(sign(create_evidence(self.id, 'supports', 'café', ['source']), self.key), self.snapshot)
    def test_report_and_exchange(self):
        self.store.ingest([self.item()])
        other = Store(':memory:')
        try:
            other.ingest(self.store.export())
            payload = report(other, self.id)
            payload['evidence']['supports'][0]['snapshot_sha256'] = '0' * 64
            self.assertEqual(verify_report(payload, self.id)['evidence']['supports'][0]['snapshot_sha256'], self.hash)
        finally:
            other.close()
    def test_bad_digest(self):
        with self.assertRaises(ValueError):
            create_snapshot_evidence(self.id, 'supports', 'café', 'source', 'BAD')
    def test_orphan(self):
        item = sign(create_snapshot_evidence('0'*64, 'supports', 'café', 'source', self.hash), self.key)
        with self.assertRaises(ValueError):
            self.store.ingest([item])
