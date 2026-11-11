# Iteration 10 — Marp CLI adapter and export fidelity (PRES-03)

- State: CLOSED / ACCEPTED (owner closeout after exact-main validation; see appended evidence ledger). The original ACTIVE scope lock remains immutable.
- Owner / reviewer: Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review, not independent).
- Tracking issue / native Project iteration: #609 / NOT ASSIGNED OR VERIFIED (connector cannot read or mutate native Iteration).
- Parent acceptance: #283 remains open; this increment contributes the Marp/PPTX/export slice only and does not satisfy its native Figma Slides/client runtime criteria.
- Previous terminal increment: Iteration 09 CLOSED / ACCEPTED, PR #632, merge 668973da197c8fb7ed9c3840ba884e0d150752a7.
- Baseline main SHA: 668973da197c8fb7ed9c3840ba884e0d150752a7.
- Lock commit SHA: a8f0dfaba01b1db8e91e20804762ec584836bba8 (record + matrix tree commit; immutable lock).
- Started at / closed at (UTC): 2026-11-10 18:07:54 UTC / 2026-11-11 17:47 UTC.

## Frozen commitment

| Issue | Outcome / acceptance IDs | Included | Excluded | Dependencies / evidence | Size |
| --- | --- | --- | --- | --- | --- |
| #609 | 609-A through 609-I | Isolated adapter using canonical DeckSpec v1; deterministic and sandboxed conversion to HTML, PDF, flattened PPTX, and opt-in experimental editable PPTX; exact runtime preflight; tests that generate and reopen outputs; visual/slide-fidelity evidence, notes/editability evidence, error/font fallback receipts | No Site/runtime registry, production plugin promotion, automatic fallback from requested editable PPTX, remote HTML/JS/assets, arbitrary script execution, theme registry, upstream skill import/adaptation, external theme scraping, changes to Report/Web Design/Investment domains | Reuse #608 schema and artifact contract; pin Marp CLI v4.5.1; browser required for PDF/PPTX; LibreOffice Impress required only for experimental editable output; isolate temp workspace and disable outbound resource loading | M |
| #283 (parent, partial) | PRES-01 parent remains open | Complete a reproducible Marp/export path useful to the parent’s multi-renderer presentation acceptance | Native Figma Slides creation, Figma render/client observation, and the rest of #283 acceptance remain open until their own exact receipts exist | Existing parent implementation PRs #284/#315 plus #608 canonical model | Parent spans bounded increments |

## Build-vs-reuse and implementation boundary

Reuse docs/presentations/canonical-deck-v1.schema.json and workflows/presentation-production/references/artifact-contract.md; do not create a second slide model. Keep the renderer in an isolated adapter under adapters/presentation-marp/ with pinned Node/package dependencies and a documented CLI interface. The adapter receives a schema-valid DeckSpec v1, emits constrained Marp Markdown and local fixture assets in a fresh temporary directory, then invokes only the pinned Marp CLI. The package is not registered with Lab/production/Site in this increment.

Allowed outputs: html, pdf, pptx_flattened (default PPTX behavior), and explicit pptx_editable_experimental. User-selected output mode is mandatory input. Missing browser or LibreOffice yields actionable BLOCKED_MISSING_RUNTIME; editable mode never downgrades to flattened output. Preflight records exact Marp, Node, browser and LibreOffice versions and executable identity.

Inputs are local canonical DeckSpec plus allowlisted local assets only. Reject remote URL fetches, path traversal, symlinks escaping the isolated input root, scripts, event-handler attributes, and unapproved raw HTML. No converter execution of upstream content. Stage into a fresh temporary directory; do not mutate source inputs. Keep invocation bounded by timeout/output-size limits and return redacted bounded error detail.

Standard PPTX is expected to be image-backed/flattened and supports Marpit presenter notes. Experimental editable PPTX requires browser + LibreOffice Impress; the result must be inspected for actual editable text/shapes, layout drift and notes (which are unsupported in that mode). Clearly report lower fidelity, complex-CSS limits and note loss. Never infer object-level editability from the command flag alone. These boundaries match [official Marp CLI guidance](https://github.com/marp-team/marp-cli/blob/main/README.md); current pinned CLI baseline is 4.5.1 per [official releases](https://github.com/marp-team/marp-cli/releases).

## Test and acceptance plan

All development is completed before the test/fix phase. Acceptance matrix records exact dependency versions, source/fixture hashes, runner identity, commands, artifact hashes, and reopened/inspection receipts. Required outputs are generated from the same 3-slide synthetic 16:9 deck, reopened and inspected: HTML, PDF, flattened PPTX and experimental editable PPTX (four artifacts; exceeds the three-artifact minimum). A repeat render checks content-level determinism after normalizing volatile container metadata.

- 609-A: audit and reuse map; canonical DeckSpec mapping; no duplicate renderer/schema.
- 609-B: pinned adapter package and install/runtime preflight; exact version identity recorded.
- 609-C: secure input handling and isolated execution; adversarial path, URL, raw HTML/script, symlink, timeout and size cases fail closed.
- 609-D: all four modes produce real outputs from the same fixture and re-open successfully in compatible tools.
- 609-E: 16:9 dimensions, slide count/order/IDs, data/units/provenance and content are checked across rendered surfaces; repeated content output is deterministic.
- 609-F: rendered comparison includes one reference screenshot per slide and a documented visual drift threshold; font fallback case is observed and recorded.
- 609-G: flattened PPTX inspection confirms slide backgrounds and notes; editable PPTX inspection confirms actual editable objects, records fidelity drift, and confirms presenter notes are absent.
- 609-H: requested editable output with missing LibreOffice/browser returns actionable BLOCKED, with no flattened fallback; malformed input and renderer errors return bounded actionable failures.
- 609-I: run adapter tests, presentation workflow contract suites, shared report/visual sentinels and all relevant GitHub CI. Site deployment/runtime registration is reviewed N/A because the adapter remains isolated and is not packaged or deployed in this increment.
- #283 parent proof remains incomplete until native Figma Slides, rendered inspection, export/round-trip and client/runtime evidence are independently observed.

All execution states begin NOT_RUN. Only opened files and content inspection count as export receipts; successful process exit or file existence alone is insufficient. No PR code implementation may start before this scope-lock PR merges.


## Closeout evidence — 2026-11-11 (append-only)

Final implementation candidate: `ee95deec75a7020007c99cffbc09975d846a51a3` (current main after #609 and #610). The #610 changes are outside this frozen #609 scope; they did not alter the Marp adapter files. The Marp adapter workflow was rerun on the exact integrated main SHA to verify the combined tree.

- PR #634 merged at `56f26c63dd551b90675c1c7882018174d5ce45e4`; adapter workflow passed on PR head, including output generation/reopen, sandbox, runtime-failure, fidelity and security steps.
- Exact-main Marp adapter run [#223](https://github.com/aras-2003/skills-factory/actions/runs/43070251831) succeeded on `ee95deec75a7020007c99cffbc09975d846a51a3`. Its retained artifact is [sf-presentation-marp-ee95deec75a7020007c99cffbc09975d846a51a3](https://github.com/aras-2003/skills-factory/actions/runs/43070251831), artifact ID `13878926304`, digest `sha256:5069ac0764368e60b8d395cb35b52019bc58996ea9a12b7d4dbe5b28985a8db6`, expiry 2027-02-09.
- On the same main SHA, Validate skills #1232, Domain integrity #1232, Site CI #620, Lab packaging #185 and Pages build #311 all completed successfully.
- The exact-main Marp job passed: adapter unit/input-security tests; canonical DeckSpec validation; missing-LibreOffice and missing-browser fail-closed checks; synthetic PDF diagnostics; generation, reopen and inspection of HTML, PDF, flattened PPTX and experimental editable PPTX; and exact source revision verification.
- The older user-provided ZIP showed black HTML captures from a pre-fix run. It is retained as defect evidence only. The capture fix is in PR #634; the exact-main workflow above regenerated and retained current captures. The old ZIP is not counted as candidate acceptance evidence.

### Final matrix disposition

| Row | Final verdict | Evidence |
| --- | --- | --- |
| 609-A | PASS | Isolated adapter and canonical DeckSpec reuse documented in PR #634. |
| 609-B | PASS | Pinned runtime identity recorded in exact-main receipts. |
| 609-C | PASS | Adapter input/security tests passed on exact main. |
| 609-D | PASS | Four modes generated, reopened and inspected in exact-main run #223. |
| 609-E | PASS | 16:9/content checks and repeated render determinism passed. |
| 609-F | PASS | Per-slide screenshots, raster comparison and font fallback evidence retained in artifact. |
| 609-G | PASS | Flattened images/notes and experimental editable-object inspection passed; note loss is recorded as a limitation. |
| 609-H | PASS | Missing browser/LibreOffice scenarios failed closed without fallback. |
| 609-I | PASS | Exact-main adapter, Validate skills, Domain integrity and Site CI passed. |
| runtime-site | reviewed N/A | No Site registration, package promotion or runtime change is in the locked scope. |

Closeout reconciliation: #609 is closed; #283 remains open for its separate native Figma Slides/client runtime, rendering and full delivery criteria. No production or Lab maturity claim is made by this increment. Owner and reviewer are the same person; this is an explicit self-review, not independent approval. No unresolved critical/major blocker remains against the frozen #609 acceptance.
