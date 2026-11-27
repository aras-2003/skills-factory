import importlib.util
from pathlib import Path
import queue
import signal
import unittest
from unittest import mock

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

    def test_final_ingress_rejects_late_and_duplicate_calls(self):
        nonces = {x: x for x in 'BAXQ'}
        base = [{'event': 'call', 'tool': tool, 'nonce': nonce} for tool, nonce in [('forbidden', 'B'), ('allowed', 'A'), ('allowed', 'Q')]]
        for extra in ([{'event': 'call', 'tool': 'forbidden', 'nonce': 'X'}], [{'event': 'call', 'tool': 'allowed', 'nonce': 'A'}], [{'event': 'call', 'tool': 'forbidden', 'nonce': 'A'}]):
            receipt = {'cases': {'SETUP': 'PASS'}}
            canary.apply_ingress(receipt, base + extra, nonces, {x: True for x in nonces})
            self.assertEqual(receipt['status'], 'FAIL')

    def test_candidate_check_requires_head_and_clean_index_and_worktree(self):
        result = lambda code, output='': type('Result', (), {'returncode': code, 'stdout': output})()
        sha = 'a' * 40
        with mock.patch.object(canary.subprocess, 'run', side_effect=[result(0, sha), result(0), result(0)]):
            self.assertTrue(canary.candidate_check(Path('/repo'), sha, 1))
        for responses in ([result(0, 'b' * 40)], [result(0, sha), result(1)], [result(0, sha), result(0), result(1)]):
            with mock.patch.object(canary.subprocess, 'run', side_effect=responses):
                self.assertFalse(canary.candidate_check(Path('/repo'), sha, 1))

    def test_cleanup_escalates_after_leader_exit(self):
        proc = mock.Mock(pid=123)
        with mock.patch.object(canary.os, 'killpg') as kill, \
             mock.patch.object(canary, 'group_exists', side_effect=[True, False]), \
             mock.patch.object(canary.time, 'monotonic', side_effect=[0, 1, 1]), \
             mock.patch.object(canary.time, 'sleep'):
            self.assertTrue(canary.stop_group(proc, 1))
        self.assertEqual(kill.call_args_list, [mock.call(123, signal.SIGTERM), mock.call(123, signal.SIGKILL)])

    def test_rpc_timeout_with_continuous_noise(self):
        class Writer:
            def write(self, value): pass
            def flush(self): pass
        class Noise:
            def get(self, timeout): return '{"method":"notification"}'
        rpc = canary.Rpc.__new__(canary.Rpc)
        rpc.proc = type('Proc', (), {'stdin': Writer()})()
        rpc.timeout, rpc.next_id, rpc.lines = 1, 0, Noise()
        with mock.patch.object(canary.time, 'monotonic', side_effect=[0, 0.25, 0.5, 1.0]):
            with self.assertRaises(TimeoutError):
                rpc.send('test', {})

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
