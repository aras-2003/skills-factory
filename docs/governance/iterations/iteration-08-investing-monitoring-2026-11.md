# Iteration 08 — Investing monitoring: KPI triggers and expectations

- State: ACTIVE; Iteration 7's owner abort and this scope lock merged in PR #603 at `40420bc28c85826c2f28cb9709c34c45f583b487` before implementation.
- Owner / reviewer: Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review; not independent).
- Tracking issue / native Project iteration: #322 (coordination-only tracking); GitHub Project iteration `08 | Investing monitoring (provisional)`.
- Previous terminal iteration: Iteration 7 owner-aborted on 2026-11-09; see [append-only abort decision](iteration-07-abort-2026-11-09.md). #306 remains unresolved and open.
- Baseline main SHA: `0646cd0c4588b889070960c777e07829c3477b9e`.
- Lock commit SHA: `0f32e76e7642cfe12f39a5034605eb2fa5fc8e26` (final frozen scope tree, including the append-only prior-iteration abort record; implementation starts after merge).
- Started at / closed at (UTC): 2026-11-09 22:55:13 / pending.
- Scope lock reviewed by / at: Arkadiusz Kamrowski, 2026-11-09 (self-review).

## Frozen commitment

| Issue | Outcome / acceptance criterion IDs | Included | Excluded | Dependencies / accepted evidence | Size |
| --- | --- | --- | --- | --- | --- |
| #308 | 308-A through 308-D | Extend existing `security-underwriting` and `thesis-monitor` contracts/tests for source-backed, time-bounded KPI triggers tied to verified canonical ACTIVE thesis assumptions; separate MONITOR/REVIEW/ESCALATE from invalidation and trade decisions. | New standalone skill, automatic sell/trade, DRAFT or surrogate baselines, canonical persistence without explicit authorization. | Existing thesis history/write boundary; trigger matrix and negative evidence cases in the iteration matrix. | M |
| #309 | 309-A through 309-D | Extend existing `security-underwriting`, `valuation-scenario-review`, and `thesis-monitor` contracts/tests with a dated, like-for-like consensus → actual → guidance bridge and no-lookahead historical earnings evaluation. | Estimate retrieval/verification, invented missing values, causal claims from price reaction alone, post-hoc thresholds, unapproved writes. | Primary-source and dated-consensus evidence must be explicit; missing/stale/conflicted inputs remain UNKNOWN/N/M and block dependent conclusions. | M |
| #310 | 310-A through 310-D | Add Polish/English regression for Investment OS methodology/workflow audits with incidental tickers; retain actual single-security routing and no unnecessary reads/writes. | Broad router rewrite, unrelated routes, research execution when the user asks for a process audit. | Existing route facade and Investment OS front door; baseline vs changed route evidence is required. | M |

## Test plan

Acceptance matrix: [`evals/campaigns/iteration-08-investing-monitoring-2026-11/acceptance-matrix.md`](../../../evals/campaigns/iteration-08-investing-monitoring-2026-11/acceptance-matrix.md). Required runtime surface: owner-only Skills Factory Cloud Next Site; Chat-host rendering is not claimed unless separately observed. Runtime access is available through the connected Cloud Next tools, but Site currently reports source `3bdeef677347d81b56fcbb5ba9e83722869a869c` / Lab `1.38.476`, older than baseline main; capture that as deployed baseline and deploy an exact merged candidate before candidate acceptance.

Changed contracts and consumers: `security-underwriting`, `thesis-monitor`, `valuation-scenario-review`; Investment OS route facade and `workflows/investment-os-review`; their tests, routing registry/evals, generated Lab package and Site catalog. Exact diff and transitive dependencies are to be reconciled before implementation PR.

Required case IDs: 308-01 threshold crossing cannot auto-sell; 308-02 verified material breach escalates; 308-03 price-only change does not invalidate business thesis; 308-04 missing ACTIVE baseline blocks. 309-01 date/source/definition-aligned expectation bridge; 309-02 missing/stale/conflicted estimate and future-published actual stay UNKNOWN/excluded; 309-03 expectation versus multiple and observed price versus unverified causality. 310-PL/EN methodology audit with incidental ticker routes to process audit/clarification without security analysis, portfolio reads or writes; 310-SEC named security remains on security review. Shared unchanged sentinels: direct portfolio review route and general investment education non-trigger. Runtime result rows start NOT_RUN and require exact receipts; no row is pre-accepted.

Regression selection: run the complete existing Investment OS route suite plus all new #310 cases because the Investment router contract changes; run all affected investing-skill case suites and test/code contracts for #308/#309, plus fixed shared sentinels. Exclusions: unrelated domains and Site UI visual checks, since this scope does not change Site UI; N/A must be reviewed before acceptance. Critical runtime cases receive three independent executions on the required surface. Preserve baseline attempts and failures; do not rerun only until green.

Campaign definition, prompt/rubric/input hashes, final changed-path impact map, exact case/execution counts, and evaluator separation will be finalized in the acceptance matrix before the test phase, after full development. First full development, then batched tests/fixes, then full offline validation and exact-Site runtime acceptance.

## Candidate history

| Candidate | Main SHA | Lab release ID / payload digest | Build + offline CI | Observed runtime identity / smoke | Supersedes / invalidated rows |
| --- | --- | --- | --- | --- | --- |
| C1 | pending | pending | NOT_RUN | NOT_RUN | none |

## Regression selection and counts

- Changed contracts / direct and transitive consumers: listed above; final source-level import/route inventory is required before test execution.
- Included cases / exclusions: full Investment OS route suite, 308/309 skill cases, 310 Polish/English and security-route neighbor cases, two unchanged sentinels; unrelated domains excluded because no shared contract is changed.
- Fixed sentinels / rotating unchanged-domain probes: existing portfolio-review positive; general investment education negative. Neither is counted as new capability acceptance.
- Last full runtime baseline candidate / behavior iterations since baseline: Iteration 7 source `89c28bf70353b4568c7bc031e128a5f57a0fe24d` / partial; this iteration changes an Investment-only router path, so full Investment OS domain route baseline is required.
- Planned distinct scenarios / executions by layer and required surface: 14 distinct scenarios (4 #308, 4 #309, 4 #310 including PL+EN, security neighbor and no-write, 2 sentinels); 3 independent executions for each critical runtime route/behavior row, exact count set in the completed matrix before execution.
- Critical stochastic scenarios repeated at least 3 times / instability history: #308-01/02/04, #309-01/02, #310-PL/EN/SEC; all attempts retained.
- PR CI / final-main checks and build / external runtime runs: required, exact runs pending.

## Defect intake and clarifications

| Bug Issue / discovery iteration | Existing contract / frozen criterion or unrelated | Severity / closure blocking | Fix PR or accepted deferral owner + future delivery iteration | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |

## Closure / abort decision

- Outcome: PENDING.
- Final candidate / matrix and immutable evidence links: pending.
- Committed Issues accepted / unresolved: #308, #309, #310 pending; #306 is prior-iteration carry-forward and excluded from this commitment.
- Required rows PASS / FAIL / NOT_RUN / BLOCKED / REVIEW_REQUIRED / reviewed N/A: all NOT_RUN before test phase.
- Shared regression verdict: pending.
- Non-blocking findings and accepted impact: pending.
- Scope compared with lock commit: pending.
- Issue / Project / PR reconciliation: pending.
- Owner proposal / reviewer acceptance / decision timestamp: pending.
- Next iteration eligibility: no automatic start or production promotion.

## Append-only issue-state correction — 2026-11-10

The frozen scope and opening status above were prepared from stale local issue data and describe #306 as unresolved. The live GitHub issue is closed as completed on 2026-11-09 through PR #600, with final Site/source receipts recorded on the issue. Therefore #306 is not an Iteration 8 carry-forward and must not be reopened or counted as Iteration 8 scope without a new explicit owner decision. Iteration 8 remains limited to #308–#310.
