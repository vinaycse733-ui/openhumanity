import unittest
import tempfile
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from openhumanity import create
from node_store import Store, sign, authentic

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.a = sign(create("Example", ["source"]), self.key)
        self.store = Store(":memory:")
    def tearDown(self):
        self.store.close()
    def test_signature(self):
        self.assertTrue(authentic(self.a))
        self.a["signature"] = "00" * 64
        self.assertFalse(authentic(self.a))
    def test_exchange(self):
        self.store.ingest([self.a])
        other = Store(":memory:")
        try:
            other.ingest(self.store.export())
            other.ingest(self.store.export())
            self.assertEqual(other.export(), [self.a])
        finally:
            other.close()
    def test_missing_parent(self):
        b = sign(create("Revision", ["source"], self.a["record"]["id"]), self.key)
        with self.assertRaises(ValueError):
            self.store.ingest([b])
        self.assertEqual(self.store.export(), [])
        self.store.ingest([b, self.a])
        self.assertEqual(len(self.store.export()), 2)
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "node.sqlite"
            s = Store(path)
            s.ingest([self.a])
            s.close()
            s = Store(path)
            try:
                self.assertEqual(s.search("example"), [self.a])
            finally:
                s.close()
    def test_invalid_atomic(self):
        with self.assertRaises(ValueError):
            self.store.ingest([self.a, {}])
        self.assertEqual(self.store.export(), [])
