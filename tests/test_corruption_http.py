import threading
import unittest
from http.client import HTTPConnection
from http.server import HTTPServer
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from node_store import Store, sign
from node_web import handler as web_handler
from peer import handler as peer_handler
from openhumanity import create

class CorruptionHttpTests(unittest.TestCase):
    def check_handler(self, factory, path):
        ready = threading.Event()
        state = {}
        def serve():
            store = Store(':memory:')
            key = Ed25519PrivateKey.generate()
            store.ingest([sign(create('claim', ['source']), key)])
            store.db.execute("UPDATE records SET envelope='broken'")
            try:
                with HTTPServer(('127.0.0.1', 0), factory(store, key)) as server:
                    state['server'] = server
                    ready.set()
                    server.serve_forever(poll_interval=0.05)
            finally:
                store.close()
        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        self.assertTrue(ready.wait(5))
        server = state['server']
        conn = HTTPConnection('127.0.0.1', server.server_port, timeout=5)
        try:
            conn.request('GET', path)
            response = conn.getresponse()
            self.assertEqual(response.status, 503)
            self.assertNotIn('broken', response.read().decode())
        finally:
            conn.close()
            server.shutdown()
            thread.join(5)

    def test_browser_rejects_corruption(self):
        self.check_handler(lambda store, key: web_handler(store, key, 'test'), '/')

    def test_peer_rejects_corruption(self):
        self.check_handler(lambda store, key: peer_handler(store), '/v1/bundle')
