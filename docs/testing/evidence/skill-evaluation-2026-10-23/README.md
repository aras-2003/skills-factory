# Skill-evaluation controlled comparison — 2026-10-23

Issue: #237. Status: execution in progress; no overall PASS, promotion or release claim.

The candidate instructions are skill-evaluation 0.3.4 from installed Lab 1.38.320+111b10aa89d5, whose package integrity was verified. The primary comparator is no skill; historical draft 0.3.3 is an additional comparator, not an accepted production release.

The frozen plans bind the three existing synthetic evidence-state cases, instructions, inputs, rubrics and identical per-variant model parameters. Executors are fresh local Ollama chat requests with no tools and no rubrics. A separate fresh evaluator receives anonymized outputs and frozen rubrics after execution. This tests the recorded local model, not the ChatGPT host or Site reasoning.

The initial 8B attempt timed out after 600 seconds without any response. Its first case is blocked/NOT_RUN and the remaining eight requests were not attempted; no behavioral failure is inferred. The subsequent 4B plan is preserved separately. Output hashes, blind scoring, comparisons and final disposition must be added after execution finishes.

## Executor completion

All nine planned responses completed normally, with no token-limit truncation. `executor-dataset.json` binds each final-answer record to its private original-record hash. Only final answers are published: local model reasoning segments are excluded identically from every variant. The original and amended evaluator scripts record a final-answer parser correction and a seed type correction before evaluator inference. No success criterion changed. The supervisor first exited on the pre-inference seed error; corrected evaluation was launched separately. Independent scoring is still in progress.
