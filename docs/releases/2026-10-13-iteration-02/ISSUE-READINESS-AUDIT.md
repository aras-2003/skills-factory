# Iteration 2 — premerge audit of all 18 tracked Issues

**As-of:** 2026-10-13; source candidate PR [#342](https://github.com/aras-2003/skills-factory/pull/342).
**Boundary:** audit of source and Issue criteria, **not runtime certification**.
Exact candidate SHA, main HEAD and CI should be rechecked after each commit or upstream change.
Source PR #338/#339 own the Issues; combined PR #340 and #342 are validation/integration only.

## Decision semantics

- **SOURCE_READY_FOR_RUNTIME** = source tests, deterministic validators and handoff exist; still needs merged version, tested provider and independent acceptance.
- **RESIDUAL_DEVELOPMENT** = a code/contract/test-harness gap remains beyond offline validators. Not development complete.
- **CONDITIONAL_REMEDIATION** = must execute exact-version retest/adjudication, then implement any confirmed still-failing paths. Do not claim PASS.
- **EXTERNAL_AUTHORIZATION** = current next step is a permission/provider/deployment decision outside this PR; no permission inferred.

| Issue / current Project marker | Premerge source disposition | Implemented evidence | **What remains before acceptance** |
| --- | --- | --- | --- |
| [#149](https://github.com/aras-2003/skills-factory/issues/149) Cloud MCP E2E / In progress | **RESIDUAL_DEVELOPMENT** | Site route-only evidence binder + no-child/no-write negatives; runtime_info and reference-tool source | Adapt capture/receipt transport to actual Site unsigned receipt shape and SVG rendering; run fresh Chat E2E on new installed version; owner-private Site identity. |
| [#240](https://github.com/aras-2003/skills-factory/issues/240) Local runner / In progress | **RESIDUAL_DEVELOPMENT** | SHA-pinned Lab runner and Desktop TEST controller, idempotent archive, fixtures, receipt protocol | Connect actual approved Desktop/Work executor to canonical receipt; isolate OS/network, test crash/concurrency and rubric withholding in real client. |
| [#242](https://github.com/aras-2003/skills-factory/issues/242) Flow/catalog availability / Validation | **SOURCE_READY_FOR_RUNTIME** | Single catalog/workflow registry parity validator and 83-component source coverage | Capture separate *installed* Site/Lab vs main vs evidence status after deployment, confirm displayed availability. |
| [#243](https://github.com/aras-2003/skills-factory/issues/243) AIS/RT known failures / In progress | **CONDITIONAL_REMEDIATION** | R17 history and affected-case retest ledger, append-only receipts | Reconcile latest affected AIS/RT failures with exact runnable receipts; fix confirmed high-risk regressions before affected release. |
| [#247](https://github.com/aras-2003/skills-factory/issues/247) Registry/capabilities / In progress | **SOURCE_READY_FOR_RUNTIME** | Canonical registry↔catalog↔capability source parity + fail-closed UNASSESSED contract | Human capability assessments where still UNASSESSED; compare actual provider permissions/tools before publishing claims. |
| [#250](https://github.com/aras-2003/skills-factory/issues/250) Runtime attestation / Validation | **SOURCE_READY_FOR_RUNTIME** | MCP runtime_info identity formats, explicit unattested fallback, tool SHA/unit checks | Fresh Site and Work runtime_info same-version observations, stale-registration browser negative test, signed/independent evidence. |
| [#251](https://github.com/aras-2003/skills-factory/issues/251) Browser MCP E2E / Validation | **RESIDUAL_DEVELOPMENT** | Browser capture/data binder, raw tool/chart/screenshot digest checks, route-only proof | Implement a provider-compatible real client evidence export/binding (Site has SVG and unsigned Site runtime SHA); collect E2E client/tool traces. |
| [#252](https://github.com/aras-2003/skills-factory/issues/252) Failure flows / In progress | **SOURCE_READY_FOR_RUNTIME** | Deterministic timeout/denial/malformed/missing schema fixtures; blocked vs failed vs not-run states | Controlled TEST provider fault injection, compare actual failure outcomes with local fixtures. |
| [#253](https://github.com/aras-2003/skills-factory/issues/253) Work/Site parity / Validation | **RESIDUAL_DEVELOPMENT** | Work/Site release/source/tool-schema/flow comparator with exact-source guards | Automate/record independently authenticated same-version Work + Site flow receipts for routing, architecture review, charts; Site and Lab SHA must stay distinct. |
| [#254](https://github.com/aras-2003/skills-factory/issues/254) Chat charts / Validation | **SOURCE_READY_FOR_RUNTIME** | Signed/zero/negative renderer regressions, source-bound SVG/PNG payload guards, separate CLIENT_RENDERED vs PAYLOAD_RENDERED | Real bar+line UI screenshot/accessibility/export; resolve any observed client presentation errors instead of assuming local render means displayed. |
| [#256](https://github.com/aras-2003/skills-factory/issues/256) R17 nine failures / In progress | **CONDITIONAL_REMEDIATION** | Immutable 36 PASS / 9 FAIL history + version-locked retest queue | Run nine comparable cases, independent review each actual failure, then implement residual fixes without changing historical verdicts. |
| [#257](https://github.com/aras-2003/skills-factory/issues/257) Two Production-only cases / Discovery | **EXTERNAL_AUTHORIZATION** | Two cases explicitly excluded from Lab; separate source-locked input-only envelopes | Case-specific owner/Production permission + isolated execution, not Lab PASS. Do not silently schedule production. |
| [#259](https://github.com/aras-2003/skills-factory/issues/259) Site publish and rollback / Validation | **EXTERNAL_AUTHORIZATION** | Site identity/rollback offline preflight and approved Sites runbook | Obtain publisher tool/access, old immutable rollback artifact + payload digest and separate Site source, then canary/publish/rollback receipts. Branch protection API 403. |
| [#286](https://github.com/aras-2003/skills-factory/issues/286) Skill lifecycle audit / Validation | **SOURCE_READY_FOR_RUNTIME** | 64-skill source lifecycle audit and source coverage matrix (original ticket 54) | Independent semantic review of REVIEW_REQUIRED subset; user acceptance and controlled runtime follow-up as separately scoped. |
| [#287](https://github.com/aras-2003/skills-factory/issues/287) Domain routing semantics / In progress | **RESIDUAL_DEVELOPMENT** | Semantic inventory and near-miss source screening; issue 303 write authorization remediation history | Complete domain-by-domain human semantic contract review and implement any confirmed routing/authorization corrections, then fresh boundary tests. |
| [#289](https://github.com/aras-2003/skills-factory/issues/289) 54-skill behavior/routing campaign / Validation | **RESIDUAL_DEVELOPMENT** | Full source inventory, synthetic 18-case triage runner, receipts/rubric isolation | Freeze risk-prioritized executable 54/64-skill positive/negative/near-miss/tool-denial campaign and independent evaluator sampling; 18-case triage cannot substitute. |
| [#290](https://github.com/aras-2003/skills-factory/issues/290) Registered workflow lifecycle / In progress | **RESIDUAL_DEVELOPMENT** | 19-workflow source audit, contract parity and source fixtures (original ticket 16) | Resolve four known REVIEW_REQUIRED workflow entrypoint/precondition findings with actual scoped source edits or explicit documented waiver; confirm semantic tests. |
| [#311](https://github.com/aras-2003/skills-factory/issues/311) Campaign remediation / Validation | **CONDITIONAL_REMEDIATION** | Historic per-case campaign evidence retained; guarded intake, TEST-only source input packages | Independent adjudication of historical 44 FAIL + 72 BLOCKED (2026-10-10 baseline), prioritize true source failures, repair and retest; unapproved real writes stay blocked. |

## Summary

**6 SOURCE_READY_FOR_RUNTIME, 7 RESIDUAL_DEVELOPMENT, 3 CONDITIONAL_REMEDIATION, 2 EXTERNAL_AUTHORIZATION = 18.**

This count describes **source next-actions**, not how many Issues may be marked Done.
All 18 original Issues remain OPEN; no model/runtime PASS or approval inferred.
Project statuses are reproduced from the Issue body `Project status` marker,
not independently read from the GitHub Projects field. A separate Projects
field check is required to certify board synchronization.

## Premerge gates

1. Confirm fresh current `main` and re-integrate any intervening commits;
   do not rely on an old green exact-HEAD or a `mergeable` flag alone.
2. Three CI jobs must all PASS on the final single integration PR #342 HEAD;
   artifacts linked to its exact SHA, 11 Lab + 7 external cases, 34 planned runs.
3. Independent code review and unresolved-review check required.
   Branch protection reading is blocked (GitHub connector HTTP 403), so
   protected-main/rules remain UNVERIFIED until owner checks them.
4. **Do not merge #338/#339/#340 separately** after they are represented in
   #342. Keep each Issue linked to exactly one authoritative source PR.
5. No Site publish without approved native publisher, old immutable artifact
   and decoded payload digest. Site worker SHA vs embedded Lab SHA are separate.
6. Postmerge Lab artifact is built from the resulting `main` commit, not
   a previous PR SHA; all runtime tests use that exact postmerge release.

See [merge/Site/QA runbook](MERGE-SITE-QA-RUNBOOK.md) for release sequence.
