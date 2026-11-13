# TDC v1.1 — post-migration quality review (2026-11-13)

**Scope:** 110 OPEN Issues in `aras-2003/skills-factory`, enumerated with GitHub searches split by creation date (`created:<2026-10-15`, `created:>=2026-11-01`) and re-read after updates. Closed historical Issues excluded.

## Verified inventory
- 110/110 open issues contained a TDC or tailored architecture change-description section.
- 102 were normalized with a new TDC summary; 8 (ES-03, ES-04, ES-06, ES-07, ES-08, XML-00, XML-09, XML-10) retained tailored change descriptions.
- All 110 were fetched via issue search and checked for the expected heading; no missing heading.
- **This is format coverage, not independent acceptance.** Existing Issues contain unverified `TO_CONFIRM` architecture ranges, condensed acceptance text and historical status context.
- The native GitHub Projects **Architecture Impact** custom field was reported by the user as created. The current GitHub connector does not expose Project-item field value reads/writes. Field values were **not** updated or verified, and no labels should be treated as a substitute.

## Quality findings — evidence-backed examples
| Issue | Observed content problem | Corrective action before Ready |
| --- | --- | --- |
| [#163](https://github.com/aras-2003/skills-factory/issues/163) PRO-05 | Header says DISCOVERY/VALIDATE although underlying scope describes a future AI-use-case-review capability; impact A0–A2 is a preliminary generality, no source-pinned component contract. | Reconcile whether output is a decision/spec or executable skill; lock type, owner skill, observed baseline and output fixture; define test cases comparing deterministic alternative vs AI recommendation. |
| [#219](https://github.com/aras-2003/skills-factory/issues/219) STR-10 | Large pipeline packed into a task; narrative acceptance includes qualitative language not mapped to case IDs; architectural impact A1–A2 is assumed. | Confirm routing from existing diagnostic/design skills, specify contract inputs/outputs, split independent implementation slices and negative routing regression tests. |
| [#283](https://github.com/aras-2003/skills-factory/issues/283) PRES-01 | EPIC identified but summary still contains many unscoped original acceptance assertions; migration does not reconcile completed PRES-02..08 with open epic obligations. | Reconcile child statuses and exact runtime evidence; keep epic as tracking only, avoid redundant implementation. |
| [#297](https://github.com/aras-2003/skills-factory/issues/297) OUT-01 | Shared DomainResult schema influences consumers but condensed description is truncated mid-list and impact A2–A3 remains TO_CONFIRM. | Define authoritative schema owner; enumerate concrete consumer interfaces, version/migration strategy and schema fixtures. A3/ADR if cross-component contract ownership changes. |
| [#317](https://github.com/aras-2003/skills-factory/issues/317) COM epic | Header explicitly says criterion mapping unverified even though detailed historical acceptance exists; broad workstreams are not independently executable. | Map child CD/EC issues to acceptance IDs; describe program closure separately; no XL implementation order. |
| [#622](https://github.com/aras-2003/skills-factory/issues/622) ES-07 | Four domains and optional PlantUML expansion coexist in one Issue. Clearer prose does not make work atomic. | Use bounded domain deliverables; preserve one Architecture IR and reject duplicate render/export stack. |
| [#674](https://github.com/aras-2003/skills-factory/issues/674) XML-01 | Named 7-skill inventory is clear but no resolved source revision or frozen case IDs in summary. | Freeze per-skill source paths, baseline cases, exact parser/packager contracts and behavioral acceptance in iteration record. |

## Critical limitations
1. No independent human handoff or semantic model-graded scoring executed for all 110; no task-level 0–10 scores asserted.
2. No systematic code-to-Issue architecture reconciliation: `TO_CONFIRM` remains an explicit blocker for architecture-sensitive Ready.
3. Original acceptance criteria were preserved, not systematically linked to executable fixture IDs.
4. Existing active/frozen iteration scopes must not be silently rewritten; this report proposes future corrections, not acceptance relaxations.
5. CI status of PR #686 is not yet positively verified; PR remains draft. No runtime invocation/verification or deployment.

## Recommended next actions
1. Configure/populate the existing native Projects Architecture Impact field with values grounded in exact-source review; verify actual field options and item membership with a Project-capable connector or authenticated Work browser.
2. Pilot independent TDC quality review with #163, #219, #297, #317, #622 and #674, recording strengths, weaknesses, concrete missing inputs, AC↔case mapping and NOT_SCORABLE until adequate evidence.
3. Reconcile open EPICs against already closed children and current runtime evidence, then adjust only next planned slices; do not re-open completed scope.
4. Add source-controlled deterministic TDC structure checks and risk-scoped semantic grading to existing evaluation infrastructure, with held-out examples and an explicit adoption gate.
5. Validate Issue Forms and required repository CI on PR #686; obtain review before changing its draft status.

**Disposition:** DOCUMENTED / REVIEW REQUIRED. Neither migration completeness nor existence of a review report means READY, TESTED or RUNTIME_VERIFIED.
