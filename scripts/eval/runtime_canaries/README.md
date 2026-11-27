# Local MCP ACL canary

Run only on an authorized local host with `codex-cli 0.159.1`:

```
python3 scripts/eval/runtime_canaries/mcp_acl_canary.py --candidate-sha <40-hex-sha> --output /path/to/sanitized-receipt.json
```

The recorded candidate SHA is supplied by the operator and must be independently verified. Two temporary HOME and CODEX_HOME directories and two App Server processes isolate the policies. The CLI version check and App Server inherit only PATH and selected locale values; credential and other coordinator environment variables are omitted, including from the fixture environment. No model turn or production integration is used. The receipt excludes nonce values and captures only the expected denial text, sanitized ingress labels, process cleanup and hashes. Exit 0 means all canary cases passed; exit 1 means failed or blocked. Cleanup failure blocks a pass. Run with an independently reviewed candidate and preserve the receipt separately from frozen evidence. This canary does not establish model-visible tool schemas, inherited policies, hosted behavior or other host versions.
