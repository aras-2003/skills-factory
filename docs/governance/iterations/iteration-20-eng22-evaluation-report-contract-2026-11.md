# Iteration 20 — ENG-22 Evaluation Report Contract v1

- **State: PLANNED / scope-lock candidate only.** Do not begin implementation until this record and its matrix are merged to main. Previous iteration 19 (#688) is CLOSED / ACCEPTED on main de94a27a289a918bf748628d93452097ec57af46.
- Tracking issue / bounded ENG-22 dependency slice: https://github.com/aras-2003/skills-factory/issues/697.
- Parent dependency: #335 was reopened only to track this bounded contract slice; its wider L-sized observability scope remains partial and is not activated by this record.
- Downstream consumer: #619, which must reuse the contract unchanged in a later separately scoped increment.
- Owner / reviewer: repository owner / owner-delegated Codex review; not independent human review.
- Baseline main SHA: de94a27a289a918bf748628d93452097ec57af46.
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
4. Missing required assertions, NOT_RUN/BLOCKED, missing comparator or incomplete required coverage produce null score / NOT_SCORABLE or null delta as appropriate; they cannot produce PASS.
5. A critical forbidden action blocks PASS regardless of numeric score. Score and decision remain separate.
6. Existing receipt schema, sample receipts and historical evidence remain unchanged/readable; no runtime adapters are introduced.
7. Full repository validator, eval tests, domain integrity and exact PR/main CI pass.

## Execution gates

Scope-lock PR first. Implementation begins only after its merge and exact main identity are recorded. Validate offline with synthetic fixtures; preserve all tests and failure results. Merge implementation only after exact-head CI. No runtime/Site verification is applicable to this static contract/calculator slice; this does not satisfy #335's broader runtime/UI acceptance or close #335.

## Closure

Close #697 and mark Iteration 20 CLOSED only after every matrix row passes with exact source/CI identities. Then update #619 to reference this shared contract as a dependency; do not implement #619 in parallel with Iteration 20.
