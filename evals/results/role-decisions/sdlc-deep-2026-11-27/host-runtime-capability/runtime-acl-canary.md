# Codex App Server runtime ACL canary — 2026-11-27

## Scope and source identity

- Related work: Issue #748, linked tool-profile work #765.
- Candidate: `f51c4fad6aceeab545943812794f6f44132239fc`.
- Candidate tree: `b071afb1802aaa6b24422bcc52c8a2e5d06d27b7`; exact tree matches merged PR #820.
- Source base: `112f545796911f3c5b545d9dbb718fbf4dbce76b`.
- Runtime: local `codex-cli 0.159.1`, App Server JSON-RPC `command/exec`; generated protocol schema from this exact CLI accepted both policy values. App Server is marked experimental by the CLI.
- Probe workspace: disposable detached worktree `/private/tmp/sdlc-cli-runtime-canary`; no repository source files were written.

## Native sandbox positive and negative control

The same `python3` create-only operation targeted `.sdlc-acl-canary-synthetic` in two separate App Server processes; `workspaceWrite` ran first, then the marker was removed before `readOnly`. The exact probe source is `app_server_acl_probe.py` (SHA-256 `579188b213e6aa8fce854025f74ddde9bb29c4c9d6946c9674b4779662c0817f`); the sanitized receipt is `runtime-acl-canary-receipt.json`. The first used `sandboxPolicy.type=workspaceWrite`; the parent verified the exact contents and SHA-256. It then removed only that marker and started the second process with `sandboxPolicy.type=readOnly`.

| Case | Result |
| --- | --- |
| Positive `workspaceWrite` | JSON-RPC `command/exec` returned exit 0; exact marker bytes verified; marker SHA-256 `86bc18bec6ac4ec29e2955fdb9bcf6500a7feb5c08d25599e8736b3c9b57b373`; stdout was 81 chars, SHA-256 `caecb7bcb936a51a99b5e55cedb53c9e31f9a4af5ce84b6634b6ccaf9625f51b`. |
| Negative `readOnly` | Same write operation returned exit 1; stderr matched a sandbox-denial indicator (raw stderr intentionally not retained), 780 chars, SHA-256 `b46645649899c219c5c64c6d72a9ab71f5136bfcc0a3f6093ac1110863a32499`; stdout empty; marker absent. |
| Postcondition | Git status clean; `HEAD` still candidate SHA above. |

Because the positive control created the same path successfully under `workspaceWrite`, and the only intentionally changed policy was `sandboxPolicy.type=readOnly` (the controls ran in separate App Server processes), the operation result is a runtime **PASS for filesystem write denial on App Server `command/exec`**. It does not independently identify Seatbelt as the denial mechanism, and it does not prove per-role MCP-tool filtering or policy enforcement by Desktop `collaboration.spawn_agent`.

## Developer High role startup

A fresh ephemeral App Server thread was started with the repository's `sf-developer-high` instructions explicitly supplied, model fallback disabled, `sandbox=read-only`, and a read-only `git rev-parse HEAD` task. Host response:

- Thread `01a21dba-c577-7540-8c53-c3b4e372f0ca`; turn `01a21dba-cdba-7a92-b744-377f84433106`.
- Selected model `gpt-6.1-terra`; reasoning effort `high`; sandbox `readOnly`.
- Named TOML auto-load / effective permission profile: `UNKNOWN` (`activePermissionProfile` was null). The role instruction bytes were supplied from `.codex/agents/sf-developer-high.toml`, SHA-256 `21eb0e7d8d07810c39ebc74f5ba666b3586707c81845ca24684dc682fed622ee`.
- The command event completed with exit 0; output 41 chars, SHA-256 `494985217b3ba75d7175078c532c0682ea6803733565e52aea8aaa532cb52575`.
- App Server turn event did not include token usage; usage for this thread is `UNKNOWN`, not zero. Currency cost is unavailable.

## Bounded resume attempt

A separate CLI session received a handoff JSON that the coordinator had validated before dispatch (SHA-256 `27e977c21dfa8de1ecf8aba33b83be0fc715142c6c0a533285cf3a2d55782d2d`). Its thread was `01a21daa-a5fa-7851-a136-bc9fc90cd069`, distinct from the preceding session `01a21da7-6f4a-7003-8c0a-611c5d9da677`. The sanitized stream shows one `read-head`-classified command exit 0, with 5,079 output characters and SHA-256 `fd30dcc4490a871ab36e88989d0f8cbf43e0ad6fcb3dd2fc5d9fc1290bc9bf00`; because the exact command/output were not retained as safe structured fields, it does not independently prove that the child checked the source-base SHA or read `AGENTS.md`. The coordinator verified the handoff, candidate, base and clean state before dispatch. No marker-write command event occurred in this Test Executor session.

The coordinator sent Ctrl-C to the preceding CLI session after observing the marker, but its retained terminal event is `turn.completed`, not a host-reported `interrupted` state; this does not satisfy the frozen interruption case. Therefore bounded resume is **PARTIAL/INCOMPLETE**, not PASS. One-time approval non-transfer was **NOT_RUN**: the fixture did not request or grant a user approval to session A. No MCP tool denial or server-side zero-call canary was run. No approval or MCP authority claim is made.

## Disposition

- Runtime filesystem ACL via Codex App Server `command/exec`: **PASS** for `workspaceWrite` vs `readOnly` on this bounded marker case, with `PermissionError` / `EPERM` / `Operation not permitted` in the negative control. The redundant `sandbox_context_indicator` is not counted as separate evidence, and the positive/negative controls used separate App Server processes.
- Developer High model/effort selection in App Server: **PASS** for the host response; named role-profile auto-loading remains `UNKNOWN`.
- Fresh session with validator-accepted bounded handoff: **PARTIAL**; a read command completed, but the saved evidence does not prove the child interpreted every declared source reference.
- No-transfer of the resumed agent's write authority: **PARTIAL**; the App Server canary proves a read-only sandbox can deny the same file operation, but no write attempt occurred in the resumed agent thread.
- Approval non-transfer, Desktop per-child ACL, MCP-tool ACL, complete runtime Developer→Executor→Reviewer→rework loop, and currency cost: **NOT_RUN/UNKNOWN**.

Earlier CLI attempts where the model omitted the write attempt are retained as `NOT_RUN`; they are not converted into host-denial evidence. Raw JSONL and raw tool output were not stored.


## App Server handoff/resume canaries (2026-11-27)

The Test Designer refined the resume case; see `resume-test-design-review.md`. App Server attempts 3–6 establish actual correlated interruption of A and a distinct fresh B thread with host-reported `readOnly`, plus validated compact handoffs and clean marker/source postconditions. Attempt 6: A `01a21e6f-c6b7-7f31-b6ff-9c1681185cdf` / turn `01a21e6f-ca2d-78e3-9c15-96cc236376cd` ended `interrupted`; B `01a21e70-0347-76a3-b28c-2f2e73deda73` / turn `01a21e70-03e1-7373-8cfa-3ea9f141bca1` completed under host `readOnly`. B's marker-targeted command item failed with exit 1 and left the marker absent. The sanitized receipt is `resume-canary-attempt-6-receipt.json`.

**Resume disposition: PARTIAL.** A's interruption, distinct B session, bounded handoff and readOnly configuration are runtime-observed. B's exact exclusive-create operation and OS denial class/errno were not retained; a local `thread/read` attempt on the ephemeral thread returned RPC `-32600`. The write-denial subcase therefore remains `NOT_RUN`, and approval non-transfer remains `NOT_RUN`. The previously isolated App Server `command/exec` write-denial control remains the only ACL PASS. No full Developer→Executor→Reviewer→rework runtime cycle is established by these canaries.
