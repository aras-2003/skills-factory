# Architect review: credential-free permission canary

Decision: A3 / Compose / Review required. The pinned Codex `rust-v0.159.1` App Server tests demonstrate that a credential-free custom Responses provider can emit `request_permissions`, receive a real App Server approval RPC, and verify Codex's tool output. The installed `codex-cli 0.159.1` still needs a separately reviewed local runtime spike; exact-file grant behavior under read-only policy is not established by upstream tests.

Sources:

- [Pinned App Server request_permissions integration test](https://github.com/openai/codex/blob/rust-v0.159.1/codex-rs/app-server/tests/suite/v2/request_permissions.rs#L243)
- [Pinned mock provider configuration](https://github.com/openai/codex/blob/rust-v0.159.1/codex-rs/app-server/tests/common/config.rs#L134)
- [Pinned permission-granted command execution test](https://github.com/openai/codex/blob/rust-v0.159.1/codex-rs/core/tests/suite/request_permissions.rs#L1243)

For a bounded fixture, use a fresh HOME, CODEX_HOME, TMPDIR, and cwd; an explicit custom provider bound to numeric `127.0.0.1:<ephemeral port>`; HTTP Responses SSE; zero retries; websockets disabled; no credential fields; no MCP; and no inherited environment except required executable path and locale. Require trusted egress controls that permit only the fixture endpoint. Validate actual provider selection, structured read-only sandbox policy with network disabled, empty MCP catalog, and fixture ingress. The fixture should validate request path/method/count and sequence only predeclared outputs. Do not retain raw prompts, bodies, headers, or paths.

Keep Gate 0's auth-broker check unchanged. A local mock is a distinct no-credential test path, not a bypass or proof of an auth broker.

Preserve existing `PERM-NT-01..07` acceptance and add a separately named enforcement challenge. In fresh B, first require a correlated valid empty turn-scoped permission result, then deliberately attempt the exact marker append through the scripted fixture. Require correlated sandbox/OS denial, failed command completion for the intended command, and unchanged marker. Any byte change is FAIL. Missing/ambiguous denial, no command execution, or command-approval prompt is BLOCKED for OS enforcement; a declined prompt does not prove denial. Never approve command escalation.

Correct canary sequencing before runtime acceptance:

- `thread/start` returns a structured sandbox policy (e.g. `{ "type": "readOnly", "networkAccess": false }`), not the request selector string `read-only`.
- Queue host approval requests observed during `turn/start`; correlate the eventual request to the independently returned thread and turn IDs, item ID, cwd, and exact requested profile before responding. Do not self-correlate using the incoming turn ID as its own expected value or assume the callback arrives before `turn/start` returns.
- Read back `function_call_output` from the fixture's subsequent Responses request when the App Server event shape is not exposed; require host-produced output before advancing the scripted response sequence.

Rollback: terminate and verify the fixture/App Server process groups, then remove temporary state. Preserve frozen evidence. Effective Architect model and reasoning effort remain UNKNOWN because the host does not expose them.
