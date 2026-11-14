# Iteration 20 — ENG-22 Evaluation Report Contract v1

- **State: CLOSED / ACCEPTED (bounded slice only).** Scope lock merged in PR #698 at `071e96c080ca40a44ebda4ea0c5c3122134bc5e7`; implementation merged by PR #699 (main `92cd882a40996ae3c2345b1bfe671b0647798d06`), boundary tests by PR #700 (main `3418f3dca5e8452d489f1eef6c43accda9c49ab5`), and high-score blocking regression by PR #701 (main `c8e96d6274599bee2629c0d46befc136dd1679a0`). Previous iteration 19 (#688) is CLOSED / ACCEPTED.
- Tracking issue / bounded ENG-22 dependency slice: https://github.com/aras-2003/skills-factory/issues/697.
- Parent source requirement: ENG-22 #335. This bounded contract slice was tracked through #697; the wider observability scope remains partial and is not accepted or completed here.
- Downstream consumer: #619, updated to reuse the merged contract unchanged in a later separately scoped increment.
- Owner / reviewer: repository owner / owner-delegated Codex review; not independent human review.
- Implementation baseline main SHA: `071e96c080ca40a44ebda4ea0c5c3122134bc5e7`.
- Native Project iteration: NOT_ASSIGNED unless independently read back.

## Problem and source evidence

#619 explicitly requires the Evaluation Report Contract v1 owned by #335, but current main has no canonical machine-readable EvaluationReport schema or deterministic 0–10 report calculator. Existing scripts/eval/receipt.py and scripts/eval/schemas/evidence-record.schema.json are the canonical per-case receipt boundary and must remain compatible. The old docs/testing/evidence/skill-evaluation-2026-10-23/evaluation-schema-v2/ experiment is historical invalid evidence, not a normative contract.

## Frozen scope

Deliver one reusable, versioned report contract slice:

- strict JSON Schema v1 and a minimal valid example;
- pure deterministic calculator and validator implementing the #335 weighted assertion, coverage, NOT_SCORABLE, and decision-gate rules;
- synthetic valid/invalid fixtures and deterministic tests;
- no mutation or reinterpretation of existing receipts.

**Excluded:** entire #335 observability architecture; Promptfoo/Phoenix/OpenTelemetry expansion; migration of historical evaluations; automatic adapters/writes into existing receipts; Site/Cloud UI; model execution; #619 implementation; release or maturity changes. This slice resolves the shared data/calculation contract only. #335 remains open/partial and #619 remains separate.

## Architecture and reuse

- Planned impact: A2, extending the existing eval evidence/report boundary; reconsider only if inspection shows a new runtime ownership boundary.
- Source of truth remains frozen evals/ cases and existing per-case receipts. The Evaluation Report composes their identities and evidence-linked findings; it does not replace them.
- Reuse JSON Schema 2020-12, the installed jsonschema dependency, and existing receipt validation conventions.
- No new dependency, service, database, evaluator, or receipt store.
- No hidden chain-of-thought; reasoning is a concise decision rationale only.

## Locked acceptance and test map

Use the companion acceptance matrix, cases 20-01 through 20-06.

1. Schema and example represent report identity/provenance, comparator or explicit N/A reason, evidence-linked strengths/weaknesses, rationale, score/profile/dimensions, coverage, decision/gates/actions, and per-case execution/evaluation/compatibility state.
2. Schema validator rejects missing/malformed identity, invalid evidence references/enums, invalid score/status combinations, unexpected properties and malformed report structure.
3. Calculator deterministically handles assertion result anchors 0/0.5/1, criticality weights, dimension/profile weights, unrounded and one-decimal scores, and thresholds.
4. Missing required assertions, NOT_RUN/BLOCKED or missing required evidence produce null score / NOT_SCORABLE and cannot produce PASS. Missing or incomparable baseline produces a null comparison delta with an explicit reason; it does not fabricate a baseline.
5. A critical forbidden action blocks PASS regardless of numeric score. Score and decision remain separate.
6. Existing receipt schema, sample receipts and historical evidence remain unchanged/readable; no runtime adapters are introduced.
7. Full repository validator, eval tests, domain integrity and exact PR/main CI pass.

## Execution and verification

- Scope lock PR #698 merged at main `071e96c080ca40a44ebda4ea0c5c3122134bc5e7` before implementation.
- Implementation PR #699 merged at `92cd882a40996ae3c2345b1bfe671b0647798d06`; test PR #700 merged at `3418f3dca5e8452d489f1eef6c43accda9c49ab5`; high-score blocking regression PR #701 merged at `c8e96d6274599bee2629c0d46befc136dd1679a0`.
- Exact-head PR CI and merged-main CI passed for PRs #699, #700 and #701; see the closeout evidence file.
- Local contract tests pass (9/9); full eval suite in GitHub CI passes. Local full-suite run was limited by the shallow checkout (6 full-history errors, 2 skipped); no code assertion failed.
- Full repository validator completed with existing MEDIUM/LOW findings; domain integrity passed. Existing receipt schema and historical evidence files were not modified.
- No runtime/Site verification applies to this static contract/calculator slice. This does not satisfy #335's broader runtime/UI acceptance or claim runtime quality.

## Closure

All locked rows are recorded in the companion matrix with exact source and CI evidence. #697 is closed as the bounded dependency slice; #619 references the shared contract and remains separate. The wider #335 scope is not completed by this slice.
