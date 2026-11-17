# PRES-10 — Executive Editorial stage 1 (four-template approval candidate)

**Decision:** user approved Executive Editorial, phased 4+6, overall independent design quality gate after the library is implemented. No merge is authorized. This branch is a candidate for **stage-one template review only**, not a completed presentation capability.

## Contract and production path
- Canonical 4-slide illustrative fixture: `docs/presentations/examples/cio-executive-editorial-stage1.json` (`decision`, `options`, `architecture`, `roadmap`). Baseline/target are marked as statements with explicit epistemic status; no claim that value has been realized.
- New composition module `adapters/presentation-marp/scripts/executive_editorial_v2.py` is **layout code only**, dispatched by the pre-existing native ODP generator when `slide.extensions.executive.editorial_v2` is provided. It is **not** a second PPTX renderer.
- Existing source-to-pattern planner `scripts/presentations/reference_style_bridge.py`, existing editorial theme and native LibreOffice ODP→PPTX export remain in charge.
- All author-visible text/criterion rows, semantic architecture IDs/typed edges, deliverables and gates are passed through the canonical fixture, never invented at rendering time. Reject incomplete or malformed stage-one structures.
- Existing ten-slide CIO path is unchanged unless a slide explicitly requests editorial-v2.
- No new third-party skills, templates or branded assets imported.

## Four editorial templates

| ID | Role | Compositional grammar | Information that must remain legible |
|---|---|---|---|
| ED2-01 | Decision | Dominant recommendation, subordinate why, bounded board ask and explicit evidence gate | provisional vs approved; benefit unverified |
| ED2-02 | Options | Evidence-aware comparative matrix with highlighted federated column | qualitative criteria, conditional decision, no fabricated numerical ranks |
| ED2-03 | Architecture | Three semantic layers with connected typed relation IDs and stable object IDs | conceptual, not verified target model; formal mapping remains #747 |
| ED2-04 | Roadmap | Four milestone stages with deliverables, transition gates and go/no-go rule | no scaling without evidence; phase windows illustrative |

## Execution and reproducibility

Run `python adapters/presentation-marp/scripts/generate-pres07-native-baseline.py docs/presentations/examples/cio-executive-editorial-stage1.json /tmp/ed2 --executive`; then convert the ODP using LibreOffice, run `adapters/presentation-marp/scripts/verify-pres10-editorial-v2.py`, reopen the PPTX in LibreOffice, and capture 4 PNG pages. See `.github/workflows/test-pres10-executive-native.yml` for executable commands and uploaded artifacts.

The static contract test in `adapters/presentation-marp/scripts/tests/test_executive_editorial_v2.py` covers missing data, unsupported role, malformed comparison and disconnected architecture. The PPTX XML QA verifies 4 editable slides, native shapes, no flattened pictures, headlines, source-authored content and semantic IDs. The screenshot evidence supports manual evaluation; CI success alone is **not** a visual quality score.

## Stage-one review criteria (for user feedback, not automatic passing grade)

1. Narrative and visual dominance: single executive takeaway per page, recommendation and board decision immediately visible.
2. Distinct grammar: options are a true criterion-by-option matrix, architecture shows layer/dependency semantics, roadmap has explicit approval gates.
3. At projected size: headline comfortably readable; option labels and sources remain readable at full 16:9 screen. No clipped/overlapping objects, no material overflows.
4. Authenticity and editable-native: original authored copy, stable model IDs and epistemic labels; objects accessible as native editable shapes.
5. No claims of final quality until a reviewer examines actual images and the template is accepted.

**Known limitations:** no formal ArchiMate/BPMN/UML serialized model linked yet; not a measured BCG/McKinsey visual benchmark; no Microsoft PowerPoint GUI edit/save test; no independent reviewer assigned; no guarantee of identical font rendering on other OS versions. The full library quality gate is deferred by explicit user choice until the 6 remaining templates are implemented.

## Stage status

- Stage-one design, fixture, tests: implemented on candidate PR #750.
- Native runtime and edited PPTX: status follows exact head commit GitHub Actions evidence. Do not infer from prior commits.
- Human visual approval: **PENDING_USER_REVIEW**.
- Merge into main: **NOT_AUTHORIZED**.
