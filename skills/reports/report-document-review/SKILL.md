---
name: report-document-review
description: >
  Critique and verify actual long-form DOCX/PDF report artifacts page by page for content fidelity, citations, style, pagination, tables, links, editability and export parity. Use for quality review or regression checks of generated written documents; do not replace Strategy/OAF analysis reviews or certify a report without rendered pages.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: draft
  risk: medium
  last_reviewed: "2026-10-10"
---

# Report Document Review

## Purpose
Independently identify fixable defects in the **written document and its real rendered artifact**, preserving domain source truth. This is not Strategy quality certification, report writing, or a slide-review skill.

## Preconditions
A report brief, semantic `ReportModel` with sources/IDs, authoring receipt, and actual native artifact/export or an explicitly limited draft. When page-render capability is absent, the review may check text logic but must label layout `NOT_RUN/BLOCKED`.

## Procedure
1. Verify artifact provenance: actual created DOCX/Google Doc/PDF IDs, creator/tool, source revision, requested outputs and privacy constraints. Reject hypothetical paths, mock links and model-only assertions as proof.
2. Compare `source_finding_id/claim_id/option_id` and statuses to paragraphs, exhibits and executive summary. Ensure recommendations are not strengthened, financial values have units/as-of, causal implications are supported, sources exist and contradiction/unknown notes survive.
3. Review writing: stated reader task met, sensible chapter progression, correct level of detail, repeat/contradiction control, consistent terminology, methodology, references and concise, source-faithful executive summary. Missing substantive domain validation stays `DOMAIN_VALIDATION=NOT_RUN/BLOCKED` rather than passing because prose reads well.
4. Inspect **all actual rendered pages** (montage plus per-page view/inspection). Check headings, TOC, crossrefs, caption/source linkage, page numbers, page breaks, footnote placement, tables across pages, clipping/overflow, widow/orphan headings, font substitution, legibility, color contrast, images, alt text and link targets. Record specific pages and visual evidence. Do not invent a page inspection when only body text is available.
5. For multiple requested formats, reopen each and compare paragraph/figure/order/caption and page/navigation parity. PDF does not prove DOCX content editability. Note known differences/feature losses explicitly; no blanket equivalence.
6. Record `ReviewFinding{finding_id,section_id,page_number?,severity,dimension,observation,source_ref?,correction,owner,retest_rule}`; classify `CRITICAL` for invented decisive claims/private leakage/missing requested artifact; `MAJOR` for unsupported key assertions, broken tables, unreadable text, wrong format, invalid TOC/links. Minor cosmetics are lower priority.
7. Delegate targeted repairs to authoring for layout, architecture for chapter/flow, source specialist for underlying decision/evidence, visual-output-design for deterministic exhibit. Keep source data/approval state immutable without domain adjudication.
8. Inspect revised affected pages **and** downstream pagination/TOC/figure references, not merely the modified sentence. Default up to two review cycles; persistent material issue is `REVIEW_REQUIRED` or `BLOCKED`, no numeric score can hide it.
9. Report independently: analytical fidelity, editorial quality, actual page review, DOCX editability, PDF creation/parity, unresolved defects and reader-display observation. No PASS from tests that were not actually run.

## Decision rules
- A complete semantic outline is not a finished report or actual page QA.
- Presentation screenshots cannot substitute for Word/PDF page layout inspection.
- Domain conclusions are owned upstream. Critical contradiction must return to Strategy/OAF/etc as `UPSTREAM_REVIEW_REQUIRED`.
- Privacy and licensed-asset defects block publication, regardless of design quality.

## Inputs
`ReportBrief, ReportModel, DomainResult?, DocumentAuthoringReceipt, source_registry, rendered_pages?, exported_formats?`.

## Output contract
`ReportReview{source_revision,artifact_refs[],domain_validation_state,editorial_state,page_render_state,format_states[],findings[],required_fixes[],rerun_targets[],verified_fixes[],remaining_risks[],final_state{APPROVED_FOR_DELIVERY|REVIEW_REQUIRED|BLOCKED|NOT_RUN}}`.

## Evidence and uncertainty
Required `PASS` evidence includes page renders, citations mapped to original sources and format receipts as relevant. If those are missing or an inspection tool was not available, report `BLOCKED`/ `NOT_RUN` with reason; do not imply the user can open the exported artifact without verifying it.

## Quality checks
- [ ] No final recommendation drift relative to source-domain pack.
- [ ] Observed page-level defects are page/section-specific and actionable.
- [ ] Real export and structural editability checks are distinguished.
- [ ] Retests cover reflow/regressions and unresolved majors block release.
