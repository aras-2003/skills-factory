# TDC v1.1 — post-migration quality review (2026-11-13)

**Scope:** 110 OPEN Issues in `aras-2003/skills-factory`, enumerated with GitHub searches split by creation date (`created:<2026-10-15`, `created:>=2026-11-01`) and re-read after updates. Closed historical Issues excluded.

## Verified inventory
- 110/110 open issues contained a TDC or tailored architecture change-description section.
- 102 were normalized with a new TDC summary; 8 (ES-03, ES-04, ES-06, ES-07, ES-08, XML-00, XML-09, XML-10) retained tailored change descriptions.
- All 110 were fetched via issue search and checked for the expected heading; no missing heading.
- The frozen manifest now locks the exact 110 Issue IDs to source main `22d31320e6114d8c1dbe6b1ed79dff12cb2223cf` with SHA-256 `253776f718f5f2da421f85feafa21f065aa8f773fd9a53b68001c8657797352f`.
- Reconciliation on 2026-11-14 found 109/110 captured Issues still open; #618 closed after the snapshot and retains its description. New tracker #688 is post-lock and excluded from the 110-item denominator. The current open Issue set is 110, including #688.
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
2. No systematic code-to-Issue architecture reconciliation: all 110 Architecture Impact entries remain `PROPOSED`, and `TO_CONFIRM` remains an explicit blocker for architecture-sensitive Ready.
3. The GitHub edit history does not provide a source-controlled before-image for every Issue body; this audit verifies current descriptions and the frozen ID/title set, but does not independently prove preservation of every original acceptance sentence or map all criteria to executable fixture IDs.
4. Project field type/options, membership and credentials have not yet been read through the dedicated workflow; no Project values were written. The sync helper now refuses writes unless an entry is explicitly `APPROVED`.
5. No production plugin or Site deployment is part of this iteration.

## Recommended next actions
1. Run a read-only Projects dry-run; review actual field options, membership and all proposed levels before marking any manifest rows `APPROVED`. Apply only approved rows and preserve per-item readback or a specific blocked reason for every other row.
2. Pilot independent TDC quality review with #163, #219, #297, #317, #622 and #674, recording strengths, weaknesses, concrete missing inputs, AC↔case mapping and NOT_SCORABLE until adequate evidence.
3. Reconcile open EPICs against already closed children and current runtime evidence, then adjust only next planned slices; do not re-open completed scope.
4. Add source-controlled deterministic TDC structure checks and risk-scoped semantic grading to existing evaluation infrastructure, with held-out examples and an explicit adoption gate.
5. Validate the dedicated workflow and forms on the exact candidate and merged-main revisions before closing the iteration.

**Disposition:** DOCUMENTED / REVIEW REQUIRED. Neither migration completeness nor existence of a review report means READY, TESTED or RUNTIME_VERIFIED.
