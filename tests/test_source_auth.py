import unittest
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from openhumanity import create, create_snapshot_evidence
from node_store import sign
from source_auth import attest, verify_publisher, verify_published_evidence


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.source = 'https://example.org/report'
        self.snapshot = b'Published excerpt.'
        self.key = Ed25519PrivateKey.generate()
        self.att = attest(self.source, self.snapshot, self.key)
        self.pin = self.att['public_key']
        target = create('Claim', [self.source])['id']
        self.evidence = sign(create_snapshot_evidence(target, 'supports', 'excerpt', self.source,
                             sha256(self.snapshot).hexdigest()), Ed25519PrivateKey.generate())
    def verify(self, att=None, snapshot=None, source=None, pin=None):
        return verify_publisher(att if att is not None else self.att,
                                snapshot if snapshot is not None else self.snapshot,
                                source if source is not None else self.source,
                                pin if pin is not None else self.pin)
    def test_publisher_signature(self):
        self.assertTrue(self.verify()['publisher_signature_valid'])
        self.assertEqual(self.verify()['identity_status'], 'caller_pinned_key_only')
    def test_changed_snapshot(self):
        with self.assertRaises(ValueError):
            self.verify(snapshot=b'Changed excerpt.')
    def test_wrong_source(self):
        with self.assertRaises(ValueError):
            self.verify(source='https://example.org/other')
    def test_untrusted_signer(self):
        other = attest(self.source, self.snapshot, Ed25519PrivateKey.generate())
        with self.assertRaises(ValueError):
            self.verify(att=other)
    def test_signature_forgery(self):
        self.att['signature'] = '0'*128
        with self.assertRaises(ValueError):
            self.verify()
    def test_two_signatures(self):
        result = verify_published_evidence(self.evidence, self.snapshot, self.att, self.source, self.pin)
        self.assertTrue(result['evidence']['exact_match'])
        self.assertTrue(result['publisher']['publisher_signature_valid'])
        self.assertEqual(result['truth_status'], 'not_determined')
    def test_evidence_source_mismatch(self):
        other = 'https://example.org/other'
        with self.assertRaises(ValueError):
            verify_published_evidence(self.evidence, self.snapshot, attest(other, self.snapshot, self.key), other, self.pin)
    def test_unsafe_source(self):
        for url in ('http://example.org', 'https://user@example.org', 'https://example.org/#fragment'):
            with self.assertRaises(ValueError):
                attest(url, self.snapshot, self.key)
