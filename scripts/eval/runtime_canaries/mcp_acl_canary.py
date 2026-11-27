#!/usr/bin/env python3
"""Local App Server 0.159.1 direct-RPC ACL canary. No model turn is made."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

FIXTURE = Path(__file__).with_name('mcp_acl_fixture.py').resolve()
DENIAL = "tool 'forbidden' is disabled for MCP server 'canary'"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def isolated_environment(root, source):
    """Allow only executable lookup and locale; isolate all user state."""
    env = {key: source[key] for key in ('PATH', 'LANG', 'LC_ALL', 'LC_CTYPE') if key in source}
    env.setdefault('PATH', os.defpath)
    env.update({'HOME': str(root), 'TMPDIR': str(root), 'CODEX_HOME': str(root / 'codex-home')})
    return env


def catalog(response):
    result = response.get('result', {})
    servers = result.get('data', [])
    if result.get('nextCursor') or len(servers) != 1 or servers[0].get('name') != 'canary' or servers[0].get('toolsError'):
        raise ValueError('unexpected or unavailable canary catalog')
    return sorted(servers[0]['tools'])


def success(response, tool, nonce):
    result = response.get('result', {})
    if 'error' in response or result.get('isError') or not isinstance(result.get('content'), list):
        return False
    return any(item.get('type') == 'text' and item.get('text') == json.dumps({'tool': tool, 'nonce': nonce}) for item in result['content'] if isinstance(item, dict))


def evaluate_ingress(records, nonces):
    calls = [r for r in records if r.get('event') == 'call']
    counts = {label: sum(r.get('nonce') == nonce and r.get('tool') == ('forbidden' if label in ('B', 'X') else 'allowed') for r in calls) for label, nonce in nonces.items()}
    unexpected = any(r.get('nonce') not in nonces.values() or r.get('tool') != ('forbidden' if r.get('nonce') in (nonces['B'], nonces['X']) else 'allowed') for r in calls)
    return counts, unexpected


class Rpc:
    def __init__(self, proc, timeout):
        self.proc, self.timeout, self.next_id = proc, timeout, 0
        self.lines = queue.Queue()
        def read():
            for line in proc.stdout:
                self.lines.put(line)
            self.lines.put(None)
        threading.Thread(target=read, daemon=True).start()

    def send(self, method, params, notification=False):
        msg = {'method': method, 'params': params}
        if not notification:
            self.next_id += 1
            msg['id'] = self.next_id
        self.proc.stdin.write(json.dumps(msg) + '\n')
        self.proc.stdin.flush()
        if notification:
            return None
        import time
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                line = self.lines.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise TimeoutError(method + ' timed out') from exc
            if line is None:
                raise RuntimeError('App Server closed transport')
            message = json.loads(line)
            if message.get('id') == msg['id'] and ('result' in message or 'error' in message):
                return message


def run_policy(binary, policy, timeout):
    root = Path(tempfile.mkdtemp(prefix='mcp-acl-canary-'))
    log = root / 'fixture.jsonl'
    config = {'mcp_servers': {'canary': {'command': sys.executable, 'args': [str(FIXTURE), str(log)]}}}
    restricted = json.loads(json.dumps(config))
    restricted['mcp_servers']['canary'][policy] = ['allowed' if policy == 'enabled_tools' else 'forbidden']
    receipt = {'policy': policy, 'status': 'BLOCKED', 'cases': {}, 'requests': [], 'threads': {}, 'config_sha256': digest(json.dumps({'baseline': config, 'restricted': restricted}, sort_keys=True).encode())}
    proc = None
    records = []
    nonces = {label: secrets.token_hex(16) for label in ('B', 'A', 'X', 'Q')}
    def request(method, params):
        response = rpc.send(method, params)
        entry = {'id': response.get('id'), 'method': method, 'class': 'error' if 'error' in response else 'result'}
        if 'error' in response:
            error = response['error']
            # Only retain the exact expected public error; avoid leaking host paths or secrets.
            entry['error'] = DENIAL if error.get('message') == DENIAL else 'unexpected error (redacted)'
            entry['code'] = error.get('code')
        receipt['requests'].append(entry)
        return response
    try:
        env = isolated_environment(root, os.environ)
        Path(env['CODEX_HOME']).mkdir()
        proc = subprocess.Popen([binary, 'app-server', '--listen', 'stdio://'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1, env=env, cwd=root, start_new_session=True)
        rpc = Rpc(proc, timeout)
        if 'error' in request('initialize', {'clientInfo': {'name': 'mcp-acl-canary', 'version': '1'}, 'capabilities': {'experimentalApi': True}}):
            raise RuntimeError('initialize rejected')
        rpc.send('initialized', {}, notification=True)
        def start(cfg):
            response = request('thread/start', {'cwd': str(root), 'sandbox': 'read-only', 'ephemeral': True, 'config': cfg})
            return response['result']['thread']['id']
        baseline = start(config)
        def status(thread):
            return catalog(request('mcpServerStatus/list', {'threadId': thread, 'serverName': 'canary', 'detail': 'toolsAndAuthOnly'}))
        b1 = status(baseline)
        restricted_id = start(restricted)
        if baseline == restricted_id:
            raise ValueError('thread IDs must differ')
        receipt['threads'] = {'baseline': baseline, 'restricted': restricted_id}
        r, b2 = status(restricted_id), status(baseline)
        receipt['catalogs'] = {'baseline': b1, 'restricted': r, 'baseline_after': b2}
        receipt['cases']['SETUP'] = 'PASS' if b1 == b2 == ['allowed', 'forbidden'] and r == ['allowed'] else 'FAIL'
        def call(thread, tool, label):
            return request('mcpServer/tool/call', {'threadId': thread, 'server': 'canary', 'tool': tool, 'arguments': {'nonce': nonces[label]}})
        b = call(baseline, 'forbidden', 'B')
        if not success(b, 'forbidden', nonces['B']):
            receipt['cases']['BASELINE'] = 'BLOCKED'
            raise RuntimeError('baseline call unavailable')
        a = call(restricted_id, 'allowed', 'A')
        x = call(restricted_id, 'forbidden', 'X')
        q = call(restricted_id, 'allowed', 'Q')
        records = [json.loads(line) for line in log.read_text().splitlines()]
        counts, unexpected = evaluate_ingress(records, nonces)
        receipt['ingress'] = counts
        receipt['fixture_calls'] = [{'tool': item.get('tool'), 'nonce': next((label for label, value in nonces.items() if value == item.get('nonce')), 'UNKNOWN')} for item in records if item.get('event') == 'call']
        receipt['unexpected_ingress'] = unexpected
        receipt['fixture_log_sha256'] = digest(log.read_bytes())
        receipt['cases'].update({'BASELINE': 'PASS' if counts['B'] == 1 else 'FAIL', 'ALLOW': 'PASS' if success(a, 'allowed', nonces['A']) and counts['A'] == 1 else 'FAIL', 'DENY': 'PASS' if x.get('error', {}).get('message') == DENIAL and counts['X'] == 0 else 'FAIL', 'BARRIER': 'PASS' if success(q, 'allowed', nonces['Q']) and counts['Q'] == 1 else 'FAIL'})
        receipt['status'] = 'PASS' if all(v == 'PASS' for v in receipt['cases'].values()) and not unexpected else 'FAIL'
    except (OSError, ValueError, KeyError, TypeError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
        receipt['reason'] = type(exc).__name__  # no raw runtime data
    finally:
        if proc:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=timeout)
            receipt['app_server_exit'] = proc.returncode
            # Group liveness includes all fixture descendants, even after the server exits.
            try:
                os.killpg(proc.pid, 0)
                receipt['residual_process_group'] = proc.pid
                receipt['status'] = 'BLOCKED'
            except ProcessLookupError:
                receipt['residual_process_group'] = None
            if log.exists():
                try:
                    final_records = [json.loads(line) for line in log.read_text().splitlines()]
                    started = {r['pid'] for r in final_records if r.get('event') == 'start'}
                    exited = {r['pid'] for r in final_records if r.get('event') == 'exit'}
                    fixture_processes = []
                    for pid in sorted(started):
                        deadline = time.monotonic() + min(timeout, 2)
                        while True:
                            try:
                                os.kill(pid, 0)
                                alive = True
                            except ProcessLookupError:
                                alive = False
                            if not alive or time.monotonic() >= deadline:
                                break
                            time.sleep(0.05)
                        fixture_processes.append({'pid': pid, 'termination_handler_observed': pid in exited, 'process_absent': not alive})
                    receipt['fixture_processes'] = fixture_processes
                    if any(not p['process_absent'] for p in fixture_processes):
                        receipt['status'] = 'BLOCKED'
                except (OSError, ValueError, KeyError):
                    receipt['fixture_processes'] = 'unavailable'
                    receipt['status'] = 'BLOCKED'
            for stream in (proc.stdin, proc.stdout):
                if stream:
                    stream.close()
        try:
            shutil.rmtree(root)
            receipt['residual_path'] = None
        except OSError:
            receipt['residual_path'] = str(root)
            receipt['status'] = 'BLOCKED'
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex', default='codex')
    parser.add_argument('--candidate-sha', required=True, help='Exact source candidate SHA (recorded, not inferred)')
    parser.add_argument('--output', required=True, help='Sanitized JSON receipt path')
    parser.add_argument('--timeout', type=float, default=20)
    args = parser.parse_args()
    if len(args.candidate_sha) != 40 or any(c not in '0123456789abcdef' for c in args.candidate_sha) or not 0 < args.timeout <= 120:
        parser.error('candidate SHA must be 40 lowercase hex digits; timeout must be in (0, 120]')
    receipt = {'candidate_sha': args.candidate_sha, 'runtime_version': None, 'harness_sha256': digest(Path(__file__).read_bytes()), 'fixture_sha256': digest(FIXTURE.read_bytes()), 'runs': [], 'model_turns': 0}
    try:
        with tempfile.TemporaryDirectory(prefix='mcp-acl-version-') as version_root:
            version_env = isolated_environment(Path(version_root), os.environ)
            Path(version_env['CODEX_HOME']).mkdir()
            version = subprocess.run([args.codex, '--version'], capture_output=True, text=True, timeout=args.timeout, check=True, env=version_env, cwd=version_root).stdout.strip()
        receipt['runtime_version'] = version if version == 'codex-cli 0.159.1' else 'unsupported or unrecognized'
        if receipt['runtime_version'] == 'codex-cli 0.159.1':
            receipt['runs'] = [run_policy(args.codex, policy, args.timeout) for policy in ('enabled_tools', 'disabled_tools')]
    except (OSError, subprocess.SubprocessError):
        receipt['runtime_version'] = 'unavailable'
    receipt['status'] = 'PASS' if len(receipt['runs']) == 2 and all(r['status'] == 'PASS' for r in receipt['runs']) else ('FAIL' if any(r['status'] == 'FAIL' for r in receipt['runs']) else 'BLOCKED')
    Path(args.output).write_text(json.dumps(receipt, indent=2) + '\n')
    return 0 if receipt['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
