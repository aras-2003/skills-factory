"""Capture coordinator-observed completions; these records are not host attestations.

The evidence directory and its parent must be trusted. Write-once means this API
never replaces files; a same-user process can still modify them outside this API.
Do not store secrets, transcripts, or sensitive free text in completion messages.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

from scripts.engineering import delegation_handoff as handoff


def _directory(path):
    path = Path(path)
    if path.is_symlink() or not path.is_dir():
        raise ValueError('attempt directory must be a real directory')
    return path


def _write(directory, name, data):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(directory / name, flags, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        # An incomplete file stays in place and blocks reuse of this attempt.
        raise


def _read(directory, name):
    # Opening an attacker-replaced FIFO in blocking mode can hang before fstat.
    fd = os.open(directory / name, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
                 | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError('record must be a single-link regular file')
        data = stream.read(handoff.MAX_HANDOFF_BYTES + 1)
    if len(data) > handoff.MAX_HANDOFF_BYTES:
        raise ValueError('record exceeds size limit')
    return data


def _json(data):
    if not isinstance(data, bytes) or len(data) > handoff.MAX_HANDOFF_BYTES:
        raise ValueError('completion must be bounded bytes')
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=handoff._unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        raise ValueError('invalid completion JSON') from None


def _text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        raise ValueError('identifier must be bounded text')


def _manifest(directory):
    return _json(_read(_directory(directory), 'manifest.json'))


def prepare(directory, input_bytes, *, task_id, attempt_id, fixture_policy_by_case):
    _text(task_id); _text(attempt_id)
    if not isinstance(input_bytes, bytes):
        raise ValueError('input must be bytes')
    item = handoff.read_input(input_bytes)
    if handoff.serialize_input(item) != input_bytes or not item.get('candidate_sha'):
        raise ValueError('canonical input and candidate required')
    cases = item['test_case_ids']
    if not isinstance(fixture_policy_by_case, dict) or set(fixture_policy_by_case) != set(cases):
        raise ValueError('fixture policy must match cases')
    for digest in fixture_policy_by_case.values():
        if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest)):
            raise ValueError('invalid fixture digest')
    manifest = {'version': 1, 'task_id': task_id, 'attempt_id': attempt_id,
                'input_sha256': hashlib.sha256(input_bytes).hexdigest(),
                'candidate_sha': item['candidate_sha'], 'role': item['role'],
                'case_ids': cases, 'fixture_policy_by_case': fixture_policy_by_case}
    path = Path(directory)
    path.mkdir(mode=0o700)  # exclusive: pre-existing directories are rejected
    _write(path, 'input.json', input_bytes)
    raw = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    _write(path, 'manifest.json', raw)
    return hashlib.sha256(raw).hexdigest()


def bind_child(directory, child_id, *, expected_manifest_sha256, expected_input_sha256):
    _text(child_id)
    path = _directory(directory)
    _trusted_manifest(path, expected_manifest_sha256, expected_input_sha256)
    _write(path, 'child.json', json.dumps({'child_id': child_id}, separators=(',', ':')).encode())


def _validate(item, manifest, expected_candidate_sha):
    return handoff.validate_result(item, expected_task_id=manifest['task_id'],
        expected_role=manifest['role'], expected_test_case_ids=manifest['case_ids'],
        expected_candidate_sha=expected_candidate_sha,
        fixture_policy_by_case=manifest['fixture_policy_by_case'])


def _trusted_manifest(path, expected_manifest_sha256, expected_input_sha256):
    raw_manifest = _read(path, 'manifest.json')
    raw_input = _read(path, 'input.json')
    if (hashlib.sha256(raw_manifest).hexdigest() != expected_manifest_sha256 or
            hashlib.sha256(raw_input).hexdigest() != expected_input_sha256):
        raise ValueError('trusted manifest or input digest mismatch')
    manifest = _json(raw_manifest)
    item = handoff.read_input(raw_input)
    if (handoff.serialize_input(item) != raw_input or manifest.get('input_sha256') != expected_input_sha256
            or manifest.get('candidate_sha') != item.get('candidate_sha')
            or manifest.get('role') != item['role'] or manifest.get('case_ids') != item['test_case_ids']):
        raise ValueError('manifest input mismatch')
    return manifest


def capture(directory, child_id, completion_bytes, *, expected_manifest_sha256, expected_input_sha256):
    """Invalid payload is not persisted: coordinator must retain it separately if safe."""
    path = _directory(directory)
    manifest = _trusted_manifest(path, expected_manifest_sha256, expected_input_sha256)
    child_raw = _read(path, 'child.json')
    if child_raw != json.dumps({'child_id': child_id}, separators=(',', ':')).encode():
        raise ValueError('child identity mismatch')
    result = _json(completion_bytes)
    _validate(result, manifest, manifest['candidate_sha'])
    _write(path, 'completion.json', completion_bytes)
    return hashlib.sha256(completion_bytes).hexdigest()


def verify(directory, *, expected_candidate_sha, expected_manifest_sha256,
           expected_input_sha256, expected_child_id, expected_completion_sha256):
    """Expected values must be retained independently from this evidence directory."""
    path = _directory(directory)
    manifest = _trusted_manifest(path, expected_manifest_sha256, expected_input_sha256)
    child_raw = _read(path, 'child.json')
    completion = _read(path, 'completion.json')
    if child_raw != json.dumps({'child_id': expected_child_id}, separators=(',', ':')).encode():
        raise ValueError('child identity mismatch')
    _text(expected_child_id)
    if hashlib.sha256(completion).hexdigest() != expected_completion_sha256:
        raise ValueError('completion digest mismatch')
    return _validate(_json(completion), manifest, expected_candidate_sha)
