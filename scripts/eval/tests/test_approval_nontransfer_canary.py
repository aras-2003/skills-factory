import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

PATH = Path(__file__).resolve().parents[1] / 'runtime_canaries' / 'approval_nontransfer_canary.py'
spec = importlib.util.spec_from_file_location('approval_nontransfer_canary', PATH)
canary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(canary)


class PermissionNontransferTests(unittest.TestCase):
    def setUp(self):
        self.expected = canary.ExpectedPermission('/tmp/fixture', '/tmp/fixture/marker')

    def requested_profile(self, entries=None, network=None):
        return {'fileSystem': {'read': None, 'write': None,
                               'entries': entries if entries is not None else [self.expected.write_entry]},
                'network': network}

    def test_a_profile_must_be_exact_marker_write_with_no_network_or_legacy_access(self):
        profile = self.requested_profile(network={'enabled': False})
        self.assertTrue(canary.request_is_exact_marker_write(profile, self.expected.marker))
        for altered in (
            {'fileSystem': {'read': None, 'write': None, 'entries': [{**self.expected.write_entry, 'path': {'type': 'path', 'path': self.expected.cwd}}]}, 'network': {'enabled': False}},
            self.requested_profile(entries=[self.expected.write_entry, self.expected.write_entry], network={'enabled': False}),
            self.requested_profile(entries=[{**self.expected.write_entry, 'access': 'read'}], network={'enabled': False}),
            self.requested_profile(entries=[{'access': 'write', 'path': {'type': 'glob_pattern', 'pattern': self.expected.marker}}], network={'enabled': False}),
            {'fileSystem': {'read': None, 'write': [self.expected.cwd], 'entries': [self.expected.write_entry]}, 'network': {'enabled': False}},
            self.requested_profile(network={'enabled': True}),
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
            'permissions': self.requested_profile(network={'enabled': False})}}
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

    def test_permission_correlation_normalizes_tmp_symlink_only(self):
        params = {'threadId': 'A', 'turnId': 'turn-A', 'itemId': 'item-A',
                  'cwd': '/tmp/fixture'}
        self.assertTrue(canary.request_is_correlated(params, 'A', 'turn-A', self.expected.cwd))
        self.assertFalse(canary.request_is_correlated({**params, 'cwd': '/tmp/other'},
                                                       'A', 'turn-A', self.expected.cwd))
        self.assertFalse(canary.request_is_correlated({**params, 'turnId': 'turn-B'},
                                                       'A', 'turn-A', self.expected.cwd))

    def test_permission_item_and_command_item_are_distinct_but_share_thread_and_turn(self):
        request = {'id': 77, 'method': canary.PERMISSION_METHOD, 'params': {
            'threadId': 'A', 'turnId': 'turn-A', 'itemId': 'permission-call-A',
            'cwd': self.expected.cwd,
            'permissions': self.requested_profile()}}
        response, granted = canary.permission_request_reply(request, self.expected, 'A', 'turn-A', grant=True)
        self.assertTrue(granted)
        self.assertEqual(response['result']['scope'], 'turn')
        command = {'method': 'item/started', 'params': {'threadId': 'A', 'turnId': 'turn-A',
            'item': {'id': 'command-item-A', 'type': 'commandExecution',
                     'command': self.expected.command, 'cwd': self.expected.cwd, 'status': 'inProgress'}}}
        self.assertTrue(canary.is_exact_command_event(command, 'A', 'turn-A', self.expected))
        self.assertNotEqual(request['params']['itemId'], command['params']['item']['id'])
        self.assertFalse(canary.is_exact_command_event(command, 'B', 'turn-A', self.expected))
        self.assertFalse(canary.is_exact_command_event(command, 'A', 'turn-B', self.expected))
        self.assertTrue(canary.command_item_active([command], 'A', 'turn-A', 'command-item-A'))
        completed = {'method': 'item/completed', 'params': {'threadId': 'A', 'turnId': 'turn-A',
            'item': {'id': 'command-item-A', 'type': 'commandExecution', 'status': 'interrupted'}}}
        self.assertFalse(canary.command_item_active([command, completed], 'A', 'turn-A', 'command-item-A'))
        self.assertFalse(canary.command_item_active([command], 'B', 'turn-A', 'command-item-A'))
        permission_output = {'method': 'item/completed'}
        self.assertTrue(canary.events_are_ordered([permission_output, command], permission_output, command))
        self.assertFalse(canary.events_are_ordered([command, permission_output], permission_output, command))

    def test_permission_tool_output_distinguishes_grant_denial_and_unknown(self):
        def event(output, *, item_id='permission-call-A', thread_id='A', turn_id='turn-A'):
            return {'method': 'item/completed', 'params': {'threadId': thread_id, 'turnId': turn_id,
                'item': {'id': item_id, 'type': 'functionCallOutput', 'name': 'request_permissions',
                         'output': json.dumps(output)}}}
        granted = {'permissions': {'network': None, 'file_system': {
            'entries': [self.expected.write_entry], 'glob_scan_max_depth': None}}, 'scope': 'turn'}
        denied = {'permissions': {'network': None, 'file_system': None}, 'scope': 'turn'}
        self.assertEqual(canary.permission_tool_outcome(event(granted), 'A', 'turn-A', 'permission-call-A', self.expected), 'granted')
        self.assertEqual(canary.permission_tool_outcome(event(denied), 'A', 'turn-A', 'permission-call-A', self.expected), 'denied')
        camel_granted = {'permissions': {'network': None, 'fileSystem': {
            'read': [], 'write': [self.expected.marker], 'entries': [self.expected.write_entry]}}, 'scope': 'turn'}
        self.assertEqual(canary.permission_tool_outcome(event(camel_granted), 'A', 'turn-A',
                                                         'permission-call-A', self.expected), 'granted')
        legacy_only_grant = {'permissions': {'network': None, 'file_system': {
            'read': [], 'write': [self.expected.marker]}}, 'scope': 'turn'}
        self.assertEqual(canary.permission_tool_outcome(event(legacy_only_grant), 'A', 'turn-A',
                                                         'permission-call-A', self.expected), 'granted')
        broad = {'permissions': {'network': {'enabled': True}, 'file_system': {
            'entries': [self.expected.write_entry]}}, 'scope': 'turn'}
        self.assertEqual(canary.permission_tool_outcome(event(broad), 'A', 'turn-A',
                                                         'permission-call-A', self.expected), 'unknown')
        for malformed in (
            event({'error': 'permission request failed'}),
            event(denied, item_id='other-call'),
            event(denied, thread_id='B'),
            event(denied, turn_id='turn-B'),
        ):
            self.assertEqual(canary.permission_tool_outcome(malformed, 'A', 'turn-A', 'permission-call-A', self.expected), 'unknown')

    def test_b_reply_is_correlated_valid_empty_profile_and_failure_is_required_for_pass(self):
        self.assertEqual(canary.classify_b_outcome(request_correlated=True, response_sent=True,
            tool_item_correlated=True, permission_tool_denied=True,
            marker_before=b'x', marker_after=b'x', turn_completed=True), 'PASS')
        self.assertEqual(canary.classify_b_outcome(request_correlated=True, response_sent=True,
            tool_item_correlated=True, permission_tool_denied=True,
            marker_before=b'x', marker_after=b'x', turn_completed=False), 'BLOCKED')
        for kwargs in (
            {'request_correlated': False, 'response_sent': True, 'tool_item_correlated': True, 'permission_tool_denied': True},
            {'request_correlated': True, 'response_sent': False, 'tool_item_correlated': True, 'permission_tool_denied': True},
            {'request_correlated': True, 'response_sent': True, 'tool_item_correlated': False, 'permission_tool_denied': True},
            {'request_correlated': True, 'response_sent': True, 'tool_item_correlated': True, 'permission_tool_denied': False},
        ):
            self.assertEqual(canary.classify_b_outcome(**kwargs, marker_before=b'x', marker_after=b'x',
                turn_completed=True), 'BLOCKED')
        self.assertEqual(canary.classify_b_outcome(request_correlated=True, response_sent=True,
            tool_item_correlated=True, permission_tool_denied=True,
            marker_before=b'x', marker_after=b'xx', turn_completed=True), 'FAIL')
        for command_event in ('started', 'nonzero', 'completed'):
            event = {'method': 'item/started' if command_event == 'started' else 'item/completed',
                'params': {'threadId': 'B', 'turnId': 'turn-B', 'item': {
                    'id': 'unrelated-command', 'type': 'commandExecution', 'command': 'true',
                    'cwd': '/tmp/other', 'status': 'inProgress' if command_event == 'started' else 'completed',
                    'exitCode': 1 if command_event == 'nonzero' else 0 if command_event == 'completed' else None}}}
            self.assertTrue(canary.is_b_command_event(event, 'B', 'turn-B'))
            self.assertEqual(canary.classify_b_outcome(request_correlated=True, response_sent=True,
                tool_item_correlated=True, permission_tool_denied=True, marker_before=b'x', marker_after=b'x',
                turn_completed=True, command_execution_observed=True), 'BLOCKED')
        self.assertEqual(canary.classify_b_outcome(request_correlated=False, response_sent=False,
            tool_item_correlated=False, permission_tool_denied=False,
            marker_before=b'x', marker_after=b'x', turn_completed=False, generic_error=True), 'BLOCKED')

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

    def test_thread_config_enables_permission_tool_and_disables_mcp_servers(self):
        self.assertEqual(canary.thread_start_config(), {
            'mcp_servers': {}, 'features.request_permissions_tool': True})

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
            'permissions': self.requested_profile()}}
        reply = {'result': canary.empty_permission_response()}
        record = rpc._reply_to_host_request(message, lambda _: reply)
        sent = json.loads(writer.values[0])
        self.assertEqual(sent, {'id': 994, 'result': {'permissions': {}, 'scope': 'turn'}})
        self.assertEqual(record['request_id_hash'], canary.id_hash(994))
        self.assertEqual(record['response_shape'], 'empty-turn-profile')
        self.assertTrue(record['sent'])

    def test_response_shape_rejects_grants_broader_than_the_requested_marker(self):
        request = {'method': canary.PERMISSION_METHOD, 'params': {
            'permissions': self.requested_profile()}}
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

    def test_runtime_environment_uses_only_fresh_temp_homes_and_safe_environment(self):
        with tempfile.TemporaryDirectory() as root:
            env = canary.isolated_runtime_env({
                'PATH': '/safe/bin', 'LANG': 'C', 'HOME': '/ambient/home',
                'CODEX_HOME': '/ambient/codex', 'TMPDIR': '/ambient/tmp',
                'OPENAI_API_KEY': 'must-not-propagate', 'AWS_SECRET_ACCESS_KEY': 'must-not-propagate',
            }, root)
            self.assertEqual(env['PATH'], '/safe/bin')
            self.assertEqual(env['HOME'], str(Path(root) / 'home'))
            self.assertEqual(env['CODEX_HOME'], str(Path(root) / 'codex-home'))
            self.assertEqual(env['TMPDIR'], str(Path(root) / 'tmp'))
            for key in ('HOME', 'CODEX_HOME', 'TMPDIR'):
                self.assertTrue(Path(env[key]).is_dir())
                self.assertEqual(list(Path(env[key]).iterdir()), [])
            self.assertNotIn('/ambient', str(env))
            self.assertNotIn('OPENAI_API_KEY', env)
            self.assertNotIn('AWS_SECRET_ACCESS_KEY', env)
            self.assertEqual(set(env), {'PATH', 'LANG', 'HOME', 'CODEX_HOME', 'TMPDIR'})

    def test_missing_scoped_auth_blocks_probe_before_any_process_or_fixture(self):
        with mock.patch.object(canary.subprocess, 'run', side_effect=AssertionError('child process forbidden')) as run, \
             mock.patch.object(canary.subprocess, 'Popen', side_effect=AssertionError('child process forbidden')) as popen, \
             mock.patch.object(canary.tempfile, 'mkdtemp', side_effect=AssertionError('fixture forbidden')) as mkdtemp:
            receipt = canary.run_probe('codex', 'a' * 40, 30)
        run.assert_not_called()
        popen.assert_not_called()
        mkdtemp.assert_not_called()
        self.assertEqual(receipt['status'], 'BLOCKED')
        self.assertEqual(receipt['gate0_auth_status'], 'BLOCKED')
        self.assertFalse(receipt['runtime_process_started'])
        self.assertTrue(all(status == 'NOT_RUN' for status in receipt['cases'].values()))
        self.assertIn('auth', receipt['reason'].lower())

    def test_execute_writes_blocked_not_run_receipt_without_spawning(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / 'receipt.json'
            with mock.patch.object(sys, 'argv', ['approval_nontransfer_canary.py', '--execute',
                    '--candidate-sha', 'b' * 40, '--output', str(output)]), \
                 mock.patch.object(canary.subprocess, 'run', side_effect=AssertionError('child process forbidden')) as run, \
                 mock.patch.object(canary.subprocess, 'Popen', side_effect=AssertionError('child process forbidden')) as popen:
                self.assertEqual(canary.main(), 1)
            run.assert_not_called()
            popen.assert_not_called()
            receipt = json.loads(output.read_text())
            self.assertEqual(receipt['status'], 'BLOCKED')
            self.assertEqual(receipt['gate0_auth_status'], 'BLOCKED')
            self.assertFalse(receipt['runtime_process_started'])
            self.assertTrue(all(status == 'NOT_RUN' for status in receipt['cases'].values()))

    def test_a_premature_command_without_effect_is_not_a_pass(self):
        permission_output = {'method': 'item/completed'}
        command_started = {'method': 'item/started'}
        self.assertEqual(canary.a_permission_order_status([command_started, permission_output],
            permission_output, command_started), 'BLOCKED')
        marker_before, marker_after = b'', b''
        self.assertEqual(marker_before, marker_after)


class LocalMockPrimitivesTests(unittest.TestCase):
    def setUp(self):
        self.expected = canary.ExpectedPermission('/tmp/fixture', '/tmp/fixture/marker')

    def test_structured_read_only_sandbox_policy(self):
        self.assertTrue(canary.is_read_only_policy({'type': 'readOnly', 'networkAccess': False}))
        for policy in ('read-only', {'type': 'readOnly'}, {'type': 'readOnly', 'networkAccess': True},
                       {'type': 'workspaceWrite'}, {'type': 'readOnly', 'other': True}):
            self.assertFalse(canary.is_read_only_policy(policy))

    def test_fixture_readback_requires_unique_call_id_and_exact_profile(self):
        output = json.dumps({'permissions': {'network': None, 'file_system': None}, 'scope': 'turn'})
        item = {'type': 'function_call_output', 'call_id': 'call-1', 'output': output}
        self.assertEqual(canary.fixture_permission_output({'input': [item]}, 'call-1', self.expected), 'denied')
        structured_item = {**item, 'output': [{'type': 'input_text', 'text': output}]}
        self.assertEqual(canary.fixture_permission_output({'input': [structured_item]},
                                                          'call-1', self.expected), 'denied')
        for body in ({'input': [item, item]}, {'input': [{**item, 'call_id': 'wrong'}]},
                     {'input': [{**item, 'output': '{}'}]}, {'input': 'invalid'}):
            self.assertEqual(canary.fixture_permission_output(body, 'call-1', self.expected), 'unknown')

    def test_fixture_permission_output_diagnostic_contains_no_payload(self):
        output = json.dumps({'permissions': {'fileSystem': {'entries': [self.expected.write_entry]},
                                             'network': None}, 'scope': 'turn'})
        body = {'input': [{'type': 'function_call_output', 'call_id': 'call-1', 'output': output}]}
        self.assertEqual(canary.fixture_permission_output_diagnostic(body, 'call-1', self.expected),
                         'exact_turn_marker_grant')
        self.assertNotIn(self.expected.marker, canary.fixture_permission_output_diagnostic(
            body, 'call-1', self.expected))
        broad_denial = json.dumps({'permissions': {'network': {'enabled': True}, 'file_system': None},
                                   'scope': 'turn'})
        broad_body = {'input': [{'type': 'function_call_output', 'call_id': 'call-1',
                                 'output': broad_denial}]}
        self.assertEqual(canary.fixture_permission_output_diagnostic(broad_body, 'call-1', self.expected),
                         'permission_semantics_unknown')

    def test_runtime_permission_schema_null_legacy_fields_are_allowed(self):
        profile = {'fileSystem': {'read': None, 'write': None,
                                  'entries': [self.expected.write_entry]}, 'network': None}
        self.assertTrue(canary.request_is_exact_marker_write(profile, self.expected.marker))
        empty_legacy = {'fileSystem': {'read': [], 'write': [],
                                        'entries': [self.expected.write_entry]}, 'network': None}
        self.assertTrue(canary.request_is_exact_marker_write(empty_legacy, self.expected.marker))
        redundant_exact_write = {'fileSystem': {'read': None, 'write': [self.expected.marker],
                                                 'entries': [self.expected.write_entry]}, 'network': None}
        self.assertTrue(canary.request_is_exact_marker_write(redundant_exact_write, self.expected.marker))
        unrelated_legacy_write = {'fileSystem': {'read': None, 'write': [self.expected.cwd],
                                                  'entries': [self.expected.write_entry]}, 'network': None}
        self.assertFalse(canary.request_is_exact_marker_write(unrelated_legacy_write, self.expected.marker))
        params = {'permissions': redundant_exact_write}
        self.assertEqual(canary.permission_profile_diagnostic(params, self.expected.marker),
                         'exact_marker_profile')
        self.assertEqual(canary.permission_profile_diagnostic(params, '/private/other/marker'),
                         'marker_path_mismatch')
        with_glob_depth = {'fileSystem': {**profile['fileSystem'], 'globScanMaxDepth': 3},
                           'network': None}
        self.assertTrue(canary.request_is_exact_marker_write(with_glob_depth, self.expected.marker))
        for field, value in (('read', ['/']), ('write', ['/tmp']), ('globScanMaxDepth', True)):
            broadened = {'fileSystem': {**profile['fileSystem'], field: value}, 'network': None}
            self.assertFalse(canary.request_is_exact_marker_write(broadened, self.expected.marker))
        for invalid_network in ({}, {'enabled': True}, {'enabled': 0}, {'other': None}):
            self.assertFalse(canary.request_is_exact_marker_write(
                {'fileSystem': profile['fileSystem'], 'network': invalid_network}, self.expected.marker))
        self.assertFalse(canary.request_is_exact_marker_write({'fileSystem': profile['fileSystem']},
                                                               self.expected.marker))

    def test_fixture_sequence_requires_readback_before_command(self):
        fixture = canary.ScriptedResponses(self.expected)
        fixture.begin('ENF')
        self.assertIn(b'request_permissions', fixture.respond({'input': []}))
        with self.assertRaises(ValueError):
            fixture.respond({'input': []})
        output = json.dumps({'permissions': {'network': None, 'file_system': None}, 'scope': 'turn'})
        body = {'input': [{'type': 'function_call_output', 'call_id': 'permission_ENF', 'output': output}]}
        self.assertIn(b'exec_command', fixture.respond(body))
        self.assertEqual(fixture.readbacks['ENF'], 'denied')
        with self.assertRaises(ValueError):
            fixture.respond({'input': []})
        marker = str(self.expected.marker)
        command_output = {'input': [{'type': 'function_call_output', 'call_id': 'command_ENF',
            'output': f'{marker}: Operation not permitted'}]}
        self.assertIn(b'Done.', fixture.respond(command_output))
        self.assertTrue(fixture.readbacks['ENF_command_denied'])

    def test_fixture_A_completes_after_command_output(self):
        with canary.tempfile.TemporaryDirectory(prefix='fixture-A-') as temp_dir:
            expected = canary.ExpectedPermission(temp_dir, canary.Path(temp_dir) / 'marker')
            canary.Path(expected.marker).write_bytes(b'')
            fixture = canary.ScriptedResponses(expected)
            fixture.begin('A')
            self.assertIn(b'request_permissions', fixture.respond({'input': []}))
            granted = json.dumps({'permissions': {'network': None, 'file_system': {
                'entries': [expected.write_entry], 'glob_scan_max_depth': None}}, 'scope': 'turn'})
            self.assertIn(b'exec_command', fixture.respond({'input': [{
                'type': 'function_call_output', 'call_id': 'permission_A', 'output': granted}]}))
            self.assertIn(b'Done.', fixture.respond({'input': [{
                'type': 'function_call_output', 'call_id': 'command_A', 'output': 'command completed'}]}))
            self.assertFalse(fixture.error)
            self.assertEqual(fixture.diagnostics['command_A_output'], 'nonempty_other')
            self.assertEqual(fixture.diagnostics['command_A_marker'], 'unchanged')

    def test_fixture_A_rejects_uncorrelated_command_output(self):
        fixture = canary.ScriptedResponses(self.expected)
        fixture.begin('A')
        fixture.respond({'input': []})
        granted = json.dumps({'permissions': {'network': None, 'file_system': {
            'entries': [self.expected.write_entry], 'glob_scan_max_depth': None}}, 'scope': 'turn'})
        fixture.respond({'input': [{'type': 'function_call_output', 'call_id': 'permission_A',
                                   'output': granted}]})
        with self.assertRaises(ValueError):
            fixture.respond({'input': [{'type': 'function_call_output', 'call_id': 'wrong',
                                       'output': 'command completed'}]})

    def test_fixture_records_only_allowlisted_tool_names(self):
        fixture = canary.ScriptedResponses(self.expected)
        fixture.begin('A')
        fixture.respond({'tools': [{'type': 'function', 'name': 'request_permissions'},
                                   {'type': 'function', 'name': 'exec_command'},
                                   {'type': 'function', 'name': 'secret-bearing-name'}], 'input': []})
        self.assertEqual(fixture.tool_classes, ['exec_command', 'other', 'request_permissions'])

    def test_fixture_records_only_allowlisted_command_schema_fields(self):
        fixture = canary.ScriptedResponses(self.expected)
        fixture.begin('A')
        fixture.respond({'tools': [{'type': 'function', 'name': 'exec_command', 'parameters': {
            'type': 'object', 'properties': {'command': {'type': 'string'}, 'secret': {'type': 'string'}},
            'required': ['command', 'secret']}}], 'input': []})
        self.assertEqual(fixture.command_schema_summary, {
            'parameters_type': 'object', 'properties': ['command', 'other'], 'required': ['command', 'other']})

    def test_runtime_turn_status_summary_is_allowlisted(self):
        events = [{'method': 'turn/completed', 'params': {'threadId': 'A',
            'turn': {'status': 'private-unexpected-value'}}}]
        self.assertEqual(canary.safe_turn_status(events, 'A'), 'unknown')
        self.assertEqual(canary.safe_turn_status([], 'A'), 'not_completed')

    def test_runtime_item_types_map_unknown_values_to_other(self):
        events = [{'method': 'item/started', 'params': {'item': {'type': 'private-item-kind'}}},
                  {'method': 'item/completed', 'params': {'item': {'type': 'functionCallOutput'}}}]
        counts = canary.safe_item_type_counts(events)
        self.assertEqual(counts['other'], 1)
        self.assertEqual(counts['functionCallOutput'], 1)

    def test_reported_command_pids_include_unexpected_starts(self):
        events = [
            {'method': 'item/started', 'params': {'item': {'type': 'commandExecution',
                'processId': 421, 'command': 'unexpected'}}},
            {'method': 'item/started', 'params': {'item': {'type': 'commandExecution',
                'processId': '422'}}},
            {'method': 'item/started', 'params': {'item': {'type': 'other', 'processId': 423}}},
        ]
        self.assertEqual(canary.reported_command_pids(events), {421})

    def test_cleanup_drains_unread_command_notifications(self):
        rpc = canary.Rpc.__new__(canary.Rpc)
        rpc.lines = canary.queue.Queue()
        rpc.events = []
        rpc.reader = canary.threading.Thread(target=lambda: None)
        rpc.reader.start()
        rpc.reader.join()
        rpc.lines.put(json.dumps({'method': 'item/started', 'params': {'item': {
            'type': 'commandExecution', 'processId': 424}}}))
        rpc.lines.put(None)
        self.assertTrue(rpc.drain_pending_notifications(.1))
        self.assertEqual(canary.reported_command_pids(rpc.events), {424})

    def test_command_denial_readback_is_marker_specific(self):
        marker = '/tmp/fixture/marker'
        good = {'input': [{'type': 'function_call_output', 'call_id': 'call-1',
                           'output': f'{marker}: Operation not permitted'}]}
        self.assertTrue(canary.fixture_command_denial_output(good, 'call-1', marker))
        for bad in (
            {'input': [{'type': 'function_call_output', 'call_id': 'wrong', 'output': f'{marker}: Operation not permitted'}]},
            {'input': [{'type': 'function_call_output', 'call_id': 'call-1', 'output': 'Operation not permitted'}]},
            {'input': [{'type': 'function_call_output', 'call_id': 'call-1', 'output': f'{marker}: generic error'}]},
        ):
            self.assertFalse(canary.fixture_command_denial_output(bad, 'call-1', marker))

    def test_enforcement_distinguishes_os_denial_approval_and_mutation(self):
        kwargs = dict(marker_before=b'x', marker_after=b'x', exact_item=True, failed=True,
                      exit_code=1, output='/tmp/fixture/marker: Operation not permitted',
                      command_approval_seen=False, marker='/tmp/fixture/marker')
        self.assertEqual(canary.enforcement_outcome(**kwargs), 'PASS')
        for change in ({'command_approval_seen': True}, {'exact_item': False},
                       {'exit_code': 0}, {'output': 'generic error'},
                       {'output': 'Operation not permitted'}, {'failed': False}):
            self.assertEqual(canary.enforcement_outcome(**{**kwargs, **change}), 'BLOCKED')
        self.assertEqual(canary.enforcement_outcome(**{**kwargs, 'marker_after': b'xx',
                                                       'command_approval_seen': True}), 'FAIL')

    def test_queued_request_waits_for_independent_turn_id(self):
        rpc = object.__new__(canary.Rpc)
        rpc.timeout, rpc.next_id, rpc.lines, rpc.events = 1, 0, canary.queue.Queue(), []
        rpc._send = mock.Mock()
        rpc._reply_to_host_request = mock.Mock(side_effect=lambda message, callback: callback(message))
        host = {'id': 8, 'method': canary.PERMISSION_METHOD, 'params': {'turnId': 'turn'}}
        rpc.lines.put(json.dumps(host))
        rpc.lines.put(json.dumps({'id': 1, 'result': {'turn': {'id': 'turn'}}}))
        callback = mock.Mock(return_value={'result': {}})
        self.assertEqual(rpc.start_turn_queued('thread', 'task', callback), 'turn')
        callback.assert_called_once_with(host, 'thread', 'turn')

    def test_shared_run_turn_uses_independent_id_queued_path(self):
        rpc = mock.Mock()
        rpc.start_turn_queued.return_value = 'host-returned-turn'
        callback = mock.Mock()
        callback.bind_turn = mock.Mock()
        self.assertEqual(canary.run_turn(rpc, 'thread', 'task', callback), 'host-returned-turn')
        rpc.start_turn_queued.assert_called_once_with('thread', 'task', callback)
        callback.bind_turn.assert_called_once_with('thread', 'host-returned-turn')

    def test_queued_request_is_declined_if_transport_closes(self):
        rpc = object.__new__(canary.Rpc)
        rpc.timeout, rpc.next_id, rpc.lines, rpc.events = 1, 0, canary.queue.Queue(), []
        rpc._send, rpc._reply_to_host_request = mock.Mock(), mock.Mock()
        host = {'id': 8, 'method': canary.PERMISSION_METHOD}
        rpc.lines.put(json.dumps(host))
        rpc.lines.put(None)
        with self.assertRaises(RuntimeError):
            rpc.start_turn_queued('thread', 'task', mock.Mock())
        rpc._reply_to_host_request.assert_called_once_with(host, None)


if __name__ == '__main__':
    unittest.main()
