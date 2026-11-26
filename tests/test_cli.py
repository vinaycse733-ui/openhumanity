import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from node_cli import main
from node_store import authentic

class CliTests(unittest.TestCase):
    def test_encrypted_identity_and_bundle_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            key = str(Path(d) / "identity.pem")
            first = str(Path(d) / "first.sqlite")
            second = str(Path(d) / "second.sqlite")
            bundle = str(Path(d) / "data.bundle.json")
            def run(*args):
                with patch("sys.argv", ["node_cli.py", *args]), patch("getpass.getpass", return_value="temporary-test-passphrase"), contextlib.redirect_stdout(io.StringIO()) as output:
                    main()
                    return output.getvalue()
            run("keygen", key)
            self.assertIn(b"ENCRYPTED PRIVATE KEY", Path(key).read_bytes())
            with self.assertRaises(FileExistsError):
                run("keygen", key)
            record_id = run("--db", first, "add", "--key", key, "--source", "https://example.org", "Example claim").strip()
            run("--db", first, "export", bundle)
            run("--db", second, "import", bundle)
            records = json.loads(run("--db", second, "search", "Example"))
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["record"]["id"], record_id)
            self.assertTrue(authentic(records[0]))
            self.assertEqual(json.loads(run("--db", second, "doctor")), {"status": "ok", "verified_records": 1})
            snapshot = str(Path(d) / "backup.sqlite")
            self.assertEqual(json.loads(run("--db", second, "backup", snapshot)), {"status": "ok", "verified_records": 1})
            self.assertEqual(json.loads(run("--db", snapshot, "search", "Example")), records)
            with self.assertRaises(FileExistsError):
                run("--db", second, "backup", snapshot)
            missing = Path(d) / "missing.sqlite"
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                run("--db", str(missing), "doctor")
            self.assertFalse(missing.exists())

    def test_missing_read_database_does_not_create_file(self):
        with tempfile.TemporaryDirectory() as d:
            missing = Path(d) / 'missing.sqlite'
            bundle = Path(d) / 'export.json'
            for command in [('search', 'query'), ('export', str(bundle))]:
                with self.subTest(command=command), patch('sys.argv', ['node_cli.py', '--db', str(missing), *command]), contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        main()
                    self.assertFalse(missing.exists())
                    self.assertFalse(bundle.exists())

    @unittest.skipUnless(__import__('os').name == 'posix', 'POSIX mode bits')
    def test_export_private_permissions(self):
        import os
        from node_store import Store
        with tempfile.TemporaryDirectory() as d:
            database = Path(d) / 'node.sqlite'
            Store(database).close()
            bundle = Path(d) / 'export.json'
            old = os.umask(0)
            try:
                with patch('sys.argv', ['node_cli.py', '--db', str(database), 'export', str(bundle)]):
                    main()
                    self.assertEqual(bundle.stat().st_mode & 0o777, 0o600)
                    with self.assertRaises(FileExistsError):
                        main()
            finally:
                os.umask(old)
