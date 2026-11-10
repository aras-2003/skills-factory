# Iteration 08 acceptance matrix — 2026-11

Baseline source: `40420bc28c85826c2f28cb9709c34c45f583b487`. Final statuses below are based on exact Site runtime evidence for merged source `03ef9f554c395db6a1cc482ef2c6434424a250e9`.

| Criterion | Observable acceptance | Planned fixture / case | Offline validation | Cloud Next runtime | State |
| --- | --- | --- | --- | --- | --- |
| 308-A | Each critical ACTIVE thesis assumption maps to KPI, basis, dated source, falsifiable threshold, rolling period, cadence, next verification and action class. | `underwriting-kpi-trigger-matrix` | case/contract checks | Load exact skill and exercise supplied trigger matrix | PASS |
| 308-B | REVIEW/ESCALATE cannot silently become invalidation or a trade; threshold crossing never automatically sells. | `monitor-kpi-threshold-crossing-no-trade` | negative case checks | Execute crossing case; inspect action boundary | PASS |
| 308-C | Verified material business breach escalates; price movement alone does not kill business thesis. | `monitor-verified-kill-criterion-escalates`; `monitor-price-only-no-thesis-invalidation` | paired positive/negative cases | Execute breach and price-only controls | PASS |
| 308-D | Missing verified canonical ACTIVE thesis blocks; no invented persistence or surrogate DRAFT baseline. | `monitor-draft-only` | missing-state case | Execute missing-baseline case | PASS |
| 309-A | Prior/revised consensus, reported result and guidance are dated and aligned on metric definition, basis and period; mismatch is visible. | `underwriting-expectations-bridge-no-lookahead`; `valuation-consensus-actual-guidance-bridge` | fixture/case checks | Load exact skill and bridge supplied historical cycle | PASS |
| 309-B | Missing/stale/conflicted estimates or future-published facts remain UNKNOWN/N/M; no look-ahead, imputation or post-hoc threshold. | `valuation-card-no-lookahead`; `valuation-stale-consensus-revisions` | adversarial temporal/data cases | Execute as-of replay with known publication timestamps | PASS |
| 309-C | Expectation change and multiple change remain separate; price move is observed, causality uncertain absent evidence; thesis quality is assessed independently of return. | `monitor-expectations-bridge-historical` | case/rubric checks | Execute with supplied price move and no causal evidence | PASS |
| 309-D | No canonical writes without explicit authorization and successful write receipts. | `monitor-analysis-without-write-authorization` | no-write negative contract | Confirm no write-capable tool invocation | PASS |
| 310-A | Polish methodology/process audit with incidental ticker routes to the Investment OS front door, not security underwriting. | `investment-methodology-audit-incidental-ticker-pl`; PL synonym case | route contract test | 3 independent `route_investment_request` calls | PASS |
| 310-B | English methodology/process audit with incidental ticker has the same bounded front-door route. | `investment-methodology-audit-incidental-ticker-en` | route contract test | 3 independent route calls | PASS |
| 310-C | Named ticker is still security-review route when security analysis is the actual user decision. | `router-positive-security-review-neighbor` | competing-route regression | 3 independent route calls | PASS |
| 310-D | Process audit does not trigger canonical portfolio reads or writes. | 310-NOWRITE | contract/risk test | inspect actual tool trace | PASS |
| 310-E | Clear process audit is directly routed to the Investment OS front door without unnecessary clarification. | 310-PL, 310-EN | route contract + bilingual evals | 3 independent route receipts per language and inspect tool trace | PASS |
| Shared-1 | Existing portfolio-review request still routes to portfolio review. | sentinel-portfolio-review | full route suite | exact runtime route receipt | PASS |
| Shared-2 | Generic investment education remains outside Investment OS execution. | sentinel-education | full route suite | exact runtime route receipt | PASS |

## Completed execution

- Development completed and merged in PRs #604 and #605. PR #605 fixed negation scope in routing and added exact regression coverage plus complete, explicitly synthetic-only KPI/earnings fixtures.
- The exact merged source was privately deployed to the existing owner-only Site as v128. The Site attested canonical source `03ef9f554c395db6a1cc482ef2c6434424a250e9`, Lab `1.38.481+03ef9f554c39`, verified identity, and deployment `appgdep_6af264fdd71c8191bbeab7c895f9ed9f` succeeded.
- Focused runtime cases for #308, #309, and #310 were evaluated against the exact packaged instructions. Every listed behavioral/routing case passed its paired rubric; expected fail-closed cases remain explicitly blocked/not-run as defined by their rubrics.
- Five critical route prompts (310-EN, 310-PL, 310-NOWRITE, 310-SEC and shared-portfolio) each have three independent successful receipts from the exact Site revision. The shared-portfolio negation regression now routes to `investment-portfolio-review`.
- Full local and GitHub validation passed. Exact receipts and case outcomes are recorded in `runtime-evidence.md`. A route/load receipt proves only that operation; no unobserved child execution, portfolio read, canonical write, or trade is claimed.

## State correction

The Iteration 7 abort record and initial Iteration 8 scope lock were written from stale local issue state and say #306 remained open. GitHub issue #306 is actually closed as completed on 2026-11-09 via PR #600; the closeout records Site v126 and source SHA `3bdeef677347d81b56fcbb5ba9e83722869a869c`. It is prior-iteration completed work, not an Iteration 8 carry-forward. Recheck source issue/project state at final reconciliation; this correction does not reopen #306 or change the frozen #308–310 commitment.

## Preserved CI attempts

- Attempt 1, PR #604 head `aac32ae1f384895e29e4ff8cd1b423967fca469f`: Site CI failed during source-bound Lab build and Domain integrity failed during source contract validation. Both identified stale runtime fixture ID/target metadata. Behavioral router and skill cases were skipped; no 308/309/310 behavior verdict was produced. Fix is in progress; this attempt remains recorded and is not replaced by a green rerun.

## Preserved CI attempt detail

- Attempt 1, PR #604 head `aac32ae1f384895e29e4ff8cd1b423967fca469f`: all four required workflows failed. Site CI and Domain integrity first failed on fixture `target`/ID metadata; Validate Skills also reported the central fixture-coverage assertion, readiness metadata drift, frozen R20/Iteration 7 hash drift, and a routing collision count change from 30 to 32; Evaluation CI failed on the same frozen-source drift. Behavioral evaluation did not run to a verdict. Corrective candidate restores the global routing/runtime registries, uses 14 Iteration 8-owned runtime cases, synchronizes readiness metadata and adds an exact hash-bound candidate handoff. The first attempt remains immutable and no pass is claimed.

- Attempt 2, head `8b8302e752292d16792ae832aa724a9907dc4276`: all required workflows failed before behavior verdicts. The central runtime registry still contained two Iteration 8 IDs, the routing registry had their cases, and moving their prompt files broke existing source references. The lifecycle audit reported `0 != 2` central cases. Corrected by restoring registry files from exact Iteration 8 base `40420bc` and keeping campaign prompts in the isolated suite.
- Attempt 3, head `5b2b66b70405ebda92a890b4b1f794d1de314591`: Domain integrity and Evaluation CI passed; Site CI reached MCP contract tests and exposed the portfolio request misroute; Validate Skills passed readiness/lifecycle/artifact builds but failed source/registry parity because generated catalog views were stale. Corrected the methodology intent boundary and synchronized CATALOG/JSON catalog versions. These were CI findings, not Site runtime acceptance.

- Attempt 4, head `ce73e526cd2cbb1f08aca92509d7efe4bed87dfb`: Site CI passed all checks. Domain integrity and Evaluation CI failed in shared campaign unit tests, and Validate Skills failed its campaign job, all from `NameError: iter08_hashes is not defined` in `separately_validated_unassigned_candidate_paths`. The candidate loaded the manifest map only in other handoff functions; this was a test-validator defect. Fixed by loading the map before the unassigned candidate hash loop. No Iteration 8 runtime cases were executed.

## Final runtime closeout

- Exact candidate: `03ef9f554c395db6a1cc482ef2c6434424a250e9`; Site v128; Lab `1.38.481+03ef9f554c39`; deployment succeeded and attestation verified.
- Final CI for PR #605 head `857970ae23cdd4937111befa3592bf8d0a14d098`: Site CI run 594, Evaluation CI run 361, Domain integrity run 953, and Validate Skills run 953 all passed.
- Local Cloud Next contract suite: 39 passed. Local campaign/eval validator suite: 314 passed, 0 failed, 2 skipped. Local hash/isolation validation passed; TypeScript, lint and production Site build passed.
- `runtime-evidence.md` records all 14 configured case outcomes, five trios of exact Site routing receipts and the limits of each receipt. Synthetic KPI/earnings data validates temporal and control behavior only; no real-world source retrieval/authentication is claimed. Production promotion remains unapproved (`release_approved=false`).
