import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from node_store import Store, sign
from node_web import handler
from openhumanity import create, create_evidence
from trust_model import ask_local


class ModelTests(unittest.TestCase):
    def setUp(self):
        key = Ed25519PrivateKey.generate()
        claim = sign(create('Claim', ['source']), key)
        self.id = claim['record']['id']
        evidence = sign(create_evidence(self.id, 'supports', 'Excerpt', ['source']), key)
        self.evidence = evidence['record']['id']
        contrary = sign(create_evidence(self.id, 'contradicts', 'Different excerpt', ['other source']), key)
        self.contrary = contrary['record']['id']
        ready = threading.Event()
        def node():
            store = Store(':memory:')
            try:
                store.ingest([claim, evidence, contrary])
                with HTTPServer(('127.0.0.1', 0), handler(store, key, 'token')) as server:
                    self.node = server
                    ready.set()
                    server.serve_forever(poll_interval=0.05)
            finally:
                store.close()
        self.thread = threading.Thread(target=node, daemon=True)
        self.thread.start()
        self.assertTrue(ready.wait(5))
        owner = self
        self.reply = {'answer': 'One contributor supports the claim.', 'citations': [self.evidence]}
        self.done = True
        self.reason = "stop"
        self.role = "assistant"
        class Endpoint(BaseHTTPRequestHandler):
            def do_POST(self):
                owner.received = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                raw = json.dumps({'done': owner.done, 'done_reason': owner.reason, 'message': {'role': owner.role, 'content': json.dumps(owner.reply)}}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
        self.model = HTTPServer(('127.0.0.1', 0), Endpoint)
        self.worker = threading.Thread(target=self.model.serve_forever, kwargs={'poll_interval': 0.05}, daemon=True)
        self.worker.start()
    def tearDown(self):
        self.model.shutdown()
        self.model.server_close()
        self.worker.join(5)
        self.node.shutdown()
        self.thread.join(5)
    def ask(self):
        return ask_local(self.id, 'What does the evidence say?', 'local-test', self.node.server_port, self.model.server_port)
    def test_local_http_contract(self):
        result = self.ask()
        self.assertEqual(result['citations'], [self.evidence])
        self.assertEqual(result['truth_status'], 'not_determined')
        self.assertEqual(result['answer_status'], 'model_generated_not_fact_checked')
        self.assertNotIn('tools', self.received)
        context = json.loads(self.received['messages'][1]['content'])
        self.assertEqual(context['report']['counts']['supports'], 1)
    def test_invented_citation_rejected(self):
        self.reply['citations'] = ['0' * 64]
        with self.assertRaises(ValueError):
            self.ask()
    def test_omitted_citation_rejected(self):
        self.reply['citations'] = []
        with self.assertRaises(ValueError):
            self.ask()
    def test_incomplete_response_rejected(self):
        self.done = False
        with self.assertRaises(ValueError):
            self.ask()
    def test_bad_model_port(self):
        with self.assertRaises(ValueError):
            ask_local(self.id, 'Question', 'local-test', self.node.server_port, 0)

    def test_uncited_conflicting_evidence_remains_visible(self):
        result = self.ask()
        self.assertTrue(result['conflicting_evidence_present'])
        self.assertEqual(result['uncited_evidence_ids']['contradicts'], [self.contrary])
        self.assertEqual(result['evidence_index']['contradicts'][0]['sources'], ['other source'])
        self.assertFalse(result['evidence_index']['contradicts'][0]['cited_by_model'])
        self.assertTrue(result['evidence_index']['supports'][0]['cited_by_model'])

    def test_cited_conflict_is_not_a_truth_verdict(self):
        self.reply['citations'] = [self.evidence, self.contrary, self.evidence]
        result = self.ask()
        self.assertEqual(result['citations'], [self.evidence, self.contrary])
        self.assertEqual(result['uncited_evidence_ids']['contradicts'], [])
        self.assertTrue(result['conflicting_evidence_present'])
        self.assertEqual(result['truth_status'], 'not_determined')

    def test_truncated_response_rejected(self):
        self.reason = "length"
        with self.assertRaises(ValueError):
            self.ask()

    def test_wrong_role_rejected(self):
        self.role = "user"
        with self.assertRaises(ValueError):
            self.ask()

    def test_injected_verdict_field_rejected(self):
        self.reply["truth_status"] = "true"
        with self.assertRaises(ValueError):
            self.ask()
