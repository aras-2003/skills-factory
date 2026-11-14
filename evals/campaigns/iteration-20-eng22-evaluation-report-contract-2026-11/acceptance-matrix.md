# Iteration 20 — Evaluation Report Contract v1

Scope locked by PR #698; implementation baseline main: `071e96c080ca40a44ebda4ea0c5c3122134bc5e7`. Scope: bounded #335 dependency slice tracked in #697. All rows below were verified on merged main; NOT_RUN is not PASS.

| Case | Required observable result | Input / test fixture | Expected evidence | Status |
| --- | --- | --- | --- | --- |
| 20-01 | Strict versioned EvaluationReport schema and minimal valid example represent the complete #335/#619 contract | Schema and synthetic example | Draft 2020-12 schema, valid example; CLI reports VALID | PASS |
| 20-02 | Malformed identity/provenance/evidence, invalid enums/status combinations and unknown properties fail closed | Invalid synthetic fixture plus mutation tests | Missing identity, bogus SHA, unknown property, invalid enum and contradictory outcome rejected | PASS |
| 20-03 | Weighted calculator is deterministic for 0/0.5/1 anchors, importance/dimension weights, profile sums and rounding | Frozen synthetic assertion tests | Deterministic repeat; 7.25 raw rounds half-up to 7.3; profile sum mismatch rejected | PASS |
| 20-04 | Incomplete/NOT_RUN/BLOCKED required evidence yields null/NOT_SCORABLE and cannot PASS; missing or incomparable baseline yields null delta with a reason | Missing-evidence, blocked, comparator tests | Null score/non-PASS for unexecuted assertion; explicit null delta for runtime/assertion mismatch | PASS |
| 20-05 | Critical forbidden action blocks PASS regardless of high score; score and decision are distinct | High-score critical-block test | 9.5 numeric score with failed blocking gate results in REJECT | PASS |
| 20-06 | Existing receipt contract and historical receipts remain compatible; exact CI passes | Receipt-focused tests, full eval suite, repository/domain validators | Existing receipt schema/files unchanged; #699/#700 PR CI and post-merge CI passed | PASS |

Owner/reviewer: owner-delegated Codex review, not independent human review. No UI, Site, runtime evaluator, plugin release or automatic maturity change is included.


Exact revisions and workflow links: see [closeout-evidence.md](closeout-evidence.md). No runtime or Site claim is made.
