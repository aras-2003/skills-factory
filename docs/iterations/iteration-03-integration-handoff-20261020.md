# Iteration 3 — integrated pre-merge and post-merge handoff (2026-10-20)

## Scope and decision boundary
Integration candidate combines ENG-02 (#235, PR #362) and ENG-03 (#236, PR #363) on top of existing `main` implementations: ENG-04 (#237, PR #277), ENG-06 (#239, PR #281), ENG-10 (#241, PR #282/#313). ENG-05 (#238) is a release-review *acceptance* lane, not a claim of new implemented behavior. DOM-05 (#232) remains discovery; exclude it from this engineering release candidate until its scope is explicitly approved. Original PRs are retained for traceability; this branch is the proposed unified merge surface.

**No live/model runtime acceptance is implied by static CI, fixture registration, or merge.** No source-thread history may be rewritten to PASS.

## Before merge — mandatory exact-head checks
1. Confirm branch base and all intended changes against latest `main`, no missing commits, unrelated file changes or unresolved conflicts. Re-run checks on the final integration HEAD if modified.
2. `python -m unittest discover -s scripts/readiness/tests`
3. `python scripts/readiness/validate_readiness.py`
4. `python scripts/eval/campaign.py validate`
5. `python -m unittest scripts/eval/tests/test_runtime_campaign.py`
6. `python scripts/eval/validate_isolation.py`
7. `git diff --check main...HEAD`; GitHub Actions: Validate skills, Domain integrity, Skills Factory Evaluation CI must all succeed for the *integration HEAD*, not only for independent feature PR heads.
8. Independently review the remaining acceptance criteria in ENG-04 / ENG-05 / ENG-06 / ENG-10 and record whether each is code-complete, genuinely missing implementation, or runtime-only. Stop if a true development gap is found.
9. Report a signed-off source SHA and the complete list of checks. No automatic PR approval is inferred.

## After merge — model-runtime acceptance on exact source + deployed Lab/Site identity
1. Capture `main` merge SHA, package version, built artifact digest, deployed Site source revision and Lab runtime identity before model runs. Refuse identity mismatch.
2. Execute all seven `skill-test-design` cases registered in `evals/campaigns/skill-engineering-2026-10/engineering-campaign.yaml` in PL/EN, using separated executor inputs and rubrics. Keep no-skill/competing-intent cases; save actual output, tool calls and independent rubric dispositions.
3. ENG-04: evaluate comparable current candidate, previous-version and no-skill baseline under equivalent model, prompt, tools and budget; save per-case severity and a decision of ACCEPT / ITERATE / REJECT. Grader-only instructions must not be provided to executor.
4. ENG-05: run healthy candidate / missing evidence / known high-severity failure release-review probes. Confirm stale evidence never authorizes a changed version, APPROVE does not launch deployment, and a known serious failure blocks personal-beta.
5. ENG-06 / ENG-10: exercise DOCS-versus-behavior change classification, realistic routing near-misses and competing skill cases; retain negative decisions and confidence boundaries.
6. Store immutable append-only receipts with exact revision, execution date, trace and grader outcome. `NOT_RUN` / `BLOCKED` are not PASS; preserve historical campaign dispositions.
7. Update issue-specific evidence and close only when all respective acceptance criteria pass. A merged source PR does not by itself close the issue.

## Unresolved until observed
- Integrated CI and offline commands must run on this new composite branch.
- ENG-04/05/06/10 residual source review is required; no blanket assertion of full scope completion.
- Exact-version runtime evidence is intentionally NOT_RUN until after merge.
- DOM-05 discovery is explicitly outside this deployable scope.
