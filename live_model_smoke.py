"""Opt-in inference smoke check with synthetic data; no model downloads."""
import argparse
import json
import threading
from http.server import HTTPServer
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from node_store import Store, sign
from node_web import handler
from openhumanity import create, create_evidence
from trust_model import ask_local


def smoke(model, model_port=11434):
    """Use an already-running trusted local model, never a user's database."""
    key = Ed25519PrivateKey.generate()
    claim = sign(create("The fictional library opens on Monday", ["Synthetic claim"]), key)
    claim_id = claim["record"]["id"]
    records = [claim, sign(create_evidence(claim_id, "supports", "The fictional schedule lists Monday", ["Synthetic schedule"]), key),
               sign(create_evidence(claim_id, "contradicts", "The fictional notice lists Tuesday", ["Synthetic notice"]), key)]
    ready = threading.Event()
    state = {}

    def serve():
        try:
            store = Store(":memory:")
            try:
                store.ingest(records)
                with HTTPServer(("127.0.0.1", 0), handler(store, key, "synthetic-smoke")) as server:
                    state["server"] = server
                    ready.set()
                    server.serve_forever(poll_interval=0.05)
            finally:
                store.close()
        except Exception as exc:
            state["error"] = exc
            ready.set()

    worker = threading.Thread(target=serve, daemon=True)
    worker.start()
    if not ready.wait(5):
        raise RuntimeError("synthetic node startup timed out")
    if "error" in state:
        raise RuntimeError("synthetic node startup failed") from state["error"]
    server = state["server"]
    try:
        result = ask_local(claim_id, "Summarize the conflicting synthetic evidence and cite its identifiers.", model, server.server_port, model_port)
        if not result["conflicting_evidence_present"] or result["truth_status"] != "not_determined":
            raise ValueError("evidence coverage invariant failed")
        return result
    finally:
        server.shutdown()
        worker.join(5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Already-installed model in a trusted local runtime")
    parser.add_argument("--model-port", type=int, default=11434)
    args = parser.parse_args()
    try:
        result = smoke(args.model, args.model_port)
    except (OSError, ValueError, RuntimeError, RecursionError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
