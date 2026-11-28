# SDLC role capability and enforcement matrix

This is the capability contract for issues #765 and #748. It describes the
project profile intent and separately records what the observed Codex Desktop
spawn surface can enforce. It is not an authorization system or a second task
ledger. Re-check host behavior when the host or permission configuration changes.

## Host observation

Observation date: 2026-11-23. The inspected source configuration is pinned to
`e0f613cbaf80cf4a278e713794662250dab2b8bc`. Host ID was `local`; the Codex
Desktop build/version was not exposed. The observed `collaboration.spawn_agent`
interface accepts a task, optional model and reasoning effort, and an optional
context-fork setting. It does not accept a named project profile, per-child
tool allowlist, working directory, path scope, network scope, or child sandbox
override. Generic child tasks for all nine role types were observed in a later
pilot, including one bounded Developer write followed by separate execution
and review. No invocation showed that a named project TOML profile was loaded
or that a specific model/effort was selected. A separate thread shares host
permissions; behavioral instructions are not an OS sandbox. The source SHA
pins the inspected profile files, not the host executable or proof that it
loaded them.

Official [Codex subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
describes project-scoped custom agents under `.codex/agents/`, including their
names, instructions, optional model/effort settings, and inheritance of the
parent's permissions. The [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
documents agent configuration and `config_file` selection. These docs are not
version-pinned to the observed Desktop build, and this session did not expose a
build identifier. They establish that Codex supports custom-agent configuration
in general; they do not prove that this session loaded a named profile or that
the observed spawn call enforced its instructions. Classifications below remain
limited to the exposed spawn-tool schema and actual task traces in this session;
they do not generalize to other Codex hosts or the separate OpenAI Agents API.
Re-observe after a host/version/configuration change.

## Role contract

`INSTRUCTION_ONLY` means the profile asks the child to follow the boundary but
the observed spawn surface does not enforce it. `UNAVAILABLE` means the
required host capability or observation was absent. `ENFORCED` is reserved for
a restriction demonstrated by the host or a repository/CI policy; this matrix
does not infer it from TOML or prose.

| Role / existing profiles | Required and optional capability | Allowed operations and scope | Network / sensitive access | Permission status on observed spawn surface | Fallback and observable receipt |
| --- | --- | --- | --- | --- | --- |
| Coordinator / primary chat | Required: issue, PR and Project read; bounded metadata updates; integration. Optional: local source read, child delegation. | Select work and coordinate; implementation is delegated by default. No production deploy by default. | Use only connectors and checkout permissions already granted to the primary chat; no production secrets. | Metadata boundary `INSTRUCTION_ONLY`; per-role tool and path narrowing `UNAVAILABLE`. | Keep native Issue/Project state and PR as record. Capture task, exact SHA, operations actually invoked, and results. |
| Research / `sf-researcher-low`, `sf-researcher-medium` | Required: bounded repository/source search and read. Optional: static inspection commands. | Read assigned paths and authoritative sources; no source edits or execution of untrusted code. | Network only through already authorized read/search tools; no secrets. | No named-profile selection `UNAVAILABLE`; no-write rule `INSTRUCTION_ONLY`. | Main coordinator performs/assigns bounded read-only work; record source URLs/paths, revision/date, method and unknowns. |
| Architect / `sf-architect` | Required: issue/AC, exact baseline SHA, contract and consumer paths. Optional: static path/schema inspection. | Produce an A1–A4 decision record when architecture triggers apply; do not implement or edit project metadata. | No production or secrets. | No named-profile selection `UNAVAILABLE`; advisor-only boundary `INSTRUCTION_ONLY`. | Use the architecture method in `docs/architecture/SOFTWARE-ARCHITECTURE-DECISIONS.md`; invoke for A1 changes to shared public contracts/trust boundaries and material A2 changes; retain SHA, source references and decision. |
| Developer / `sf-developer-medium`, `sf-developer-high` | Required: assigned worktree, Git, scoped source writes, agreed build/test and PR operations. Optional: approved package tools. | Write only assigned paths; base and candidate SHA recorded. | No production secrets, production deploy or unapproved network. | Worktree isolation is host-provisioned, not spawn-controlled here; path limit `INSTRUCTION_ONLY`; named profile and access narrowing `UNAVAILABLE`. | Coordinator provisions a clean worktree and inspects diff scope; record base/candidate SHA, changed paths, commands and exits. |
| Test Designer / `sf-test-designer` | Required: issue/AC, source baseline and consumer map. Optional: existing test conventions. | Write test specifications only; no implementation or execution. | No secrets or production. | No-write rule `INSTRUCTION_ONLY`; per-role tool filter `UNAVAILABLE`. | Treat output as design, not execution. Record case IDs, fixture/input, expected and forbidden behavior. |
| Test Executor / `sf-test-executor` | Required: exact candidate SHA, fixtures and test command. Optional: temporary result output. | Run agreed tests; no product source or test edits. | No secrets or production. | No-write rule `INSTRUCTION_ONLY`; per-role path/tool filter `UNAVAILABLE`. | Coordinator verifies source status before/after; record command, output, exit code, fixture and SHA. Any edit attempt is a defect, not proof of prevention. |
| Independent Reviewer / `sf-independent-reviewer` | Required: exact diff, issue criteria, CI and evidence. Optional: review comment when authorized. | Read-only review and findings. | No secrets, production or deploy. | Read-only boundary `INSTRUCTION_ONLY`; tool/path isolation `UNAVAILABLE`. | Use GitHub review controls and branch rules where configured; record reviewer identity, SHA and findings. Self-review is not independent. |
| Skill Evaluator / `sf-skill-evaluator` | Required: frozen baseline/candidate, rubric, cases and evaluator oracle. Optional: evaluation runner. | Evaluate without editing candidate, fixture, rubric or expected outcomes. | Held-out materials must remain separately controlled; no developer handoff of raw held-outs. | Held-out access separation `UNAVAILABLE` on this spawn surface; no-edit boundary `INSTRUCTION_ONLY`. | Do not claim a blinded evaluation unless access separation is proven; report `NOT_SCORABLE`/`BLOCKED` when not. |
| Release/Evidence / `sf-release-evidence` | Required: exact SHA, CI/eval/runtime receipts and artifact identities. Optional: read-only release metadata. | Reconcile evidence only; no merge, publish, deploy or promotion. | No production secrets or deployment by default. | Read-only/no-promotion boundary `INSTRUCTION_ONLY`; deployment privilege narrowing `UNAVAILABLE`. | Native release workflow and owner gates remain authoritative; capture each evidence state separately. |

## Least privilege and capability loading

The project can reduce prompt/context exposure by handing a child only the
assigned objective, acceptance criteria, source references, paths and case IDs.
Select only the needed skill instructions and references through the existing
skill-loading path. Do not pass full transcripts, evaluator rubrics, held-out
fixtures or raw tool logs by default. These are operating controls, not a claim
that unselected tools or files are inaccessible.

The observed surface did not expose the child's effective tool schema, a schema
digest, prompt/schema token counts, or actual load traces for selected and
unselected skill bodies. These measurements are **UNAVAILABLE**, not zero.
Tests `TOOL-01`–`TOOL-07` therefore remain host execution requirements: observe
role discovery and allowed developer work; attempt denied write, secret and
deploy canaries; prove lazy-load behavior; simulate missing MCP/interruption;
and compare schema/tokens only when the host exposes them. Static profile tests
do not satisfy these runtime cases.

## Current-runtime operating mode (2026-11-28)

The local Codex CLI/App Server `0.159.1` exposes useful enforcement surfaces,
but they are not interchangeable with native Desktop child-agent permissions.
Use the existing `collaboration.spawn_agent` role workflow for role selection,
bounded handoffs, Developer work, Executor runs and independent review. Use a
dedicated worktree, exact candidate SHA, handoff/scope validators and before /
after source checks. A role's requested model and effort remain requested values
unless the host returns trustworthy effective-turn telemetry.

Observed App Server evidence narrows two permissions surfaces:

- App Server `command/exec` with explicit `sandboxPolicy` passed one bounded
  filesystem control: a write under the declared `tests/` root succeeded while
  a write outside that root was denied. See the `runtime-e2e-01` receipt and
  execution evidence. This proves that operation in that tested turn only.
- App Server per-thread MCP filtering passed direct JSON-RPC allow / deny
  controls on CLI `0.159.1`; see the dated runtime ACL receipt. This does not
  prove the model-visible tool schema, native child inheritance, hosted MCP,
  or policy inheritance between threads.
- A fresh credential-filtered, zero-model-turn MCP ACL canary after PR #832
  also passed both `enabled_tools` and `disabled_tools` policies on candidate
  `3bea5127ef154aa55cb118c4b304521c554a4a30` (tree
  `40c94fc5cf66a1eba97406542083a073af9c1e9d`). The restricted catalog exposed
  only `allowed`; App Server rejected the `forbidden` call and the fixture
  observed zero ingress for it. See
  [`appserver-mcp-tool-acl-canary.json`](../../evals/results/runtime-canaries/sdlc-deep-2026-11-28/appserver-mcp-tool-acl-canary.json).
  This is direct thread-scoped App Server MCP filtering, not native subagent
  inheritance or filesystem ACL evidence. The candidate tree matches the
  post-merge source tree from PR #832.
- The credential-free approval-transfer local-mock canary was attempted on
  candidate `e3c6b529fc8bd1a3dd51296af459b6e00a735d71` and stopped in
  `fixture_setup` with a sanitized `os_error` before any App Server process
  started. The marker remained empty and cleanup passed; PERM-NT-01–06 and
  ENF-01–03 are `NOT_RUN`. See
  [`approval-nontransfer-local-mock-blocked.json`](../../evals/results/runtime-canaries/sdlc-deep-2026-11-28/approval-nontransfer-local-mock-blocked.json).
  This does not test approval transfer or runtime permission enforcement.
- A fresh isolated App Server profile probe on 2026-11-28 returned
  `activePermissionProfile.id=:workspace`, returned the requested model, and
  rejected an unknown profile. The response reported no writable roots. The
  positive write control failed and the outside-workspace write was denied.
  Disposition: **BLOCKED / incomplete positive control**. Do not use that probe
  as evidence that the selected profile grants the intended workspace, or as a
  role sandbox guarantee. Its sanitized receipt is linked from the runtime
  evidence note.
- App Server turn lifecycle did not expose effective reasoning effort; model
  and effort for the turn therefore remain `UNKNOWN`. The `thread/start` model
  value and a `turn/start` request are configuration readback / requested
  inputs, not proof of effective per-turn execution.

Operational adaptation: prefer the already tested explicit per-turn
`sandboxPolicy` plus narrow writable roots when a separately launched App
Server command runner is used. Keep each run ephemeral and isolated. Do not
start it with ambient user credentials or the coordinator's Codex home for
credential-bound tests. Treat approval non-transfer, secret isolation,
Desktop child ACL, and production/deployment authorization as `BLOCKED`,
`NOT_RUN`, or `UNKNOWN` until separately demonstrated. A passing direct MCP
ACL canary does not upgrade those gates. Continue using repository branch
protections, PR review and explicit owner authorization for integration and
release.

## Remediation order

1. Use the host's supported permission or isolated-worktree controls to run a
   fresh test session, then capture actual child identity, permission policy,
   tool invocation and before/after source status.
2. If the host cannot isolate children by role, route untrusted or read-only
   work through a separately permissioned session/worktree and keep mutations
   behind normal review and branch protections. Do not claim child-level least
   privilege from instructions.
3. Add schema/token comparisons only when the host provides effective schema
   and usage evidence. Until then leave `TOOL-03`, `TOOL-04`, `TOOL-05` and
   `TOOL-07` as `BLOCKED` or `NOT_RUN` according to the attempted execution.

Rollback: revert project-local profile documentation/config changes and start a
fresh trusted session. No global permissions, credentials, production access,
MCP manifests or branch-protection settings are changed by this matrix.
