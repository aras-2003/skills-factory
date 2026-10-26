# Iteration 05 — interface-design candidate acceptance

- State: ACTIVE
- Owner: Arkadiusz Kamrowski
- Reviewer: Arkadiusz Kamrowski (self-review; not independent)
- Tracking Issue: [#471](https://github.com/aras-2003/skills-factory/issues/471)
- Native Project Iteration: not set; repository record is authoritative.
- Previous terminal iteration: Iteration 04, closed at main `508f35cdba43e2f93a231ae6f828d46b70534ba9`.
- Baseline main SHA: `508f35cdba43e2f93a231ae6f828d46b70534ba9`.
- Started at: 2026-10-26 23:23 UTC (2026-10-27 01:23 Europe/Warsaw).
- Lock commit SHA: `709522475f6e1671b7b3600f1c8b3a72bbf3df08` (scope-lock merge commit; fixed commitment is unchanged).
- Scope lock reviewed by / at: owner self-review, 2026-10-26 UTC (2026-10-27 Europe/Warsaw).

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
| C1 | `508f35cdba43e2f93a231ae6f828d46b70534ba9` | Site embeds `1.38.360+508f35cdba43`; payload `4c3f8ff795b415c7c8793f6cda27bcac912f83d3145ec25579f6e8db96823bdb`; Lab currently remains on `1.38.354+6dcbd09aa8f2` | Merge checks for #461 and main packaging are historical; final-main checks pending verification in this iteration. Campaign validation pending rerun. | Current Lab/Site identity observations documented above; paired behavior pending. | None |

## Regression selection and counts

- Changed contract: `interface-design` input/output behavior and natural selection only. Inspect current routing registry and consumers before finalizing exclusions.
- Included cases: six frozen skill cases, existing natural positive and report/diagram route cases, implementation near-miss, fixed sentinels and two unchanged-domain probes.
- Exclusions: no unrelated skill catalog-wide semantic sweep; no production data, writes, or Site publication test. Reason: isolated skill addition with no shared runtime/permission contract changes; fixed sentinels and probes detect cross-domain drift.
- Critical routing cases repeated 3x per required surface. One failed required run remains a failure until cause, fix and full impacted retest are recorded.
- Full-baseline applicability: this increment is not a production promotion and does not alter a shared interface. It does not claim a full runtime baseline.

## Defect intake

| Bug Issue / discovery iteration | Existing contract / frozen criterion | Severity / blocks closure | Fix / deferral | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |
| None identified yet | — | — | — | — | — |

## Closure decision

- Outcome: PENDING.
- Final candidate / matrix: pending execution.
- Required rows: NOT_RUN/BLOCKED until actual runtime execution and same-candidate Lab availability.
- Scope compared with lock commit: pending.
- Issue / Project / PR reconciliation: pending.
- Owner proposal / reviewer acceptance: pending; reviewer is the owner and is not independent.
- Next iteration eligibility: only after CLOSED or ABORTED.
