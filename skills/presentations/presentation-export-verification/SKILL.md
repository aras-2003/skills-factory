---
name: presentation-export-verification
description: >
  Verify a presentation's actual rendered slides, delivery format, PowerPoint/PDF round-trip behavior, editability, fonts and animation limitations. Use when a deck exists and the user needs final deliverable QA; do not treat a planned export or tool invocation as successful delivery.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: draft
  risk: medium
  last_reviewed: "2026-10-09"
---

# Presentation Export Verification

## Purpose
Establish what was **actually** created, rendered, exported and checked. Be precise about native deck quality, PPTX/PDF parity and editability rather than making export promises.

## Preconditions
A real deck file ID or actual exported file; target delivery format and editing expectations; authoring and evidence receipts.

## Procedure
1. Confirm a real artifact identifier and requested target(s): Figma Slides, Canva native, PPTX, PDF or alternatives; inspect actual tools available for export, download, render/open and structural inspection.
2. Render all actual slides where supported (overview montage) and inspect the highest-risk ones individually: dense charts, tables, technical diagrams, complex fonts, animated/media elements, source notes and final ask. If render tool missing, record `RENDER_BLOCKED`, not PASS.
3. Run deterministic checks where available: slide count/order, off-slide objects/overlap, clipping, missing glyphs/fonts, links, contrast, source attribution, notes, chart labels, aspect ratios, image resolution and asset licensing.
4. If PPTX/PDF was requested, invoke **real exporter** and preserve `export_action,artifact_path_or_url,bytes_or_resource_id,source_id,time,tool_receipt`; if absent, use `EXPORT_UNAVAILABLE`. Do not treat an export settings screenshot as an exported file.
5. Reopen or independently render the exported artifact with suitable software/tool. Compare key layout regions against source deck; examine text/chart editability (not just image appearance), slide order, speaker notes, font substitutions, hyperlinks and media/animations.
6. Describe platform caveats as conditional checks: Figma Slides PPTX editable-or-flattened export modes, possible font replacement and static interactive elements; Canva PPTX may alter layout and may not preserve animation/video. Do not infer an individual file suffered a defect until observed.
7. Classify outcomes by target: `NATIVE_RENDER_VERIFIED | EXPORT_VERIFIED | EXPORT_PARITY_WARNING | BLOCKED_NO_EXPORTER | BLOCKED_NO_REOPEN | FAIL_RENDER | FAIL_EXPORT | NOT_RUN`. Retain provenance/source identity and artifact links.
8. Send observed fixes to authoring and review; rerender and reverify until critical/major defects are resolved or delivery is explicitly conditional. Never alter facts to fit a layout.
9. Produce a delivery note separating passed assertions, unverified features and known losses, plus a concise source/rights statement.

## Decision rules
- A native editable Figma file is not proof of an editable PPTX. A PPTX screenshot is not proof of native editability.
- Do not advertise animations, interactive controls or notes as present in PPTX without checking the exported format.
- No client-display success claim without observable evidence from that client surface; returned payload and displayed output are different states.

## Inputs
Deck ID/URL or artifact file, target formats, source images and evidence ledger, tool capabilities.

## Output contract
`Verification{native_deck,requested_exports,actions,render_receipts,export_receipts,roundtrip_receipts,editability_by_exhibit,parity_findings,limitations,delivery_links,overall_status}`.

## Evidence/uncertainty handling
A file URL alone may confirm a file exists but not that a slide layout is correct. When reopen is unavailable, mark round-trip unverified. Verify only requested formats.

## Quality checks
- [ ] Actual deck or export bytes/resource inspected.
- [ ] Requested editing behavior confirmed per object class.
- [ ] Actual export compared to native deck.
- [ ] No phantom download, visual, animation or client display.
