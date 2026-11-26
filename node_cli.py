"""Local node CLI. Exchange signed bundles without a central service."""
import argparse
import getpass
import json
import os
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
            with open(args.file, "x", encoding="utf-8") as f:
                json.dump(store.export(), f, ensure_ascii=False, indent=2)
        else:
            print(json.dumps(store.search(args.query), ensure_ascii=False, indent=2))
    finally:
        store.close()

if __name__ == "__main__":
    main()
