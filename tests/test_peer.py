import threading
import unittest
from http.server import HTTPServer
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from node_store import Store, sign
from openhumanity import create
from peer import handler, pull

class PeerTests(unittest.TestCase):
    def test_loopback_exchange(self):
        ready = threading.Event()
        state = {}
        item = sign(create("Shared claim", ["source"]), Ed25519PrivateKey.generate())
        def run():
            s = Store(":memory:")
            s.ingest([item])
            with HTTPServer(("127.0.0.1", 0), handler(s)) as server:
                state["port"] = server.server_port
                server.timeout = 5
                ready.set()
                server.handle_request()
            s.close()
        t = threading.Thread(target=run, daemon=True)
        t.start()
        self.assertTrue(ready.wait(5))
        target = Store(":memory:")
        try:
            self.assertEqual(pull(target, "http://127.0.0.1:" + str(state["port"])), 1)
            self.assertEqual(target.export(), [item])
            with self.assertRaises(ValueError):
                pull(target, "http://example.org")
        finally:
            target.close()
            t.join(6)
