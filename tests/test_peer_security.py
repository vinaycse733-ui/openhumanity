import threading
import unittest
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
from peer import handler, pull

class PeerSecurityTests(unittest.TestCase):
    def setUp(self):
        class SharedStore:
            def export(self):
                return [{"example": "shared"}]
        self.server = HTTPServer(("127.0.0.1", 0), handler(SharedStore()))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
    def tearDown(self):
        self.server.shutdown()
        self.thread.join(5)
        self.server.server_close()
    def request(self, headers=None):
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            conn.request("GET", "/v1/bundle", headers=headers or {})
            response = conn.getresponse()
            return response.status, response.read()
        finally:
            conn.close()
    def test_untrusted_host(self):
        status, body = self.request({"Host": "untrusted.example"})
        self.assertEqual(status, 403)
        self.assertNotIn(b"shared", body)
    def test_browser_request(self):
        self.assertEqual(self.request({"Origin": "https://untrusted.example"})[0], 403)
        self.assertEqual(self.request({"Sec-Fetch-Site": "cross-site"})[0], 403)
    def test_normal_client(self):
        self.assertEqual(self.request()[0], 200)
    def test_loopback_ignores_proxy(self):
        class Receiver:
            def ingest(self, bundle):
                self.bundle = bundle
        receiver = Receiver()
        with patch.dict("os.environ", {"http_proxy": "http://127.0.0.1:1", "no_proxy": ""}):
            self.assertEqual(pull(receiver, f"http://127.0.0.1:{self.server.server_port}"), 1)
        self.assertEqual(receiver.bundle, [{"example": "shared"}])

    def test_invalid_peer_response_rejected_before_ingest(self):
        class Receiver:
            def ingest(self, bundle):
                raise AssertionError("invalid response reached ingest")
        class Fixture(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", self.server.content_type)
                self.send_header("Content-Length", str(self.server.length))
                self.end_headers()
                self.wfile.write(b"[]")
        with HTTPServer(("127.0.0.1", 0), Fixture) as server:
            worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
            worker.start()
            try:
                for content_type, length in (("text/html", 2), ("application/json", 10)):
                    with self.subTest(content_type=content_type, length=length):
                        server.content_type, server.length = content_type, length
                        with self.assertRaises(ValueError):
                            pull(Receiver(), f"http://127.0.0.1:{server.server_port}")
            finally:
                server.shutdown()
                worker.join(5)
