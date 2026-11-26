"""Opt-in replication over loopback HTTP or verified HTTPS."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPRedirectHandler
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
    with build_opener(NoRedirect()).open(url.rstrip("/") + "/v1/bundle", timeout=15) as response:
        raw = response.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError("bundle too large")
    bundle = json.loads(raw)
    store.ingest(bundle)
    return len(bundle)

def handler(store):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/v1/bundle":
                self.send_error(404)
                return
            bundle = store.export()
            raw = json.dumps(bundle, ensure_ascii=False).encode("utf-8")
            if len(bundle) > 1000 or len(raw) > LIMIT:
                self.send_error(503, "bundle exceeds prototype limits")
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
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
    store = Store(args.db)
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
