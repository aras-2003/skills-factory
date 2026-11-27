# Architect A2 — current Codex/MCP runtime capability boundary

Source tree reviewed: `b071afb1802aaa6b24422bcc52c8a2e5d06d27b7`, identical to the merged main tree for PR #820 at `e161ac30314d720f1f2173312ca94bed9b9488bf`. The local checkout commit is `f51c4fad6aceeab545943812794f6f44132239fc`. Runtime attestation on 2026-11-27 remains Lab 1.38.607 / source `538d800534cf7f7eca32640592a90d252f6dbada`.

**Decision: A2 / COMPOSE.** Keep Codex Desktop as coordinator and use separate Codex CLI or App Server sessions for tasks that require host-enforced sandboxing. Cloud Next remains the instruction and domain-tool surface. This composes existing host capabilities; it does not retrofit role ACL into the generic Desktop `spawn_agent` surface. Confirm the managed host permits the selected profiles/settings before relying on them.

## Verified source and host facts

- `.codex/config.toml` and `.codex/agents/*.toml` declare model, effort and role instructions. They do not declare per-child tool/path ACLs.
- `collaboration.spawn_agent` exposes task, model/effort override and context fork; it has no named profile selector, per-child tool allowlist, working-directory selector, path scope, network scope or child sandbox override. Repository docs correctly classify behavioral role limits as instruction-only.
- Cloud Next `runtime_info` reports `host_model_executes_loaded_instructions`, source `538d800...`, and no child spawn/ACL capability. MCP call receipts cannot establish Codex child configuration.
- Local CLI is `codex-cli 0.159.1`. `codex exec --help` exposes `--sandbox read-only`, `--ephemeral`, `--json`, explicit model, profile and working-directory options. `codex app-server --help` exposes the local experimental App Server entry point.
- Attempting `codex sandbox macos --help` in this managed task exited 71 with `sandbox-exec: sandbox_apply: Operation not permitted`. This is a sandbox-launch failure, not an attempted unauthorized write or a denial receipt.
- Official [subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents#approvals-and-sandbox-controls) states subagents inherit parent sandbox and approval settings. Official [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) and [Codex JSONL](https://learn.chatgpt.com/docs/non-interactive-mode#make-output-machine-readable) describe session-level configuration and machine-readable run events. Docs do not prove this managed host permits them.

## Required proof before acceptance

1. Use two fresh CLI/App Server sessions at one exact SHA. Session A writes only a disposable marker in a scratch checkout, then is interrupted after a compact validated handoff is saved.
2. Session B has a distinct host session ID, receives only the bounded handoff, successfully reads an allowed file, attempts the same marker write, and receives an actual OS sandbox denial. Verify the marker remains absent and capture the actual command/result receipts. Distinguish a sandbox denial from model refusal.
3. If using MCP tool filtering, withhold a benign instrumented test tool from B; record the host denial and independently verify that the test server received no call. A missing tool in discovery alone proves visibility filtering only.
4. Record role/session IDs, exact SHA, requested and host-observed model/effort/profile separately, allowed/denied operation results, command exits, and token usage where the host returns it. Currency cost remains `UNKNOWN` without billing evidence.
5. A no-permission-transfer PASS additionally requires Session A to receive a real one-time approval in a managed fixture and Session B to show that approval is not inherited. The current probe has no such approval evidence; keep this test `NOT_RUN`.

**Current disposition:** generic Desktop child ACL `BLOCKED`; effective TOML profile and effort `UNKNOWN`; CLI/App Server role-level canary `NOT_RUN`; approval non-transfer `NOT_RUN`. Use the existing #748/#765/#768 matrix and campaign cases, not a new task ledger. If the local sandbox launch remains unsupported, stop and keep the denial case `BLOCKED`; do not try a less restrictive mode or claim that instructions enforce access.

Rollback is to stop the pilot sessions and return to the existing Desktop configuration; no Cloud Next/Site change is needed for this host capability probe.
