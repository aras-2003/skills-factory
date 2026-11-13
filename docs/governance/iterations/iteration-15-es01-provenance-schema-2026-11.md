# Iteration 15 — canonical capability provenance schema and migration (ES-01)

Template derived from the iteration delivery policy. This is a scope lock proposal; it does not start implementation.

- State: ACTIVE; scope locked by merged PR #660 (`0919deabab159cd6a8406b0c867fe4cbbf9cdf7c`).
- Owner / reviewer: Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review; not independent).
- Tracking Issue / native Project iteration: #616 / not assigned; native Project iteration remains a scheduling mirror.
- Previous terminal iteration: Iteration 14 CLOSED / ACCEPTED, #614; implementation PR #658 and evidence closeout PR #659; final main SHA `834c29258ce48d111a147b26540f13554a83be34`.
- Baseline main SHA: `834c29258ce48d111a147b26540f13554a83be34`.
- Lock commit SHA: `0919deabab159cd6a8406b0c867fe4cbbf9cdf7c`; recorded in #616.
- Started at / closed at (UTC): 2026-11-13T08:12:20Z / pending.
- Scope lock reviewed by / at: owner self-review / 2026-11-13; not independent.

## Frozen commitment

| Issue | Outcome / acceptance criterion IDs | Included | Excluded | Dependencies / accepted evidence | Size |
| --- | --- | --- | --- | --- | --- |
| #616 | 616-A1–A6 | Define and validate one canonical, structured provenance schema for existing skills and workflows; represent OWN, IMPORTED, EXTENDED, COMPOSED, and explicit UNKNOWN legacy state; preserve component lineage for compositions; deterministically migrate/classify the complete current inventory; generate existing catalog and release-facing provenance views from canonical source metadata. | External source intake/scanning or execution; update detection, matching/adaptation, and rollback; Site/Cloud Next UI or deployment; domain refactors/pilots; production promotion; silently treating UNKNOWN as OWN; provenance changing maturity, channel availability, security, or license state. | Parent #615 remains PLANNED. Reuse ENG-14 #242, STR-22 #450, and current catalog/release contracts after inspection. Source metadata is canonical; generated catalogs/manifests remain derived. | M |

## Design and ownership boundary

The canonical metadata is attached to each source skill or workflow record in the repository's existing source format, using a versioned schema and explicit fields. Generated `CATALOG.md`, `docs/catalog.json`, Lab/production capability manifests, and release manifests consume that same source representation; they are not separate sources of truth. Existing unspecified records are migrated to explicit `UNKNOWN` with `NOT_CLASSIFIED` verification. No attribution, SPDX identifier, or ownership is inferred. `COMPOSED` describes structure and retains per-component origin and revision; it does not replace component provenance or license review.

Provenance remains orthogonal to maturity, channel availability, security review, and license status. Any license/SPDX claim is present only when verified; an unverified value remains absent/unknown with its verification state recorded. Immutable upstream identity is recorded when available (URL/provider/path/version/commit/content digest); local changes, parents/dependencies, update policy, review time, and owner are explicit. Schema validation rejects contradictory or malformed states rather than normalizing them silently.

The inventory boundary is all skill and workflow source records on the locked baseline, including records with missing metadata. Generated documentation/catalog/manifest outputs are validated from a clean deterministic build. No external instructions or scripts are executed in this increment.

## Frozen acceptance criteria

- **616-A1 Taxonomy/schema:** A versioned JSON/YAML schema and source-format contract cover OWN, IMPORTED, EXTENDED, COMPOSED, and UNKNOWN. Valid fixtures for each state and a hybrid/composed fixture pass; invalid/missing required field and contradictory-state fixtures fail with actionable diagnostics.
- **616-A2 Lineage and claims:** IMPORTED/EXTENDED records retain immutable upstream identity and local modification lineage; COMPOSED records preserve every component's origin/revision. License/SPDX, attribution, ownership, and verification claims are never inferred or fabricated; malformed digests and unverified license claims are rejected or represented explicitly as unknown.
- **616-A3 Complete migration:** An inventory report maps every existing skill and workflow to a classified record or explicit UNKNOWN. No legacy record is assumed OWN. Migration is deterministic and reviewable, preserves existing behavior/metadata, and does not hand-edit generated outputs.
- **616-A4 Derived surfaces:** `CATALOG.md`, `docs/catalog.json`, Lab/production capability manifests, and release manifests expose compatible projections of the canonical schema without conflating provenance with maturity, channel availability, security review, or license status.
- **616-A5 Reproducibility/backward compatibility:** Repeated generation from the same locked inputs produces byte-stable generated outputs; existing catalog/package consumers remain compatible or receive an explicit, tested versioned migration. No source change occurs during generation.
- **616-A6 Regression/security:** Existing validation, packaging, domain integrity, and catalog consumer tests pass; negative fixtures prove no unreviewed external execution, no privilege/promotion changes, and no public secrets or source content leakage.

## Test plan

The fixed ledger is `evals/campaigns/iteration-15-es01-provenance-schema-2026-11/acceptance-matrix.md`. All required rows start `NOT_RUN`. Required surfaces are source schema/parser, migration and inventory, each generated catalog/manifest consumer, repository validation/packaging CI, and deterministic rebuild. External intake, Site runtime, and production runtime are out of scope and are not acceptance surfaces here. Shared regression sentinels include (1) catalog-to-package identity/compatibility and (2) provenance orthogonality with maturity/channel/security/license metadata. The complete current skill/workflow inventory is counted at implementation baseline and recorded with source revision and generated report hashes before migration.

## Candidate history (append; never overwrite)

| Candidate | Main SHA | Lab release ID / payload digest | Build + offline CI | Observed runtime identity / smoke | Supersedes / invalidated rows |
| --- | --- | --- | --- | --- | --- |
| Scope baseline | `834c29258ce48d111a147b26540f13554a83be34` | Pending implementation candidate | Existing exact-main checks from #614 closeout; new iteration checks not run | N/A for scope lock; no Site behavior | None |
| Implementation + final acceptance | `bb255409fc0eabba494a17841d3528459aeb7201` (PR #662 implementation `f092c0bde5a30fb8a6d07bb889539e16cd2d02d7`; PR #663 deterministic-generation gate `bb255409fc0eabba494a17841d3528459aeb7201`) | Exact-main Lab ZIP SHA-256 `96be0ceffda710f3dd69ab83bae2b1a133cc9e65ba33e76a12d1dfe02b7c12a3` (artifact 14027180796) | PR #662 and #663 checks PASS; exact main Validate [43404821673](https://github.com/aras-2003/skills-factory/actions/runs/43404821673), Domain [43404821698](https://github.com/aras-2003/skills-factory/actions/runs/43404821698), Site CI [43404821673](https://github.com/aras-2003/skills-factory/actions/runs/43404821673), Lab build [43404821655](https://github.com/aras-2003/skills-factory/actions/runs/43404821655), Pages deploy [43404820917](https://github.com/aras-2003/skills-factory/actions/runs/43404820917) all PASS | No external runtime behavior in scope; no Site/plugin promotion; inventory is explicitly 98 UNKNOWN records | Supersedes planning-only row; no acceptance rows invalidated |

## Regression selection and counts

- Changed contracts / direct and transitive consumers: source skill/workflow metadata parser; catalog generators; catalog JSON; Lab/production capability and release manifests; validation and packaging consumers. Confirm exact call graph during implementation before changing files.
- Included cases / exclusions: schema valid/invalid fixtures; complete source inventory; deterministic migration/generation; generated consumer compatibility. Excludes external source intake, Site UI, and domain adoption by frozen sequence.
- Fixed sentinels / rotating unchanged-domain probes: package/catalog identity; orthogonality with existing maturity/channel/security/license fields; at least two unchanged-domain skill/workflow probes selected and recorded before final validation.
- Last full runtime baseline candidate / behavior iterations since baseline: Iteration 14 exact main `834c29258ce48d111a147b26540f13554a83be34`; no runtime behavior changes in this iteration are proposed.
- Planned distinct scenarios / executions: 8 fixed ledger rows; schema fixture suite (5 positive provenance states plus hybrid; negative contradictory, incomplete, malformed digest, and unverified license); full inventory audit; two clean generation runs; package/catalog regression and required CI on PR and exact main.
- Critical stochastic scenarios repeated at least 3 times / instability history: none; migration and generation must be deterministic.
- PR CI / final-main checks and build / external runtime runs: Validate Skills, Domain Integrity, Evaluation CI/catalog tests, Lab packaging, Pages if affected; verify successful exact-main runs and artifact provenance after merge. No external runtime run is required.

## Defect intake and clarifications (append; intake always open)

| Bug Issue / discovery iteration | Existing contract / frozen criterion or unrelated | Severity / closure blocking | Fix PR or accepted deferral owner + future delivery iteration | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |
| None at scope lock | Baseline audit begins after lock; no defect inferred before inventory | N/A | N/A | N/A | Owner |

## Closure / abort decision

- Outcome: CLOSED / ACCEPTED.
- Final candidate: exact main SHA `bb255409fc0eabba494a17841d3528459aeb7201`; implementation PR [#662](https://github.com/aras-2003/skills-factory/pull/662), reproducibility validation PR [#663](https://github.com/aras-2003/skills-factory/pull/663). Final matrix: [Iteration 15 acceptance results](../../../../evals/campaigns/iteration-15-es01-provenance-schema-2026-11/acceptance-matrix.md).
- Immutable build evidence: exact-main Lab artifact [run 43404821655](https://github.com/aras-2003/skills-factory/actions/runs/43404821655), artifact ID 14027180796, SHA-256 `96be0ceffda710f3dd69ab83bae2b1a133cc9e65ba33e76a12d1dfe02b7c12a3`.
- Committed Issue accepted: #616. Parent #615 remains PLANNED and open as the umbrella.
- Required rows: 8 PASS, 0 FAIL, 0 NOT_RUN, 0 BLOCKED, 0 REVIEW_REQUIRED, 0 reviewed N/A; source inventory 98 records (79 skills, 19 workflows), explicitly UNKNOWN.
- Shared regression verdict: PASS. Exact-main Validate, Domain Integrity, Site CI, Lab build, release packaging preparation, and Pages checks all passed; the source-contract job performed two catalog generations and confirmed identical SHA-256 outputs with source registry/audit unchanged.
- Non-blocking finding: historical sources remain UNKNOWN until separately reviewed; this is the intended fail-closed outcome and does not imply ownership, license, security review, runtime availability or production readiness.
- Scope compared with lock: unchanged. No external intake, Site UI/runtime change, plugin promotion or production release is claimed.
- Issue / Project / PR reconciliation: implementation PR #662 and validation PR #663 are merged; #616 is closed after this acceptance closeout; #615 remains open/planned. Native Project Iteration remains unassigned as locked.
- Owner proposal / reviewer acceptance: Arkadiusz Kamrowski / self-review (not independent). Completed 2026-11-13 UTC.
- If ABORTED: N/A.
- Next iteration eligibility: #617 may begin under a new scope lock; no other planned issue is started by this closeout.
