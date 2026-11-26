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

RELATIONS = ("supports", "contradicts", "context")

def create_evidence(target, relation, excerpt, sources):
    if not isinstance(target, str) or len(target) != 64 or any(c not in "0123456789abcdef" for c in target):
        raise ValueError("invalid evidence target")
    if relation not in RELATIONS:
        raise ValueError("invalid evidence relation")
    body = create(excerpt, sources)["body"]
    body.update(version=2, target=target, relation=relation)
    return {"body": body, "id": digest(body)}

def verify(record):
    try:
        body = record["body"]
        if type(body["version"]) is not int:
            return False
        if body["version"] == 1:
            expected = create(body["claim"], body["sources"], body["parent"])
        elif body["version"] == 2:
            expected = create_evidence(body["target"], body["relation"], body["claim"], body["sources"])
        else:
            return False
        return canonical(expected) == canonical(record)
    except (KeyError, TypeError, ValueError, RecursionError):
        return False
