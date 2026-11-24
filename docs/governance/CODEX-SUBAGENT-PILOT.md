# Luna-first context-efficient agent team — Issue #748

## Scope and boundaries

One primary Codex chat coordinates context, planning, implementation, integration and reporting. Project-scoped custom agents provide short, bounded role work with compact handoffs and no duplicate write ownership. This is an opt-in Codex project pilot; it does not claim support in ordinary Chat, mobile Chat or every Work surface.

Reuse `AGENTS.md`, `docs/governance/SDLC-OPERATING-PROCESS.md`, `docs/TESTING.md`, `workflows/skill-development/WORKFLOW.md`, `skill-test-design`, existing CI and receipts. Do not create a second SDLC, task registry, evidence store or release gate. No merge, deployment, production promotion, additional spend or credential change is implied.

Architecture impact is A1: project-local agent configuration, instructions and contract tests only. Skills Factory skill behavior, runtime, routing, stores, CI gates and production eligibility do not change.

## Host and model configuration

- `.codex/config.toml` enables agents, caps active child threads at two and selects the default child model/effort as Luna Medium.
- Project configuration sets **subagent defaults**, not the main chat model. Select Luna High in the host for the primary coordinator when available; record unavailable or unknown if the host does not expose this control.
- Agent files set bounded role-specific child model/effort. The project config does not prove the host loaded these files or honored a model override.
- Agent instructions are behavioral; a child thread inherits host permissions. They do not establish a separate OS sandbox.
- When the host cannot spawn a required role, cannot expose a required model or cannot run the requested test, report BLOCKED/NOT_RUN. Never substitute same-thread narration or infer runtime success from config parsing/CI.

## Role catalogue and routing

| Role | Model / effort | Responsibility and boundary |
| --- | --- | --- |
| Coordinator / primary chat | Luna High (selected in host; not set by project TOML) | Owns scope, decisions and integration. |
| `sf-architect` | Sol High | Risk-triggered A2–A4 architecture advice; no implementation. |
| `sf-developer-medium` | Luna Medium | Bounded small/moderate implementation. |
| `sf-developer-high` | Terra High | Explicitly escalated complex implementation. |
| `sf-test-designer` | Terra Medium | Designs case IDs, fixtures and expected/forbidden outcomes before code; does not execute. |
| `sf-test-executor` | Luna Low | Runs agreed exact-SHA checks; does not edit source/tests. |
| `sf-independent-reviewer` | Terra High | Independent risk-based review; does not implement. |
| `sf-skill-evaluator` | Terra Medium | Frozen baseline/candidate evaluation with existing rubrics and held-outs. |
| `sf-researcher-low` | Luna Low | Bounded repository/primary-source fact collection. |
| `sf-researcher-medium` | Luna Medium | Multi-source research only after explicit coordinator escalation. |
| `sf-release-evidence` | Luna Low | Reconciles exact-source CI/eval/runtime evidence; cannot merge or release. |

The primary chat owns scope and integration. It may implement when appropriate, but only one agent owns writes to a given shared interface at a time. Use the test designer before material behavior/shared-contract changes, then delegate execution separately when available. Use architecture advice for material A2–A4 decisions or security/shared-contract risk; do not call Sol for cosmetic A0 work. Use a reviewer for independent review when existing SDLC requires one. The evaluator does not set acceptance thresholds or approve release.

For A2–A4 or incomplete consumer evidence, route the Architect through
[`SOFTWARE-ARCHITECTURE-DECISIONS.md`](../architecture/SOFTWARE-ARCHITECTURE-DECISIONS.md)
and the [software decision template](../../templates/architecture/software-decision.md).
This gives the role a concrete method without changing its host permissions.

## Required handoff

Each delegated task receives the issue/AC, exact source or candidate SHA, bounded paths, relevant baseline/consumers, case IDs and expected output. The coordinator retains the dispatched task ID, role and requested case IDs, then supplies those expected values when validating the result. The helper rejects a mismatching task ID, role, candidate SHA or case set; duplicate IDs are rejected rather than deduplicated. A `PASS` also requires evidence references, only `PASS` case outcomes and zero command exit codes; a Test Executor `PASS` with requested cases also requires an observed command exit record. A `BLOCKED` or `NOT_RUN` result still enumerates every requested case with its individual state. Evidence references are opaque identifiers and must be independently opened and checked by the coordinator; the helper does not authenticate receipts. The v1 logical fields are checked by `scripts/engineering/delegation_handoff.py`: input serialization is canonical UTF-8 JSON bounded by the declared `context_budget` (and 16 KiB hard maximum); result readback binds to the exact dispatch and candidate. Results without directly observed usage retain `usage: null` (UNKNOWN), never zero. The helper only validates references and size; it does not persist handoffs, spawn agents, enforce access or establish a security boundary.

Treat the GitHub issue and source tree at that exact revision as the source of truth; exclude stale chat context. The child returns only findings and evidence needed by the coordinator: exact revision, action/command, real exit status, case or fixture identity, evidence reference, limitations and BLOCKED/NOT_RUN reason. Do not paste full thread logs into the main context. The validator rejects transcript/log, evaluator/held-out, credentials and permission/approval fields; it does not inspect free-text values for accidental sensitive content, so handoffs must still use source references rather than copied evidence.

Focused static verification: `python3 -m unittest discover -s tests -p 'test_delegation_handoff.py'`. This verifies field validation, round-trip readback, dispatch/task/role/case binding, stale SHA rejection, PASS evidence consistency, forbidden fields and UNKNOWN usage behavior. It does not satisfy the separate new-chat host smoke or prove that a host can restart and resume a child from serialized data.

For Developer handoff acceptance, `scripts/engineering/delegation_handoff.py` offers `validate_developer_result(...)`, which validates the compact result and calls `scripts/engineering/developer_scope.py`'s `verify_candidate_scope(repo, base_sha=..., candidate_sha=..., writable_paths=..., reported_changed_paths=...)`. Supply the trusted dispatch base SHA/grants and the reported paths independently. A grant without a trailing slash names one exact file; a trailing slash grants descendants of that directory. The verifier compares the committed Git diff with both lists and reports `PASS`, `FAIL`, or `BLOCKED`; changed symlinks and submodules fail closed. It requires the checkout HEAD to match the candidate and rejects tracked or untracked dirt. Git-ignored files are not inspected. Developer `PASS` is rejected unless scope verification also passes. This is post-execution consistency checking, not host access control, proof of task completion, or protection from concurrent mutations.

## New-chat smoke protocol

Run against the implementation PR head in a **new Codex chat** and trusted checkout:

1. Read `AGENTS.md`, this runbook, `.codex/config.toml` and the role TOMLs at the exact PR head. Record checkout SHA and actual host/model visibility; do not infer them.
2. Select Luna High for the primary coordinator if available. Confirm that the project config loaded only from observable host evidence.
3. Explicitly spawn `sf-test-designer` to produce a bounded plan, then `sf-test-executor` to run one existing deterministic check on the same exact SHA. Record each child thread, visible model/effort, case IDs, command and real exit status.
4. For a complex architecture case, explicitly route `sf-architect`; verify the advice is bounded and does not modify code. Test Medium/High developer routing with small and complex examples only if the host exposes the settings and the task is safe.
5. For a risk-required review, spawn `sf-independent-reviewer` as a separate thread. A missing reviewer remains BLOCKED; do not count self-review or CI.
6. Verify compact handoffs and observe source status before/after the executor; any attempted edits are a defect. This observation does not prove OS-level isolation.
7. Include a negative case: if spawn/model/execution is unavailable, the result is BLOCKED/NOT_RUN, with no simulated receipt.
8. Report gates separately: `CONFIG_PARSED`, `SUBAGENT_SPAWN`, `MODEL_IDENTITY`, `TEST_DESIGN`, `TEST_EXECUTION`, `DEVELOPER_ROUTING`, `ARCHITECTURE_ADVICE`, `REVIEW_INDEPENDENCE`, `CI`, `RUNTIME`. Report cost only when directly measured.

## Offline acceptance

- All ten role TOMLs parse; names, model IDs and effort values match the role matrix.
- Project config parses, caps threads at two and does not set a primary session model.
- Tests confirm design/execution separation, bounded write ownership, fail-closed missing evidence and no merge/release authority.
- `AGENTS.md` and this runbook route to the same roles.
- Run the focused contract test with `python3 -m unittest discover -s tests -p 'test_codex_agent_team.py'`; this proves static configuration contracts only.

## New-chat kickoff prompt

```text
Run Skills Factory issue #748 as a Codex multi-agent smoke test at this exact PR head.
Read AGENTS.md and docs/governance/CODEX-SUBAGENT-PILOT.md. Do not change code,
open/merge a PR, deploy or treat this prompt as proof that the project config loaded.

Select Luna High as the primary coordinator if the host supports it; report actual
model/effort visibility. Explicitly spawn sf-test-designer and sf-test-executor as
separate child threads for one bounded existing deterministic check. Inspect the
threads, exact candidate SHA, case IDs, command, real output and exit status. If
required spawning/model/execution is unavailable, mark it BLOCKED/NOT_RUN; never
simulate the child. Use sf-architect or sf-independent-reviewer only when the
defined risk warrants them. Return the gate matrix and compact evidence links.
```

## Baseline and linked tasks

#710 adopted the SDLC, #724 extended the coordinator, and #712 measures delivery outcomes separately. #749 supplied the initial two-role pilot; this extension completes the owner-directed role split. Keep the real new-chat smoke as independent host evidence. Do not rewrite #712's frozen sample or claim runtime acceptance from CI.
