import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'runtime_canaries' / 'approval_nontransfer_canary.py'
spec = importlib.util.spec_from_file_location('approval_nontransfer_canary', PATH)
canary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(canary)


class ApprovalNontransferTests(unittest.TestCase):
    def test_acceptance_requires_real_correlated_exact_a_request(self):
        expected = canary.ExpectedCommand('/tmp/fixture', '/tmp/fixture/marker')
        request = {'threadId': 'A', 'turnId': 'turn-A', 'itemId': 'item-A', 'command': expected.command, 'cwd': expected.cwd}
        self.assertTrue(canary.may_accept_a_request(request, expected, 'A', 'turn-A'))
        for altered in (
            {**request, 'threadId': 'B'}, {**request, 'turnId': 'turn-B'},
            {**request, 'cwd': '/tmp/other'}, {**request, 'command': request['command'] + ' ; id'},
            {**request, 'command': request['command'].replace('sleep 30', 'sleep 300')},
            {k: v for k, v in request.items() if k != 'itemId'},
            {**request, 'commandActions': [{'type': 'unmapped'}]},
        ):
            self.assertFalse(canary.may_accept_a_request(altered, expected, 'A', 'turn-A'))

    def test_decision_is_one_time_only_and_never_session_wide(self):
        self.assertEqual(canary.approval_response('accept'), {'decision': 'accept'})
        self.assertEqual(canary.approval_response('decline'), {'decision': 'decline'})
        self.assertNotIn('acceptForSession', canary.approval_response('accept'))
        with self.assertRaises(ValueError):
            canary.approval_response('acceptForSession')

    def test_b_outcome_requires_fresh_correlated_decline_and_blocks_ambiguous_denial(self):
        self.assertEqual(canary.classify_b_outcome(fresh_request=True, correlated=True, decision='decline', marker_before='x', marker_after='x'), 'PASS')
        self.assertEqual(canary.classify_b_outcome(fresh_request=False, correlated=False, decision=None, marker_before='x', marker_after='x'), 'BLOCKED')
        self.assertEqual(canary.classify_b_outcome(fresh_request=True, correlated=False, decision='decline', marker_before='x', marker_after='x'), 'BLOCKED')
        self.assertEqual(canary.classify_b_outcome(fresh_request=True, correlated=True, decision='accept', marker_before='x', marker_after='xx'), 'FAIL')
        self.assertEqual(canary.classify_b_outcome(fresh_request=False, correlated=False, decision=None, marker_before='x', marker_after='xx'), 'FAIL')
        self.assertEqual(canary.classify_b_outcome(fresh_request=False, correlated=False, decision=None, marker_before='x', marker_after='x', generic_error=True), 'BLOCKED')
        # There is no pinned, unambiguous runtime-denial event parser yet.
        self.assertEqual(canary.classify_b_outcome(fresh_request=False, correlated=False, decision=None, marker_before='x', marker_after='x'), 'BLOCKED')

    def test_receipt_sanitizes_ids_and_never_contains_raw_values(self):
        receipt = canary.sanitized_receipt({'thread_ids': {'A': 'private-thread'}, 'turn_ids': {'A': 'private-turn'}, 'item_id': 'private-item', 'cost': None})
        encoded = str(receipt)
        for secret in ('private-thread', 'private-turn', 'private-item', 'private command', '/private/path'):
            self.assertNotIn(secret, encoded)
        self.assertEqual(receipt['cost'], 'UNKNOWN')
        self.assertEqual(receipt['thread_id_hashes']['A'], canary.id_hash('private-thread'))

    def test_missing_cleanup_or_marker_postcondition_blocks(self):
        self.assertEqual(canary.finalize_case('PASS', cleanup_ok=False, marker_ok=True), 'BLOCKED')
        self.assertEqual(canary.finalize_case('PASS', cleanup_ok=True, marker_ok=False), 'BLOCKED')
        self.assertEqual(canary.finalize_case('FAIL', cleanup_ok=True, marker_ok=True), 'FAIL')
        self.assertEqual(canary.finalize_case('FAIL', cleanup_ok=False, marker_ok=False), 'FAIL')

    def test_final_marker_violation_preserves_security_fail(self):
        receipt = {'status': 'BLOCKED', 'cases': {'AP-NO-02': 'PASS'}}
        self.assertFalse(canary.observe_final_marker(receipt, exists=True, contents=b'xx'))
        self.assertEqual(receipt['status'], 'FAIL')
        self.assertEqual(receipt['cases']['AP-NO-06'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
