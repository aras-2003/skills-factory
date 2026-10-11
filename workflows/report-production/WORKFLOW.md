# Report Production — Evidence-backed Long-form Documents

## Purpose

Produce an **audience-specific, source-faithful, professionally authored long-form document** when the user explicitly requests a report file or an external editable/paginated document. This workflow owns orchestration; it delegates subject analysis, report semantics, exhibits and actual file actions.

## Source and scope

**Status:** DRAFT; intentionally **not registered** in the runtime registry. No model execution, DOCX/PDF generation, page inspection or release PASS is implied by the source definition.

Read `references/document-contract.md` and `references/quality-standard.md` as needed and the shared [cross-OS contract](../../docs/architecture/content-to-artifact-contract.md). Source of truth is the user's supplied materials or compatible, versioned domain output.

**Enter:** explicit DOCX, PDF, Google Docs, long-form document/report deliverable, comprehensive external study/white paper/architecture document. If user requests a substantial **report only in chat**, prefer existing `report-composer` without creating a file. Short memo → PRO-04/report-composer. Slides → presentation-production. Article/publication → Writing. A narrow question does not start a report production pipeline. Follow requested medium, depth and output rather than the mere keyword “report”.

## Stage 0 — Capability, scope and privacy preflight

Inspect actual available actions for sources/Drive, source retrieval, full-content editing, charts, native document creation, DOCX/PDF export, reopen, PDF page rendering and final downloadable artifact. Separately record Canva/Figma only for an explicit deck request; neither is required for Report OS. Canva account access is not evidence for document DOCX/PDF capabilities. Record `AVAILABLE|UNAVAILABLE|UNKNOWN` for each; no generic “integration installed” shortcut.

Assess source confidentiality, external upload rights, publication privileges, third-party graphics/license and document confidentiality. Before sending private material to external design providers, obtain appropriate authorization. Any requested essential unsupported export → `BLOCKED`, with a clearly verified alternative; do not call a text outline an artifact.

## Stage 1 — Intent and report brief

Extract: what; who reads; why; decision/understanding sought; domain; research method/standard; horizon/scope; expected length and depth; language; audience familiarity; delivery urgency; brand/styles; files/figures; editability; outputs; privacy. Infer already-known inputs. Ask only decision-changing missing questions (normally at most three), not a form by default. Do not invent a 30/50-page requirement. Profiles: board strategy, executive decision, market/competitor, architecture, transformation, due diligence, policy, technical research.

Gate B: `READY|ASSUMPTIONS_VISIBLE|BLOCKED_CRITICAL_CONTEXT`; intended reader outcome and file outputs are clear enough.

## Stage 2 — Domain analysis and evidence handoff (upstream-owned)

Use existing compatible domain `DomainResult` with finding/option/evidence IDs, source revision/as-of, uncertainty and approval state. If **new analysis** is explicitly part of the request, delegate to the proper specialist, e.g. Strategy OS or OAF; Report OS must not assume these planned capabilities are installed. If available data are insufficient, request/perform only bounded research through appropriate domain/shared source-capable tools; do not create fictitious findings.

For a missing Strategy OS or contradictory material recommendation, report `DOMAIN_VALIDATION=NOT_RUN|BLOCKED` or `UPSTREAM_REVIEW_REQUIRED`, and mark a provisional document accordingly. Do not silently change approved options or elevate user claims to externally verified.

Gate E: all decision-material claims have traceable support/uncertainty; missing material data lead to a qualified report, targeted research, or a block.

## Stage 3 — Long-form argument and document architecture (`report-document-architecture`)

Select one reading mode from audience and usage, then design report `section_id, purpose, reader_question, key_claims, evidence_ids, exhibits, transitions, detail_level, annex_rule`. Reuse `report-composer`'s integrated narrative/evidence/implication semantics, but do not assume its chat profile is a Word/PDF layout. Draft a factual executive summary *from the supported full argument* (update it after substantive revisions). Include evidence methodology, counterarguments, assumptions and decision/action only when fit for the request. Distinguish internal paper vs externally circulated report.

Gate A: outline has no redundant chapters and every section contributes evidence, explanation or action. No manufactured length.

## Stage 4 — Evidence-linked drafting and exhibits

Draft sections maintaining IDs and one integrated report (not repeated summaries). Tie factual paragraphs, tables, visuals and recommendation to ledger entries. Preserve quote and license limits. Give charts to `visual-output-design` only with actual source data and render receipts. Use real table/chart/diagram primitives if supported; illustrative generated imagery never substitutes for quantitative evidence. Run contradictions and unit/date checks. Support notes/references/methodology/annexes where appropriate. No new external artifacts until user-requested output.

Gate D: unsupported causal claims, invented citations, unsupported numbers, confidentiality violations and undocumented exhibits block release.

## Stage 5 — Native production (`report-document-authoring`)

Execute with currently callable authoring provider(s): editable DOCX; Google Docs when supported/requested; PDF export via a documented rendering tool. Styles include page dimensions/margins, grid, typography, heading levels, tables/captions, footnotes/endnotes if supported, page numbers, links, accessibility and figure alt text. Keep a source-linked section manifest, distinguish an editable artifact from flattened PDF, and note provider-specific losses. Do not infer editability or file success from planned instructions.

Gate N: **actual created artifact** with exact file path/URL and tool receipt for each requested medium, or `BLOCKED`. An ordinary chat reply is not a generated document.

## Stage 6 — Independent report review and repair (`report-document-review`)

Review two dimensions separately:
- **Analytical/editorial fidelity:** source mapping, method and counterargument, audience needs, recommendation/approval status, consistent terminology, clear argument, appropriate executive summary, no fabricated data/citations.
- **Layout/production:** actual rendered pages with montage **and every page inspected** (focus additionally on dense tables/footnotes/appendices), headings/TOC, page numbering, widow/orphan, split tables, clipping, font substitution, references, image quality, contrast, links and alt text.

Record defects by section/page and severity `CRITICAL|MAJOR|MINOR` with evidence, fix and retest instructions. Fix the smallest responsible component and re-render changed pages plus affected content/TOC neighbors. Two targeted review rounds by default; if a major unresolved issue remains, `REVIEW_REQUIRED`, never cosmetic averaging into PASS. Independent reviewer/model may contribute only with observed receipt.

## Stage 7 — Export and round-trip verification

Open/render requested **DOCX** and **PDF** (and Google Docs if used) with supported tools; check page content and source citations, table/figure placement, bookmarks/links, crossrefs/TOC, page count and font behavior. Compare source draft to native document and exported PDF, recording editability and actual differences. PDF viewability is not proof DOCX structural editability. User-visible claims about final document are permitted only with matching creation/render/export evidence.

Track `DOCX_CREATED, DOCX_EDITABILITY_CHECKED, PAGES_RENDERED, EDITORIAL_QA, LAYOUT_QA, PDF_CREATED, DOCX_PDF_PARITY, CLIENT_DISPLAY_OBSERVED` **separately**, using `NOT_RUN|PASS|FAIL|BLOCKED|UNVERIFIED`. A blocked subcapability cannot be inferred from another PASS.

## Final output and stop

Provide precise output type, file link(s) only when actually created, report focus, source/assumption note, unverified parts and QA receipt. If requested file is unavailable, make that limitation explicit rather than silently substituting a chat report. Never publish/share externally unless separately authorized. Completion of the source definition does not equal production readiness; runtime and real document round-trip tests remain mandatory before registry/package promotion.
