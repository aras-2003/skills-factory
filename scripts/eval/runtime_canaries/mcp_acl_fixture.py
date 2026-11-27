#!/usr/bin/env python3
"""Disposable, newline-delimited JSON-RPC MCP fixture; never use with real data."""
import json
import os
import signal
import sys

log = sys.argv[1]
with open(log, 'a', encoding='utf-8', buffering=1) as out:
    out.write(json.dumps({'event': 'start', 'pid': os.getpid()}) + '\n')
    def terminate(signum, frame):
        out.write(json.dumps({'event': 'exit', 'pid': os.getpid(), 'signal': signum}) + '\n')
        sys.exit(0)
    signal.signal(signal.SIGTERM, terminate)
    for line in sys.stdin:
        try:
            msg = json.loads(line)
            method, params = msg.get('method'), msg.get('params') or {}
            if method == 'initialize':
                result = {'protocolVersion': params['protocolVersion'], 'capabilities': {'tools': {}}, 'serverInfo': {'name': 'canary', 'version': '1'}}
            elif method == 'tools/list':
                result = {'tools': [{'name': name, 'inputSchema': {'type': 'object', 'properties': {'nonce': {'type': 'string'}}, 'required': ['nonce']}} for name in ('allowed', 'forbidden')]}
            elif method == 'tools/call':
                name, nonce = params.get('name'), (params.get('arguments') or {}).get('nonce')
                out.write(json.dumps({'event': 'call', 'tool': name, 'nonce': nonce}) + '\n')
                result = {'content': [{'type': 'text', 'text': json.dumps({'tool': name, 'nonce': nonce})}]}
            elif method == 'ping':
                result = {}
            else:
                if 'id' in msg:
                    print(json.dumps({'jsonrpc': '2.0', 'id': msg['id'], 'error': {'code': -32601, 'message': 'method not found'}}), flush=True)
                continue
            if 'id' in msg:
                print(json.dumps({'jsonrpc': '2.0', 'id': msg['id'], 'result': result}), flush=True)
        except (ValueError, KeyError, TypeError):
            sys.exit(2)
