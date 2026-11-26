# Architect review: SDLC Deep

Source: exact `origin/main` revision `538d800534cf7f7eca32640592a90d252f6dbada`. Role requested as `sf-architect` / `gpt-6.2-sol` / high. Host exposed effective model `gpt-6.2-sol`; effective effort and named-profile loading were not exposed and remain UNKNOWN.

## Finding: validator routing/timing disagreement

The current role-decision validator has two false rejections against the published routing policy:

1. A natural A1 Architect INVOKE triggered by a shared public contract or trust boundary can be `ON_TIME`, but the validator applies the A0/A1 “UNKNOWN or UNNECESSARY” timing restriction to every A1 invocation.
2. A2 can be a valid Architect SKIP when no material boundary, shared contract, or dependency decision is implicated, but the validator treats every A2–A4 `CORRECT_SKIP` as inconsistent and requires `MISSED` or `UNKNOWN`.

Relevant code: `scripts/eval/role_decision_record.py`; policy: `docs/architecture/SOFTWARE-ARCHITECTURE-DECISIONS.md` and `docs/governance/CODEX-ROLE-OBSERVABILITY.md`.

## Recommended bounded change

Add an explicit structured routing trigger to the existing sidecar contract (proposed v1.2): `NONE`, `UNKNOWN`, and policy-defined A1/A2 trigger classes. Keep routing-decision correctness separate from chronology; `ON_TIME` means dispatch preceded the dependent action, not that the trigger justified dispatch. Missing/contradictory trigger evidence must fail closed for correctness. Preserve all v1.0/v1.1 behavior and add v1.2 chronology handling explicitly; do not let the current exact `schema_version == "1.1"` branch route v1.2 into v1.0 behavior.

Rollout: reader and schema compatibility first, then v1.2 writer; validate historical sidecars and CI consumers. Rollback stops new v1.2 writes but keeps a compatible reader for already-created records. Consumers include the validator CLI, CI, governance docs/runbook, tests and sidecars. No source change is made in this audit because the native development WIP limit is full (2/2).

## Backlog evidence boundaries

- #748/#767 still need a real coordinator validation of a child's result against an independently retained source SHA, assigned scope and fixture map; helper coverage alone is not runtime proof.
- #765 can gain coarse capability reduction through Codex custom-agent feature flags, but inherited sandbox/MCP policy and actual profile loading remain host-dependent. Instruction-only restrictions are not ACLs.
- #766's owner-accepted `load_skill` architecture remains the accepted contract; this audit's validator defect is a separate observability gap.
- #768's `E2E-01..05` and gates `G0..G10` remain `NOT_RUN`. Security denials require actual host denial receipts; unavailable controls are `BLOCKED`, never a synthetic PASS.
- #769's prior unresolved-edge note is stale after `242fe476`; refresh `--affected` against current main. Workflow frequency remains `UNRANKED_FREQUENCY_UNKNOWN` until an observation window and denominator exist.

## Evidence status

This is an architecture advisory, not implementation, independent review, runtime acceptance, profile-load proof, or production authorization. The exact-main unit baseline and synthetic RED reproduction are recorded in `test-design-and-baseline.md`.
