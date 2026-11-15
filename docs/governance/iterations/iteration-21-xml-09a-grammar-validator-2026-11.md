# Iteration 21 — canonical XML grammar and static skill-body validation

- State: CLOSEOUT PROPOSED — implementation merged at main `fde66293d7c1285724017fa15e84e3c18d2571af`; line-location hardening is in PR #707. PR CI run `43656361340` passed XML validation and 104 tests, but the required domain/readiness/release job is blocked by expired readiness records. Owner review and final-main validation remain pending.
- Owner / reviewer: repository owner / owner-delegated Codex review (not independent human review).
- Tracking Issue / native Project iteration: #704 / `21 | Core extraction (provisional)`; assigned and read back after the scope lock merged.
- Previous terminal iteration: Iteration 20 CLOSED / ACCEPTED at main `54ac64a3029923c788b828ce63acdc0b88f18872`.
- Baseline main SHA: `54ac64a3029923c788b828ce63acdc0b88f18872`.
- Lock commit SHA: `cb3e73d1e3d00aca733fec1e888f595511f118c9`; recorded in #704 before implementation.
- Started at / closed at (UTC): 2026-11-14 23:16 / pending owner review of closeout.
- Scope lock reviewed by / at: repository owner / owner-delegated Codex review; merged via PR #705 after explicit owner approval. Review was not independent.

## Frozen commitment

| Issue | Outcome / acceptance criterion IDs | Included | Excluded | Dependencies / accepted evidence | Size |
| --- | --- | --- | --- | --- | --- |
| #704 (child of #682) | AC-01, AC-02, AC-03, AC-04, AC-05 | Canonical, human-readable XML grammar and section matrix; deterministic static validator; authoring template; positive and negative fixtures; actionable errors; unchanged-contract regression validation. | Migration of the five meta skills or any other skills; loader, routing, permission, evaluation-rubric, package or release behavior changes; claims of model behavior or cross-channel compatibility. | Baseline main SHA above; `docs/governance/TASK-DEFINITION-STANDARD.md`; `templates/skill-template/SKILL.md`; current repository validators and test conventions. | M |

The parent #682 remains an XL umbrella and is not an additional implementation commitment in this iteration. Its five skill migrations and runtime compatibility requirements remain open for later separately scoped work.

## Test plan

The acceptance matrix is `iteration-21-acceptance-matrix.md`. Required checks are deterministic offline tests and all applicable repository CI. The changed deliverable is authoring/validation tooling and documentation; it does not alter any shipped skill instructions, loader, runtime tool, package or permission. Runtime interpretation and channel compatibility are therefore explicitly outside this iteration and remain NOT_RUN under #682. A later skill-migration increment must book exact surfaces and test observed candidate artifacts before implementation.

## Candidate history (append; never overwrite)

| Candidate | Main SHA | Lab release ID / payload digest | Build + offline CI | Observed runtime identity / smoke | Supersedes / invalidated rows |
| --- | --- | --- | --- | --- | --- |
| XML grammar and static validator, PR #706 | Main `fde66293d7c1285724017fa15e84e3c18d2571af` (PR head `9048301bfb7d1917affe9b4c3170c760fdd86657`) | Lab payload SHA-256 `923cbb284617ca188d6c187e4b28bef0d883948d63b4bcbeaf8975db9c728c86`; no Lab release was made. | PASS: all PR checks on the exact rebased head and all post-merge checks on final main. [PR validation](https://github.com/aras-2003/skills-factory/actions/runs/43654775145); [main validation](https://github.com/aras-2003/skills-factory/actions/runs/43655090657). | N/A for this static-only slice; no runtime artifacts or skill behavior are changed. | — |
| Exact semantic error locations, closeout PR #707 | PR head `3e52552cd8ac53b142758e163aa4c524a53e662d`; final-main CI pending. | Same Lab payload as prior candidate; no packaged skill changes. | PASS: XML validator tests and full repository validator in [PR run 43656361340](https://github.com/aras-2003/skills-factory/actions/runs/43656361340). Repository-wide check remains blocked by expired readiness records in the separate domain/readiness/release job; no readiness dates or approvals changed. | N/A; no runtime artifacts or skill behavior change. | Adds 21-AC02-T02j; prior rows unchanged. |

## Regression selection and counts

- Changed contracts / direct and transitive consumers (evidence links): TDC XML grammar, static validator, authoring template and validation documentation. No runtime or packaged contract consumer is changed.
- Included cases / exclusions with bounded-impact rationale: eleven parser/authoring fixture scenarios, five shared offline sentinels, two unchanged-skill probes and repository validation are listed in the matrix. Runtime/model cases and cross-channel compatibility are excluded because no skill body, loader or package output changes; these remain explicit requirements of #682.
- Fixed sentinels / rotating unchanged-domain probes (minimum 2): offline regression checks for YAML frontmatter parsing, skill routing/catalog registrations, tool permission declarations, evaluator-only fixture isolation, and package/catalog manifests; two unchanged skill fixtures are selected in the matrix.
- Last full runtime baseline candidate / behavior iterations since baseline (maximum 4): current Site Lab attestation is source `1d55767564bd092935c4d8a21fa0debc7a382db2`, older than this scope baseline. No runtime baseline claim is made; this tooling-only slice does not change runtime behavior.
- Planned distinct scenarios / executions by layer and required surface: eleven parser/authoring fixture scenarios, five shared offline sentinels, two unchanged-skill probes, and full applicable offline CI; runtime surface N/A with the scope rationale above.
- Critical stochastic scenarios repeated at least 3 times / instability history: N/A; this scope introduces no model behavior or stochastic runtime path.
- PR CI / final-main checks and build / external runtime runs: PR #706 validation passed on rebased head `9048301bfb7d1917affe9b4c3170c760fdd86657`; post-merge validation passed on main `fde66293d7c1285724017fa15e84e3c18d2571af`. Closeout PR #707 run `43656361340` passed XML validation, the repository validator and XML unit tests, and artifact checks. Its domain/readiness/release job failed because the review date and 28 pending exceptions in `release/production-readiness.yaml` expired on 2026-11-14. These records were not altered. No final-main validation or external runtime run has occurred for PR #707.

## Defect intake and clarifications (append; intake always open)

| Bug Issue / discovery iteration | Existing contract / frozen criterion or unrelated | Severity / closure blocking | Fix PR or accepted deferral owner + future delivery iteration | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |
| First CI run found validator/template top-level ordering disagreement. | AC-01 / AC-03; closure-blocking. | Corrected canonical order; retested on final PR head and main. | Fixed in PR #706. | AC-01, AC-03, AC-04. | Owner approved PR #706; Codex review, not independent. |
| Scope-lock probe R02 named a directory without a `SKILL.md`. | AC-04 probe selection; closure-blocking. | Replaced with existing `skills/investing/investment-record-store/SKILL.md`; source and generated Lab instruction bodies hash-match. | Corrected in closeout matrix; no runtime/product code change. | 21-AC04-R02. | Owner review of closeout record. |
| Semantic validator errors used line 1 for nested elements instead of the element line. | AC-02 actionable location; closure-blocking. | Added source-order line mapping and a second-step placeholder regression test. | Fixed in closeout code change. | 21-AC02-T02j and full validator suite. | Owner review of closeout record. |

## Closure / abort decision

- Outcome: PROPOSED CLOSED — ACCEPTED, pending owner review and merge of this closeout PR.
- Final candidate / matrix and immutable evidence links: main `fde66293d7c1285724017fa15e84e3c18d2571af`; acceptance matrix in this directory; PR #706 merged as `fde66293d7c1285724017fa15e84e3c18d2571af`; PR and post-merge CI links above; line-location fix is in the closeout PR.
- Committed Issues accepted / unresolved: #704 accepted; #682 remains open and partial for the five meta-skill migrations and runtime/channel compatibility.
- Required rows PASS / FAIL / NOT_RUN / BLOCKED / REVIEW_REQUIRED / reviewed N/A: 21 PASS, 0 NOT_RUN, 1 reviewed N/A, 0 FAIL, 0 BLOCKED, 0 REVIEW_REQUIRED. The PR-level repository-wide required check remains blocked by the expired-readiness gate; this is recorded separately from the scope rows.
- Shared regression verdict: prior implementation PR and post-merge main checks passed; PR #707 XML validation and package checks passed. Both rotating probes preserve their instruction bodies in the generated Lab package. Required overall CI is not green because the domain/readiness/release check rejects expired records; the unchanged final-main behavior is not inferred.
- Non-blocking findings and accepted impact (owner/reviewer + future Issue): runtime/model and channel compatibility remain explicitly deferred to #682; no runtime claim is made.
- Scope compared with lock commit: no product/runtime scope expansion; the final matrix adds three strict-grammar regression cases and corrects the invalid second probe path.
- Issue / Project / PR reconciliation: #705, #703 and #706 are merged; #704 issue and native Project Status closeout remain pending owner review and PR #707. PR #707 has a required readiness CI blocker; no merge is proposed until it is resolved or explicitly accepted by the owner.
- Owner proposal / reviewer acceptance / decision timestamp: owner approved #703 and #706 on 2026-11-14; owner review of this closeout record is requested through its PR.
- If ABORTED: reason, partial evidence and complete unresolved-criterion mapping: N/A
- Next iteration eligibility (no automatic start or production promotion): Iteration 21 is accepted; a separately scoped next increment may begin after GitHub issue and Project status reconciliation.
