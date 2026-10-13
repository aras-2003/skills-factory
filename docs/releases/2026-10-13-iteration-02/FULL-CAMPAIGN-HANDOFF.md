# Iteration 2 — full-source behavior campaign handoff

**Scope:** all currently registered 64 skills and 19 workflows, using **existing real source fixtures**. This is separate from the 18 Issue / 34 attempt triage. Generated under PR #342 without merging or executing a model.

## Source implementation

- `scripts/eval/iteration02_full_behavior_campaign.py` builds the fixture inventory directly from the lifecycle auditors and canonical runtime workflow registry.
- Every present local `tests/cases.yaml` and central `evals/runtime-fixtures.yaml` is read for exact prompt and existing expected rubric. A missing or malformed fixture blocks the build. Generator never synthesizes a prompt, answer, successful write, model behavior, or evaluator result.
- Skill polarity: at least two real source positive and two negative/near-miss cases are required; workflow case coverage must have local or central fixtures. Audit counts must cover the exact source inventory.
- Case identity + source + prompt SHA + separate rubric SHA allow isolated evaluator lookup later. Reviewers should inspect data consistency and known class boundaries, not assume quality because metadata match.
- Only `source-audit.json` and `executor-inputs.json` are uploaded in the **executor** artifact. `evaluator-only/rubrics.json` stays separate in the local CI workspace and is not uploaded to the unassisted executor. The rubrics remain reproducible from versioned repository source for an independent evaluator.

## Exact-head evidence

- CI at candidate `8cfd6725a5b0f472c8e3dad449537d32584941c0`: [Validate skills PASS](https://github.com/aras-2003/skills-factory/actions/runs/38401936292), [Domain integrity PASS](https://github.com/aras-2003/skills-factory/actions/runs/38401936113), [Eval integrity PASS](https://github.com/aras-2003/skills-factory/actions/runs/38401936337). New fixture generator and its negative tests are included.
- Full-source executor artifact (not a model trace): **11815566989**, SHA256 `7dc16b254647b8c00d55a2f18b06190ea8d2ce36f77f045bc9fa58541cd91b74`. The exact artifact expires 2026-10-27.
- Separate 18-Issue campaign artifacts remain 11 Lab + 7 external test-only inputs; they are not a substitute for this all-component campaign.

## Execution gate after merge

1. Verify the final `main` merge SHA; re-run builder from **postmerge** main, not this earlier PR SHA. Rebuild all artifacts to exactly match installed Lab source/release/payload and captured capability/tool schema.
2. Preflight a disposable, isolated TEST environment. Native provider/model runner must be connected separately, with explicit operator permission and no inherited external-write credentials.
3. Dispatch each source fixture to the intended channel with its exact prompt, without sending evaluator rubrics to the executor. Retry only with recorded idempotency key; preserve raw model/tool/client observations, no manual score copying.
4. Independent evaluator loads rubric from exactly the matching source SHA, verifies tool and output traces and distinguishes failures, no steps, missing capability, and denied writes from execution PASS.
5. Run sampled repetitions and risk-prioritized near misses; do not average away authorization or security failures. Keep historical R17/R20 receipts immutable and appended comparisons source-bound.

## Outstanding development / release boundary

- No real Work/Desktop/Browser provider batch API is exposed here. This artifact is a **runnable-input manifest**, not an executable model session or a 64-skill behavioral certificate.
- Four workflow contracts have documented entry/permission gaps (#290): `oaf-strategy-execution-reset`, `investment-attention-review`, `investment-security-review`, `investment-theme-discovery`. Source edits were rehearsed and automatically rejected by the R20 exact-historical-source gate. **They were reverted instead of repinning R20 or disabling tests**. Prepare these as a distinct new behavior version with independently reviewed source delta and new campaign; do not claim #290 fully implemented.
- Investment theme/security unconditional persistence instructions remain a release risk until the new versioned update. Permission support in a connector does not grant permission to write during read-only advice.
- Full provider E2E, authentic client-visible evidence, independent evaluator verdicts and production Site/rollback permissions remain external test/release gates.

**No merge, Site publishing, external writes, or runtime PASS happened in preparing this handoff.**
