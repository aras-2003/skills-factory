# Iteration 21 — canonical XML grammar and static skill-body validation

- State: ACTIVE; scope lock merged at main `cb3e73d1e3d00aca733fec1e888f595511f118c9`. Implementation is now underway.
- Owner / reviewer: repository owner / owner-delegated Codex review (not independent human review).
- Tracking Issue / native Project iteration: #704 / `21 | Core extraction (provisional)`; assigned and read back after the scope lock merged.
- Previous terminal iteration: Iteration 20 CLOSED / ACCEPTED at main `54ac64a3029923c788b828ce63acdc0b88f18872`.
- Baseline main SHA: `54ac64a3029923c788b828ce63acdc0b88f18872`.
- Lock commit SHA: `cb3e73d1e3d00aca733fec1e888f595511f118c9`; recorded in #704 before implementation.
- Started at / closed at (UTC): 2026-11-14 23:16 / not closed.
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
| No implementation candidate yet | Main `cb3e73d1e3d00aca733fec1e888f595511f118c9` | N/A | Scope-lock checks passed; implementation checks not run yet. | N/A for this static-only slice; no runtime artifacts or skill behavior are changed. | — |

## Regression selection and counts

- Changed contracts / direct and transitive consumers (evidence links): TDC XML grammar, static validator, authoring template and validation documentation. No runtime or packaged contract consumer is changed.
- Included cases / exclusions with bounded-impact rationale: eight parser/authoring fixture scenarios, five shared offline sentinels, two unchanged-skill probes and repository validation are listed in the matrix. Runtime/model cases and cross-channel compatibility are excluded because no skill body, loader or package output changes; these remain explicit requirements of #682.
- Fixed sentinels / rotating unchanged-domain probes (minimum 2): offline regression checks for YAML frontmatter parsing, skill routing/catalog registrations, tool permission declarations, evaluator-only fixture isolation, and package/catalog manifests; two unchanged skill fixtures are selected in the matrix.
- Last full runtime baseline candidate / behavior iterations since baseline (maximum 4): current Site Lab attestation is source `1d55767564bd092935c4d8a21fa0debc7a382db2`, older than this scope baseline. No runtime baseline claim is made; this tooling-only slice does not change runtime behavior.
- Planned distinct scenarios / executions by layer and required surface: eight parser/authoring fixture scenarios, five shared offline sentinels, two unchanged-skill probes, and full applicable offline CI; runtime surface N/A with the scope rationale above.
- Critical stochastic scenarios repeated at least 3 times / instability history: N/A; this scope introduces no model behavior or stochastic runtime path.
- PR CI / final-main checks and build / external runtime runs: required PR checks on the exact scope commit and final main source; post-merge offline CI. No external runtime run is required for this static-only slice.

## Defect intake and clarifications (append; intake always open)

| Bug Issue / discovery iteration | Existing contract / frozen criterion or unrelated | Severity / closure blocking | Fix PR or accepted deferral owner + future delivery iteration | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |
| None recorded at scope lock. | — | — | — | — | — |

## Closure / abort decision

- Outcome: PENDING (CLOSED or ABORTED only after decision)
- Final candidate / matrix and immutable evidence links: pending
- Committed Issues accepted / unresolved: #704 pending; #682 remains open/partial.
- Required rows PASS / FAIL / NOT_RUN / BLOCKED / REVIEW_REQUIRED / reviewed N/A: pending
- Shared regression verdict: pending
- Non-blocking findings and accepted impact (owner/reviewer + future Issue): pending
- Scope compared with lock commit: pending
- Issue / Project / PR reconciliation: pending closeout; #704 is assigned to Iteration 21 and In progress after native Project readback; PR #705 is merged.
- Owner proposal / reviewer acceptance / decision timestamp: pending
- If ABORTED: reason, partial evidence and complete unresolved-criterion mapping: N/A
- Next iteration eligibility (no automatic start or production promotion): only after this increment is CLOSED or formally ABORTED.
