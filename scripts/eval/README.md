# Runtime eval protocol

This directory defines the evidence boundary for runtime evaluations.

## Isolation rule

The executor receives only files ending in `.input.md` plus the runtime catalog needed for the case. It must never receive files ending in `.rubric.yaml`, expected routing, expected answer, PASS/FAIL criteria, or evaluator notes.

There is no single universal runtime registry. R18 composes Commerce cases from `evals/runtime-fixtures.yaml`, natural-routing cases from `evals/routing/registry.yaml`, split executive-role cases and supplemental routing regressions. Its active definition is `evals/campaigns/runtime-validation-2026-10-r18/campaign.yaml`; all active cases are pinned to Lab. Production-only fallback regressions are explicitly excluded because a Lab run cannot establish Production catalog behavior. R17 retains the historical 36 PASS / 9 FAIL transcript verdicts. R16 remains the historical inline-visual campaign.

`skill-release-review-2026-10` is an isolated meta-skill runtime campaign. It exercises five release-gate decisions against the candidate Lab package and records the exact source revision, Lab package identity, skill digest, executor-input hashes and evaluator-rubric hashes. The executor pack contains only prompts and the Lab artifact; rubrics remain in the repository. The R16 campaign definition and pin remain unchanged. Its behavior pin excludes only `skills/meta/skill-release-review/SKILL.md` when the dedicated campaign validates the matching candidate version.

Validate and prepare it with:

- `python scripts/eval/skill_release_campaign.py validate`
- `python scripts/eval/skill_release_campaign.py prepare --lab .tmp/lab --output .tmp/runtime-campaign-skill-release-review`

The Lab packager copies only executor inputs.

## Test-suite validation vs execution

`scripts/validate/validate_tests.py` statically validates the definitions under both `skills/**/tests/cases.yaml` and `workflows/**/tests/cases.yaml`: YAML, schema, IDs and required assertion fields.

That validator does **not** execute the behavioral assertions against a model/runtime. In particular, the `oaf-health-check` confidence cases are planned behavioral regressions until an actual evaluator/runtime run executes them. A structurally valid case is not runtime PASS.

## Evidence receipts

Use `receipt.py` to create or validate a record. `NOT_RUN` is a first-class status and is required when runtime/model access is unavailable. Historical narrative summaries are not receipts for a later component version.

A receipt binds evidence to input/rubric digests and a source revision. It also records runtime/model identity, reasoning setting, available catalog/tools, prompt, actual output and trace digests, reviewer, assisted/unassisted state, and separate source-component vs packaged runtime-artifact identity where available. Historical receipts can be validated against their recorded source revision.

New receipts record `outcome` (`passed`, `failed`, or `null`) separately from `execution_state` (`executed`, `blocked`, `awaiting_runner`, `no_steps`, or `not_executed`). `evaluation.status` remains as a compatibility field for existing tooling. A `NOT_RUN` receipt must have a null outcome, a non-executed state, and a reason; `PASS`, `FAIL`, and `REVIEW_REQUIRED` require `execution_state=executed`. The fields are optional when validating historical 1.0 receipts, but when either new field is present both are required and checked against the compatibility status.

For example, record infrastructure deferrals with `--status NOT_RUN --execution-state awaiting_runner --execution-state-reason "No runner assigned"`. Do not encode a status mismatch or an inability to reach a page as `CLOSED`: use `FAIL` only when the executed test's stated requirement failed, and use `NOT_RUN` with the appropriate execution state when no verdict can be reached.

An assisted run cannot be recorded as PASS.

## Commands

- `python scripts/eval/validate_isolation.py`
- `python scripts/eval/validate_isolation.py --artifact <built-lab-dir>`
- `python -m unittest discover -s scripts/eval/tests -p 'test_*.py'`
- `python scripts/eval/campaign.py validate`
- `python scripts/eval/campaign.py prepare --output .tmp/runtime-campaign-r16`
- `python scripts/eval/campaign.py queue --include-supplemental`
- `python scripts/eval/campaign.py validate-evidence`
- `python scripts/eval/receipt.py validate evals/results/<record>.json`

Provider/runtime execution remains external to the offline harness. Exact-version smoke requires independently observed package release/source/payload/component identity; values copied from the lock are not evidence. A routing mismatch may be archived as `FAIL` or `REVIEW_REQUIRED`, but it blocks `PASS`. Offline synthetic regressions are not runtime evidence.

## One-command local preflight (ENG-08)

Run `python scripts/eval/local_preflight.py --output .tmp/offline-eval-preflight.json`
from a checked-out repository. It calls the existing isolation, natural-routing
fixture and test-case-schema validators, and writes a deterministic JSON result.
The command is repeatable and invokes **no model, browser or external action**.
`overall_status: PASS` means only that those static gates passed. Every result
explicitly retains `runtime_case_execution: NOT_RUN` and
`runtime_compatibility: NOT_VERIFIED`. It is **not** a replacement for a
model-executed campaign receipt or the external Desktop/browser runner.
