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
    def test_missing_parent_on_read(self):
        child = sign(create("Revision", ["source"], self.item["record"]["id"]), Ed25519PrivateKey.generate())
        self.store.ingest([child])
        self.store.db.execute("DELETE FROM records WHERE id=?", (self.item["record"]["id"],))
        with self.assertRaisesRegex(ValueError, "missing revision parent"):
            self.store.export()
    def test_corruption_blocks_new_ingest(self):
        self.store.db.execute("UPDATE records SET envelope='broken'")
        self.store.db.commit()
        new = sign(create("New", ["source"]), Ed25519PrivateKey.generate())
        with self.assertRaisesRegex(ValueError, "database integrity"):
            self.store.ingest([new])
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM records").fetchone()[0], 1)

    def test_reject_noncanonical_stored_envelope(self):
        self.store.db.execute("UPDATE records SET envelope=?", (json.dumps(self.item),))
        with self.assertRaisesRegex(ValueError, "database integrity"):
            self.store.export()

    def test_reject_oversized_signed_stored_record(self):
        from openhumanity import canonical
        item = sign(create("x" * 66000, ["source"]), Ed25519PrivateKey.generate())
        self.store.db.execute("INSERT INTO records VALUES (?, ?, ?)", (item["record"]["id"], item["public_key"], canonical(item).decode("utf-8")))
        with self.assertRaisesRegex(ValueError, "database integrity"):
            self.store.export()

    @unittest.skipUnless(__import__('os').name == 'posix', 'POSIX mode bits')
    def test_new_database_private_permissions(self):
        import os
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'private.sqlite'
            old = os.umask(0)
            try:
                Store(path).close()
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                path.chmod(0o640)
                Store(path).close()
                self.assertEqual(path.stat().st_mode & 0o777, 0o640)
            finally:
                os.umask(old)

    def test_read_only_store_prevents_mutation(self):
        import sqlite3
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'node #%.sqlite'
            store = Store(path)
            try:
                store.ingest([self.item])
            finally:
                store.close()
            reader = Store(path, read_only=True)
            try:
                self.assertEqual(reader.export(), [self.item])
                with self.assertRaises(sqlite3.OperationalError):
                    reader.ingest([self.item])
            finally:
                reader.close()
