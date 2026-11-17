# Context-efficient AI Engineering Team — Issue #748

## Decision and scope
One primary **Luna Medium** Codex thread is a thin delivery coordinator. Large or context-heavy research, implementation, test authoring/execution and review are delegated to short-lived bounded subagents, with normally at most two simultaneous child threads. This is an opt-in project-scoped Codex configuration, not a second SDLC or evidence ledger.

Existing authority: `AGENTS.md`, `docs/governance/SDLC-OPERATING-PROCESS.md`, `workflows/skill-development/WORKFLOW.md`, `docs/TESTING.md`, the native Architecture Impact A0–A4 and CI/eval/receipt gates. Links: #710, #724 (delivered), #712 (separate process observation), #748 (this team pilot).

## Role-to-model routing

| Codex role | Model / effort | Activation / write responsibility |
| --- | --- | --- |
| Main (not a child) | `gpt-6-luna` / `medium` | Every task: scope, delegate, decide, integrate; avoid long logs and routine implementation |
| `sf-solution-architect` | `gpt-6.2-sol` / `high` | Architecture decision, A3/A4, complex A2; read-only |
| `sf-developer-medium` | `gpt-6-luna` / `medium` | Small/local scoped code and documentation changes |
| `sf-developer-high` | `gpt-6-luna` / `high` | Complex/large implementation, cross-component integrations, difficult debugging |
| `sf-test-designer` | `gpt-6-luna` / `medium` | AC-to-test mapping, test code, fixtures, oracle; assigned tests only |
| `sf-test-executor` | `gpt-6-luna` / `low` | Execute approved tests, capture exact SHA, exit codes and receipts; no edits |
| `sf-independent-reviewer` | `gpt-6-luna` / `high` | Material/risk-required independent review; read-only |
| `sf-skill-evaluator` | `gpt-6-luna` / `high` | Semantic routing/behavior/regression evaluations; read-only |
| `sf-research-analyst` | `gpt-6-luna` / `low` | Bounded source discovery; read-only |
| `sf-research-medium` | `gpt-6-luna` / `medium` | Complex research escalated from Low; read-only |
| `sf-release-evidence` | `gpt-6-luna` / `low` | CI/evidence/status inspection; read-only, no merge/deploy |

This is role configuration, **not proof** the host honored the named model or thinking effort. In the Codex host, observe actual spawned threads/model if exposed. No automatic Sol/Astra fallback and no new production spending. Only issue-specific bounded architecture decisions go to Sol.

## Delegation / staffing policy
- Default small A0 editorial: main or sf-developer-medium + existing static CI, no mandatory subagent.
- Small A1: sf-developer-medium; sf-test-designer only when tests change, sf-test-executor for independent test execution where useful/required.
- Material A2 or complex multi-component development: sf-developer-high; sf-test-designer Medium maps AC/fixtures before behavior changes; sf-test-executor Low checks the exact candidate; risk-required reviewer High.
- A3/A4, architectural conflicts, migrations/shared contracts: ask sf-solution-architect Sol High for a **bounded decision brief** before implementation; enforce existing architecture approvals, consumer regression, rollback and independent review.
- ROUTING/BEHAVIOR: sf-skill-evaluator High assesses baseline/candidate and meaningful near-miss/competing skill; executor Low handles deterministic portions.
- Security or destructive changes require review as in existing SDLC irrespective of A-level; an instruction to use a reviewer does not establish independence or authorization.
- A child may keep context across bounded fix attempts within a package, then expires; new package is a new context. Do not use agent chat history as persistent project memory. Use GitHub issues, ADR, commits, PR, Actions artifacts and existing receipts.

## Context isolation contract
Task package: issue and AC, requested role, exact candidate SHA, relevant source paths/consumer map, approved tests or architecture question, permissions, expected output. Explicitly **exclude** unrelated chat history, stale logs, entire catalogs, private inputs and unsupported guesses. Request just-in-time source reads with revision pins.

Result handoff (normally <=250 words; material issues exempt):
```yaml
issue: 748
role: sf-test-executor
candidate_sha: "<full-40-character-sha>"
execution_state: NOT_RUN # PASS / FAIL / NOT_RUN / BLOCKED
observed:
  case_ids: []
  commands_exit_codes: []
evidence_links: []
material_findings: []
blockers: []
decision_required: null
next_action: "Run smoke on exact PR HEAD"
```
Never paste entire logs or analysis transcripts into Main. Link to existing evidence; do not create a new log or memory registry. If the target SHA changes, relevant previous acceptance evidence must be rechecked for compatibility. Do not label a CI run a runtime PASS.

## Capability and security boundaries
Project `.codex/config.toml` selects main Luna Medium by default and at most two child threads. Real model access, tool permissions and child spawning depend on the Codex host/account. Child no-write text is **behavioral**, not an OS-level sandbox. No agent can bypass independent external approval for production, credentials, security or destructive actions. Agents share a checkout unless separate worktrees are actually configured; therefore restrict concurrent writes to disjoint paths or serialize them.

## Pilot acceptance / new chat
Run an isolated test in a **new Codex chat** in a trusted checkout at the latest head of PR #749, not in an ordinary Chat session. The prior two-role smoke is superseded by this full-team smoke.

1. Verify the exact checkout SHA, `AGENTS.md`, `.codex/config.toml` and all `.codex/agents/*.toml` are actually loaded. Parse TOML using a local parser. Confirm main Luna Medium effective model/effort if host reveals it.
2. Ask main to **actually spawn** `sf-research-analyst` for one source-fact question, then `sf-developer-medium` for a **no-edit plan** of a tiny hypothetical change. Observe distinct child threads, concise handoffs and model identity; do not modify code merely to demonstrate routing.
3. Spawn `sf-test-designer` for a selected acceptance-to-case mapping and `sf-test-executor` for a safe, existing deterministic test command against current SHA. Compare the case map to actual command/exit output; no fabricated evidence. Keep logs out of Main.
4. Exercise the **complex** dispatch decision without modifying product: ask when `sf-developer-high` would replace Medium, and require `sf-solution-architect` to produce a bounded risk/decision brief on an A3 example, without code edits. Observe Sol model only if exposed.
5. For an actual risk-required review, spawn `sf-independent-reviewer` in a separate thread. If not spawned, mark independent gate BLOCKED (do not use a same-thread narrative). Optionally exercise `sf-skill-evaluator` on a frozen existing skill case and `sf-release-evidence` on the PR checks.
6. Validate a negative case: absent host support, unavailable named model, missing fixture, or unobserved tool execution must remain BLOCKED/NOT_RUN, not PASS.
7. Record exact SHA, observed child identity/model/effort (or UNKNOWN), case IDs, commands and exit codes, source links, time and any measured token use. Compare main context volume/hand-off size to a nondelegated run only when measured.
8. Report separate `CONFIG_PARSED`, `AGENT_DISCOVERY`, `SPAWN`, `MODEL_ROUTING`, `TEST_EXECUTION`, `REVIEW_INDEPENDENCE`, `CI`, `RUNTIME`; PASS/FAIL/NOT_RUN/BLOCKED. Link result in PR #749 / Issue #748. Do not merge or deploy as part of the smoke.

### Copy-paste kickoff
```text
Validate the full Skills Factory Luna-first Context-Efficient Team on PR #749
in a NEW Codex chat, without changing code or deploying.
Read AGENTS.md and docs/governance/CODEX-SUBAGENT-PILOT.md at exact PR HEAD.
Verify project config, custom agent definitions, requested model/effort and
real child spawning (not role-play). Main should be Luna Medium.
Demonstrate bounded Research, Developer Medium/High routing, Test Designer
Medium, Test Executor Low, Architect Sol High, Independent Reviewer High,
and conditional Skill Evaluator/Release Evidence. Execute at least one safe
existing deterministic check via the actual sf-test-executor and record its
exit status and exact SHA. Keep raw logs out of main; use <=250-word handoffs.
Return PASS/FAIL/NOT_RUN/BLOCKED for config, spawn, models, test, review, CI,
runtime with evidence links; no invented cost or execution; no merge/deploy.
```

## Exclusions
No automatic global chat memory, cross-chat synchronization, new persistence, automatic issue/project mutation, background execution, global configuration, production deployment, model entitlement guarantee or production release permission. Implementation only becomes runtime verified after this separate new-chat smoke succeeds.
