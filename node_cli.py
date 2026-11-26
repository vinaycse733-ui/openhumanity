"""Local node CLI. Exchange signed bundles without a central service."""
import argparse
import contextlib
import getpass
import json
import os
import sqlite3
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from node_store import Store, sign
from openhumanity import create

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="node.sqlite")
    sub = p.add_subparsers(dest="command", required=True)
    k = sub.add_parser("keygen")
    k.add_argument("key")
    a = sub.add_parser("add")
    a.add_argument("--key", required=True)
    a.add_argument("--source", action="append", required=True)
    a.add_argument("--parent")
    a.add_argument("claim")
    for name in ("import", "export"):
        sub.add_parser(name).add_argument("file")
    sub.add_parser("search").add_argument("query")
    sub.add_parser("doctor", help="Check SQLite and signed revision integrity")
    sub.add_parser("backup", help="Create a verified SQLite snapshot").add_argument("file")
    args = p.parse_args()
    if args.command == "keygen":
        password = getpass.getpass("New key passphrase: ").encode()
        if len(password) < 12:
            p.error("passphrase must be at least 12 bytes")
        if password != getpass.getpass("Repeat passphrase: ").encode():
            p.error("passphrases differ")
        key = Ed25519PrivateKey.generate().private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption(password))
        with os.fdopen(os.open(args.key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as f:
            f.write(key)
        return
    if args.command in ("doctor", "backup") and not Path(args.db).is_file():
        p.error("database does not exist")
    store = Store(args.db)
    try:
        if args.command == "add":
            key = serialization.load_pem_private_key(Path(args.key).read_bytes(), password=getpass.getpass("Key passphrase: ").encode())
            if not isinstance(key, Ed25519PrivateKey):
                p.error("expected an Ed25519 key")
            item = sign(create(args.claim, args.source, args.parent), key)
            store.ingest([item])
            print(item["record"]["id"])
        elif args.command == "import":
            with open(args.file, "rb") as f:
                data = f.read(64 * 1024 * 1024 + 1)
            if len(data) > 64 * 1024 * 1024:
                raise ValueError("bundle too large")
            store.ingest(json.loads(data))
        elif args.command == "export":
            records = store.export()
            payload = json.dumps(records, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            if len(records) > 1000 or len(payload) > 64 * 1024 * 1024:
                raise ValueError("bundle exceeds v0.1 import limits")
            with open(args.file, "xb") as f:
                f.write(payload)
        elif args.command == "backup":
            destination = Path(args.file)
            fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(fd)
            try:
                with contextlib.closing(sqlite3.connect(destination)) as target:
                    store.db.backup(target)
                snapshot = Store(destination)
                try:
                    if snapshot.db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                        raise ValueError("backup SQLite integrity check failed")
                    count = len(snapshot.export())
                finally:
                    snapshot.close()
            except BaseException:
                destination.unlink(missing_ok=True)
                raise
            print(json.dumps({"status": "ok", "verified_records": count}))
        elif args.command == "doctor":
            rows = store.db.execute("PRAGMA quick_check").fetchall()
            if rows != [("ok",)]:
                raise ValueError("SQLite integrity check failed")
            records = store.export()
            print(json.dumps({"status": "ok", "verified_records": len(records)}))
        else:
            print(json.dumps(store.search(args.query), ensure_ascii=False, indent=2))
    finally:
        store.close()

if __name__ == "__main__":
    main()
