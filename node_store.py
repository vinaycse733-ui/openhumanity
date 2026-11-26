"""Persistent signed knowledge records, with explicit bundle exchange."""
import json
import sqlite3
import re
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from openhumanity import canonical, verify

def sign(record, key):
    if not verify(record):
        raise ValueError("invalid record")
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    return {"record": record, "public_key": public, "signature": key.sign(canonical(record)).hex()}

def authentic(envelope):
    try:
        if set(envelope) != {"record", "public_key", "signature"}:
            return False
        if not verify(envelope["record"]):
            return False
        if not re.fullmatch("[0-9a-f]{64}", envelope["public_key"]) or not re.fullmatch("[0-9a-f]{128}", envelope["signature"]):
            return False
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(envelope["public_key"])).verify(bytes.fromhex(envelope["signature"]), canonical(envelope["record"]))
        return True
    except (InvalidSignature, ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return False

class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS records (id TEXT, author TEXT, envelope TEXT NOT NULL, PRIMARY KEY(id, author))")
    def close(self):
        self.db.close()
    def ingest(self, bundle):
        if not isinstance(bundle, list) or len(bundle) > 1000:
            raise ValueError("invalid bundle size")
        for item in bundle:
            if not authentic(item) or len(canonical(item)) > 65536:
                raise ValueError("invalid signed record")
        with self.db:
            ids = {row[0] for row in self.db.execute("SELECT DISTINCT id FROM records")}
            ids.update(item["record"]["id"] for item in bundle)
            for item in bundle:
                parent = item["record"]["body"]["parent"]
                if parent is not None and parent not in ids:
                    raise ValueError("missing parent")
                self.db.execute("INSERT OR IGNORE INTO records VALUES (?, ?, ?)", (item["record"]["id"], item["public_key"], canonical(item).decode("utf-8")))
    def export(self):
        records = []
        for record_id, author, raw in self.db.execute("SELECT id, author, envelope FROM records ORDER BY id, author"):
            try:
                item = json.loads(raw)
                if not authentic(item) or item["record"]["id"] != record_id or item["public_key"] != author:
                    raise ValueError("invalid stored record")
            except (ValueError, TypeError, RecursionError) as exc:
                raise ValueError("database integrity check failed") from exc
            records.append(item)
        return records
    def search(self, query):
        return [item for item in self.export() if query.casefold() in json.dumps(item["record"]["body"], ensure_ascii=False).casefold()]
