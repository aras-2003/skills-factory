# Presentation renderer and canonical-model reuse audit

Scope: Iteration 09 / #608 against the locked main revision. This is an inventory of existing source contracts, not proof that a connector, export path or runtime skill is available.

## Build vs reuse

| Capability | Existing source / owner | Decision | Gap to address in this increment | Boundary / risk |
| --- | --- | --- | --- | --- |
| Brief, claims, evidence, domain handoff, storyline, slides, exhibits and artifact receipts | `workflows/presentation-production/references/artifact-contract.md` | Reuse and formalize as versioned DeckSpec/SlideSpec v1; publish a JSON Schema and preserve the current unversioned form through an explicit adapter | The prose contract has no machine-readable versioned schema; slide IDs, notes and editability names differ across the consumers | The model is semantic and tool-neutral. It must not claim a vendor-specific action succeeded. |
| Slide-authoring semantic input | `skills/presentations/presentation-slide-authoring/SKILL.md` (`id`, `headline`, `source_ids`, `exhibits`, `layout`, `notes`, `alternative_text`) | Map aliases into the canonical slide fields; retain unknown legacy fields in an explicit extension during migration | `headline`/`id` and `speaker_notes`/`notes` need a documented mapping; desired editability is a request and must stay separate from observed editability | Migration must never infer editability from a visual or tool call. |
| Presentation storyline and ghost deck | `skills/presentations/presentation-storyline/SKILL.md`; workflow artifact contract | Reuse the current action-title, claim, source-finding and transition semantics | Add stable `slide_id` and connect claims/data to exhibits without replacing domain ownership | Storyline controls communication order, not strategic recommendations. |
| Exhibit selection and shared rendering | `skills/presentations/presentation-exhibit-design/SKILL.md`; `skills/meta/visual-output-design/SKILL.md`; `docs/VISUAL-OUTPUT-ARCHITECTURE.md` | Reuse the shared ExhibitSpec and visual-output-design renderer-selection boundary | Bind exhibit data references, units, provenance, desired editability and actual renderer status to a slide | Do not add a second chart engine or generate factual charts with image tools. |
| Chat report composition | `skills/meta/report-composer/SKILL.md`; `docs/INTEGRATED-REPORT-ARCHITECTURE.md` | Reuse Report Composer for chat report structure and its ExhibitSpec handoff | No changes needed to report structure in #608 | A chat report is not an external slide deck. |
| DOCX/PDF reports | `skills/reports/README.md`; `workflows/report-production/` | Reuse report-document-architecture, authoring and review for their own formats | No new PDF/document renderer | Do not make Presentation OS the owner of document pagination/export. |
| Figma Slides, Canva and Google Slides | `presentation-slide-authoring` and connected Figma/Canva/Google Slides tools | Keep each as an adapter behind capability preflight; choose one primary target per deck | #608 records capability boundaries only; actual native creation/editability receipts belong to #283 and later slices | Connector availability is session-specific. Canva edit commit requires preview and explicit approval; export is a separate capability. |
| Marp Markdown, HTML, PDF and PPTX | No existing Marp CLI adapter identified in source tree | Defer new adapter to #609 | Define canonical source now so the future adapter consumes a stable model | Do not add Marp or LibreOffice dependencies in #608. |
| Theme tokens, asset manifests and cross-format QA | Existing creative-direction/design-library references, ExhibitSpec and export-verification skill | Reuse the existing roles; defer registry, asset pipeline and QA matrix expansion to #611–#613 | Represent layout tokens and desired editability without claiming rendered fidelity | Fonts, licensed assets, notes, visual fidelity and object editability vary by target. |
| Renderer/export verification | `skills/presentations/presentation-export-verification/SKILL.md` | Reuse its receipt and round-trip boundary | Canonical model carries the references needed for later receipts; no export implementation here | Planned output or a successful create call is not reopened/export-verified output. |

## Canonical v1 decisions

- `docs/presentations/canonical-deck-v1.schema.json` versions the existing draft artifact contract. It does not replace the roles or create a vendor API schema.
- `SlideSpec.slide_id` is the stable slide identity. Legacy `id` is mapped explicitly.
- `action_title` remains an evidence-supported claim where the slide is analytical; teaching, cover and agenda slides may use a question or label as already documented.
- Claims are objects with stable IDs and epistemic status; data references preserve the submitted value, exact unit, source IDs and as-of context without numeric coercion.
- `exhibits` refer to slide-local data-reference IDs. A slide owns `layout.layout_id` and `layout.tokens`, notes, provenance and `desired_editability`.
- Requested editability (`desired_editability`) is independent of observed exhibit editability (`EDITABLE_NATIVE`, `EDITABLE_PARTIAL`, `RASTER_ASSET`, `FLATTENED`, `UNKNOWN`).
- Unversioned legacy decks are normalized by an explicit compatibility adapter. Its output archives the original source object under `extensions.legacy_source`; unsupported legacy exhibit fields are preserved and reported for review instead of being discarded.

No renderer, runtime registration, global routing, Site behavior or production artifact changes are justified by this audit. Later increments must use this contract and their own issue/scope acceptance.
