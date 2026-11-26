import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from live_model_smoke import smoke


class SmokeTests(unittest.TestCase):
    def test_synthetic_smoke_with_http_fixture(self):
        seen = []

        class Fixture(BaseHTTPRequestHandler):
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                context = json.loads(payload['messages'][1]['content'])
                report = context['report']
                seen.append(report)
                response = {'done': True, 'done_reason': 'stop', 'message': {
                    'role': 'assistant', 'content': json.dumps({'answer': 'Fixture response, not inference.',
                    'citations': [report['evidence']['supports'][0]['id']]})}}
                raw = json.dumps(response).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        with HTTPServer(('127.0.0.1', 0), Fixture) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                result = smoke('fixture-only', server.server_port)
            finally:
                server.shutdown()
                worker.join(5)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0]['counts'], {'supports': 1, 'contradicts': 1, 'context': 0})
        self.assertTrue(result['conflicting_evidence_present'])
        self.assertEqual(len(result['uncited_evidence_ids']['contradicts']), 1)
        self.assertEqual(result['truth_status'], 'not_determined')
        self.assertEqual(result['answer_status'], 'model_generated_not_fact_checked')
