import json
import threading
import unittest
from http.server import HTTPServer
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from node_store import Store, sign
from node_web import handler
from openhumanity import create, create_evidence
from trust_client import fetch_verified_report
from urllib.error import HTTPError

class ClientTests(unittest.TestCase):
    def setUp(self):
        self.ready = threading.Event()
        key = Ed25519PrivateKey.generate()
        claim = sign(create('Claim', ['source']), key)
        self.id = claim['record']['id']
        self.author = claim['public_key']
        evidence = sign(create_evidence(self.id, 'supports', 'Excerpt', ['source']), key)
        def serve():
            store = Store(':memory:')
            try:
                store.ingest([claim, evidence])
                with HTTPServer(('127.0.0.1', 0), handler(store, key, 'token')) as server:
                    self.server = server
                    self.ready.set()
                    server.serve_forever(poll_interval=0.05)
            finally:
                store.close()
        self.thread = threading.Thread(target=serve, daemon=True)
        self.thread.start()
        self.assertTrue(self.ready.wait(5))
    def tearDown(self):
        self.server.shutdown()
        self.thread.join(5)
    def test_real_local_node(self):
        result = fetch_verified_report(self.id, self.server.server_port, [self.author])
        self.assertEqual(result['counts']['supports'], 1)
        self.assertEqual(result['truth_status'], 'not_determined')
        self.assertTrue(result['evidence']['supports'][0]['trusted_by_caller'])
    def test_missing_claim(self):
        with self.assertRaises(HTTPError):
            fetch_verified_report('0'*64, self.server.server_port)
    def test_invalid_request(self):
        for value in ('../', 'http://example.org', 'x'*64):
            with self.assertRaises(ValueError):
                fetch_verified_report(value, self.server.server_port)
        with self.assertRaises(ValueError):
            fetch_verified_report(self.id, 0)
