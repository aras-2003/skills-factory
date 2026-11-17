# Luna-first independent assurance pilot — Issue #748

## Scope and non-goals
A single **Codex** primary chat carries discovery, scoped implementation and integration. Two short-lived custom agents can run bounded tests and independent review. This is a project-scoped **opt-in pilot**; it does not guarantee the same configuration in ordinary Chat, mobile Chat or every Work surface.
No new SDLC, registry, release gate, evidence store, production deployment or new model spending is authorized. Reuse `AGENTS.md`, `docs/governance/SDLC-OPERATING-PROCESS.md`, `docs/TESTING.md`, `workflows/skill-development/WORKFLOW.md`, existing CI and receipts.

## Runtime/configuration
- Project file `.codex/config.toml` enables up to two open subagent threads and sets default child model to `gpt-6-luna`, effort `medium`; it **does not pin the primary model**.
- `.codex/agents/sf-test-engineer.toml`: Luna Medium; scoped test execution and objective receipts, no source edits.
- `.codex/agents/sf-independent-reviewer.toml`: Luna High; independent risk-based review, no source edits.
- Model access and whether these file settings are honored depend on the actual Codex host, trusted checkout and account. Read `https://learn.chatgpt.com/docs/agent-configuration/subagents`; inspect the child-thread activity and actual model where the host exposes it.
- Custom-agent instructions cannot establish an OS-level no-write sandbox. The child inherits parent permissions; protected operations remain subject to host approvals.
- An unobserved spawn, missing tool access or ignored model override is **NOT_RUN/BLOCKED**, not PASS. Do not substitute a same-thread simulation.

## Delegation policy
1. Default: main Luna does context, plan, implementation, fast developer checks, integration and reporting.
2. A0 editorial-only: use static/CI checks without a child unless required by risk.
3. Material changes A1/A2 or ROUTING/BEHAVIOR: spawn **sf-test-engineer** for independent selected regression evidence when available. Evaluate held-out cases with an independent oracle; child execution is not by itself proof of semantic independence.
4. A3/A4, security, destructive data changes, release-gate/shared-contract changes: additionally spawn **sf-independent-reviewer** or obtain other genuinely independent review required by existing SDLC. The agent does not replace human authorization or external security controls.
5. Validate exact commit, tests, fixtures and environment compatibility before reporting PASS; maintain CI, merge, runtime and production as different gates. Do not create a duplicate evidence ledger.
6. If spawning is unavailable, mark delegated QA BLOCKED, still run safe CI checks and do not declare a required independent review complete. Do not needlessly escalate to Sol/Astra.

## New-chat smoke protocol (run on a checked-out PR branch)
1. Open a **new Codex chat** in a trusted checkout of `aras-2003/skills-factory` at the head SHA of the PR linked to issue #748. Select `gpt-6-luna` as primary if available. Do not assume configuration loaded until observed.
2. Ask the coordinator to print the exact checked-out SHA and read `AGENTS.md`, this runbook, and the actual `.codex` TOML files. Confirm selected models or report unavailable/unknown.
3. Have it **explicitly spawn** `sf-test-engineer`, giving only this PR's changed files and deterministic checks. Use `python3 -m unittest discover -s tests` only if the existing bootstrap and test layout support it; otherwise select the correct existing repository validator without inventing execution.
4. Inspect the spawned thread in the host. Record child identity, visible model if shown, actions, exact candidate SHA, actual exit codes, tests and any evidence artifacts.
5. **Negative smoke:** in the same test report ask what happens if the host cannot spawn `sf-independent-reviewer`. Expected: required review remains BLOCKED and CI alone cannot satisfy it. Do not fabricate an actual failed spawn.
6. If appropriate, explicitly spawn `sf-independent-reviewer` against the same SHA; record substantive findings separate from implementation.
7. Report final gate matrix: `CONFIG_PARSED`, `SUBAGENT_SPAWN`, `MODEL_IDENTITY`, `TEST_EXECUTION`, `REVIEW_INDEPENDENCE`, `CI`, `RUNTIME`. Use PASS/FAIL/NOT_RUN/BLOCKED per gate, with links to observed evidence. Report token/cost only if measured.
8. Link the result to the implementation PR and issue #748; use #712 solely as an optional comparable observation, without rewriting that pilot's frozen sample.

## Acceptance criteria for this pilot
- The config is valid TOML, both agent roles are discoverable and project-scoped.
- A real child agent thread is observed; a same-chat narrative is not enough.
- Child produces at least one genuine exact-SHA test execution result or marks execution unavailable.
- A required reviewer is independent of the author; its absence is not self-waived.
- Model/cost claims are supported by host evidence; no default Sol/Astra calls.
- No merge, production promotion or runtime PASS follows automatically from configuration or green CI.

## New-chat kickoff prompt
```text
Run Skills Factory issue #748 as a Codex Luna-first multi-agent smoke test.
Read AGENTS.md and docs/governance/CODEX-SUBAGENT-PILOT.md on the exact
checked-out PR head. Do NOT change code, open/merge a PR, or deploy.

Use the real project-scoped sf-test-engineer custom subagent for one
bounded deterministic validation. Inspect its thread and report its actual
model if visible. If the host cannot spawn the agent, mark the delegation
gate BLOCKED; never simulate it in the main thread.

Run only proportionate existing checks. For a risk-required review, spawn
sf-independent-reviewer as a separate agent, or report BLOCKED. Produce a
case-level matrix with candidate SHA, commands, real exit codes, evidence,
model identity confidence, remaining gaps and next action. Do not call a
CI PASS a runtime PASS. Report token/cost only if observed.
```

## Baseline and linked tasks
#710 adopted SDLC, #724 delivered Dev Coordinator extension; #712 separately measures real delivery changes. This experiment does not re-open those tasks. Its first candidate is the implementation of #748 itself, not an unrelated production skill.
