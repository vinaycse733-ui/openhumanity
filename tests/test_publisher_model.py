import argparse
import json
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from node_store import Store, sign
from openhumanity import create, create_snapshot_evidence, create_evidence
from publisher_policy import PublisherPolicy, SCHEMA
from publisher_report import add_proof_arguments, load_proof_arguments
from source_auth import attest
from trust import report
from trust_model import ask_local


class PublisherModelTests(unittest.TestCase):
    def setUp(self):
        self.source = 'https://example.org/report'
        self.snapshot = b'The source excerpt.'
        key = Ed25519PrivateKey.generate()
        claim = sign(create('Claim', [self.source]), key)
        self.claim_id = claim['record']['id']
        evidence = sign(create_snapshot_evidence(self.claim_id, 'supports', 'excerpt', self.source,
                        sha256(self.snapshot).hexdigest()), key)
        self.evidence_id = evidence['record']['id']
        contrary = sign(create_evidence(self.claim_id, 'contradicts', 'Contrary excerpt', ['other source']), key)
        with_store = Store(':memory:')
        try:
            with_store.ingest([claim, evidence, contrary])
            self.payload = report(with_store, self.claim_id)
        finally:
            with_store.close()
        self.attestation = attest(self.source, self.snapshot, Ed25519PrivateKey.generate())
        self.document = {'schema': SCHEMA, 'pins': {self.source: [self.attestation['public_key']]}, 'revoked_keys': []}
        self.policy = PublisherPolicy(self.document)
        self.proofs = {self.evidence_id: (self.snapshot, self.attestation)}

    def test_local_file_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'policy.json').write_text(json.dumps(self.document), encoding='utf-8')
            (root / 'snapshot.txt').write_bytes(self.snapshot)
            (root / 'attestation.json').write_text(json.dumps(self.attestation), encoding='utf-8')
            parser = argparse.ArgumentParser()
            add_proof_arguments(parser)
            argv = ['--publisher-policy', str(root / 'policy.json'), '--publisher-proof', self.evidence_id,
                    str(root / 'snapshot.txt'), str(root / 'attestation.json')]
            policy, proofs = load_proof_arguments(parser.parse_args(argv))
            self.assertEqual(proofs, self.proofs)
            self.assertIsInstance(policy, PublisherPolicy)
            with self.assertRaises(ValueError):
                load_proof_arguments(parser.parse_args(argv + argv[2:]))

    def test_no_policy_rejected(self):
        parser = argparse.ArgumentParser()
        add_proof_arguments(parser)
        with self.assertRaises(ValueError):
            load_proof_arguments(parser.parse_args(['--publisher-proof', self.evidence_id, 'x', 'y']))

    def test_invalid_proof_blocks_model_before_request(self):
        from io import BytesIO
        from email.message import Message
        from contextlib import nullcontext
        response = BytesIO(json.dumps(self.payload).encode())
        response.headers = Message()
        response.headers['Content-Type'] = 'application/json'
        with patch('trust_client.build_opener') as node, patch('trust_model.build_opener') as model:
            node.return_value.open.return_value = nullcontext(response)
            with self.assertRaises(ValueError):
                ask_local(self.claim_id, 'Question', 'test', policy=self.policy,
                          proofs={self.evidence_id: (b'changed', self.attestation)})
            model.assert_not_called()

    def test_verified_report_reaches_model(self):
        from io import BytesIO
        from email.message import Message
        from contextlib import nullcontext
        def response(payload):
            value = BytesIO(json.dumps(payload).encode())
            value.headers = Message()
            value.headers['Content-Type'] = 'application/json'
            return nullcontext(value)
        with patch('trust_client.build_opener') as node, patch('trust_model.build_opener') as model:
            node.return_value.open.return_value = response(self.payload)
            model.return_value.open.return_value = response({'done': True, 'message': {'role': 'assistant',
                'content': json.dumps({'answer': 'Fixture response', 'citations': [self.evidence_id]})}})
            result = ask_local(self.claim_id, 'Question', 'test', policy=self.policy, proofs=self.proofs)
            request = model.return_value.open.call_args.args[0]
            context = json.loads(json.loads(request.data)['messages'][1]['content'])['report']
            self.assertEqual(context['publisher_verified_counts']['supports'], 1)
            self.assertEqual(result['publisher_verified_counts']['supports'], 1)
            self.assertTrue(result['conflicting_evidence_present'])
            self.assertEqual(result['evidence_index']['contradicts'][0]['publisher_status'], 'proof_not_supplied')
