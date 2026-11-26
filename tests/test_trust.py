import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from openhumanity import create, create_evidence, verify
from node_store import Store, sign
from trust import report

class TrustTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.store = Store(":memory:")
        self.claim = sign(create("Example claim", ["source"]), self.key)
        self.id = self.claim["record"]["id"]
        self.store.ingest([self.claim])
    def tearDown(self):
        self.store.close()
    def evidence(self, relation, text="Example evidence", key=None):
        return sign(create_evidence(self.id, relation, text, ["source"]), key or self.key)
    def test_empty_evidence_not_truth(self):
        r = report(self.store, self.id)
        self.assertEqual(r["truth_status"], "not_determined")
        self.assertEqual(r["counts"], {"supports": 0, "contradicts": 0, "context": 0})
    def test_conflicting_evidence(self):
        a = self.evidence("supports")
        b = self.evidence("contradicts")
        self.store.ingest([a, b])
        r = report(self.store, self.id, [a["public_key"]])
        self.assertEqual(r["counts"]["supports"], 1)
        self.assertEqual(r["counts"]["contradicts"], 1)
        self.assertTrue(r["evidence"]["supports"][0]["trusted_by_caller"])
        self.assertEqual(r["truth_status"], "not_determined")
    def test_duplicate_signers_not_independent(self):
        a = self.evidence("supports")
        b = self.evidence("supports", key=Ed25519PrivateKey.generate())
        self.store.ingest([a, b])
        r = report(self.store, self.id)
        self.assertEqual(r["counts"]["supports"], 1)
        self.assertEqual(len(r["evidence"]["supports"]), 2)
        self.assertFalse(r["evidence"]["supports"][0]["trusted_by_caller"])
    def test_invalid_target_rejected(self):
        item = sign(create_evidence("0" * 64, "context", "Evidence", ["source"]), self.key)
        with self.assertRaises(ValueError):
            self.store.ingest([item])
        self.assertEqual(len(self.store.export()), 1)
    def test_tampered_relation(self):
        item = self.evidence("supports")
        item["record"]["body"]["relation"] = "contradicts"
        self.assertFalse(verify(item["record"]))
        with self.assertRaises(ValueError):
            self.store.ingest([item])
    def test_bundle_exchange(self):
        self.store.ingest([self.evidence("context")])
        other = Store(":memory:")
        try:
            other.ingest(self.store.export())
            self.assertEqual(report(other, self.id), report(self.store, self.id))
        finally:
            other.close()
    def test_missing_claim(self):
        with self.assertRaises(KeyError):
            report(self.store, "0" * 64)
