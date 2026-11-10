# Iteration 09 — Canonical presentation model and reuse boundary (PRES-02)

- State: ACTIVE (activated after scope lock commit `153b7428839048871bff8d8d7c0ed7c4dc6c3f93`; no implementation PR preceded it).
- Owner / reviewer: Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review; not independent).
- Tracking Issue / native Project iteration: #608 / NOT ASSIGNED OR VERIFIED (available GitHub connector cannot mutate/read the native Project Iteration field).
- Previous terminal iteration / closure link: Iteration 08 CLOSED / ACCEPTED in PR #629 at `cfcb1c9b6f0f5ee512d7cbc44da98740198f9898`; Iteration 7 ABORTED, terminal.
- Baseline main SHA: `cfcb1c9b6f0f5ee512d7cbc44da98740198f9898`.
- Lock commit SHA: `153b7428839048871bff8d8d7c0ed7c4dc6c3f93` (first complete record+matrix tree on this branch; preserve this as the immutable lock).
- Started at / closed at (UTC): 2026-11-10 17:16:22 UTC / pending.
- Scope lock reviewed by / at: Arkadiusz Kamrowski, self-review, 2026-11-10.

## Frozen commitment

| Issue | Outcome / acceptance criterion IDs | Included | Excluded | Dependencies / accepted evidence | Size |
| --- | --- | --- | --- | --- | --- |
| #283 (parent, partial only) | PRES-01 foundation slice; contributes a stable source/model contract but is not a closure of the epic | Use its already merged source design as the input to the audit and define how its existing semantic slide model migrates to the canonical model | The remainder of PRES-01 acceptance (native deck creation, rendered inspection, export/round-trip, runtime/client proof and release review) stays open for later bounded increments; do not mark #283 Done | Source exists in main from PRs #284/#315. Issue remains open / Validation; source presence is not runtime acceptance. | XL parent decomposed across later increments |
| #608 | 608-A through 608-G | Audit current presentation/report/visual pipeline and renderer ownership; document build-vs-reuse; formalize and version the existing semantic/evidence model in `workflows/presentation-production/references/artifact-contract.md` as DeckSpec/SlideSpec; add JSON Schema and deterministic validator; add a synthetic example DeckSpec and exact round-trip/legacy-compatibility tests for numbers, units, sources, notes, claims, data references, exhibits, layout tokens and desired editability | No Marp adapter, format router, theme registry, asset renderer, PPTX/PDF export, Figma/Canva authoring operation, Site/runtime registration, production promotion, or broad global refactor. No edits to Report OS or `visual-output-design` behavior unless the audit proves a minimal justified contract fix is required; any such capability belongs in a new scope. | PRES-01 source in main; reuse `presentation-slide-authoring` semantic fields, existing `ExhibitSpec`, Report OS and visual-output ownership. Dependency is the existing source/design baseline only; no claim that #283's open runtime acceptance has passed. | M |

## Test plan

Acceptance matrix: [iteration-09-pres02-canonical-model/acceptance-matrix.md](../../../evals/campaigns/iteration-09-pres02-canonical-model-2026-11/acceptance-matrix.md).

Required surface: local deterministic Python/JSON Schema validation plus all applicable GitHub CI. No runtime/MCP/Site surface is changed by this slice: no runtime registration, prompt, connector, renderer, package, or external artifact creation. Current Site v132 is only an observed baseline, not candidate acceptance. #283's Figma Slides/runtime acceptance remains required before closing #283 and is deliberately not claimed by #608.

Planned tests:
- 608-A: source inventory and build-vs-reuse decision table covers Presentation OS, Report OS, shared chart/visual, Figma/Canva integration points and existing exports; explicitly inspect the existing `artifact-contract.md` model (PresentationBrief, Claim/Evidence, DomainHandoff, Storyline/Slide, Exhibit and QA receipt), and map every existing contract to a disposition.
- 608-B: a versioned JSON Schema formalizes the existing semantic/evidence contract rather than introducing a competing DeckSpec; it includes stable slide identity, action title, claim/data references, exhibit, layout tokens, notes, provenance and desired editability with an explicit mapping to today's names/fields.
- 608-C: validator rejects malformed version, missing required fields, invalid references and incompatible types; accepts valid optional/unknown-safe fields according to the documented compatibility policy.
- 608-D: synthetic example deck validates with the same repository validator.
- 608-E: exact round-trip preserves numeric values, units, source IDs/URLs, notes, claim-to-slide and data-to-exhibit references, layout tokens and desired editability without coercion or omission.
- 608-F: compatibility mapping accepts the existing `presentation-slide-authoring` semantic model or reports every intentional, lossless normalization; it never silently drops existing content.
- 608-G: run affected presentation and workflow contract suites, shared Report Composer / Visual Output Design checks, the two rotating unchanged probes below, plus all required PR CI.
- Shared sentinels: `report-composer` no-unsolicited-artifact and evidence-preservation cases; `visual-output-design` no-fabrication and capability-preflight cases.
- Rotating unchanged-domain probes: `economics-post-cac-reconciliation` and `monitor-analysis-without-write-authorization`; these remain regression checks only and do not widen the presentation scope.
- No model/runtime repetitions: no runtime behavior or model-facing contract is changed. If implementation changes that boundary, stop and lock an expanded scope before merging behavior changes.

Development completes before the test/fix phase. The exact changed-path impact map, fixture hashes and validators are finalized after implementation and before tests. All execution states begin NOT_RUN and failures remain visible.

## Scope clarification — 2026-11-10

Inspection found that `workflows/presentation-production/references/artifact-contract.md` already defines draft `Storyline / Slide`, `Exhibit`, `Claim / Evidence` and artifact/QA receipt structures. Therefore 608-A/B must formalize and version that existing contract with explicit compatibility mappings; a second parallel semantic model is out of scope. This clarification narrows implementation choices and does not relax or add acceptance criteria.

## Candidate history (append only)

| Candidate | Main SHA | Lab release ID / payload digest | Build + offline CI | Observed runtime identity / smoke | Supersedes / invalidated rows |
| --- | --- | --- | --- | --- | --- |
| C1 | pending | not applicable to schema-only scope | NOT_RUN | NOT_REQUIRED for this scope; see test plan | none |

## Regression selection and counts

- Changed contracts / direct and transitive consumers: inspect `presentation-slide-authoring`, `presentation-exhibit-design`, `presentation-storyline`, `presentation-evidence-review`, `presentation-production`, `report-composer`, `report-document-architecture`, `visual-output-design`, visual/output architecture docs, export formats and existing validators.
- Included cases / exclusions: all existing Presentation skill suites and `presentation-production` E2E definitions; Report Composer and Visual Output Design shared contract suites; the two unchanged probes named above. Model-based runtime execution and Figma/Canva artifact creation are excluded from #608 but remain part of #283's later acceptance.
- Fixed sentinels / rotating unchanged-domain probes (minimum 2): report/visual evidence and no-artifact sentinels; `economics-post-cac-reconciliation`; `monitor-analysis-without-write-authorization`.
- Last full runtime baseline candidate / behavior iterations since baseline: current owner-only Site v132, canonical source `3dd79a8df6071b3b8a429293cb565890c19c6ec5`; this iteration does not change runtime behavior, so no new full runtime baseline is applicable.
- Planned distinct scenarios / executions by layer and required surface: 7 issue criteria plus 4 shared/rotating regression probes; deterministic tests once per PR revision and full affected CI. Additional cases may be added only to test existing acceptance, not to broaden scope.
- Critical stochastic scenarios repeated at least 3 times / instability history: N/A; no stochastic or model/runtime criterion.
- PR CI / final-main checks and build / external runtime runs: PR validation/domain/eval integrity and Lab build jobs as applicable; Site/runtime and production release are N/A for this source-only contract.

## Defect intake and clarifications (append only)

| Bug Issue / discovery iteration | Existing contract / frozen criterion or unrelated | Severity / closure blocking | Fix PR or accepted deferral owner + future delivery iteration | Retest rows | Reviewer |
| --- | --- | --- | --- | --- | --- |

## Closure / abort decision

- Outcome: PENDING.
- Final candidate / matrix and immutable evidence links: pending.
- Committed Issues accepted / unresolved: #608 pending; parent #283 remains open until its later runtime/export acceptance.
- Required rows PASS / FAIL / NOT_RUN / BLOCKED / REVIEW_REQUIRED / reviewed N/A: all NOT_RUN before implementation.
- Shared regression verdict: pending.
- Non-blocking findings and accepted impact: pending.
- Scope compared with lock commit: pending.
- Issue / Project / PR reconciliation: pending; native Project Iteration assignment is unverified.
- Owner proposal / reviewer acceptance / decision timestamp: pending; self-review must be explicit.
- If ABORTED: reason, partial evidence and complete unresolved-criterion mapping: N/A.
- Next iteration eligibility: no automatic start or promotion; close this increment before the next one.
