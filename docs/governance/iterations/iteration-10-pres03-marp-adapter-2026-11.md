# Iteration 10 — Marp CLI adapter and export fidelity (PRES-03)

- State: ACTIVE (activated in PR #633 after immutable scope lock commit a8f0dfaba01b1db8e91e20804762ec584836bba8; no implementation PR preceded activation).
- Owner / reviewer: Arkadiusz Kamrowski / Arkadiusz Kamrowski (self-review, not independent).
- Tracking issue / native Project iteration: #609 / NOT ASSIGNED OR VERIFIED (connector cannot read or mutate native Iteration).
- Parent acceptance: #283 remains open; this increment contributes the Marp/PPTX/export slice only and does not satisfy its native Figma Slides/client runtime criteria.
- Previous terminal increment: Iteration 09 CLOSED / ACCEPTED, PR #632, merge 668973da197c8fb7ed9c3840ba884e0d150752a7.
- Baseline main SHA: 668973da197c8fb7ed9c3840ba884e0d150752a7.
- Lock commit SHA: a8f0dfaba01b1db8e91e20804762ec584836bba8 (record + matrix tree commit; immutable lock).
- Started at / closed at (UTC): 2026-11-10 18:07:54 UTC / pending.

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
