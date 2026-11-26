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
