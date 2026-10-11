---
name: presentation-exhibit-design
description: >
  Choose data-faithful charts, diagrams and presentation exhibits for an approved slide claim and audience, delegating actual rendering to existing visual-output-design and deterministic tools. Use after storyline/evidence planning; do not use for decorative image prompts alone.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: draft
  risk: medium
  last_reviewed: "2026-10-09"
---

# Presentation Exhibit Design

## Purpose
Translate a supported claim and its evidence into a clear, editable exhibit specification. This skill does not invent analysis or perform the full deck narrative.

## Preconditions
Slide claim/purpose, audience, source-supported numbers/relationships and a known or discoverable renderer.

## Procedure
1. For each slide, select the single comprehension job: compare magnitude, show composition, change over time, trade-off, causal mechanism, flow, hierarchy, architecture, scenario, decision or illustrative context.
2. Match grammar: ranked bars for categories; time-series only for real dated sequences; waterfall for mathematically valid bridges; range/dots for uncertainty; matrix for choices/trade-offs; step-flow for process; network only for evidenced relationships. Avoid 3D, meaningless decoration and unsupported composite scores.
3. Define semantic exhibit `type,reason,claim_id,source_ids,fields,units,labels,denominators,as_of,uncertainty,annotations,interaction`. A visual summary must not imply greater certainty than the ledger.
4. Call `visual-output-design` for actual component rendering where available. Follow its `capability_preflight` and `renderer_execution_status`: distinguish specification from emitted payload and client display. Quantitative charts require deterministic numeric renderer; image/video generation is **not** a factual chart renderer.
5. For non-quantitative illustrations, optionally use tools/media generators only when it helps understanding, with license, provenance and prompt/asset manifest. Do not render customer/org facts through artistic generation.
6. Ensure typography, plot labels, source line, legend, visual encoding and annotations are readable at the intended device/distance; show uncertainty and accessible alternative text.
7. Prefer editable native shapes/charts/text where proven supported by the authoring adapter. If a visual is raster, label `RASTER_ASSET`, not `EDITABLE_NATIVE`.
8. Send exhibit plan and verified payload receipts to `presentation-slide-authoring`.

## Decision rules
A visual is justified by information value. Slides may be text-led where that better serves the communication objective. Prioritize one decisive exhibit rather than a dashboard of unrelated metrics.

## Inputs
Slide semantic model, evidence ledger, desired authoring tool and design tokens.

## Output contract
`ExhibitSpec{slide_id,claim_id,visual_job,visual_type,data_schema,provenance,as_of,units,annotations,alternative_text,editability_expected,capability_status,renderer_execution_status,asset_receipt,blocked_reason}`.

## Evidence and failure handling
If numeric chart renderer is absent: `BLOCKED_NO_RENDERER` for required exhibits and explicit non-visual diagnostic fallback. If sources are incomplete, do not construct phantom curves, charts or hierarchies. A design mockup is not an emitted chart.

## Quality checks
- [ ] The exhibit proves/clarifies the headline.
- [ ] Numeric graphics have deterministic source/units/as-of.
- [ ] Interaction/editability verified rather than implied.
- [ ] Source, uncertainty, license and alternative text preserved.
