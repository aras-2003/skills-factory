# A2 decision — per-thread App Server MCP tool filtering

**Source:** canonical main `bd00737b5c7331d377b57d75b119ec62879e6dd2`

**Requested role profile:** `sf-architect`, `gpt-6.2-sol` / high

**Host-observed model, effort, profile:** UNKNOWN; collaboration metadata did not expose these values

**Decision:** REUSE existing Codex App Server thread configuration, then require local runtime verification. Do not add a second orchestrator or modify the Cloud Next MCP adapter.

## Evidence

- The Codex 0.159.1 App Server protocol accepts an open-ended `config` object on `thread/start`.
- Version-pinned 0.159.1 source passes those overrides into per-thread configuration and the MCP connection manager applies `enabled_tools` / `disabled_tools` before dispatching a tool call. The expected host denial is `tool '<tool>' is disabled for MCP server '<server>'`.
- `mcpServerStatus/list` can query the selected thread's MCP server catalog. `mcpServer/tool/call` accepts a `threadId`, server, tool and optional arguments, allowing a deterministic direct host call without running a model turn.
- Official Codex configuration documents MCP allowlists and denylists; local behavior remains unverified until the canary below runs on 0.159.1.

## Test design and decision boundary

Run two separate, fresh App Server processes to isolate `enabled_tools` and `disabled_tools`. Each process uses one disposable stdio server with exactly `allowed` and `forbidden` tools, and two fresh threads: baseline and restricted. The fixture logs and flushes every received `tools/call` with its tool and unique nonce before returning.

For each filter mode:

1. Confirm the baseline thread sees both tools and can successfully call `forbidden` with nonce B.
2. Confirm the restricted thread sees `allowed`, omits `forbidden`, and can call `allowed` with nonce A.
3. Directly call `forbidden` on the restricted thread with distinct nonce X.
4. Require the exact host denial, then issue an `allowed` barrier call with nonce Q. Inspect the flushed fixture log and require zero `tools/call` ingress entries for X. Initialization, list traffic, and A/B/Q calls may appear.

Cases: `MCP-ACL-SETUP`, `MCP-ACL-BASELINE`, `MCP-ACL-RESTRICTED-ALLOW`, `MCP-ACL-RESTRICTED-DENY-NO-INGRESS` for each mode (`enabled_tools` and `disabled_tools`). Baseline failure, wrong catalog, timeout, unsupported RPC, or unexpected error is FAIL/BLOCKED as applicable; a forbidden nonce reaching the server is FAIL.

## Limits and rollback

A PASS will establish only that local App Server 0.159.1 blocks a direct forbidden MCP tool call before the disposable server receives it under the two tested thread policies. It will not establish what the model was shown, child-thread inheritance, behavior of hosted Site Apps/connectors, production integration ACLs, or compatibility with other versions. No source or persistent configuration change is required. Stop both processes and remove temporary fixture/config files; retain only a sanitized receipt with exact version, thread/policy IDs, call outcomes, zero-ingress result and source revision.

References: [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference); version-pinned [thread config overlay](https://github.com/openai/codex/blob/rust-v0.159.1/codex-rs/app-server/src/config_manager.rs#L405-L447), [MCP connection filtering](https://github.com/openai/codex/blob/rust-v0.159.1/codex-rs/codex-mcp/src/connection_manager.rs#L941-L999), and [MCP request handler](https://github.com/openai/codex/blob/rust-v0.159.1/codex-rs/app-server/src/request_processors/mcp_processor.rs#L539-L569).
