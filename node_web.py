"""Local signed-node browser UI. No remote access or implicit sharing."""
import argparse
import getpass
import html
import secrets
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from node_store import Store, sign
from openhumanity import create

def esc(value):
    return html.escape(str(value), quote=True)

def handler(store, key, token):
    class Handler(BaseHTTPRequestHandler):
        timeout = 10

        def trusted_host(self):
            return self.headers.get("Host") == "127.0.0.1:" + str(self.server.server_port)

        def page(self, query="", error="", code=200):
            cards = []
            try:
                items = store.search(query)
            except (ValueError, sqlite3.Error):
                self.send_error(503, "Knowledge database unavailable; restore a verified backup")
                return
            for item in items:
                record = item["record"]
                body = record["body"]
                cards.append("<article><h3>" + esc(body["claim"]) + "</h3><p>" + "<br>".join(esc(s) for s in body["sources"]) + "</p><small>Record: " + esc(record["id"]) + "<br>Signer: " + esc(item["public_key"]) + "<br>Parent: " + esc(body["parent"] or "None") + "</small></article>")
            markup = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>OpenHumanity | Signed node</title><style>body{font:16px/1.6 system-ui;max-width:850px;margin:32px auto;padding:0 20px;background:#f5f4ef;color:#202722}h1{font-size:42px;letter-spacing:-.05em}section,article{background:white;border:1px solid #ccd4cc;padding:20px;margin:16px 0;border-radius:10px;overflow-wrap:anywhere}label{display:block;font-weight:bold}input,textarea{box-sizing:border-box;width:100%;font:inherit;padding:10px;margin:5px 0 12px;border:1px solid #aeb8af;border-radius:5px}button{font:inherit;padding:9px 16px;background:#214c38;color:white;border:0;border-radius:5px}</style><h1>OpenHumanity</h1><p>Signed knowledge, stored on this device. Signatures identify keys, not truth or real-world identity.</p>"""
            markup += "<p role='status'>" + esc(error) + "</p>"
            markup += '<section><h2>Publish locally</h2><form method="post" action="/add"><input type="hidden" name="token" value="' + esc(token) + '"><label for="claim">Claim</label><textarea id="claim" name="claim" maxlength="4000" required></textarea><label for="sources">Sources (one per line)</label><textarea id="sources" name="sources" maxlength="8000" required></textarea><label for="parent">Parent record ID (optional)</label><input id="parent" name="parent" maxlength="64"><button>Sign and save</button></form></section>'
            markup += '<section><h2>Knowledge library</h2><form action="/" method="get"><label for="q">Search</label><input id="q" name="q" value="' + esc(query) + '" maxlength="200"><button>Search</button></form>' + ("".join(cards) or "<p>No matching records.</p>") + "</section></html>"
            raw = markup.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if not self.trusted_host():
                self.send_error(403)
                return
            u = urlsplit(self.path)
            if u.path != "/":
                self.send_error(404)
                return
            self.page(parse_qs(u.query).get("q", [""])[0][:200])

        def do_POST(self):
            if not self.trusted_host() or self.headers.get("Origin") != "http://127.0.0.1:" + str(self.server.server_port):
                self.send_error(403)
                return
            if self.path != "/add" or self.headers.get_content_type() != "application/x-www-form-urlencoded":
                self.send_error(400)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 50000:
                    raise ValueError("invalid body length")
                data = parse_qs(self.rfile.read(size).decode("utf-8"), keep_blank_values=True, max_num_fields=8)
                field = lambda name: data.get(name, [""])[0]
                if not secrets.compare_digest(field("token").encode("utf-8"), token.encode("utf-8")):
                    self.send_error(403)
                    return
                claim, sources = field("claim").strip(), field("sources")
                if len(claim)>4000 or len(sources)>8000:
                    raise ValueError("record too large")
                item = sign(create(claim, [s.strip() for s in sources.splitlines() if s.strip()], field("parent").strip() or None), key)
                store.export()  # Fail closed if existing signed records are corrupted.
                store.ingest([item])
            except sqlite3.Error:
                self.send_error(503, "Knowledge database unavailable")
                return
            except (ValueError, UnicodeError):
                self.page(error="Record rejected. Check the claim, sources and parent.", code=400)
                return
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
    return Handler

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="node.sqlite")
    p.add_argument("--key", required=True)
    p.add_argument("--port", default=8000, type=int)
    args = p.parse_args()
    key = serialization.load_pem_private_key(Path(args.key).read_bytes(), password=getpass.getpass("Key passphrase: ").encode())
    if not isinstance(key, Ed25519PrivateKey):
        p.error("expected an Ed25519 key")
    store = Store(args.db)
    try:
        with HTTPServer(("127.0.0.1", args.port), handler(store, key, secrets.token_urlsafe(32))) as server:
            print("Open http://127.0.0.1:" + str(server.server_port), flush=True)
            server.serve_forever()
    finally:
        store.close()

if __name__ == "__main__":
    main()
