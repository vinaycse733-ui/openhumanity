"""Opt-in replication over loopback HTTP or verified HTTPS."""
import argparse
import json
import re
import sqlite3
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler
from node_store import Store

LIMIT = 8 * 1024 * 1024

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def pull(store, url):
    u = urlsplit(url)
    if u.username or u.password or u.query or u.fragment:
        raise ValueError("unexpected URL components")
    if not (u.scheme == "https" and u.hostname or u.scheme == "http" and u.hostname in ("127.0.0.1", "::1", "localhost")):
        raise ValueError("use HTTPS or loopback HTTP")
    opener = build_opener(NoRedirect(), ProxyHandler({})) if u.scheme == "http" else build_opener(NoRedirect())
    with opener.open(url.rstrip("/") + "/v1/bundle", timeout=15) as response:
        if response.headers.get_all("Content-Type") is None or len(response.headers.get_all("Content-Type")) != 1 or response.headers.get_content_type() != "application/json":
            raise ValueError("expected a JSON peer bundle")
        lengths = response.headers.get_all("Content-Length")
        expected = None
        if lengths is not None:
            if len(lengths) != 1 or not re.fullmatch(r"[0-9]{1,10}", lengths[0]) or response.headers.get("Transfer-Encoding") is not None:
                raise ValueError("invalid peer response framing")
            expected = int(lengths[0])
            if expected > LIMIT:
                raise ValueError("bundle too large")
        raw = response.read(LIMIT + 1)
        if expected is not None and len(raw) != expected:
            raise ValueError("truncated peer response")
    if len(raw) > LIMIT:
        raise ValueError("bundle too large")
    bundle = json.loads(raw)
    store.ingest(bundle)
    return len(bundle)

def handler(store):
    class Handler(BaseHTTPRequestHandler):
        timeout = 10

        def do_GET(self):
            port = self.server.server_port
            if self.headers.get_all("Host") not in ([f"127.0.0.1:{port}"], [f"localhost:{port}"]):
                self.send_error(403)
                return
            if self.headers.get("Origin") is not None or self.headers.get("Sec-Fetch-Site") is not None:
                self.send_error(403)
                return
            if self.path != "/v1/bundle":
                self.send_error(404)
                return
            try:
                bundle = store.export()
            except (ValueError, sqlite3.Error):
                self.send_error(503, "Knowledge database unavailable")
                return
            raw = json.dumps(bundle, ensure_ascii=False).encode("utf-8")
            if len(bundle) > 1000 or len(raw) > LIMIT:
                self.send_error(503, "bundle exceeds prototype limits")
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(raw)
    return Handler

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="node.sqlite")
    commands = p.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--port", type=int, default=8765)
    fetch = commands.add_parser("pull")
    fetch.add_argument("url")
    args = p.parse_args()
    read_only = args.command == "serve"
    if read_only and not Path(args.db).is_file():
        p.error("database does not exist")
    store = Store(args.db, read_only=read_only)
    try:
        if args.command == "serve":
            with HTTPServer(("127.0.0.1", args.port), handler(store)) as server:
                print("Serving every record in this database on loopback. Use only a dedicated shareable database.", flush=True)
                server.serve_forever()
        else:
            print(f"Processed {pull(store, args.url)} signed records")
    finally:
        store.close()

if __name__ == "__main__":
    main()
