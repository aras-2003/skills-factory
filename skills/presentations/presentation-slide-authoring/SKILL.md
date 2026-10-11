---
name: presentation-slide-authoring
description: >
  Create or revise an editable presentation in a supported Figma Slides or Canva runtime from a validated storyboard and exhibit plan. Use when a user requests actual native slides or deck edits; do not claim a deck exists from specifications, images or unsupported connector actions.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: draft
  risk: medium
  last_reviewed: "2026-10-09"
---

# Presentation Slide Authoring

## Purpose
Turn an approved semantic story and evidence-backed exhibit plan into a native **editable** presentation, subject to the actual capabilities of the user's connected destination. This is not the strategy/evidence/QA authority.

## Preconditions
A sufficient presentation brief; ghost deck with slide IDs/headlines; evidence ledger for material claims; visual/exhibit specs; brand and privacy constraints; user requested an external deck.

## Procedure
1. **Destination preflight** before creating files. Inspect actual connected tools/API actions and permissions for Figma Slides or Canva; verify create/edit capability for this session, asset upload permissions and supported rich-text/shape/chart operations. Figma `create_new_file(editorType="slides")` and `use_figma` may be available in connected runtimes, but do not assume use_figma features in Slides are identical to Design. Canva generation requires actually callable design creation, not marketplace presence alone. A successful Canva account read (`search_designs`) does **not** establish creation/editing/export. For Canva provider-specific rules and approvals use `workflows/presentation-production/references/canva-connector-contract.md` (repo-root path).
2. Select the requested destination; without explicit selection recommend the best currently callable tool given editable requirement, analytic vs creative deck, animation, brand assets and export target. Report meaningful trade-offs.
3. Build a semantic slide model first: `id,role,headline,body,source_ids,exhibits,layout,notes,alternative_text,transition`. Bind every element to its slide, claim and source where applicable.
4. Define minimal repeatable design tokens: aspect ratio (16:9 by default), grid, typography scale, restrained accent palette, text contrast, spacing, chart colors, source line, footer and slide number. Use licensed user-approved branding; do not copy proprietary consultancy templates/logos.
5. Vary layouts by information structure (hero, claim+exhibit, comparison, split, matrix, timeline, architecture, appendix). For live presentation, optimize distance/pace; for leave-behind, prioritize complete independent comprehension while retaining legibility.
6. For Canva: `create_design` returns an async generation job; obtain a completed design ID/link before claiming a native deck. For Canva revision transactions: preview actual changes and obtain **explicit user approval before commit**, do not claim uncommitted edits saved. Current Canva connector may not expose a PPTX export action; preflight export separately. For Figma use only documented callable Slides functions. Create native deck and editable objects through **documented connected actions**. Use real sourced charts or reproducible native equivalents; insert generated illustrations only as illustrations. Embed citation/provenance where appropriate. Keep content separated from layout so revisions don't silently change analytical claims.
7. Add useful speaker notes when supported; avoid unnecessary animation. Do not treat video or raster assets as editable shapes, or treat a rendered preview as native deliverable.
8. Collect `file_url, file_id, platform, tool actions, created slide IDs, editability checks, tool/renderer receipts`. Only report `DECK_CREATED` after actual tool success and a readable artifact identifier; otherwise `BLOCKED_DESTINATION` or `AUTHORING_FAILED`.
9. Send actual deck to `presentation-deck-review` and `presentation-export-verification` if requested; implement targeted fixes from review. Do not autonomously distribute/share/publish.

## Decision rules
- Default to full native objects when supported, with explicit `EDITABLE_NATIVE / EDITABLE_PARTIAL / FLATTENED / UNKNOWN` per exhibit.
- Quantitative exhibits must remain linked to deterministic inputs, not generated in artistic image tools.
- A tool's unsupported command must not be simulated or asserted; offer a verified alternate route if useful.
- If confidentiality or rights are unclear, do not upload private content to an external design service until appropriately authorized.

## Inputs
Brief, storyline, evidence ledger, exhibits, target design system, user authoring preference, allowed assets/licenses.

## Output contract
`AuthoringResult{platform,capability_preflight,design_tokens,deck_id,url,slides[],receipts,unresolved_layouts,asset_manifest,editability,created_status,blocked_reason}`.
`created_status = DECK_CREATED | AUTHORING_FAILED | BLOCKED_DESTINATION`.

## Evidence/uncertainty
Track source IDs and source dates on individual claims; distinguish live Figma/Canva evidence from marketing capabilities or planned calls. Keep `client_display_status=NOT_OBSERVABLE` unless actually inspected by a capable tool or evaluator.

## Quality checks
- [ ] Actual file creation/editing actions succeeded.
- [ ] Native slide element editability not inferred from picture quality.
- [ ] Consistent grid/hierarchy, diverse claim-fit layouts.
- [ ] No confidential externalization without permission.
- [ ] Canva read/auth, async create completion, explicit edit-save approval and PPTX/PDF export are separate verified capabilities.
