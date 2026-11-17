# PRES-10: executive-native PPTX composition (bounded implementation)

**Owner:** Presentation OS / #745. **Implementation:** PR #750. **Scope:** reuse the existing PRES-07 ODP native baseline generator and LibreOffice conversion. No second presentation renderer, no external third-party skill import, no protected firm-branded slide templates.

## Entry points and actual outputs

- Input: canonical DeckSpec v1 JSON. Required: slide IDs, role, action title, claims with epistemic status and source reference lineage. The `role` must map to the selected PRES-09 pattern; missing references or contradictory claims fail closed.
- Source selection: `scripts/presentations/reference_style_bridge.py` + `docs/presentations/consulting-reference-patterns-v1.json` from #744.
- Native theme: existing `adapters/presentation-marp/themes/registry.json` / `sf-editorial` tokens. Layout font styles are rendered as native text shapes, and background/lines/boxes as native shapes.
- Executive layout grammar: `adapters/presentation-marp/scripts/executive_odp_layouts.py` (10 independently authored role-specific layouts: decision/options/capability/architecture/governance/roadmap/kpi/risks/value/handoff).
- Existing emitter: `adapters/presentation-marp/scripts/generate-pres07-native-baseline.py <deck.json> <outdir> --executive`. It produces `native-baseline.odp` and `executive-layout-manifest.json`.
- Conversion: `libreoffice --headless --convert-to pptx --outdir <outdir> <outdir>/native-baseline.odp`. The original ODP remains available as an editable source.
- Audit: `adapters/presentation-marp/scripts/verify-pres10-native.py` confirms 10-slide golden fixture, PPTX zip/XML validity, actual text content (including source-authored overrides), 8+ native editable shapes per slide, layout IDs, rights and revisions. LibreOffice reopens the PPTX as PDF; pdftoppm captures all rendered PNGs. CI artifact provides the actual deck and image evidence.

## Content provenance and non-CIO reuse

The versioned CIO fixture `docs/presentations/examples/cio-reference-golden-v1.json` is **illustrative**; goal, recommendation, architecture and governance content are hypotheses, except explicitly tagged user-supplied baseline and target. No saving or regulatory assertions are inferred.

For other decks, use `slide.extensions.executive.copy` to author **every required text element** for the role (keys in `REQUIRED_COPY`); missing fields raise an error. This prevents accidental reuse of CIO-scenario assumptions. Up to ten slides are allowed. `slide.action_title` remains the canonical, unoverridden headline; footers are derived from source lineage rather than arbitrary user copy.

## Run

```bash
python adapters/presentation-marp/scripts/generate-pres07-native-baseline.py \
  docs/presentations/examples/cio-reference-golden-v1.json /tmp/pres10 --executive
libreoffice --headless --convert-to pptx --outdir /tmp/pres10 /tmp/pres10/native-baseline.odp
python adapters/presentation-marp/scripts/verify-pres10-native.py \
  docs/presentations/examples/cio-reference-golden-v1.json \
  /tmp/pres10/executive-layout-manifest.json /tmp/pres10/native-baseline.pptx \
  /tmp/pres10/native-baseline.odp /tmp/pres10/native-verification.json
```

GitHub workflow: `.github/workflows/test-pres10-executive-native.yml`, with commit-pinned Actions and read-only permissions. Artifact retention is 14 days. No external content fetch during rendering.

## Acceptance ledger

| Criterion | Evidence | Current disposition |
|---|---|---|
| 10 unique original executive role layouts | Code, fixture, source lineage | IMPLEMENTED; verify latest CI |
| Native text/shape objects in PPTX | PPTX XML editability audit + ODP source | CI evidence, not PowerPoint GUI guarantee |
| Real 16:9 PPTX opens and renders | LibreOffice roundtrip to PDF and 10 PNG previews | CI evidence |
| Stable sources, claim IDs and uncertainty labels | DeckSpec v1 + reference-manifest + XML audit | CI evidence |
| Repeatable golden fixture | Deterministic source/role selection, pinned theme; CI rerun | Partial: semantic repeatability verified; byte/pixel determinism unverified |
| Native PowerPoint editing/save-close-reopen | Not performed in Microsoft PowerPoint | NOT_RUN |
| Quantitative/qualitative before-after board quality benchmark | Separate independent design review required | NOT_RUN |
| Formal executable ArchiMate/BPMN/UML semantic projection | Owned by #747 / #739 | NOT_RUN |
| Production release | Scope lock, independent visual QA and complete acceptance required | BLOCKED |

**Known risk:** ODP-to-PPTX preserves native text/shapes in observed artifacts but may reflow under different Office font stacks. A file opening and passing XML checks is not an executive-grade visual acceptance. #746 must review actual pixels, including headings, content density and perceived clarity. No claim of BCG/McKinsey/Accenture official design quality is made.
