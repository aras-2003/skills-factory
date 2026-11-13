# Iteration 18 — capability overlap matcher and external skill adaptation (ES-03)

This scope lock defines the bounded implementation of #618. Follow [iteration delivery](../ITERATION-DELIVERY.md); changes to frozen criteria require a separately reviewed clarification.

- State: CLOSED / ACCEPTED; implementation PRs merged and all 15 acceptance-matrix rows PASS, including host-selected routing 18-11, based on owner self-review; no independent reviewer claim.
- Owner / reviewer: Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review; not independent).
- Tracking Issue / native Project iteration: #618 / not assigned; native Project iteration remains a scheduling mirror.
- Previous terminal iteration / closure link: Iteration 17 / #620 CLOSED / ACCEPTED; [closeout PR #670](https://github.com/aras-2003/skills-factory/pull/670), merged to main as `ae0e26dc210496c5b488f11535bdaf50158e227f`.
- Baseline main SHA: `ae0e26dc210496c5b488f11535bdaf50158e227f`.
- Lock commit SHA: `f55776b3953edbf8459c0aaf78a1264ddaafd901` (scope-lock PR #671).
- Started at / closed at (UTC): `2026-11-13T17:07:53Z` / 2026-11-13 (closure documented after host-selection evidence; exact clock timestamp NOT_RECORDED).
- Scope lock reviewed by / at: owner self-review / 2026-11-13; not independent.

## Frozen commitment

| Issue | Outcome / acceptance criterion IDs | Included | Excluded | Dependencies / accepted evidence | Size |
| --- | --- | --- | --- | --- | --- |
| #618 | 618-A1–A4 | Add a deterministic, evidence-producing matcher over candidate and current capabilities by trigger, outputs, tools, dependencies, domain semantics and conflicts; return only the issue's decisions REUSE_EXISTING / IMPORT / EXTEND / COMPOSE / REJECT, with conflict escalation represented separately and fail-closed. Integrate a review-gated adapter into the existing skill-development workflow that consumes the exact pinned/quarantined intake receipt from #617 and creates a portable, repository-valid package proposal with source/license/local-change lineage. Emit a scoped proposal artifact; require human review for derivatives and conflicts; preserve explicit trigger/nontrigger, failure and runtime dependency behavior. Add fixtures proving duplicate rejection/reuse, complementary extension, conflict escalation, portability and routing discrimination. | Arbitrary network retrieval, execution of candidate instructions/scripts, direct mutation of main/production, automatic PR merge/publish/maturity/license/security approval, new provenance taxonomy, Site UI/MCP features, upstream update/rollback (#619), domain pilot work (#621/#622), and the broad Presentation OS #283 acceptance. | #616 provenance schema and #617 secure intake are accepted and closed; reuse #617's immutable receipt/quarantine boundary, canonical provenance registry, skill-specification, skill-authoring and existing skill-development workflow. Baseline: main SHA above. | M |

## Design and data boundary

The matcher is a deterministic decision aid, not a semantic approval engine. It compares explicit candidate/current capability facts and reports evidence by facet; it must not silently treat missing facts as a match or non-conflict. Keep the issue's five decision values stable. A conflict has an explicit escalation field/state and cannot automatically authorize EXTEND, COMPOSE or IMPORT. Same-function duplicates are not imported again; reuse points to the existing canonical identity.

Adaptation consumes only a completed secure-intake receipt and its quarantined files. It must not fetch arbitrary URLs, execute or import candidate code, access secrets, or write into canonical skill directories. It produces an isolated package proposal plus a scoped diff/manifest that can be reviewed and later submitted through ordinary Git review. Preserve exact upstream repository/commit/file digests and original license claims/decision; separately identify local modifications, components and unresolved review states. No unknown license or provenance state is upgraded by inference.

Keep repo package contract and portability explicit: required SKILL.md frontmatter, trigger and non-trigger boundary, required/optional inputs, output, stop/escalation conditions, progressive disclosure resources, and runtime dependencies. Unsupported or unavailable dependencies are surfaced as blockers instead of simulated. Existing skill-development remains the orchestration workflow; do not duplicate it with a parallel lifecycle.

## Frozen acceptance criteria

- **618-A1 Match and decide:** compare trigger, output, tools, dependencies, domain semantics and conflict evidence; emit only REUSE_EXISTING, IMPORT, EXTEND, COMPOSE or REJECT with per-facet evidence and explicit missing/unknown values. Same-function duplicate is not re-imported; complementary capabilities may be adapted; unresolved conflict fails closed and escalates to human review.
- **618-A2 Adapt and package:** consume only a verified #617 source pin/receipt and quarantined content; create an isolated, portable package proposal that passes current repository skill package and progressive-disclosure validation. Do not modify canonical skills during proposal generation.
- **618-A3 Preserve lineage and human gate:** retain upstream source/ref/commit/content hashes, license claim/decision, verification state, components and local change lineage. Require human review before derivatives or conflicts can proceed to scoped PR proposal. Proposal binds the exact source receipt, decision evidence and output digest; no automatic merge, publish, trust, maturity or license approval.
- **618-A4 Route and integrate safely:** integrate with existing skill-development orchestration; explicit positive/negative trigger cases distinguish the new adaptation capability from duplicate reuse, ordinary skill authoring, secure intake and unrelated requests. Missing/stale evidence and unavailable dependencies stop or escalate without side effects.

## Test plan

Authoritative ledger: [Iteration 18 acceptance matrix](../../../evals/campaigns/iteration-18-es03-capability-overlap-adaptation-2026-11/acceptance-matrix.md). All rows start NOT_RUN. Required validation includes deterministic matcher boundaries, duplicate/complement/conflict fixtures, secure-intake receipt tampering and staleness, source/license/change lineage, package portability/frontmatter/resources, explicit review authorization, no-execution/no-network/no-write adversarial cases, workflow integration, four routing cases (direct positive, indirect positive, near-miss negative, competing-capability conflict), applicable full offline CI and exact-main checks, candidate package integrity and exact-version runtime smoke for any changed packaged behavior. Site MCP is N/A only if the final diff changes no Site/MCP/runtime adapter; re-evaluate this against the actual diff at close. Any actual runtime test must use the exact Lab artifact/candidate and preserve input/rubric isolation and receipts.

Required direct consumers/dependencies to inspect before implementation: #617 intake manifest/receipt contract, canonical provenance registry/schema and validator, current skill-validation/package code, skill-development workflow, skill-specification, skill-authoring and generated Lab catalog. Use the repository's locked test environment. No external repository fetch is planned; local pinned synthetic intake fixtures are sufficient and repeatable.

## Candidate history (append; never overwrite)

| Candidate | Main SHA | Lab release ID / payload digest | Build + offline CI | Observed runtime identity / smoke | Supersedes / invalidated rows |
| --- | --- | --- | --- | --- | --- |
| Scope baseline | `ae0e26dc210496c5b488f11535bdaf50158e227f` | N/A for scope lock | Prior Iteration 17 closure CI passed | Iteration 17 runtime acceptance was bound to canonical source `197f12e96a2282eb13cf787246e76e3621c960eb`, Site mirror `b0216d283dad3fd297b6e3a64293a4434b8245f6`, Site v133 | None |
| ES-03 implementation candidate | `1d55767564bd092935c4d8a21fa0debc7a382db2` | Lab `1.38.531+1d55767564bd`; payload `350723b32224f4efab35ac95eb0b208a7f718a782be1fad941cd2d5706d228d5` | Validate Skills, Domain Integrity, Site CI, Lab packaging and Pages all succeeded; local engineering/security/package tests 27/64/102 passed | Site v134, mirror `6e608c569ecc6048c3ac3de1e4eedd90d64a07cb`; private deployment succeeded; attestation verified and exact `skill-development` package loaded | Supersedes scope baseline; row 18-11 PASS per transcript-linked evidence |

## Regression selection and counts

- Changed contracts / direct and transitive consumers: new comparison/adaptation contract, secure intake receipt, provenance lineage, skill package validation, skill-development workflow routing, generated Lab package and associated fixtures. Verify and record the actual dependency graph before implementation.
- Included cases / exclusions: rows 18-01–18-15; secure receipt mutation/staleness; missing metadata; exact and complementary overlap; conflict; package portability; positive/negative routing; no-execution/security; existing provenance, packaging, validation and domain integrity CI. No arbitrary external source retrieval.
- Fixed sentinels / rotating unchanged-domain probes: unknown evidence never authorizes adaptation; no execution/no canonical write; exact source digest and lineage survive; package validation remains fail-closed. Preselected and executed Investment OS and Presentation OS probes are recorded in the acceptance matrix and [closeout evidence](../../../evals/campaigns/iteration-18-es03-capability-overlap-adaptation-2026-11/closeout-evidence.md).
- Last full runtime baseline candidate / behavior iterations since baseline: Iteration 17 source `197f12e96a2282eb13cf787246e76e3621c960eb` (Site v133); one closed behavior-bearing iteration since. This iteration requires a full supported runtime baseline only if change impact cannot be bounded to the new workflow/tool boundary.
- Planned distinct scenarios / executions by layer: at least 10 deterministic matcher/adapter assertions; 4 routing cases; all applicable repo CI on each PR and exact main; one exact package identity/runtime smoke if packaged behavior changes; two unchanged-domain probes; adversarial missing/stale receipt and conflicting capability checks. Offline, package, CI, provenance and unchanged-domain evidence is recorded. The four model-selected routing prompts and three conflict repetitions are recorded as executed PASS in the acceptance matrix and closeout evidence, with individual Chat transcripts; the manual `load_skill` smoke alone was not used for this verdict.
- Critical stochastic scenarios repeated at least 3 times / instability history: comparison helper is deterministic; runtime routing conflict/escalation is critical and will run 3 independent times per applicable surface if model-mediated behavior is introduced. Otherwise no stochastic claims.
- PR CI / final-main checks and build / external runtime runs: Exact-main Validate Skills, Domain Integrity, Site CI, Lab packaging and Pages all passed. The exact Lab package was built and validated, then privately deployed to Site v134; runtime attestation and `list_skills`/`load_skill` receipts are recorded in [closeout evidence](../../../evals/campaigns/iteration-18-es03-capability-overlap-adaptation-2026-11/closeout-evidence.md). This is a private test, not a production plugin promotion.

## Defect intake and clarifications (append; intake always open)

| Bug Issue / discovery iteration | Existing contract / frozen criterion or unrelated | Severity / closure blocking | Fix PR or accepted deferral owner + future delivery iteration | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |
| None at scope lock | Baseline reviewed; no implementation defects inferred yet | N/A | N/A | N/A | Owner |

## Closure / abort decision

- Outcome: ACCEPTED / CLOSED by owner self-review on 2026-11-13; exact close clock timestamp NOT_RECORDED. Acceptance matrix 18-01..18-15 PASS. Not independent review or production-plugin promotion.
- Final candidate / matrix and immutable evidence links: `1d55767564bd092935c4d8a21fa0debc7a382db2`; [acceptance matrix](../../../evals/campaigns/iteration-18-es03-capability-overlap-adaptation-2026-11/acceptance-matrix.md) and [execution evidence](../../../evals/campaigns/iteration-18-es03-capability-overlap-adaptation-2026-11/closeout-evidence.md).
- Committed Issues accepted / unresolved: implementation for #618 is merged; #618 closure authorized by this reviewed evidence; issue closure occurs separately and is not evidence of a runtime test. #283 is excluded and remains tracked separately.
- Required rows PASS / FAIL / NOT_RUN / BLOCKED / REVIEW_REQUIRED / reviewed N/A: 15 PASS; 0 FAIL; 0 REVIEW_REQUIRED; 0 NOT_RUN / BLOCKED; no rows are claimed N/A.
- Shared regression verdict: validators, 193 targeted unit tests, two preselected unchanged-domain probes, exact-main CI, package validation and private Site runtime identity/smoke passed; host-selected routing cases are linked and PASS (4 core routes + 3 conflict repetitions).
- Non-blocking findings and accepted impact: repository validator reports existing MEDIUM/LOW advisories; no blocking validator failure. Site runtime is verified for the exact candidate and remains owner-only.
- Scope compared with lock commit: implementation remains within #618's frozen matcher, adapter, lineage and runtime dependency boundary; no Site UI/MCP feature, upstream update, domain pilot or #283 acceptance was added.
- Issue / Project / PR reconciliation: scope lock PR #671 merged; #618 is accepted for closure, and #615 remains the tracking umbrella. Follow-on work becomes eligible after the exact-main closure merge and issue state reconciliation.
- Owner proposal / reviewer acceptance / decision: ACCEPTED / CLOSED on 2026-11-13 by owner self-review; independent review not claimed. Row 18-11 supported by frozen Chat transcripts.
- If ABORTED: not applicable — ACCEPTED.
- Next iteration eligibility: after this closure document is merged to main and #618 is closed, planned Iteration 19 may be activated under its own scope lock; no automatic production plugin promotion.
