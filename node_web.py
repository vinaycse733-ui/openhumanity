"""Local signed-node browser UI. No remote access or implicit sharing."""
import argparse
import getpass
import html
import json
import re
import secrets
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from node_store import Store, sign
from openhumanity import create, create_evidence
from trust import report

def esc(value):
    return html.escape(str(value), quote=True)

def evidence_page(result):
    """Render signed local evidence without treating relationships as verified facts."""
    claim_id = esc(result["claim_id"])
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Evidence review | OpenHumanity</title><style>body{font:17px/1.6 system-ui;max-width:900px;margin:32px auto;padding:0 20px;background:#f5f4ef;color:#202722}a{color:#174d36}a:focus-visible,summary:focus-visible{outline:3px solid #174d36;outline-offset:4px}article,section{background:white;border:1px solid #ccd4cc;padding:20px;margin:16px 0;border-radius:10px;overflow-wrap:anywhere}h1,h2,h3{line-height:1.25}summary{cursor:pointer}code{overflow-wrap:anywhere}ul{padding-left:24px}.counts{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px}.counts div{padding:12px;border:1px solid #ccd4cc;border-radius:8px}dt{font-weight:600}dd{margin:4px 0 12px}</style></head><body><nav aria-label="Navigation"><a href="/">Knowledge library</a></nav><main><h1>Evidence review</h1><p>Truth status: not determined. Signatures identify keys, not facts. Publisher proofs have not been checked in this browser view.</p>"""
    page += '<section aria-labelledby="claim-heading"><h2 id="claim-heading">Claim</h2><p>' + esc(result["claim"]["claim"]) + '</p><p>Record ID: <code>' + claim_id + '</code></p><a href="/v1/claims/' + claim_id + '/report">View report as JSON</a></section>'
    labels = {"supports": "Supporting evidence", "contradicts": "Contradictory evidence", "context": "Contextual evidence"}
    page += '<h2>Evidence overview</h2><dl class="counts">'
    for relation, label in labels.items():
        page += '<div><dt>' + label + '</dt><dd>' + esc(result["counts"][relation]) + '</dd></div>'
    page += '</dl><p>Counts represent distinct records, not independent sources or votes for truth.</p>'
    if result["counts"]["supports"] and result["counts"]["contradicts"]:
        page += '<p><strong>Conflicting evidence is present.</strong> Review both relationships before drawing conclusions.</p>'
    for relation, label in labels.items():
        page += '<section><h2>' + label + '</h2>'
        for item in result["evidence"][relation]:
            page += '<article><h3>Contributor excerpt</h3><p>' + esc(item["excerpt"]) + '</p><h3>Referenced sources</h3><ul>' + ''.join('<li>' + esc(source) + '</li>' for source in item["sources"]) + '</ul><details><summary>Record and signature details</summary><p>Record: <code>' + esc(item["id"]) + '</code></p><p>Signer: <code>' + esc(item["signer"]) + '</code></p><p>Signed source fingerprint: <code>' + esc(item.get("snapshot_sha256") or "Not supplied") + '</code></p></details></article>'
        if not result["evidence"][relation]:
            page += '<p>No evidence of this relationship in the local report.</p>'
        page += '</section>'
    return page + '</main></body></html>'


def handler(store, key, token):
    class Handler(BaseHTTPRequestHandler):
        timeout = 10

        def trusted_host(self):
            return self.headers.get_all("Host") == ["127.0.0.1:" + str(self.server.server_port)]

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
                label = "Evidence: " + esc(body["relation"]) + " for " + esc(body["target"]) if body["version"] in (2, 3) else '<a href="/claims/' + esc(record["id"]) + '">Review evidence</a> · <a href="/v1/claims/' + esc(record["id"]) + '/report">JSON report</a>'
                cards.append("<article><p>" + label + "</p><h3>" + esc(body["claim"]) + "</h3><p>" + "<br>".join(esc(s) for s in body["sources"]) + "</p><small>Record: " + esc(record["id"]) + "<br>Signer: " + esc(item["public_key"]) + "<br>Parent: " + esc(body["parent"] or "None") + "</small></article>")
            markup = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>OpenHumanity | Signed node</title><style>body{font:16px/1.6 system-ui;max-width:850px;margin:32px auto;padding:0 20px;background:#f5f4ef;color:#202722}h1{font-size:42px;letter-spacing:-.05em}section,article{background:white;border:1px solid #ccd4cc;padding:20px;margin:16px 0;border-radius:10px;overflow-wrap:anywhere}label{display:block;font-weight:bold}input,textarea,select{box-sizing:border-box;width:100%;font:inherit;padding:10px;margin:5px 0 12px;border:1px solid #aeb8af;border-radius:5px}button{font:inherit;padding:9px 16px;background:#214c38;color:white;border:0;border-radius:5px}</style><h1>OpenHumanity</h1><p>Signed knowledge, stored on this device. Signatures identify keys, not truth or real-world identity.</p>"""
            markup += "<p role='status'>" + esc(error) + "</p>"
            markup += '<section><h2>Publish locally</h2><form method="post" action="/add"><input type="hidden" name="token" value="' + esc(token) + '"><label for="claim">Claim</label><textarea id="claim" name="claim" maxlength="4000" required></textarea><label for="sources">Sources (one per line)</label><textarea id="sources" name="sources" maxlength="8000" required></textarea><label for="parent">Parent record ID (optional)</label><input id="parent" name="parent" maxlength="64"><button>Sign and save</button></form></section>'
            markup += '<section><h2>Add evidence</h2><p>Relationships are contributor assertions, not verified facts. For signed source-file fingerprints, use the CLI.</p><form method="post" action="/evidence"><input type="hidden" name="token" value="' + esc(token) + '"><label for="target">Claim ID</label><input id="target" name="target" maxlength="64" required><label for="relation">Relationship</label><select id="relation" name="relation" required><option value="supports">Supports</option><option value="contradicts">Contradicts</option><option value="context">Context</option></select><label for="excerpt">Evidence excerpt</label><textarea id="excerpt" name="claim" maxlength="4000" required></textarea><label for="evidence-sources">Sources (one per line)</label><textarea id="evidence-sources" name="sources" maxlength="8000" required></textarea><button>Sign and save evidence</button></form></section>'
            markup += '<section><h2>Knowledge library</h2><form action="/" method="get"><label for="q">Search</label><input id="q" name="q" value="' + esc(query) + '" maxlength="200"><button>Search</button></form>' + ("".join(cards) or "<p>No matching records.</p>") + "</section></html>"
            raw = markup.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if not self.trusted_host():
                self.send_error(403)
                return
            origins = self.headers.get_all("Origin")
            fetch_sites = self.headers.get_all("Sec-Fetch-Site")
            if origins not in (None, ["http://127.0.0.1:" + str(self.server.server_port)]) or (fetch_sites is not None and fetch_sites not in (["same-origin"], ["none"])):
                self.send_error(403)
                return
            u = urlsplit(self.path)
            json_match = re.fullmatch(r"/v1/claims/([0-9a-f]{64})/report", u.path)
            html_match = re.fullmatch(r"/claims/([0-9a-f]{64})", u.path)
            match = json_match or html_match
            if match:
                try:
                    result = report(store, match.group(1))
                    raw = (evidence_page(result) if html_match else json.dumps(result, ensure_ascii=False)).encode("utf-8")
                except KeyError:
                    self.send_error(404, "Claim not found")
                    return
                except (ValueError, sqlite3.Error):
                    self.send_error(503, "Knowledge database unavailable")
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8" if html_match else "application/json; charset=utf-8")
                if html_match:
                    self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'")
                    self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cross-Origin-Resource-Policy", "same-origin")
                self.end_headers()
                self.wfile.write(raw)
                return
            if u.path != "/":
                self.send_error(404)
                return
            self.page(parse_qs(u.query).get("q", [""])[0][:200])

        def do_POST(self):
            if not self.trusted_host() or self.headers.get_all("Origin") != ["http://127.0.0.1:" + str(self.server.server_port)]:
                self.send_error(403)
                return
            if self.path not in ("/add", "/evidence") or self.headers.get_content_type() != "application/x-www-form-urlencoded":
                self.send_error(400)
                return
            try:
                lengths = self.headers.get_all("Content-Length")
                if not lengths or len(lengths) != 1 or self.headers.get("Transfer-Encoding") is not None:
                    raise ValueError("invalid framing")
                size = int(lengths[0])
                if not 0 < size <= 50000:
                    raise ValueError("invalid body length")
                data = parse_qs(self.rfile.read(size).decode("utf-8"), keep_blank_values=True, max_num_fields=8)
                if any(len(values) != 1 for values in data.values()):
                    raise ValueError("duplicate fields")
                field = lambda name: data.get(name, [""])[0]
                if not secrets.compare_digest(field("token").encode("utf-8"), token.encode("utf-8")):
                    self.send_error(403)
                    return
                claim, sources = field("claim").strip(), field("sources")
                if len(claim)>4000 or len(sources)>8000:
                    raise ValueError("record too large")
                source_list = [s.strip() for s in sources.splitlines() if s.strip()]
                if self.path == "/evidence":
                    record = create_evidence(field("target").strip(), field("relation"), claim, source_list)
                else:
                    record = create(claim, source_list, field("parent").strip() or None)
                item = sign(record, key)
                store.ingest([item])
            except sqlite3.Error:
                self.send_error(503, "Knowledge database unavailable")
                return
            except (ValueError, UnicodeError):
                self.page(error="Record rejected. Check the claim, sources, relationship and target or parent.", code=400)
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
