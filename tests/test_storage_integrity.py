import json
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from node_store import Store, sign
from openhumanity import create

class StorageIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        self.item = sign(create("Claim", ["source"]), Ed25519PrivateKey.generate())
        self.store.ingest([self.item])
    def tearDown(self):
        self.store.close()
    def test_valid_read(self):
        self.assertEqual(self.store.export(), [self.item])
    def test_tampered_envelope(self):
        self.item["record"]["body"]["claim"] = "Changed"
        self.store.db.execute("UPDATE records SET envelope=?", (json.dumps(self.item),))
        with self.assertRaisesRegex(ValueError, "database integrity"):
            self.store.search("Changed")
    def test_tampered_index(self):
        self.store.db.execute("UPDATE records SET id=?", ("0" * 64,))
        with self.assertRaisesRegex(ValueError, "database integrity"):
            self.store.export()
    def test_corrupt_json(self):
        self.store.db.execute("UPDATE records SET envelope='not-json'")
        with self.assertRaisesRegex(ValueError, "database integrity"):
            self.store.export()
