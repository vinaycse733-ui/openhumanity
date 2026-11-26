import copy
import unittest
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from node_store import Store, sign
from openhumanity import create, create_evidence
from trust import report
from trust_sdk import verify_report, check_excerpt


class SDKTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        self.key = Ed25519PrivateKey.generate()
        claim = sign(create("Claim", ["source"]), self.key)
        self.id = claim["record"]["id"]
        evidence = sign(create_evidence(self.id, "supports", "Excerpt", ["source"]), self.key)
        self.store.ingest([claim, evidence])
        self.payload = report(self.store, self.id)
    def tearDown(self):
        self.store.close()
    def test_recompute_unsigned_summary(self):
        self.payload["truth_status"] = "true"
        self.payload["counts"]["supports"] = 999
        self.payload["claim"]["claim"] = "Forged"  # shared object in original report; detach first in real JSON
        # Restore the signed proof, leaving the unsigned claim summary forged.
        self.payload["claim_envelopes"] = report(self.store, self.id)["claim_envelopes"]
        entry = self.payload["evidence"]["supports"][0]
        entry["trusted_by_caller"] = True
        entry["excerpt"] = "Forged"
        verified = verify_report(self.payload, self.id)
        self.assertEqual(verified["claim"]["claim"], "Claim")
        self.assertEqual(verified["counts"]["supports"], 1)
        self.assertEqual(verified["evidence"]["supports"][0]["excerpt"], "Excerpt")
        self.assertFalse(verified["evidence"]["supports"][0]["trusted_by_caller"])
        self.assertEqual(verified["truth_status"], "not_determined")
    def test_caller_trust(self):
        key = self.payload["claim_signers"][0]
        self.assertTrue(verify_report(self.payload, self.id, [key])["evidence"]["supports"][0]["trusted_by_caller"])
    def test_wrong_claim(self):
        with self.assertRaises(ValueError):
            verify_report(self.payload, "0" * 64)
    def test_wrong_relation(self):
        self.payload["evidence"]["contradicts"] = self.payload["evidence"]["supports"]
        self.payload["evidence"]["supports"] = []
        with self.assertRaises(ValueError):
            verify_report(self.payload, self.id)
    def test_invalid_signature(self):
        self.payload["evidence"]["supports"][0]["envelope"]["signature"] = "0" * 128
        with self.assertRaises(ValueError):
            verify_report(self.payload, self.id)
    def test_duplicate(self):
        self.payload["evidence"]["supports"] *= 2
        with self.assertRaises(ValueError):
            verify_report(self.payload, self.id)
    def test_missing_proof(self):
        self.payload["claim_envelopes"] = []
        with self.assertRaises(ValueError):
            verify_report(self.payload, self.id)
    def test_missing_evidence_not_completeness(self):
        self.payload["evidence"]["supports"] = []
        self.assertEqual(verify_report(self.payload, self.id)["completeness"], "not_determined")
    def test_exact_unicode_excerpt(self):
        snapshot = "日本語 café".encode()
        result = check_excerpt(snapshot, "café", sha256(snapshot).hexdigest())
        self.assertTrue(result["exact_match"])
        self.assertEqual(result["byte_offset"], len("日本語 ".encode()))
        self.assertTrue(result["expected_digest_checked"])
        self.assertEqual(result["entailment"], "not_determined")
    def test_missing_excerpt_and_bad_digest(self):
        self.assertFalse(check_excerpt(b"abc", "ABC")["exact_match"])
        with self.assertRaises(ValueError):
            check_excerpt(b"abc", "a", "0" * 64)
    def test_invalid_snapshot(self):
        with self.assertRaises(ValueError):
            check_excerpt(b"\xff", "a")
        with self.assertRaises(ValueError):
            check_excerpt(b"abc", " ")
