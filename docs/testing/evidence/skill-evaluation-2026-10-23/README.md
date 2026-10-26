# Skill-evaluation controlled comparison — 2026-10-23

Issue #237. Disposition: **ITERATE**, not candidate-ready or released.

Nine tool-free local Qwen3:4b executor responses completed for the three frozen evidence-state cases and no-skill / historical draft 0.3.3 / current 0.3.4 variants. All ended normally, without token-limit truncation. Plans bind input, rubric, instruction and model hashes, temperature 0, seed 237, context 8192 and output budget 2048. Executors had no rubric contents or tools. The primary baseline is no skill; historical 0.3.3 is not an accepted production comparator. The initial 8B timeout is separately preserved as NOT_RUN, not behavioral failure.

`responses/` contains final answers only; original private record hashes and a uniform final-answer parser transformation are recorded. No hidden reasoning is published. Exact runner/evaluator scripts and pre-inference seed/parser amendments are preserved for audit.

Both attempted anonymous model evaluators are **invalid**: v1 echoed inputs, v2 produced inconsistent assertion/aggregate results. Their outputs remain under `evaluation-invalid-v1/` and `evaluation-schema-v2/`; neither counts as PASS or FAIL. Those two attempts provide no valid blind score; the later independent review is recorded below. The schema mechanism is documented at https://docs.ollama.com/capabilities/structured-outputs.

`manual-audit.json` and `AUDIT.md` report the parent Codex review with visible variant labels. This is separate from the Qwen executor but not a blind review or independent release approval. No skill passed 0/3; historical 0.3.3 and 0.3.4 each passed 1/3. The omissions are missing explicit NOT_RUN fields and live-source URL/check-time requirements.

## Source correction and retest

Draft 0.3.5 at source `15740806f57d7058c0d2d3ac02f51c586e15e635` makes existing output fields and live-source prerequisites explicit; maturity and description/routing remain unchanged. Skill and generated catalog validation pass.

`candidate-0.3.5/` contains the frozen plan, exact instructions/runner, three new final-answer records and assertion audit. The same model digest, parameters, inputs and unchanged rubrics apply. Six earlier no-skill/0.3.4 comparator records are explicitly reused, not counted as fresh executions.

Parent audit: **2/3 PASS** for 0.3.5 versus 1/3 for 0.3.4 and 0/3 baseline. Contradictory PASS and blocked-browser cases pass. The queued case still omits explicit NOT_RUN status and the unassigned-runner condition. It is a real observed FAIL. No criterion was waived and no candidate promotion is claimed. These are source-pinned local-model runs, not a new installed Lab or deployed Site. Single samples do not establish general model quality or variance.

## Withdrawn template experiment 0.3.6

All three source-pinned responses completed. The queued case now emits complete statuses and both conditions, but the browser case emits evaluation.status=BLOCKED instead of required NOT_RUN. This observed contract regression is preserved in candidate-0.3.6; the 0.3.6 template is withdrawn from the proposed source, which returns to 0.3.5. No results are deleted. The separately frozen 8B evaluator timed out after 600 seconds without an assessment; it remains NOT_RUN_EVALUATION.

## Independent blind review under Luna orchestration

`blind-review/` preserves the anonymous frozen packet, initial assessment, separate corrected review, label mapping and deterministic aggregate validation. The evaluator received only final answers and unchanged assertions, without version labels or mapping. Luna orchestrated the review; the parent unblinded it only after scoring. The initial review incorrectly claimed the browser answer lacked check time. The same evaluator corrected it in a separate immutable review; both reports remain available.

Independent aggregate: no-skill **0/3**, current 0.3.4 **1/3**, proposed 0.3.5 **2/3**. The queued 0.3.5 answer still lacks required NOT_RUN status fields and additional runner condition. Some other queued assertion interpretations differ from the parent audit; these do not alter the case failure. **Final evaluation disposition: ITERATE**, with no release, promotion, installed-runtime compatibility or general model-quality claim.

This completes the bounded matched-comparison/evaluation work requested in #237: executor rubrics were isolated, runtime/model/input/budget matched, missing execution was not converted to a pass, and the independent review gives an evidence-backed ITERATE decision. Remaining candidate hardening is tracked in PR #410 and does not require concealing negative results or forcing every evaluation to PASS.

## Closeout retest — 2026-10-26

A further frozen 0.3.7 template experiment used the identical local Qwen3:4b digest, inputs, rubrics, seed and budgets. All three responses completed; the unchanged final-answer parser excluded hidden reasoning and retained raw-response hashes. Parent labeled self-review found 1/3 PASS: queued output still omitted required fields and the browser output failed the explicit unknown-status requirement while suggesting policy bypass. The experiment is withdrawn; proposed source remains 0.3.5, draft, with its previously documented 2/3 result and unresolved queued omission. No criterion was relaxed and no historical outcome changed.

This PR delivers the completed bounded evaluation record and the incremental 0.3.5 contract clarification. Merging it does not certify this draft across models or promote it. A future candidate requires a fresh frozen comparison; the Meta review P1 remediation plan remains the next scope.
