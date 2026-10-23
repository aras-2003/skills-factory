# Skill-evaluation controlled comparison — 2026-10-23

Issue #237. Disposition: **ITERATE**, not candidate-ready or released.

Nine tool-free local Qwen3:4b executor responses completed for the three frozen evidence-state cases and no-skill / historical draft 0.3.3 / current 0.3.4 variants. All ended normally, without token-limit truncation. Plans bind input, rubric, instruction and model hashes, temperature 0, seed 237, context 8192 and output budget 2048. Executors had no rubric contents or tools. The primary baseline is no skill; historical 0.3.3 is not an accepted production comparator. The initial 8B timeout is separately preserved as NOT_RUN, not behavioral failure.

`responses/` contains final answers only; original private record hashes and a uniform final-answer parser transformation are recorded. No hidden reasoning is published. Exact runner/evaluator scripts and pre-inference seed/parser amendments are preserved for audit.

Both attempted anonymous model evaluators are **invalid**: v1 echoed inputs, v2 produced inconsistent assertion/aggregate results. Their outputs remain under `evaluation-invalid-v1/` and `evaluation-schema-v2/`; neither counts as PASS or FAIL. No blind score is claimed. The schema mechanism is documented at https://docs.ollama.com/capabilities/structured-outputs.

`manual-audit.json` and `AUDIT.md` report the parent Codex review with visible variant labels. This is separate from the Qwen executor but not a blind review or independent release approval. No skill passed 0/3; historical 0.3.3 and 0.3.4 each passed 1/3. The omissions are missing explicit NOT_RUN fields and live-source URL/check-time requirements.

## Source correction and retest

Draft 0.3.5 at source `15740806f57d7058c0d2d3ac02f51c586e15e635` makes existing output fields and live-source prerequisites explicit; maturity and description/routing remain unchanged. Skill and generated catalog validation pass.

`candidate-0.3.5/` contains the frozen plan, exact instructions/runner, three new final-answer records and assertion audit. The same model digest, parameters, inputs and unchanged rubrics apply. Six earlier no-skill/0.3.4 comparator records are explicitly reused, not counted as fresh executions.

Parent audit: **2/3 PASS** for 0.3.5 versus 1/3 for 0.3.4 and 0/3 baseline. Contradictory PASS and blocked-browser cases pass. The queued case still omits explicit NOT_RUN status and the unassigned-runner condition. It is a real observed FAIL. No criterion was waived and no candidate promotion is claimed. These are source-pinned local-model runs, not a new installed Lab or deployed Site. Single samples do not establish general model quality or variance.
