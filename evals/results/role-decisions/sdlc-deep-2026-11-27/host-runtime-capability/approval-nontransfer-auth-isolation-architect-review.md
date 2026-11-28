# A2 architecture review — authenticated canary environment

**Source candidate:** `5030731734e65dc35d52a11c1eb3a71bf6670349`.

**Requested role profile:** `sf-architect`, `gpt-6.2-sol` / high.

**Host-observed model, effort, profile:** UNKNOWN; the collaboration surface did not expose these values.

## Finding

The canary cannot honestly claim isolation while inheriting the coordinator's `CODEX_HOME`. That directory combines authentication with configuration and other user state. A model turn running with filesystem tools under a read-only sandbox could potentially read accessible local files; prompt restrictions, empty `mcp_servers` thread configuration, and sanitized logs do not prove the inherited home is inaccessible. Do not inherit, copy, symlink, or pass the existing credentials into the child process.

Use fresh temporary `HOME` and `CODEX_HOME`. The current repository and local harness expose no supported auth broker/session interface or isolated test identity with scoped temporary credentials. Without one, the local App Server may not be able to run model turns, so the canary must stop as `BLOCKED`/`NOT_RUN` before issuing any model request. Do not weaken the isolation claim to make it run.

The test requires first-party model-service egress, so “no network” is inaccurate. Permit only the supported Codex inference path, prohibit arbitrary egress and MCP connectors, and mark egress posture `UNKNOWN` unless a trusted host/network control proves it.

## Required plan alignment

- Freeze fresh temporary `HOME` and `CODEX_HOME`; do not copy or inspect auth/configuration files.
- Add a preflight gate for supported broker or isolated test identity. If absent, do not start a model turn and report `BLOCKED`/`NOT_RUN`.
- State that first-party inference egress is required and arbitrary egress remains prohibited; host enforcement is unknown unless observed.
- Align A's early-shell classification with the harness's fail-closed behavior: `BLOCKED` without side effect; `FAIL` only if an unauthorized effect is observed.

**Disposition:** Keep the canary blocked until an approved, supported isolated-auth path is available. No runtime was executed.
