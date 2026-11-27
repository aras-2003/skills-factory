import importlib.util
import json
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'runtime_canaries' / 'approval_nontransfer_canary.py'
spec = importlib.util.spec_from_file_location('approval_nontransfer_canary', PATH)
canary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(canary)


class PermissionNontransferTests(unittest.TestCase):
    def setUp(self):
        self.expected = canary.ExpectedPermission('/tmp/fixture', '/tmp/fixture/marker')

    def test_a_profile_must_be_exact_marker_write_with_no_network_or_legacy_access(self):
        profile = {'fileSystem': {'entries': [self.expected.write_entry]}, 'network': {'enabled': False}}
        self.assertTrue(canary.request_is_exact_marker_write(profile, self.expected.marker))
        for altered in (
            {'fileSystem': {'entries': [{**self.expected.write_entry, 'path': {'type': 'path', 'path': self.expected.cwd}}]}},
            {'fileSystem': {'entries': [self.expected.write_entry, self.expected.write_entry]}},
            {'fileSystem': {'entries': [{**self.expected.write_entry, 'access': 'read'}]}},
            {'fileSystem': {'entries': [{'access': 'write', 'path': {'type': 'glob_pattern', 'pattern': self.expected.marker}}]}},
            {'fileSystem': {'entries': [self.expected.write_entry], 'write': [self.expected.marker]}},
            {'fileSystem': {'entries': [self.expected.write_entry]}, 'network': {'enabled': True}},
            {'fileSystem': {'entries': [self.expected.write_entry]}, 'other': {}},
        ):
            self.assertFalse(canary.request_is_exact_marker_write(altered, self.expected.marker))

    def test_responses_have_exact_turn_scope_and_distinct_profiles(self):
        self.assertEqual(canary.permission_response(self.expected), {
            'permissions': {'fileSystem': {'entries': [self.expected.write_entry]}}, 'scope': 'turn'})
        self.assertEqual(canary.empty_permission_response(), {'permissions': {}, 'scope': 'turn'})
        self.assertNotIn('session', str(canary.permission_response(self.expected)))

    def test_a_grant_requires_correlated_ids_and_exact_permission_request(self):
        message = {'id': 77, 'method': canary.PERMISSION_METHOD, 'params': {
            'threadId': 'A', 'turnId': 'turn-A', 'itemId': 'item-A', 'cwd': self.expected.cwd,
            'permissions': {'fileSystem': {'entries': [self.expected.write_entry]}, 'network': {'enabled': False}}}}
        response, granted = canary.permission_request_reply(message, self.expected, 'A', 'turn-A', grant=True)
        self.assertEqual(response, {'result': canary.permission_response(self.expected)})
        self.assertTrue(granted)
        for bad in (
            {**message, 'params': {**message['params'], 'threadId': 'B'}},
            {**message, 'params': {**message['params'], 'turnId': 'turn-B'}},
            {**message, 'params': {**message['params'], 'itemId': ''}},
            {**message, 'params': {**message['params'], 'permissions': {'fileSystem': {'entries': []}}}},
        ):
            safe_reply, was_granted = canary.permission_request_reply(bad, self.expected, 'A', 'turn-A', grant=True)
            self.assertEqual(safe_reply, {'result': canary.empty_permission_response()})
            self.assertFalse(was_granted)

    def test_b_reply_is_correlated_valid_empty_profile_and_failure_is_required_for_pass(self):
        self.assertEqual(canary.classify_b_outcome(request_correlated=True, response_sent=True,
            item_correlated=True, item_status='failed', marker_before=b'x', marker_after=b'x'), 'PASS')
        for kwargs in (
            {'request_correlated': False, 'response_sent': True, 'item_correlated': True, 'item_status': 'failed'},
            {'request_correlated': True, 'response_sent': False, 'item_correlated': True, 'item_status': 'failed'},
            {'request_correlated': True, 'response_sent': True, 'item_correlated': False, 'item_status': 'failed'},
            {'request_correlated': True, 'response_sent': True, 'item_correlated': True, 'item_status': 'completed'},
        ):
            self.assertEqual(canary.classify_b_outcome(**kwargs, marker_before=b'x', marker_after=b'x'), 'BLOCKED')
        self.assertEqual(canary.classify_b_outcome(request_correlated=True, response_sent=True,
            item_correlated=True, item_status='completed', marker_before=b'x', marker_after=b'xx'), 'FAIL')
        self.assertEqual(canary.classify_b_outcome(request_correlated=False, response_sent=False,
            item_correlated=False, item_status='failed', marker_before=b'x', marker_after=b'x', generic_error=True), 'BLOCKED')

    def test_unknown_host_request_uses_json_rpc_error_not_permissions_response(self):
        reply = canary.unknown_request_reply({'id': 88, 'method': 'unknown/request'})
        self.assertEqual(reply, {'error': {'code': -32601, 'message': 'Unsupported App Server request'}})
        self.assertNotIn('result', reply)
        command_reply = canary.unknown_request_reply({'id': 89, 'method': canary.COMMAND_APPROVAL_METHOD})
        self.assertEqual(command_reply, {'result': {'decision': 'decline'}})
        self.assertNotIn('permissions', command_reply.get('result', {}))

    def test_mcp_status_requires_explicit_empty_list(self):
        self.assertTrue(canary.mcp_status_is_empty({'result': {'data': []}}))
        for malformed in (
            {'result': {}}, {'result': {'data': None}},
            {'result': {'data': {}}}, {'result': {'data': [], 'nextCursor': 'more'}},
            {'error': {'code': -1}},
        ):
            self.assertFalse(canary.mcp_status_is_empty(malformed))

    def test_response_must_match_original_json_rpc_and_host_item_ids(self):
        request = {'id': 77, 'threadId': 'thread-B', 'turnId': 'turn-B', 'itemId': 'item-B'}
        record = {'request_id_hash': canary.id_hash(77), 'thread_id_hash': canary.id_hash('thread-B'),
            'turn_id_hash': canary.id_hash('turn-B'), 'item_id_hash': canary.id_hash('item-B'),
            'response_shape': 'empty-turn-profile', 'scope': 'turn', 'sent': True}
        self.assertTrue(canary.response_matches([record], request, shape='empty-turn-profile'))
        self.assertFalse(canary.response_matches([{**record, 'request_id_hash': canary.id_hash(78)}], request, shape='empty-turn-profile'))
        self.assertFalse(canary.response_matches([{**record, 'item_id_hash': canary.id_hash('other')}], request, shape='empty-turn-profile'))

    def test_rpc_echoes_permission_reply_with_original_host_request_id(self):
        class Writer:
            def __init__(self):
                self.values = []
            def write(self, value):
                self.values.append(value)
            def flush(self):
                pass
        writer = Writer()
        rpc = canary.Rpc.__new__(canary.Rpc)
        rpc.proc = type('Proc', (), {'stdin': writer})()
        rpc.host_responses = []
        message = {'id': 994, 'method': canary.PERMISSION_METHOD, 'params': {
            'threadId': 'B', 'turnId': 'turn-B', 'itemId': 'item-B', 'cwd': self.expected.cwd,
            'permissions': {'fileSystem': {'entries': [self.expected.write_entry]}}}}
        reply = {'result': canary.empty_permission_response()}
        record = rpc._reply_to_host_request(message, lambda _: reply)
        sent = json.loads(writer.values[0])
        self.assertEqual(sent, {'id': 994, 'result': {'permissions': {}, 'scope': 'turn'}})
        self.assertEqual(record['request_id_hash'], canary.id_hash(994))
        self.assertEqual(record['response_shape'], 'empty-turn-profile')
        self.assertTrue(record['sent'])

    def test_response_shape_rejects_grants_broader_than_the_requested_marker(self):
        request = {'method': canary.PERMISSION_METHOD, 'params': {'permissions': {
            'fileSystem': {'entries': [self.expected.write_entry]}}}}
        self.assertEqual(canary.permission_reply_shape(request,
            {'result': canary.permission_response(self.expected)}), 'turn-profile')
        broad = {'result': {'permissions': {'fileSystem': {'entries': [
            self.expected.write_entry, self.expected.write_entry]}}, 'scope': 'turn'}}
        self.assertEqual(canary.permission_reply_shape(request, broad), 'invalid-permission-reply')

    def test_receipt_hashes_ids_and_omits_commands_paths_and_raw_request(self):
        receipt = canary.sanitized_receipt(thread_ids={'A': 'private-A', 'B': 'private-B'},
            turn_ids={'A': 'turn-A', 'B': 'turn-B'}, item_ids={'A': 'item-A', 'B': 'item-B'},
            marker=b'x', cost=None)
        encoded = str(receipt)
        for value in ('private-A', 'private-B', 'turn-A', 'turn-B', 'item-A', 'item-B', '/tmp/fixture', 'printf'):
            self.assertNotIn(value, encoded)
        self.assertEqual(receipt['cost'], 'UNKNOWN')
        self.assertEqual(receipt['marker_length'], 1)

    def test_cleanup_gates_pass_without_erasing_proven_fail(self):
        self.assertEqual(canary.finalize_case('PASS', cleanup_ok=False, marker_ok=True), 'BLOCKED')
        self.assertEqual(canary.finalize_case('PASS', cleanup_ok=True, marker_ok=False), 'BLOCKED')
        self.assertEqual(canary.finalize_case('FAIL', cleanup_ok=False, marker_ok=False), 'FAIL')


if __name__ == '__main__':
    unittest.main()
