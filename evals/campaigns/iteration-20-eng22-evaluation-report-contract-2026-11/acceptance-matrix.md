# Iteration 20 — Evaluation Report Contract v1

Scope locked by PR #698; implementation baseline main: `071e96c080ca40a44ebda4ea0c5c3122134bc5e7`. Scope: bounded #335 dependency slice in #697. NOT_RUN is not PASS.

| Case | Required observable result | Input / test fixture | Expected evidence | Status |
| --- | --- | --- | --- | --- |
| 20-01 | Strict versioned EvaluationReport schema and minimal valid example represent the complete #335/#619 contract | Schema and synthetic example | Schema URI/version, valid example and deterministic validator output | NOT_RUN |
| 20-02 | Malformed identity/provenance/evidence, invalid enums/status combinations and unknown properties fail closed | Invalid synthetic fixtures | Named rejection assertions; no mutation to historical receipts | NOT_RUN |
| 20-03 | Weighted calculator is deterministic for 0/0.5/1 anchors, assertion criticality, dimensions, profile sums, rounding and boundaries | Frozen synthetic assertion fixtures | Exact expected raw and displayed score, calculation version | NOT_RUN |
| 20-04 | Incomplete/NOT_RUN/BLOCKED required evidence yields null/NOT_SCORABLE and cannot PASS; missing or incomparable baseline yields null delta with a reason | Missing-evidence, blocked, comparator-missing fixtures | Validator and decision output explicitly not scorable / non-PASS; no fabricated delta | NOT_RUN |
| 20-05 | Critical forbidden action blocks PASS regardless of high score; score and decision are distinct | High-score critical-block fixture | Explicit blocking gate and non-PASS decision | NOT_RUN |
| 20-06 | Existing receipt contract and historical receipts remain compatible; exact CI passes | Current receipt tests + full validation | Existing receipt fixtures unchanged/readable; PR and main check URLs | NOT_RUN |

Owner/reviewer: owner-delegated Codex review, not independent human review. No UI, Site, runtime evaluator, plugin release or automatic maturity change is included.
