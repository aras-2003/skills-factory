# Iteration 08 acceptance matrix — 2026-11

Baseline source: `0646cd0c4588b889070960c777e07829c3477b9e`. Statuses below are planned; no test has run.

| Criterion | Observable acceptance | Planned fixture / case | Offline validation | Cloud Next runtime | State |
| --- | --- | --- | --- | --- | --- |
| 308-A | Each critical ACTIVE thesis assumption maps to KPI, basis, dated source, falsifiable threshold, rolling period, cadence, next verification and action class. | `underwriting-kpi-trigger-matrix` | case/contract checks | Load exact skill and exercise supplied trigger matrix | NOT_RUN |
| 308-B | REVIEW/ESCALATE cannot silently become invalidation or a trade; threshold crossing never automatically sells. | `monitor-kpi-threshold-crossing-no-trade` | negative case checks | Execute crossing case; inspect action boundary | NOT_RUN |
| 308-C | Verified material business breach escalates; price movement alone does not kill business thesis. | `monitor-verified-kill-criterion-escalates`; `monitor-price-only-no-thesis-invalidation` | paired positive/negative cases | Execute breach and price-only controls | NOT_RUN |
| 308-D | Missing verified canonical ACTIVE thesis blocks; no invented persistence or surrogate DRAFT baseline. | `monitor-draft-only` | missing-state case | Execute missing-baseline case | NOT_RUN |
| 309-A | Prior/revised consensus, reported result and guidance are dated and aligned on metric definition, basis and period; mismatch is visible. | `underwriting-expectations-bridge-no-lookahead`; `valuation-consensus-actual-guidance-bridge` | fixture/case checks | Load exact skill and bridge supplied historical cycle | NOT_RUN |
| 309-B | Missing/stale/conflicted estimates or future-published facts remain UNKNOWN/N/M; no look-ahead, imputation or post-hoc threshold. | `valuation-card-no-lookahead`; `valuation-stale-consensus-revisions` | adversarial temporal/data cases | Execute as-of replay with known publication timestamps | NOT_RUN |
| 309-C | Expectation change and multiple change remain separate; price move is observed, causality uncertain absent evidence; thesis quality is assessed independently of return. | `monitor-expectations-bridge-historical` | case/rubric checks | Execute with supplied price move and no causal evidence | NOT_RUN |
| 309-D | No canonical writes without explicit authorization and successful write receipts. | `monitor-analysis-without-write-authorization` | no-write negative contract | Confirm no write-capable tool invocation | NOT_RUN |
| 310-A | Polish methodology/process audit with incidental ticker routes to the Investment OS front door, not security underwriting. | `investment-methodology-audit-incidental-ticker-pl`; PL synonym case | route contract test | 3 independent `route_investment_request` calls | NOT_RUN |
| 310-B | English methodology/process audit with incidental ticker has the same bounded front-door route. | `investment-methodology-audit-incidental-ticker-en` | route contract test | 3 independent route calls | NOT_RUN |
| 310-C | Named ticker is still security-review route when security analysis is the actual user decision. | `router-positive-security-review-neighbor` | competing-route regression | 3 independent route calls | NOT_RUN |
| 310-D | Process audit does not trigger canonical portfolio reads or writes. | 310-NOWRITE | contract/risk test | inspect actual tool trace | NOT_RUN |
| 310-E | Clear process audit is directly routed to the Investment OS front door without unnecessary clarification. | 310-PL, 310-EN | route contract + bilingual evals | 3 independent route receipts per language and inspect tool trace | NOT_RUN |
| Shared-1 | Existing portfolio-review request still routes to portfolio review. | sentinel-portfolio-review | full route suite | exact runtime route receipt | NOT_RUN |
| Shared-2 | Generic investment education remains outside Investment OS execution. | sentinel-education | full route suite | exact runtime route receipt | NOT_RUN |

## Execution rules

- Complete all scoped development before executing the above tests.
- Preserve the deployed Site as the baseline; it currently attests source `3bdeef677347d81b56fcbb5ba9e83722869a869c` and Lab `1.38.476`. It is not the candidate.
- After development, run focused offline batches for #308, #309 and #310; fix failures in batches and rerun every impacted case. Then run full configured repository validation.
- Run the full Investment OS route suite because the route facade changes. Run three independent attempts for critical behavior/routing rows on the exact merged Site revision; record each attempt, including failures. No retries for a green-only sample.
- Close each criterion only with exact-revision evidence. CI, `load_skill`, or routing receipts alone do not prove behavioral acceptance.

## State correction

The Iteration 7 abort record and initial Iteration 8 scope lock were written from stale local issue state and say #306 remained open. GitHub issue #306 is actually closed as completed on 2026-11-09 via PR #600; the closeout records Site v126 and source SHA `3bdeef677347d81b56fcbb5ba9e83722869a869c`. It is prior-iteration completed work, not an Iteration 8 carry-forward. Recheck source issue/project state at final reconciliation; this correction does not reopen #306 or change the frozen #308–310 commitment.

## Preserved CI attempts

- Attempt 1, PR #604 head `aac32ae1f384895e29e4ff8cd1b423967fca469f`: Site CI failed during source-bound Lab build and Domain integrity failed during source contract validation. Both identified stale runtime fixture ID/target metadata. Behavioral router and skill cases were skipped; no 308/309/310 behavior verdict was produced. Fix is in progress; this attempt remains recorded and is not replaced by a green rerun.

## Preserved CI attempt detail

- Attempt 1, PR #604 head `aac32ae1f384895e29e4ff8cd1b423967fca469f`: all four required workflows failed. Site CI and Domain integrity first failed on fixture `target`/ID metadata; Validate Skills also reported the central fixture-coverage assertion, readiness metadata drift, frozen R20/Iteration 7 hash drift, and a routing collision count change from 30 to 32; Evaluation CI failed on the same frozen-source drift. Behavioral evaluation did not run to a verdict. Corrective candidate restores the global routing/runtime registries, uses 14 Iteration 8-owned runtime cases, synchronizes readiness metadata and adds an exact hash-bound candidate handoff. The first attempt remains immutable and no pass is claimed.
