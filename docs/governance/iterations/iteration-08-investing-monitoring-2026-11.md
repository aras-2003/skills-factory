# Iteration 08 — Investing monitoring: KPI triggers and expectations

- State: CLOSED / ACCEPTED. The original lock began in PR #603 at `40420bc28c85826c2f28cb9709c34c45f583b487`; exact-candidate acceptance and terminal disposition are recorded below. The initial scope, candidate and test history remain unchanged.
- Owner / reviewer: Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review; not independent).
- Tracking issue / native Project iteration: #322 (coordination-only tracking); GitHub Project iteration `08 | Investing monitoring (provisional)`.
- Previous terminal iteration: Iteration 7 owner-aborted on 2026-11-09; see [append-only abort decision](iteration-07-abort-2026-11-09.md). #306 remains unresolved and open.
- Baseline main SHA: `0646cd0c4588b889070960c777e07829c3477b9e`.
- Lock commit SHA: `0f32e76e7642cfe12f39a5034605eb2fa5fc8e26` (final frozen scope tree, including the append-only prior-iteration abort record; implementation starts after merge).
- Started at / closed at (UTC): 2026-11-09 22:55:13 / 2026-11-10 00:47:01.
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
| PR #604 / CI attempt at `aac32ae1f384895e29e4ff8cd1b423967fca469f` | New runtime fixture IDs and target metadata did not match the existing runtime fixture/rubric contract. Validators blocked Lab packaging and domain validation before behavioral cases ran. | Blocking for PR, not a product behavior failure. | Correct fixture IDs to registry IDs and add `target`; owner; same Iteration 8. | Repeat validate-runtime, full Lab build, all affected CI, then campaign tests. | Pending |

## Closure / abort decision

- Outcome: CLOSED / ACCEPTED for the frozen Iteration 08 scope #308–#310.
- Final candidate / matrix and immutable evidence links: exact behavior candidate `03ef9f554c395db6a1cc482ef2c6434424a250e9`; [acceptance matrix](../../../evals/campaigns/iteration-08-investing-monitoring-2026-11/acceptance-matrix.md); [runtime evidence](../../../evals/campaigns/iteration-08-investing-monitoring-2026-11/runtime-evidence.md); final evidence PR #606 merged at `4ec40476f92ffa28ddb9ca223ed007a9b79b927a`.
- Committed Issues accepted / unresolved: #308, #309 and #310 accepted and closed completed; #306 was already completed in Iteration 7 and excluded from this commitment.
- Required rows: all 16 acceptance/shared rows PASS; runtime campaign records 14 configured outcomes and 15 exact-Site route receipts across five critical triples. Synthetic fixtures validate behavior/no-lookahead only; real-world source retrieval/authenticity is not claimed. No writes, trades or production promotion are claimed.
- Shared regression verdict: PASS on the exact accepted candidate; the shared portfolio-route negation regression was fixed in PR #605 and its exact Site receipt is in the runtime evidence.
- Non-blocking findings and accepted impact: release/promotion remains unapproved; this is a deliberate release gate, not an accepted production claim.
- Scope compared with lock commit: unchanged; only append-only corrections clarified #306's actual state and documented final evidence.
- Issue / Project / PR reconciliation: #308–#310 closed after exact Site v128 acceptance; PRs #604, #605 and #606 merged; native Project Iteration field is not verifiable through the available connector.
- Owner proposal / reviewer acceptance / decision timestamp: owner/reviewer Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review, not independent); accepted 2026-11-10 00:47:01 UTC.
- Next iteration eligibility: prior slot released; next work still requires its own committed scope lock. Production promotion remains a separate decision.

## Append-only issue-state correction — 2026-11-10

The frozen scope and opening status above were prepared from stale local issue data and describe #306 as unresolved. The live GitHub issue is closed as completed on 2026-11-09 through PR #600, with final Site/source receipts recorded on the issue. Therefore #306 is not an Iteration 8 carry-forward and must not be reopened or counted as Iteration 8 scope without a new explicit owner decision. Iteration 8 remains limited to #308–#310.

## Append-only first CI correction — 2026-11-10

PR #604 attempt 1 (`aac32ae1f384895e29e4ff8cd1b423967fca469f`) failed all four required CI workflows. In addition to the fixture `target`/ID mismatch, the run exposed frozen-campaign hash drift after Iteration 8 content was added to global routing/runtime registries: the R20/Iteration 7 source locks rejected the changed files and routing collision coverage changed from 30 to 32. No behavioral test verdict was produced. The corrective candidate restores both global registries to their PR-head bytes, moves all Iteration 8 runtime prompts/rubrics into its own 14-case suite, synchronizes Lab readiness versions, and adds a narrow exact-hash handoff so only the Iteration 8 candidate may supersede the affected historical source hashes. The historical campaign definitions remain unchanged. This correction has not yet passed CI or runtime validation.

## Append-only second and third CI corrections — 2026-11-10

- Attempt 2, PR #604 head `8b8302e752292d16792ae832aa724a9907dc4276`: restored the wrong baseline (the first PR head instead of `main`) for global routing/runtime registries. CI reported the two Iteration 8 fixture IDs in central coverage, missing relocated prompt paths, and a lifecycle fixture-count assertion (`0 != 2`). No candidate behavior verdict was produced.
- Attempt 3, PR #604 head `5b2b66b70405ebda92a890b4b1f794d1de314591`: restoring the registries to `main` made Domain integrity and Evaluation CI pass, and the Lab build passed. Site contract tests caught a route regression where “Review my investment portfolio; routing only” selected the process-audit route. Validate Skills found generated catalog views stale for the three versioned skills. The next candidate narrows the methodology detector and updates the generated catalog views; neither change promotes maturity or approves a release.

## Append-only fourth CI correction — 2026-11-10

Attempt 4, PR #604 head `ce73e526cd2cbb1f08aca92509d7efe4bed87dfb`: Site CI passed, including Lab build and MCP contracts. Domain integrity, Evaluation CI and Validate Skills were blocked by a `NameError` in the strict unassigned-candidate hash handoff, which referenced the Iteration 8 manifest before loading it. No campaign behavior result is inferred from that test harness failure. The next candidate initializes the exact Iteration 8 source-hash map before checking legacy candidates; no historical source locks are relaxed.


## Append-only closure reconciliation — 2026-11-10

The original opening header and pending closure block above were never reconciled after the final acceptance PR; they are superseded by this evidence-based terminal decision. Iteration 08 is **CLOSED / ACCEPTED** for its frozen scope #308–#310.

- Exact behavior candidate: `03ef9f554c395db6a1cc482ef2c6434424a250e9`, privately deployed and attested on owner-only Site v128 (Lab `1.38.481+03ef9f554c39`), deployment `appgdep_6af264fdd71c8191bbeab7c895f9ed9f`.
- The acceptance matrix records every required criterion PASS. Runtime evidence preserves all 14 configured outcomes and 15 route receipts across five critical triples; synthetic KPI/earnings fixtures test behavior and no-lookahead only, not live source retrieval/authenticity. No write, trade, or production promotion is claimed.
- Final evidence PR #606 merged as `4ec40476f92ffa28ddb9ca223ed007a9b79b927a`; all 14 check runs on its exact head passed. Issues #308, #309, and #310 were closed completed at 2026-11-10 00:46 UTC.
- Later main changes through `3339fd72121c897b9b3f4ba848eaf718786794cc` updated the interface-design skill and campaign/hash bookkeeping; they did not change the frozen Investment OS behavior paths listed above. The connected Site now attests this exact current main revision at v132.
- Owner/reviewer: Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review; not independent). Decision timestamp: 2026-11-10. The prior iteration slot is released. Production approval remains separate and false.

This append-only correction supersedes the stale initial status and pending closure fields; it does not alter the frozen scope, candidate, or historical attempts.
