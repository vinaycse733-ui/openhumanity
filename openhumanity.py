"""Minimal portable knowledge record protocol, version 1."""
import hashlib
import json

def canonical(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")

def digest(record):
    return hashlib.sha256(canonical(record)).hexdigest()

def create(claim, sources, parent=None):
    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("claim required")
    if not isinstance(sources, list) or not sources or any(not isinstance(s, str) or not s.strip() for s in sources):
        raise ValueError("sources required")
    if parent is not None and (not isinstance(parent, str) or len(parent) != 64 or any(c not in "0123456789abcdef" for c in parent)):
        raise ValueError("invalid parent")
    body = {"version": 1, "claim": claim, "sources": list(sources), "parent": parent}
    return {"body": body, "id": digest(body)}

def verify(record):
    try:
        body = record["body"]
        return create(body["claim"], body["sources"], body["parent"]) == record
    except (KeyError, TypeError, ValueError):
        return False
