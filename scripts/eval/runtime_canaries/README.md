# Local MCP ACL canary

Run only on an authorized local host with `codex-cli 0.159.1`:

```
python3 scripts/eval/runtime_canaries/mcp_acl_canary.py --candidate-sha <40-hex-sha> --output /path/to/sanitized-receipt.json
```

Before launching App Server, the harness requires the supplied candidate SHA to match Git HEAD and checks both tracked worktree and index for changes. Untracked files are ignored. Two temporary HOME and CODEX_HOME directories and two App Server processes isolate the policies. The CLI version check and App Server inherit only PATH and selected locale values; credential and other coordinator environment variables are omitted, including from the fixture environment. No model turn or production integration is used. The receipt excludes nonce values and captures only the expected denial text, sanitized ingress labels, process cleanup and hashes. Exit 0 means all canary cases passed; exit 1 means failed or blocked. Ingress assertions use the final fixture log after process-group termination. Cleanup failure blocks a pass and preserves the temporary path when a process may still write to it. Run with an independently reviewed candidate and preserve the receipt separately from frozen evidence. This canary does not establish model-visible tool schemas, inherited policies, hosted behavior or other host versions.
