# Iteration 05 — interface-design candidate acceptance

- State: ABORTED
- Owner: Arkadiusz Kamrowski
- Reviewer: Arkadiusz Kamrowski (self-review; not independent)
- Tracking Issue: [#471](https://github.com/aras-2003/skills-factory/issues/471)
- Native Project Iteration: not set; repository record is authoritative.
- Previous terminal iteration: Iteration 04, closed at main `508f35cdba43e2f93a231ae6f828d46b70534ba9`.
- Baseline main SHA: `508f35cdba43e2f93a231ae6f828d46b70534ba9`.
- Lock commit SHA: `709522475f6e1671b7b3600f1c8b3a72bbf3df08` (scope-lock merge commit; frozen scope unchanged).
- Scope lock reviewed by / at: owner self-review, 2026-10-26 UTC (2026-10-27 Europe/Warsaw).
- Started at: 2026-10-26 23:23 UTC (2026-10-27 01:23 Europe/Warsaw).

## Frozen commitment

| Issue | Outcome / acceptance criterion IDs | Included | Excluded | Dependencies / accepted evidence | Size |
| --- | --- | --- | --- | --- | --- |
| #423 UX-02 | AC-01–AC-07 | Finish acceptance of the already-merged `interface-design` 0.1.0 candidate: deterministic contracts, six isolated behavioral cases, natural routing, exact runtime identity, cross-surface and shared regression. Corrective fixes only when a frozen criterion fails. | New design capabilities, implementation workflow, maturity promotion without evidence, production publication. #424–#426, #445, #456 and all other no-iteration tickets remain outside this lock. | Implementation #461 is merged; static case set and source-bound Site package-load receipt exist. Neither proves runtime behavior. | M |

## Acceptance criteria and planned cases

| Criterion | Acceptance | Planned evidence |
| --- | --- | --- |
| AC-01 | Existing candidate and six-case set are structurally valid, isolated from evaluator rubrics, and pass all applicable final-main offline checks. | `ID-OFFLINE-01..04` |
| AC-02 | Natural interface-design positive routes to `interface-design`; report/diagram and implementation near-misses do not. | `ID-ROUTE-POS`, `ID-ROUTE-REPORT`, `ID-ROUTE-IMPLEMENT` |
| AC-03 | All six frozen behavioral cases pass: direct, indirect, report/diagram near-miss, implementation near-miss, insufficient context, permission/unavailable-data accessibility edge. | `interface-design-2026-10` six case IDs |
| AC-04 | Actual outputs cover mobile/desktop, loading/empty/error/unavailable, accessible keyboard/focus/announcement behavior, preserve supplied constraints, distinguish facts from assumptions, and do not claim implementation or invent data. | Per-case assertions in `skills/web-design/interface-design/tests/cases.yaml` |
| AC-05 | Runtime identity is independently observed on Lab and Site; any parity claim is against the same release/source/payload. Site attestation and embedded package identity are recorded separately. | `ID-IDENTITY-LAB`, `ID-IDENTITY-SITE`, `ID-SAME-CANDIDATE` |
| AC-06 | Fixed regression sentinels and two preselected unchanged-domain capability probes pass without data writes or persistence. | I01-SENT-001/002; `ID-PROBE-INV`, `ID-PROBE-COM` |
| AC-07 | #423 remains Verification until all required rows pass. Release/maturity decision records evidence; production deployment is not required for issue Done. | `ID-ISSUE-CLOSE` |

## Test plan

- Required surfaces: Skills Factory Lab and Skills Factory Cloud Next Site in ordinary Chat; Luna is not an executor or evaluator.
- Candidate under test: main `508f35cdba43e2f93a231ae6f828d46b70534ba9`; Site runtime reports embedded Lab `1.38.360+508f35cdba43`, payload `4c3f8ff795b415c7c8793f6cda27bcac912f83d3145ec25579f6e8db96823bdb`.
- Lab observed at lock planning: `1.38.354+6dcbd09aa8f2`, payload `2596fa5ba3357ffc813a975a97cedf97e6592d8b2f9e2bf365b322e6e78a90af`, package integrity verified, host unattested. This differs from the Site candidate; same-candidate paired acceptance is BLOCKED until Lab is updated. Do not infer compatibility from the version label.
- Executor: ChatGPT ordinary Chat using the default configured host model; capture the model/reasoning shown for each execution. Use fresh conversations for case runs; do not expose evaluator rubrics to the executor.
- Existing campaign: `evals/campaigns/interface-design-2026-10/campaign.yaml`; case definitions: `skills/web-design/interface-design/tests/cases.yaml`; route fixtures and rubric hashes are in the matrix.
- Run all six behavioral cases once per surface; run the three routing-critical natural prompts three independent times per surface. Run identity/load smoke, both fixed sentinels, and both rotating probes once per surface. Retain each attempt, including failures.
- Fixed sentinels: I01-SENT-001 (punctuation-only request; no unrelated routing/persistence) and I01-SENT-002 (synthetic 123 PLN gross at 23% VAT; compute 100 PLN net without external calls).
- Rotating probes selected before execution: synthetic Investment Opportunity Hunter request from `scripts/package/tests/test_investment_runtime.py::test_candidate_screen_is_not_misrouted_by_incidental_xtb_history`; synthetic unit-economics computation from I01-SENT-002. The existing unrelated prompt probe is retained as a sentinel, not relabeled as a capability test. No investment data access, external research, writes or persistence.
- Regression impact: candidate adds one skill and does not change adapters, schemas, shared workflow handoffs, permissions, packaging or existing routing code. Exact graph/source check required before treating this boundary as isolated. Last full supported runtime baseline: R20 historical; do not use R20 as the behavioral acceptance for this candidate. No production promotion in scope.
- Planned totals: 15 distinct scenario types per surface (identity, load, six behavioral, three routing, two sentinels, two probes); 21 executions per surface after repeating each of the three routing-critical cases three times; 42 runtime executions total. Plus four offline checks.
- Offline checks: campaign validation, evaluator-isolation validation, candidate contract/unit suites, and final-main required CI/package checks.
- Evidence retention: store immutable case receipts, input/output hashes, tool traces, runtime identity and timestamps in the matrix/linked artifact before CI artifact expiry.

## Candidate history

| Candidate | Main SHA | Lab release ID / payload digest | Build + offline CI | Runtime identity / smoke | Supersedes |
| --- | --- | --- | --- | --- | --- |
| C1 | `508f35cdba43e2f93a231ae6f828d46b70534ba9` | Site embeds `1.38.360+508f35cdba43`; payload `4c3f8ff795b415c7c8793f6cda27bcac912f83d3145ec25579f6e8db96823bdb`; Lab currently remains on `1.38.354+6dcbd09aa8f2` | #472 scope-lock PR CI: all checks PASS; local targeted suite 25 tests, 1 skipped; skill contract 6/6; campaign and isolation validation PASS. | Site natural positive invocation and candidate load observed; direct-positive behavior FAIL due invented records/data. Same-candidate Lab pairing BLOCKED. | None |
| C2 | Corrective PR pending | Pending Lab artifact / Site deployment from post-fix main | Required after corrective merge; run all applicable final-main gates. | Reinstall Lab and publish Site from same candidate; full locked matrix must be rerun. | C1 behavior evidence superseded where impact applies; preserve C1 FAIL. |

## Regression selection and counts

- Changed contract: `interface-design` input/output behavior and natural selection only. Inspect current routing registry and consumers before finalizing exclusions.
- Included cases: six frozen skill cases, existing natural positive and report/diagram route cases, implementation near-miss, fixed sentinels and two unchanged-domain probes.
- Exclusions: no unrelated skill catalog-wide semantic sweep; no production data, writes, or Site publication test. Reason: isolated skill addition with no shared runtime/permission contract changes; fixed sentinels and probes detect cross-domain drift.
- Critical routing cases repeated 3x per required surface. One failed required run remains a failure until cause, fix and full impacted retest are recorded.
- Full-baseline applicability: this increment is not a production promotion and does not alter a shared interface. It does not claim a full runtime baseline.

## Defect intake

| Bug Issue / discovery iteration | Existing contract / frozen criterion | Severity / blocks closure | Fix / deferral | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |
| [#474](https://github.com/aras-2003/skills-factory/issues/474) | #423 AC-04 / `interface-design-direct-positive`: do not invent order data | Major / blocks closure | Corrective changes in #475 and #478; no scope expansion | All six behavior cases, all routing cases, sentinels, probes, identity and smoke on the follow-up candidate | Owner self-review; not independent |
| [#480](https://github.com/aras-2003/skills-factory/issues/480) | #423 AC-03/AC-04 / `interface-design-insufficient-context`: do not import unrelated prior-chat context | Major / blocks closure | Corrective change in #481; context-boundary rule and stronger existing case only | Retest vague prompt and affected routing/behavior rows on Site after deployment; Lab is supplemental under future policy | Owner self-review; not independent |

## Abort decision — 2026-10-27 09:03 Europe/Warsaw

- **Outcome: ABORTED. This is not PASS, Done, release approval, or a waiver of any frozen criterion.**
- Owner decision: the user directed that Iteration 05 be stopped and specified that future substantive Cloud Next behavior checks use Site MCP, with Lab as an additional consistency check. Lab availability or version lag must not block a complete Site MCP behavioral result in future scopes.
- Reason: this frozen lock requires ordinary-Chat runtime acceptance on both Lab and Site and same-candidate identity. The required Lab surface was not available in ordinary Chat. The owner chose to terminate this lock rather than rewrite its frozen acceptance in place.
- Frozen commitment, exclusions, C1/C2 failures and all missing verdicts remain intact. The new runtime-surface policy in `docs/governance/ITERATION-DELIVERY.md` applies prospectively; it does not retrospectively mark Iteration 05 cases as passing.

### Final observed candidate and evidence boundary

- Current GitHub main at the abort decision: `aa060dc1c620a15e52329376ff1fd4a5af206acf`, including #481's context-boundary correction.
- A fresh Site `runtime_info` observation completed `2026-10-27T08:06:57.702Z`: embedded Lab release `1.38.366+63b9c002c7e6`, canonical source `63b9c002c7e672bb2999cca79cb7fae88b1e7260`, payload SHA-256 `d79b146627f7356e2b4ccd5eac7495fa29ca808202c3d4aff47c7cfe66cdb9f6`; Site attestation was `verified`, and provider mirror revision was `90623d4608444ce051ff3d8b959211b2ff59ff39`. Receipt output SHA-256: `c16477f240bf96ffad3cd7690a0246ca5d31bdbc5942259974802cbc024b2878`. This deployed source predates current main and does not contain #481.
- The four 4/4 routing-only Site calls documented on #456 are unrelated to the `interface-design` behavioral acceptance and are not credited to this matrix. They did not execute a child workflow.
- No post-#481 `interface-design` runtime retest was observed on Site. No Lab acceptance result was observed in ordinary Chat. Site identity evidence and package build evidence do not substitute for behavioral execution.

### Preserved verdicts and complete unresolved-criterion mapping

| Frozen criterion / finding | Abort-time disposition | Replacement work |
| --- | --- | --- |
| AC-01 — offline structure, isolation and final-main gates | Earlier candidate checks remain historical sub-evidence; no complete final-main iteration acceptance is claimed. | #423: rerun required offline gates on the follow-up candidate and record exact main SHA. |
| AC-02 — natural positive and near-miss routing | NOT_RUN as a complete final-candidate Site matrix. The separate #456 route-only matrix does not count. | #423: execute the frozen positive, report/diagram and implementation prompts on Site MCP. |
| AC-03 — six behavioral cases | Incomplete. Preserve the direct-positive FAIL in #474 and insufficient-context FAIL in #480; remaining final-candidate cases are NOT_RUN. | #423: execute all six frozen cases; #474: retest direct-positive; #480: retest insufficient context after deploying #481. |
| AC-04 — output quality, responsive/accessibility states, no invented facts or implementation claims | C1 and C2 direct-positive failures remain FAIL; post-fix behavior is NOT_RUN. | #423 and #474: rerun all applicable output assertions on the Site MCP candidate. |
| AC-05 — exact runtime identity and same-candidate pairing | Site identity is verified for source `63b9c002…`; it is older than current main `aa060dc…`. The required Lab observation in ordinary Chat and same-candidate pair are BLOCKED/NOT_RUN. | #423: verify the deployed Site candidate for semantic tests. Record any supplemental Lab identity separately; do not claim parity without matching identities. |
| AC-06 — fixed sentinels and two rotating probes | NOT_RUN on the final post-#481 candidate. | #423: execute both fixed sentinels and both preselected probes on Site MCP, with no data writes. |
| AC-07 — issue closure and release decision | NOT_RUN; #423 remains open and unaccepted. | #423: make a new evidence-based closure decision only after AC-01–AC-06 are resolved. |
| #474 — invented operational data | Historical FAILs remain immutable; the source correction is merged but not behaviorally accepted on the final current-main Site. | Keep #474 open; link its retest to #423's next locked scope. |
| #480 — unrelated prior-chat context | Historical FAIL remains immutable; #481 is merged, but the observed Site package predates #481. | Keep #480 open; publish/test the source containing #481 under a future scope and link the actual Chat evidence. |

Issues #423, #474 and #480 remain open; aborting this iteration does not close them or change their acceptance results. #424–#426 were explicitly excluded from this lock and remain backlog items dependent on #423. No replacement iteration is started by this abort decision.

### Reconciliation

- Scope compared with lock commit: unchanged; termination is administrative, not a scope rewrite.
- Preserved failed and unrun evidence: retained in #423, #474, #480 and their original chat/runtime records.
- Project status: the tracking issue must show an aborted disposition without `Done`; child behavior issues stay in Verification until their replacement criteria are actually tested.
- Next iteration eligibility: released after this ABORTED record is merged. A new scope requires its own PLANNED record, test matrix and tracking link.
