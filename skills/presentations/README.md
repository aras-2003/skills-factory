# Presentation OS — draft candidate domain

**Status:** source-only candidate design, created for [PRES-01 #283](https://github.com/aras-2003/skills-factory/issues/283). Not registered in `workflows/runtime-registry.yaml`, not packaged or production-ready. There is no runtime model/connector/export PASS from file creation.

Seven narrowly routed skills:
- `presentation-brief` — brief sufficiency, audience and requested action.
- `presentation-storyline` — argument, flow and action-title ghost deck.
- `presentation-evidence-review` — sources, numeric integrity, contradictions and permissions.
- `presentation-exhibit-design` — evidence-faithful chart/diagram specifications; reuses existing `visual-output-design`.
- `presentation-slide-authoring` — Figma/Canva connected authoring preflight, editable native deck.
- `presentation-deck-review` — skeptical consultant/editorial and visual QC; targeted repair loop.
- `presentation-export-verification` — actual render, PPTX/PDF parity, editability, animation/notes limitations.

Orchestration: [presentation-production](../../workflows/presentation-production/WORKFLOW.md).

**Integration with planned Strategy OS:** Strategy owns strategic evidence, alternatives, recommended choices and approval status; Presentation owns audience-specific story, design and native delivery. Handoffs follow STR-16 proposal, preserve finding/option IDs and must be validated against its eventual released schema. STR-12–STR-15 supply semantic analysis/report profiles, not deck rendering. STR-17 measures Strategy quality independently of Presentation OS deck benchmarks. When Strategy workflows are not actually available in the runtime, report that missing capability instead of substituting presentation persuasion for strategy development.

Delivery checklist to move from draft to candidate/production:
1. Run repo structural/static + global routing/collision/security checks.
2. Validate cases individually and end-to-end against no-skill and vendor-generic baselines.
3. Implement + verify Figma Slides adapter with actual native edit receipts; Canva adapter only after connected app verified.
4. Use live render/inspection and PPTX round-trip receipts; record skipped/blocked separately.
5. Review release readiness against pinned revision. No promotion by assumption.

Do not duplicate `report-composer` or `visual-output-design` ownership; only Presentation OS orchestrates entire deck and artifact lifecycle.
