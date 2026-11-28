# A2 architecture review — one-time approval non-transfer

**Source:** canonical main `c5c15a3a49a504c12bd969934f5acc435370ec42`.

**Requested role profile:** `sf-architect`, `gpt-6.2-sol` / high.

**Host-observed model, effort, profile:** UNKNOWN; collaboration metadata did not expose these values.

## Decision

A bounded local App Server 0.159.1 canary is feasible. It must exercise a real approval request in interrupted session A, perform one bounded effect, and then start fresh session B from a limited handoff. B repeats the same operation and must receive a fresh approval request or a runtime denial before the operation can have an effect. If B succeeds without a new request, the case fails. If the host does not emit a correlatable approval request, mark the case `BLOCKED`/`NOT_RUN`; do not synthesize one.

The protocol distinguishes command decision `accept` from `acceptForSession`, which adds a matching command to the session-scoped approval cache. The canary must answer only the correlated request from A with `accept`; it must never use `acceptForSession`. This is command-approval evidence, not evidence of a user-confirmed added filesystem permission profile.

## Evidence and limits

The version-pinned 0.159.1 `ServerRequest.json` defines `CommandExecutionRequestApprovalParams` with `threadId` and `turnId`, a unique `approvalId` for some approval kinds, and command/cwd fields. `CommandExecutionApprovalDecision` includes `accept`, `acceptForSession`, `decline`, and `cancel`. This establishes protocol vocabulary only; it does not prove which policy generates a prompt in the installed host or whether permission state crosses threads.

Use the same App Server process for A and B so the test detects a process/session-scoped cache leak, while using distinct threads and a fresh B handoff without transcript, prior approval fields, or permission grant. Keep the fixture under a disposable directory, restrict the operation to one predeclared marker, verify exact postconditions after A and B, interrupt A only after observing A's operation result, and clean up all processes and files. Store only sanitized request IDs, thread/turn correlation, decisions, command class, marker digests/presence and exit states. Do not retain commands, prompts, transcript or raw host logs.

The Test Designer must freeze the exact trigger mechanism and controls before implementation. The strongest alternative, a direct `command/exec` RPC, is insufficient unless it demonstrably exercises App Server's approval path. A PASS would cover only this host version, approval kind, and fresh-thread case; it would not prove Desktop child inheritance or Cloud Next behavior.
