#!/usr/bin/env python3
"""Exercise Codex app-server command/exec sandbox policies with one synthetic marker."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path('/private/tmp/sdlc-cli-runtime-canary')
MARKER = ROOT / '.sdlc-acl-canary-synthetic'
DATA = b'SDLC ACL canary 2026-11-27\n'


def call(policy: str) -> dict:
    source = (
        "from pathlib import Path; import hashlib; "
        "p=Path('.sdlc-acl-canary-synthetic'); "
        f"data={DATA!r}; p.open('xb').write(data); "
        "print('WRITE_SUCCEEDED', hashlib.sha256(data).hexdigest())"
    )
    proc = subprocess.Popen(
        ['codex', 'app-server', '--listen', 'stdio://'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )

    def send(message):
        proc.stdin.write(json.dumps(message, separators=(',', ':')) + '\n')
        proc.stdin.flush()

    def receive(target_id, timeout=30):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            line = proc.stdout.readline()
            if not line:
                raise RuntimeError('app-server closed before response')
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get('id') == target_id:
                return msg
        raise TimeoutError('app-server response timed out')

    try:
        send({'method':'initialize','id':1,'params':{'clientInfo':{'name':'sdlc-acl-canary','title':'SDLC ACL Canary','version':'1'},'capabilities':{'experimentalApi':True}}})
        init = receive(1)
        if 'error' in init:
            return {'phase':'initialize','rpc_error_code':init['error'].get('code')}
        send({'method':'initialized','params':{}})
        send({'method':'command/exec','id':2,'params':{
            'command':['python3','-c',source],
            'cwd':str(ROOT),
            'sandboxPolicy':{'type':policy},
            'timeoutMs':10000,
        }})
        result = receive(2, timeout=30)
        if 'error' in result:
            err = result['error']
            return {'phase':'command','rpc_error_code':err.get('code'),'rpc_error_message_length':len(err.get('message',''))}
        payload = result.get('result',{})
        err = payload.get('stderr','')
        out = payload.get('stdout','')
        low = err.lower()
        errno_match = re.search(r"\[errno\s+(\d+)\]\s*([^\n]+)", err, re.IGNORECASE)
        exception_match = re.search(r"\b(PermissionError|OSError|FileNotFoundError)\b", err)
        denial_phrase = next((phrase for phrase in (
            'operation not permitted',
            'permission denied',
            'read-only file system',
            'sandbox denied',
        ) if phrase in low), None)
        return {
            'phase':'command',
            'policy':policy,
            'exit_code':payload.get('exitCode'),
            'stdout_chars':len(out),
            'stdout_sha256':hashlib.sha256(out.encode()).hexdigest() if out else None,
            'stderr_chars':len(err),
            'stderr_sha256':hashlib.sha256(err.encode()).hexdigest() if err else None,
            'denial_indicator':denial_phrase is not None,
            'denial_phrase_category':denial_phrase.replace(' ', '_') if denial_phrase else None,
            'exception_type':exception_match.group(1) if exception_match else None,
            'os_errno':int(errno_match.group(1)) if errno_match else None,
            'os_error_category':errno_match.group(2).strip()[:80] if errno_match else None,
            'sandbox_context_indicator':any(s in low for s in ('sandbox','seatbelt','operation not permitted')),
            'success_indicator':'WRITE_SUCCEEDED' in out,
        }
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)


if MARKER.exists():
    raise SystemExit('probe marker must be absent before start')
positive = call('workspaceWrite')
pos_bytes = MARKER.read_bytes() if MARKER.exists() else None
positive['marker_exact'] = pos_bytes == DATA
positive['marker_sha256'] = hashlib.sha256(pos_bytes).hexdigest() if pos_bytes is not None else None
if MARKER.exists():
    MARKER.unlink()
negative = call('readOnly')
negative['marker_absent'] = not MARKER.exists()
negative['source_status_clean'] = subprocess.run(['git','status','--porcelain'],cwd=ROOT,capture_output=True,text=True).stdout.strip() == ''
negative['candidate_sha'] = subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip()
print(json.dumps({'positive_control':positive,'negative_control':negative},sort_keys=True,separators=(',',':')))
