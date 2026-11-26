import threading
import unittest
from http.client import HTTPConnection
from http.server import HTTPServer
from urllib.parse import urlencode
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from node_store import Store
from node_web import handler

class WebTests(unittest.TestCase):
    def setUp(self):
        self.ready = threading.Event()
        self.state = {}
        def run():
            store = Store(":memory:")
            try:
                with HTTPServer(("127.0.0.1", 0), handler(store, Ed25519PrivateKey.generate(), "test-token")) as server:
                    self.state["server"] = server
                    self.ready.set()
                    server.serve_forever(poll_interval=0.05)
            finally:
                store.close()
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        self.assertTrue(self.ready.wait(5))
        self.port = self.state["server"].server_port
        self.origin = "http://127.0.0.1:" + str(self.port)

    def tearDown(self):
        self.state["server"].shutdown()
        self.thread.join(5)

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request(method, path, body, headers or {})
            response = connection.getresponse()
            return response.status, response.read().decode("utf-8")
        finally:
            connection.close()

    def add(self, token="test-token", origin=None):
        return self.request("POST", "/add", urlencode({"token":token,"claim":"<script>alert(1)</script>","sources":"https://example.org","parent":""}), {"Content-Type":"application/x-www-form-urlencoded","Origin":origin or self.origin})

    def test_publish_search_escape(self):
        self.assertEqual(self.add()[0], 303)
        code, page = self.request("GET", "/?q=alert")
        self.assertEqual(code, 200)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("Signer:", page)

    def test_reject_cross_origin_and_bad_token(self):
        self.assertEqual(self.add(origin="https://example.org")[0], 403)
        self.assertEqual(self.add(token="wrong")[0], 403)
        self.assertEqual(self.add(token="é")[0], 403)
        self.assertIn("No matching records.", self.request("GET", "/")[1])

    def test_reject_untrusted_host(self):
        self.assertEqual(self.request("GET", "/", headers={"Host":"example.org"})[0], 403)
