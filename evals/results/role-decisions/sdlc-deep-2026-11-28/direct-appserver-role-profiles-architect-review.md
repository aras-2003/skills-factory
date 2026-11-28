# Architecture review — direct App Server role profiles

**Decision:** A3 / COMPOSE. Keep native `sf-*` subagent dispatch as the SDLC
role workflow. Treat App Server as a distinct execution surface for bounded
runtime checks; a successful App Server probe does not prove native child
inheritance.

The inspected local `codex-cli 0.159.1` protocol supports thread-scoped
permission profile selection, profile listing, and explicit
`command/exec.permissionProfile`. Use the least-privilege profile and require
the host's `activePermissionProfile` readback. Test unknown-profile rejection
without fallback. Keep command-level enforcement evidence separate from
thread / child inheritance claims. A positive and negative marker probe must
both succeed before calling a profile control PASS.

The no-model canary in
`evals/results/runtime-canaries/sdlc-deep-2026-11-28/direct-appserver-profile-canary.json`
confirmed that `:workspace` is listed as allowed, was reported active on the
thread, and an unknown profile was rejected. However, the returned profile had
an empty writable-root list and the in-workspace positive write failed. The
outside-workspace negative write was denied and cleanup succeeded. Overall
status is **BLOCKED** because the positive / negative control pair is
incomplete. This result does not establish that the profile grants the intended
workspace. Do not fall back to `:danger-full-access`.

For current execution, use the already demonstrated per-turn `sandboxPolicy`
with explicit narrow writable roots, exact candidate SHA, dedicated worktree,
validated compact handoffs, separate executor and reviewer, and coordinator
checks of source status before and after. Existing runtime evidence supports
only a bounded write-under-`tests/` / deny-outside control and direct App Server
MCP allow / deny filtering. It does not prove native Desktop child ACL,
approval non-transfer, secret isolation, production authorization, or hosted
behavior. Effective per-turn model / effort remain unknown when the host omits
them.

**Disposition:** COMPOSE the available controls; retain unproven gates as
`UNKNOWN`, `BLOCKED`, or `NOT_RUN`. No orchestrator, Cloud Next adapter, global
permissions, or production configuration change is warranted by this probe.
