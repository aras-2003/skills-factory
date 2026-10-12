# AI Skills expansion roadmap — 2026-10-05

This directory preserves the expansion analysis and 90 tracked development tasks. It is a planning artifact, not a release or runtime-readiness declaration.

## Start here

1. Read [the proposal and full backlog](PROPOSAL-AND-BACKLOG.md) for architecture boundaries, rationale, flows and rollout order.
2. Treat [BACKLOG.json](BACKLOG.json) as a **dated historical inventory** of 90 IDs and original decisions; it is **not** an independently maintained live delivery status. The current matching issues are indexed in [the 90-ID map](../../governance/backlog-legacy-issue-map.json). Track actionable changes and review evidence in [GitHub Issues](https://github.com/aras-2003/skills-factory/issues) and the [Project board](https://github.com/users/aras-2003/projects/1), with the full cutover/readback gate still open.
3. [BACKLOG.csv](BACKLOG.csv) is a historical derived snapshot; do not edit either snapshot to silently simulate a new status or overwrite earlier decisions.

The proposal is a dated analytical snapshot. Its source revision and installed runtime identity are recorded inside it. The main baseline when saving these documents was `007f659995945084ce18e4ca62b38c92523e414a`; some documentation findings were already corrected after the analysis. Recheck current source and evidence before implementing any task. Do not reopen resolved AIS/RT findings from historical descriptions alone.

## Development handoff

- Start with reconciliation and the existing Skill Engineering chain, then pilot Consumer purchases and article development.
- Select a task by its stable ID; confirm its dependencies and current need before implementation.
- Record the current owner, progress and evidence in the corresponding GitHub Issue; explicitly mark BLOCKED/NOT_RUN when relevant. Historical JSON status stays as provenance, never as a second competing current status.
- Keep acceptance criteria intact. Add implementation PR/commit and evidence references when a task progresses; retain historical findings.
- Link implementation PRs and tested commit revisions in the relevant GitHub Issues; use the documented Project-status sync and verify Project readback before declaring the board authoritative.
- Use project context for private profiles and state, skills for methods, workflows for orchestration, scripts for deterministic work, and existing connectors for actions.
- New IDs supplement AIS/RT and do not replace those backlogs.
- Preserve the original analysis when decisions change; append a dated decision note or link an architecture decision rather than silently rewriting history.

Saving and merging this roadmap does not authorize execution of all proposed tasks, production promotion, purchases, external messages or publication.

## Strategy addition — 2026-10-05

The dated proposal now includes an additive Strategy decision and tasks STR-01 through STR-17: a separate domain, strategic-analysis, deep competitive intelligence, strategy-design, a marketing strategy specialist, PESTEL/Porter/SWOT-TOWS presentation profiles, domain handoffs and pilots. See the appended section in [the proposal](PROPOSAL-AND-BACKLOG.md). Original tasks remain unchanged; the total was 76 after the 2026-10-05 hardening addendum and is now 84 after the 2026-10-06 governance/domain-review decision.


## Near-term hardening gate — 2026-10-05

Before materially accelerating net-new skill/domain development, prioritize the platform hardening tranche:

1. **ENG-15 (P0)** — Agent Skill Security Scanner.
2. **ENG-16 (P0)** — capability and side-effect contract.
3. **ENG-10 (P0, strengthened)** — global routing collision gate across the full catalog.
4. **ENG-17 (P0)** — generated machine-readable skill registry.

These are sequencing controls, not claims that current skills are unsafe or routing is broken. Existing committed pilots and evidence work may continue where useful, but broad catalog expansion should not outrun these controls.

**ENG-18 (P1)** captures a later controlled skill-improvement loop. Do not implement a self-modifying production path before sufficient real failure receipts exist, and do not let an optimizer see evaluator-only rubrics or the full held-out corpus.

Architecture decision retained from the benchmark: do **not** require every production skill to contain scripts/references/assets merely to satisfy a quality gate. A reasoning procedure may be a valid skill when the reusable method itself creates value; add deterministic code or references only when the task requires them.

Implementation tracking: ENG-10, ENG-15, ENG-16 and ENG-17 are `IN_PROGRESS` on [merged PR #122](https://github.com/aras-2003/ai-skills/pull/122). The P0 hardening infrastructure is on `main`; runtime/model-routing evidence remains `NOT_RUN`, and 70 source components still need explicit capability review. No maturity was changed. ENG-20 is now `IN_PROGRESS`: Actions references and dependency locks are being hardened; GitHub reports `main` and `production` as unprotected, and that state has not been changed.


## Controlled domain reviews — 2026-10-06

Do not downgrade any current maturity as a result of the Claude review or the new domain-review backlog. Close the currently open quality processes/campaigns with explicit statuses and evidence first. Then review one implemented domain at a time, with WIP limited to one. Each review produces a conformity record and a scoped adopt/adapt/update/defer/no-change plan; it does not itself change code, maturity or publication state.

The first queue covers the five implemented source domains: Meta, Career, Commerce, Investing and OAF (`DOM-01`–`DOM-05`). Select the starting domain only after quality closure, based on actual use, risk and dependencies. Planned/placeholder domains enter this queue only after they have real implementations.

Supporting hardening work is tracked separately: `ENG-20` covers branch, CI and publication supply-chain controls; `ENG-21` records minimum public-repository governance, including an explicit licensing decision without assigning a license by default.

## Free-first test platform — 2026-10-09

**ENG-22 (P1)** now captures the target testing architecture before broad net-new skill expansion. It does not replace the existing runner, receipts or browser E2E work. The intended stack is: repository `evals/` + versioned synthetic fixtures as source of truth; Promptfoo Community as a pinned regression harness; layered GitHub Actions; vendor-neutral OpenTelemetry/OpenInference traces; and local Arize Phoenix OSS for trace/debug/experiments. No additional ChatGPT plugin or paid SaaS is required.

Keep deterministic assertions first. Add trajectory/forbidden-action checks for provenance and PROD access. Use fixtures/mocks and ephemeral persistence first; add a persistent Supabase TEST environment only when a test needs cross-session state or realistic remote persistence. The current platform-cost target is **0 PLN** apart from actual model inference or CI usage beyond free allowances.
