---
name: report-document-authoring
description: >
  Turn an approved long-form report model into a real editable and professionally typeset DOCX, Google Doc or paginated PDF using available document tools. Use when an external report document with headings, citations, figures and page layout is explicitly requested; do not claim exported files from chat prose or create presentation slides.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: draft
  risk: medium
  last_reviewed: "2026-10-10"
---

# Report Document Authoring

## Purpose
Own the **execution and fidelity of actual external document production**, not research, domain recommendations, or the logic of an analytical report. Never pretend tool availability, export success, page rendering or font/editability parity.

## Preconditions
A coherent `ReportModel` with sections/IDs, supported content, source citations, figures/tables (or explicit placeholders), target format(s), confidentiality and approved external transfer policy.

## Procedure
1. Inspect **current callable** authoring and file capabilities, not installed brand names: DOCX create/edit/save, Google Docs create/batch edit, PDF conversion/export, page rendering, DOCX re-open, document style system and source file access. Record `AVAILABLE|UNAVAILABLE|UNKNOWN` per action and requested target; no phantom APIs.
2. Select lowest-friction verified provider compatible with actual requested file and privacy. A Canva integration can make designs but does not itself prove native DOCX/PDF report production. If critical format is unsupported, return `BLOCKED_TARGET_FORMAT` with a verified alternative; do not silently replace editable Word with raster PDF or plain text.
3. Build/consume `DocumentLayoutSpec`: trim/page size, margins, heading scale, body typography, line spacing, controlled color, caption/footnote style, table behavior, page numbers/header/footer, TOC, references, links and accessibility. Template assets/fonts must be licensed and available; no private font redistribution.
4. Write content with actual headings, consistent styles and unique anchors/bookmarks where supported. Embed text as editable document content; avoid full-page image replacements. Use real table/chart/diagram assets supported by tool, preserve numeric data units, date and sources. If a font/feature is unavailable, record it and use a safe fallback.
5. Author a navigable table of contents only where supported by the actual engine; do not assert automatic refresh or cross-reference behavior without checking it. Citations, URLs, footnotes and bibliography must correspond to real sources. Warn where a feature cannot be implemented natively.
6. Perform actual create/save action and retain returned file path/ID/URL and provider receipts. A markdown plan, canvas snapshot or dummy filename does **not** satisfy `DOCX_CREATED` or `PDF_CREATED`.
7. If PDF is requested, execute actual export or conversion from the authored document and store the output receipt; do not assume PDF rendering looks like Word or preserves editability.
8. Route artifacts to `report-document-review` for rendered per-page QA, content/page/links checks and DOCX/PDF comparison. Revise only observed defects and regenerate/recheck affected outputs; authoring does not self-certify review.
9. Return true artifact addresses, capabilities and gaps. Do not report a delivered file if it is absent from verified output or inaccessible to the user.

## Decision rules
- File format follows the user, not a preferred tool. Google Docs is optional and user-directed; PDF can be view-only by nature, while editability requirements call for DOCX/native document.
- A missing visual renderer is recorded separately; a table substitute cannot satisfy a specifically required chart unless the user accepts changed scope.
- Do not send confidential source text to an external provider without authorization. Do not publish, invite recipients or share publicly unless separately requested.

## Inputs
`ReportModel, DocumentLayoutSpec?, target_formats[], editing_requirements, provider_preferences?, permissions, supported_media[], source_licenses`.

## Output contract
`DocumentAuthoringReceipt{report_id,source_revision,provider,capabilities,format_statuses,docx_id_or_path?,google_doc_url?,pdf_id_or_path?,creation_receipts[],export_receipts[],layout_spec,embedded_media_manifest,known_feature_losses[],review_required}`.
States `NOT_RUN|PASS|FAIL|BLOCKED|UNVERIFIED` per format. No final publication PASS from source-only artifacts.

## Evidence and failure
Record exact missing tool/capability and whether attempt occurred. When a target cannot be written, disclose blockage and keep compatible semantic material for another provider; do not invent download URLs. Export conversion and actual user/client display require distinct receipts.

## Quality checks
- [ ] Real native document creation with content and editability checked separately.
- [ ] Real PDF export/round trip where requested; no automatic parity claim.
- [ ] Sources/rights, style hierarchy and figures mapped to semantic report.
- [ ] Actual output sent to page-level QA, not released based on authoring alone.
