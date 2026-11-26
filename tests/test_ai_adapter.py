import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from ai_adapter import summarize

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.report = {'claim_id': 'a'*64, 'evidence': {'supports': [{'id': 'b'*64}], 'contradicts': [{'id': 'c'*64}], 'context': []}, 'counts': {'supports': 1, 'contradicts': 1, 'context': 0}}
        self.reply = {'answer': 'Sources disagree.', 'citations': ['b'*64, 'c'*64]}
        self.done = True
        self.reason = 'stop'
        self.calls = []
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                owner.calls.append((self.path, json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                raw = json.dumps({'done': owner.done, 'done_reason': owner.reason, 'message': {'role': 'assistant', 'content': json.dumps(owner.reply)}}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
        self.server = HTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
    def tearDown(self):
        self.server.shutdown()
        self.thread.join(5)
        self.server.server_close()
    def run_summary(self):
        return summarize(self.report, 'What evidence exists?', 'test-model', self.server.server_port)
    def test_local_http_contract(self):
        result = self.run_summary()
        self.assertEqual(result['truth_status'], 'not_determined')
        self.assertFalse(result['model_output_verified'])
        self.assertEqual(len(result['cited_evidence_ids']), 2)
        path, body = self.calls[0]
        self.assertEqual(path, '/api/chat')
        self.assertFalse(body['stream'])
        self.assertNotIn('tools', body)
        self.assertIn('untrusted_evidence', body['messages'][1]['content'])
    def test_unknown_citation(self):
        self.reply['citations'] = ['d'*64]
        with self.assertRaises(ValueError):
            self.run_summary()
    def test_duplicate_citation(self):
        self.reply['citations'] *= 2
        with self.assertRaises(ValueError):
            self.run_summary()
    def test_incomplete_output(self):
        self.reason = 'length'
        with self.assertRaises(ValueError):
            self.run_summary()
    def test_oversize_context(self):
        self.report['claim'] = 'x'*70000
        with self.assertRaises(ValueError):
            self.run_summary()
        self.assertEqual(self.calls, [])
    def test_invalid_port(self):
        with self.assertRaises(ValueError):
            summarize(self.report, 'Question', 'test-model', 0)
    def test_unexpected_verdict(self):
        self.reply['truth_status'] = 'true'
        with self.assertRaises(ValueError):
            self.run_summary()
    def test_omitted_citations_rejected(self):
        self.reply['citations'] = []
        with self.assertRaises(ValueError):
            self.run_summary()
    def test_conflict_remains_visible(self):
        self.reply['citations'] = ['b'*64]
        result = self.run_summary()
        self.assertTrue(result['conflicting_evidence_present'])
        self.assertEqual(result['uncited_evidence_ids']['contradicts'], ['c'*64])
        self.assertFalse(result['evidence_index']['contradicts'][0]['cited_by_model'])
