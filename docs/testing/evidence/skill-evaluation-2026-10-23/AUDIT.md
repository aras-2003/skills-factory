# Observed omissions and grouped correction

The parent Codex agent reviewed the nine Qwen final answers against the existing frozen assertions. This is a review by a different agent/model from the executor; version labels were visible. It is not claimed to be blind human review. Both local blind-evaluator attempts are invalid and preserved separately.

| Case | No skill | Historical 0.3.3 | Current 0.3.4 |
|---|---|---|---|
| Contradictory no-steps PASS | FAIL | PASS | PASS |
| Browser blocked | FAIL | FAIL | FAIL |
| Queued without steps | FAIL | FAIL | FAIL |

The baseline incorrectly turns non-execution into candidate failure. Both skill versions prevent that error in the contradictory-PASS case. However, the browser answers omit the required URL and check-time prerequisites. The queued answers omit explicit NOT_RUN evaluation status; 0.3.3 additionally omits the unassigned-runner condition. These are observed final-answer omissions, not hypotheses about hidden reasoning. The full assertion-index audit is in manual-audit.json.

Disposition for 0.3.4: ITERATE, not ready from this comparison. The 0.3.5 correction at 15740806f57d7058c0d2d3ac02f51c586e15e635 makes existing status fields and live-source evidence requirements explicit in the output contract. Static skill and catalog validation pass. The same three inputs and unchanged rubrics are being rerun with the same local model, temperature, seed, context and output budget. Six prior no-skill/0.3.4 comparator runs are explicitly reused, not represented as new executions.

This bounded comparison does not establish general model quality or authorize promotion/publication. The new source candidate is not claimed to be installed Lab or a Site deployment.

## 0.3.5 retest completed

All three new responses ended normally. Parent review: 2/3 PASS versus 1/3 for 0.3.4 and 0/3 no-skill. The queued answer still omits explicit NOT_RUN status fields and the missing-runner condition. See candidate-0.3.5/audit.json. Final disposition remains ITERATE; no promotion or installed-runtime claim.
