import unittest
from openhumanity import create, verify

class ProtocolTests(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(verify(create("Example claim", ["https://example.org"])))
    def test_tampered(self):
        r = create("Original", ["https://example.org"])
        r["body"]["claim"] = "Changed"
        self.assertFalse(verify(r))
    def test_revision(self):
        a = create("Original", ["source"])
        b = create("Revised", ["source"], a["id"])
        self.assertTrue(verify(b))
        self.assertNotEqual(a["id"], b["id"])
    def test_no_sources(self):
        with self.assertRaises(ValueError):
            create("Claim", [])
    def test_malformed(self):
        self.assertFalse(verify({}))
    def test_determinism(self):
        self.assertEqual(create("Claim", ["source"]), create("Claim", ["source"]))
    def test_strict_version(self):
        for version in (True, 1.0, "1", 2, None):
            with self.subTest(version=version):
                record = create("Claim", ["source"])
                record["body"]["version"] = version
                self.assertFalse(verify(record))
    def test_extra_fields_rejected(self):
        record = create("Claim", ["source"])
        record["extra"] = True
        self.assertFalse(verify(record))
    def test_unicode_round_trip(self):
        self.assertTrue(verify(create("తెలుగు ज्ञान café", ["日本語"])))
    def test_unpaired_surrogate_rejected(self):
        record = create("Claim", ["source"])
        record["body"]["claim"] = "\ud800"
        self.assertFalse(verify(record))
