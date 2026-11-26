"""Model-independent evidence reports. No automatic truth verdicts."""
import argparse
import getpass
import json
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from openhumanity import RELATIONS, create_evidence
from node_store import Store, sign

def report(store, claim_id, trusted_keys=()):
    records = store.export()
    claims = [item for item in records if item["record"]["id"] == claim_id and item["record"]["body"]["version"] == 1]
    if not claims:
        raise KeyError("claim not found")
    trusted = set(trusted_keys)
    groups = {relation: [] for relation in RELATIONS}
    for item in records:
        body = item["record"]["body"]
        if body["version"] == 2 and body["target"] == claim_id:
            groups[body["relation"]].append({
                "id": item["record"]["id"], "excerpt": body["claim"],
                "sources": body["sources"], "signer": item["public_key"],
                "trusted_by_caller": item["public_key"] in trusted,
                "signature_valid": True
            })
    # Multiple keys or links do not establish independent corroboration.
    return {
        "schema": "openhumanity.trust-report.v1",
        "claim_id": claim_id, "claim": claims[0]["record"]["body"],
        "claim_signers": [item["public_key"] for item in claims],
        "signature_valid": True,
        "evidence": groups,
        "counts": {relation: len({item["id"] for item in group}) for relation, group in groups.items()},
        "truth_status": "not_determined",
        "limitations": ["Evidence relations are asserted by contributors, not verified against source contents.",
                        "Signatures verify key control, not identity, independence, accuracy or source availability.",
                        "The local database may not contain all relevant evidence."]
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("evidence")
    add.add_argument("target")
    add.add_argument("relation", choices=RELATIONS)
    add.add_argument("excerpt")
    add.add_argument("--source", action="append", required=True)
    add.add_argument("--key", required=True)
    read = commands.add_parser("report")
    read.add_argument("claim_id")
    read.add_argument("--trusted-key", action="append", default=[])
    args = parser.parse_args()
    if not Path(args.db).is_file():
        parser.error("database does not exist")
    store = Store(args.db)
    try:
        if args.command == "evidence":
            key = serialization.load_pem_private_key(Path(args.key).read_bytes(), password=getpass.getpass("Key passphrase: ").encode())
            if not isinstance(key, Ed25519PrivateKey):
                parser.error("expected an Ed25519 key")
            item = sign(create_evidence(args.target, args.relation, args.excerpt, args.source), key)
            store.ingest([item])
            print(item["record"]["id"])
        else:
            print(json.dumps(report(store, args.claim_id, args.trusted_key), ensure_ascii=False, indent=2))
    except (ValueError, KeyError) as exc:
        parser.error(str(exc))
    finally:
        store.close()

if __name__ == "__main__":
    main()
