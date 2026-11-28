"""Coordinator-observed native completion capture contract, without host attestation."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from scripts.engineering import delegation_handoff as handoff
from tests.test_delegation_handoff import valid_input


class CaptureFacade:
    """Coordinator-retained anchors, outside the evidence directory."""
    def __init__(self, api):
        self.api, self.anchors = api, {}

    def prepare(self, directory, input_bytes, **kwargs):
        manifest_sha = self.api.prepare(directory, input_bytes, **kwargs)
        self.anchors[str(directory)] = {'manifest': manifest_sha, 'input': hashlib.sha256(input_bytes).hexdigest()}
        return manifest_sha

    def bind_child(self, directory, child_id):
        a = self.anchors[str(directory)]
        self.api.bind_child(directory, child_id, expected_manifest_sha256=a['manifest'], expected_input_sha256=a['input'])
        a['child'] = child_id

    def capture(self, directory, child_id, raw):
        a = self.anchors[str(directory)]
        digest = self.api.capture(directory, child_id, raw, expected_manifest_sha256=a['manifest'], expected_input_sha256=a['input'])
        a['completion'] = digest
        return digest

    def verify(self, directory, *, expected_candidate_sha):
        a = self.anchors[str(directory)]
        return self.api.verify(directory, expected_candidate_sha=expected_candidate_sha,
            expected_manifest_sha256=a['manifest'], expected_input_sha256=a['input'],
            expected_child_id=a['child'], expected_completion_sha256=a['completion'])


class NativeHandoffCaptureTests(unittest.TestCase):
    def setUp(self):
        from scripts.engineering import native_handoff_capture
        self.capture = CaptureFacade(native_handoff_capture)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name) / 'attempt'
        self.input = handoff.serialize_input(valid_input())
        self.policy = {'AGENT-01': None, 'HANDOFF-01': None}
        self.result = {
            'task_id': 'task-1', 'role': 'sf-test-executor', 'status': 'PASS',
            'candidate_sha': 'b' * 40, 'changed_paths': [],
            'test_case_outcomes': [{'case_id': k, 'status': 'PASS'} for k in self.policy],
            'command_exit_codes': [{'command': 'python -m unittest', 'exit_code': 0}],
            'evidence_refs': ['tests/test_delegation_handoff.py'], 'material_findings': [],
            'residual_risks': [], 'next_action': 'review', 'usage': None,
        }

    def prepare(self):
        return self.capture.prepare(self.directory, self.input, task_id='task-1',
                                    attempt_id='attempt-1', fixture_policy_by_case=self.policy)

    def wire(self):
        return json.dumps(self.result, ensure_ascii=False, indent=2).encode('utf-8') + b'\n'

    def test_capture_preserves_bytes_and_rejects_stale_candidate(self):
        self.prepare()
        self.capture.bind_child(self.directory, 'child-1')
        raw = self.wire()
        self.capture.capture(self.directory, 'child-1', raw)
        verified = self.capture.verify(self.directory, expected_candidate_sha='b' * 40)
        self.assertEqual('PASS', verified['status'])
        with self.assertRaisesRegex(ValueError, 'candidate SHA mismatch'):
            self.capture.verify(self.directory, expected_candidate_sha='c' * 40)
        self.assertEqual('PASS', self.capture.verify(self.directory, expected_candidate_sha='b' * 40)['status'])
        self.assertEqual(raw, (self.directory / 'completion.json').read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), hashlib.sha256((self.directory / 'completion.json').read_bytes()).hexdigest())

    def test_attempt_and_result_are_write_once_and_child_is_bound(self):
        self.prepare()
        with self.assertRaises((ValueError, FileExistsError)):
            self.prepare()
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.capture.capture(self.directory, 'child-1', self.wire())
        self.capture.bind_child(self.directory, 'child-1')
        with self.assertRaises((ValueError, FileExistsError)):
            self.capture.bind_child(self.directory, 'child-2')
        with self.assertRaises(ValueError):
            self.capture.capture(self.directory, 'child-2', self.wire())
        self.capture.capture(self.directory, 'child-1', self.wire())
        with self.assertRaises((ValueError, FileExistsError)):
            self.capture.capture(self.directory, 'child-1', b'{}')
        self.assertEqual('PASS', self.capture.verify(self.directory, expected_candidate_sha='b' * 40)['status'])

    def test_rejects_incorrect_trusted_policy_or_input(self):
        with self.assertRaises(ValueError):
            self.capture.prepare(self.directory, self.input, task_id='task-1', attempt_id='a',
                                 fixture_policy_by_case={'AGENT-01': None})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                self.capture.prepare(Path(tmp) / 'x', b'{}', task_id='task-1', attempt_id='a',
                                     fixture_policy_by_case=self.policy)

    def test_rejects_untrusted_completion_shapes_and_permissions(self):
        for raw in (b'{', b'\xff', b'[]', b' ' * 16385,
                    b'{"task_id":"x","task_id":"y"}',
                    self.wire().replace(b'"usage": null', b'"permissions": {}, "usage": null')):
            with self.subTest(raw=raw[:60]), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp) / 'attempt'
                self.capture.prepare(directory, self.input, task_id='task-1', attempt_id='a',
                                     fixture_policy_by_case=self.policy)
                self.capture.bind_child(directory, 'child-1')
                with self.assertRaises(ValueError):
                    self.capture.capture(directory, 'child-1', raw)

    def test_rejects_result_binding_mismatch(self):
        for field, value in (('task_id', 'wrong'), ('role', 'sf-developer-high'),
                             ('candidate_sha', 'c' * 40)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp) / 'attempt'
                self.capture.prepare(directory, self.input, task_id='task-1', attempt_id='a',
                                     fixture_policy_by_case=self.policy)
                self.capture.bind_child(directory, 'child-1')
                payload = dict(self.result, **{field: value})
                with self.assertRaises(ValueError):
                    self.capture.capture(directory, 'child-1', json.dumps(payload).encode())

    def test_rejects_symlink_attempt_directory(self):
        target = Path(self.tmp.name) / 'existing'
        target.mkdir()
        self.directory.symlink_to(target, target_is_directory=True)
        with self.assertRaises((ValueError, OSError)):
            self.prepare()
        self.assertEqual([], list(target.iterdir()))

    def test_tampered_records_are_rejected(self):
        for filename in ('input.json', 'manifest.json', 'child.json', 'completion.json'):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp) / 'attempt'
                self.capture.prepare(directory, self.input, task_id='task-1', attempt_id='a',
                                     fixture_policy_by_case=self.policy)
                self.capture.bind_child(directory, 'child-1')
                self.capture.capture(directory, 'child-1', self.wire())
                with (directory / filename).open('ab') as stream:
                    stream.write(b' ')
                with self.assertRaises(ValueError):
                    self.capture.verify(directory, expected_candidate_sha='b' * 40)

    def test_replacing_all_records_cannot_replace_external_anchors(self):
        self.prepare()
        self.capture.bind_child(self.directory, 'child-1')
        self.capture.capture(self.directory, 'child-1', self.wire())
        manifest = json.loads((self.directory / 'manifest.json').read_bytes())
        manifest['task_id'] = 'attacker'
        (self.directory / 'manifest.json').write_text(json.dumps(manifest))
        (self.directory / 'child.json').write_text('{"child_id":"attacker"}')
        forged = dict(self.result, task_id='attacker')
        (self.directory / 'completion.json').write_text(json.dumps(forged))
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            self.capture.verify(self.directory, expected_candidate_sha='b' * 40)

    @unittest.skipUnless(hasattr(os, 'mkfifo') and hasattr(os, 'O_NONBLOCK'), 'requires FIFO support')
    def test_fifo_record_is_rejected_without_blocking(self):
        self.prepare()
        path = self.directory / 'manifest.json'
        path.unlink()
        os.mkfifo(path)
        # Bound the entire attempt so a blocking open fails the regression promptly.
        code = (
            'from pathlib import Path\n'
            'from scripts.engineering.native_handoff_capture import _read\n'
            'import sys\n'
            'try:\n _read(Path(sys.argv[1]), "manifest.json")\n'
            'except ValueError:\n sys.exit(0)\n'
            'sys.exit(1)\n'
        )
        result = subprocess.run([sys.executable, '-c', code, str(self.directory)],
                                capture_output=True, timeout=3, check=False)
        self.assertEqual(0, result.returncode, result.stderr.decode(errors='replace'))

    def test_fixture_digest_must_match_independently_frozen_policy(self):
        self.policy['HANDOFF-01'] = 'd' * 64
        self.prepare()
        self.capture.bind_child(self.directory, 'child-1')
        self.result['test_case_outcomes'][1]['fixture_sha256'] = 'c' * 64
        with self.assertRaises(ValueError):
            self.capture.capture(self.directory, 'child-1', self.wire())
        self.result['test_case_outcomes'][1]['fixture_sha256'] = 'd' * 64
        self.capture.capture(self.directory, 'child-1', self.wire())
        self.assertEqual('PASS', self.capture.verify(self.directory, expected_candidate_sha='b' * 40)['status'])

    def test_concurrent_completion_has_single_writer(self):
        self.prepare()
        self.capture.bind_child(self.directory, 'child-1')
        def attempt():
            try:
                self.capture.capture(self.directory, 'child-1', self.wire())
                return 'success'
            except FileExistsError:
                return 'exists'
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: attempt(), range(2)))
        self.assertCountEqual(['success', 'exists'], outcomes)
        self.assertEqual('PASS', self.capture.verify(self.directory, expected_candidate_sha='b' * 40)['status'])


if __name__ == '__main__':
    unittest.main()
