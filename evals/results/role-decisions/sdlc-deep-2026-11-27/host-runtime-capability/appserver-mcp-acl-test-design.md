# Test design — App Server per-thread MCP ACL canary

**Source candidate:** canonical main `bd00737b5c7331d377b57d75b119ec62879e6dd2`

**Runtime target:** local `codex-cli 0.159.1`, App Server JSON-RPC

**Architect:** A2 / REUSE, review required; local runtime behavior is `NOT_RUN`.

**Test Designer:** requested `sf-test-designer`, Terra Medium; host-effective model/profile were not exposed by the collaboration surface.

## Fixture

Disposable local stdio MCP server with exactly two tools, `allowed` and `forbidden`. Both accept a unique string `nonce`, return the tool and nonce, and append a flushed JSONL record at the start of every received `tools/call`. Lifecycle and `tools/list` may also be logged, but the assertion counts only call ingress by nonce. No model turn, network, credentials, production MCP, or project source write is needed.

## Paired runs

Use two isolated temporary directories and fresh App Server processes so the allowlist and denylist semantics are tested independently. Each run uses the same server implementation and two threads in one process: baseline and restricted.

| Case | Operation | Expected outcome |
| --- | --- | --- |
| `MCP-ACL-E-SETUP` / `MCP-ACL-D-SETUP` | Query `mcpServerStatus/list` for each thread and exact server. | Baseline exposes both tools; restricted exposes `allowed`, omits `forbidden`; baseline remains unchanged after restricted thread starts. |
| `MCP-ACL-E-BASELINE` / `MCP-ACL-D-BASELINE` | Directly call baseline `forbidden` with nonce B. | Success and exactly one ingress record for B. This is the positive control proving tool and fixture work. |
| `MCP-ACL-E-ALLOW` / `MCP-ACL-D-ALLOW` | Directly call restricted `allowed` with nonce A. | Success and exactly one ingress record for A. |
| `MCP-ACL-E-DENY` / `MCP-ACL-D-DENY` | Directly call restricted `forbidden` with nonce X. | Host error exactly `tool 'forbidden' is disabled for MCP server 'canary'`; zero fixture `tools/call` ingress for X. |
| `MCP-ACL-E-BARRIER` / `MCP-ACL-D-BARRIER` | After denial response, call restricted `allowed` with nonce Q. | Success and one ingress for Q, proving the fixture log is flushed and the host/server remain responsive before checking X. |

Expected ingress records may include B, A and Q; initialization and listing calls are outside the denial assertion. A successful forbidden response, any ingress for X, wrong thread/server, unexpected error, or timeout fails the case. If the baseline or transport is unavailable, mark the run `BLOCKED`; do not treat a missing tool from discovery alone as a denial PASS.

## Execution evidence and cleanup

Capture only sanitized version, candidate SHA, run/policy IDs, thread IDs, request IDs, exact host response class/error, fixture ingress records, exit statuses, and hashes of the harness/config/log. Use bounded timeouts and distinct nonces. Stop App Server and fixture child processes and verify both exited. Delete disposable files after preserving the sanitized receipt. A cleanup failure is recorded as a residual process/path.

## Claim limits

A PASS proves direct RPC enforcement before fixture-handler ingress for the tested App Server 0.159.1 policies. It does not prove effective model tool schema, native child inheritance, hosted Sites/connector behavior, all bypasses, or other host versions. Usage/cost is N/A because no model turn is run.
