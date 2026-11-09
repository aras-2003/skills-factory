# Iteration 08 acceptance matrix — 2026-11

Baseline source: `0646cd0c4588b889070960c777e07829c3477b9e`. Statuses below are planned; no test has run.

| Criterion | Observable acceptance | Planned fixture / case | Offline validation | Cloud Next runtime | State |
| --- | --- | --- | --- | --- | --- |
| 308-A | Each critical ACTIVE thesis assumption maps to KPI, basis, dated source, falsifiable threshold, rolling period, cadence, next verification and action class. | 308-01 | skill static/case checks | Load exact skill and exercise supplied trigger matrix | NOT_RUN |
| 308-B | REVIEW/ESCALATE cannot silently become invalidation or a trade; threshold crossing never automatically sells. | 308-02 | negative case checks | Execute trigger cases; inspect for action boundary | NOT_RUN |
| 308-C | Verified material business breach escalates; price movement alone does not kill business thesis. | 308-03 | paired positive/negative cases | Execute breach and price-only controls | NOT_RUN |
| 308-D | Missing verified canonical ACTIVE thesis blocks; no invented persistence or surrogate DRAFT baseline. | 308-04 | missing-state case | Execute missing-baseline case | NOT_RUN |
| 309-A | Prior/revised consensus, reported result and guidance are dated and aligned on metric definition, basis and period; mismatch is visible. | 309-01 | fixture/case checks | Load exact skill and bridge supplied historical cycle | NOT_RUN |
| 309-B | Missing/stale/conflicted estimates or future-published facts remain UNKNOWN/N/M; no look-ahead, imputation or post-hoc threshold. | 309-02 | adversarial temporal/data cases | Execute as-of replay with known publication timestamps | NOT_RUN |
| 309-C | Expectation change and multiple change remain separate; price move is observed, causality uncertain absent evidence; thesis quality is assessed independently of return. | 309-03 | case/rubric checks | Execute with supplied price move and no causal evidence | NOT_RUN |
| 309-D | No canonical writes without explicit authorization and successful write receipts. | 309-04 | no-write negative contract | Confirm no write-capable tool invocation | NOT_RUN |
| 310-A | Polish methodology/process audit with incidental ticker routes to the process audit/clarification, not security underwriting. | 310-PL | route contract test | 3 independent `route_investment_request` calls | NOT_RUN |
| 310-B | English methodology/process audit with incidental ticker has the same bounded route. | 310-EN | route contract test | 3 independent route calls | NOT_RUN |
| 310-C | Named ticker is still security-review route when security analysis is the actual user decision. | 310-SEC | competing-route regression | 3 independent route calls | NOT_RUN |
| 310-D | Process audit does not trigger canonical portfolio reads or writes. | 310-NOWRITE | contract/risk test | inspect actual tool trace | NOT_RUN |
| Shared-1 | Existing portfolio-review request still routes to portfolio review. | sentinel-portfolio-review | full route suite | exact runtime route receipt | NOT_RUN |
| Shared-2 | Generic investment education remains outside Investment OS execution. | sentinel-education | full route suite | exact runtime route receipt | NOT_RUN |

## Execution rules

- Complete all scoped development before executing the above tests.
- Preserve the deployed Site as the baseline; it currently attests source `3bdeef677347d81b56fcbb5ba9e83722869a869c` and Lab `1.38.476`. It is not the candidate.
- After development, run focused offline batches for #308, #309 and #310; fix failures in batches and rerun every impacted case. Then run full configured repository validation.
- Run the full Investment OS route suite because the route facade changes. Run three independent attempts for critical behavior/routing rows on the exact merged Site revision; record each attempt, including failures. No retries for a green-only sample.
- Close each criterion only with exact-revision evidence. CI, `load_skill`, or routing receipts alone do not prove behavioral acceptance.
