import importlib.util
from pathlib import Path
import queue
import unittest

PATH = Path(__file__).resolve().parents[1] / 'runtime_canaries' / 'mcp_acl_canary.py'
spec = importlib.util.spec_from_file_location('mcp_acl_canary', PATH)
canary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(canary)


class CanaryTests(unittest.TestCase):
    def test_environment_is_allowlisted_and_home_is_disposable(self):
        source = {'PATH': '/bin', 'LANG': 'en_US.UTF-8', 'LC_ALL': 'C', 'OPENAI_API_KEY': 'secret', 'AWS_SECRET_ACCESS_KEY': 'secret', 'PYTHONPATH': '/unsafe', 'HOME': '/real/home', 'CODEX_HOME': '/real/codex'}
        env = canary.isolated_environment(Path('/tmp/canary'), source)
        self.assertEqual(env, {'PATH': '/bin', 'LANG': 'en_US.UTF-8', 'LC_ALL': 'C', 'HOME': '/tmp/canary', 'TMPDIR': '/tmp/canary', 'CODEX_HOME': '/tmp/canary/codex-home'})

    def test_catalog_requires_exact_server_and_complete_page(self):
        response = {'result': {'data': [{'name': 'canary', 'tools': {'forbidden': {}, 'allowed': {}}}]}}
        self.assertEqual(canary.catalog(response), ['allowed', 'forbidden'])
        response['result']['nextCursor'] = 'more'
        with self.assertRaises(ValueError):
            canary.catalog(response)

    def test_success_requires_matching_nonce_and_non_error_result(self):
        response = {'result': {'content': [{'type': 'text', 'text': '{"tool": "allowed", "nonce": "A"}'}]}}
        self.assertTrue(canary.success(response, 'allowed', 'A'))
        self.assertFalse(canary.success(response, 'allowed', 'B'))
        response['result']['isError'] = True
        self.assertFalse(canary.success(response, 'allowed', 'A'))

    def test_ingress_counts_and_wrong_tool(self):
        nonces = {x: x for x in 'BAXQ'}
        calls = [{'event': 'call', 'tool': 'forbidden', 'nonce': 'B'}, {'event': 'call', 'tool': 'allowed', 'nonce': 'A'}, {'event': 'call', 'tool': 'allowed', 'nonce': 'Q'}]
        self.assertEqual(canary.evaluate_ingress(calls, nonces), ({'B': 1, 'A': 1, 'X': 0, 'Q': 1}, False))
        calls.append({'event': 'call', 'tool': 'allowed', 'nonce': 'X'})
        self.assertTrue(canary.evaluate_ingress(calls, nonces)[1])
        calls[-1]['tool'] = 'forbidden'
        self.assertEqual(canary.evaluate_ingress(calls, nonces)[0]['X'], 1)

    def test_rpc_timeout_is_bounded_without_input(self):
        class Writer:
            def write(self, value): pass
            def flush(self): pass
        rpc = canary.Rpc.__new__(canary.Rpc)
        rpc.proc = type('Proc', (), {'stdin': Writer()})()
        rpc.timeout, rpc.next_id, rpc.lines = 0.01, 0, queue.Queue()
        with self.assertRaises(TimeoutError):
            rpc.send('test', {})


if __name__ == '__main__':
    unittest.main()
