"""Bounded local HTTP client for independently verified AI evidence retrieval."""
import argparse
import json
import re
from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler
from trust_sdk import verify_report
from publisher_report import verify_with_publishers, add_proof_arguments, load_proof_arguments

MAX_REPORT_BYTES = 8 * 1024 * 1024

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch_verified_report(claim_id, port=8000, trusted_keys=(), *, policy=None, proofs=None):
    """Read a local node report and rebuild it from signed records.

    No URL is accepted from a model or evidence record. No source is visited.
    The application chooses the expected claim ID and local port.
    """
    if not isinstance(claim_id, str) or not re.fullmatch(r"[0-9a-f]{64}", claim_id):
        raise ValueError("invalid claim identifier")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("invalid local port")
    url = f"http://127.0.0.1:{port}/v1/claims/{claim_id}/report"
    opener = build_opener(ProxyHandler({}), NoRedirect())
    with opener.open(url, timeout=10) as response:
        if response.headers.get_content_type() != "application/json":
            raise ValueError("expected a JSON report")
        raw = response.read(MAX_REPORT_BYTES + 1)
    if len(raw) > MAX_REPORT_BYTES:
        raise ValueError("report exceeds response limit")
    payload = json.loads(raw)
    if policy is not None:
        return verify_with_publishers(payload, claim_id, policy, proofs if proofs is not None else {}, trusted_keys)
    if proofs is not None:
        raise ValueError("publisher proofs require a trusted policy")
    return verify_report(payload, claim_id, trusted_keys)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("claim_id")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--trusted-key", action="append", default=[])
    add_proof_arguments(parser)
    args = parser.parse_args()
    try:
        policy, proofs = load_proof_arguments(args)
        result = fetch_verified_report(args.claim_id, args.port, args.trusted_key, policy=policy, proofs=proofs)
    except (OSError, ValueError, RecursionError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
