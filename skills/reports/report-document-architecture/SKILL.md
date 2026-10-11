---
name: report-document-architecture
description: >
  Plan the section hierarchy and evidence-backed reading flow for a substantial written report or technical document before DOCX/PDF production. Use when a long-form analytical document needs a coherent chapter outline, section arguments, exhibits, appendix and citation plan; do not design slide storylines or redo domain research.
metadata:
  owner: arkadiusz-kamrowski
  version: "0.1.0"
  maturity: draft
  risk: medium
  last_reviewed: "2026-10-10"
---

# Report Document Architecture

## Purpose
Turn a sufficient report brief and a supplied/versioned evidence or domain result into a *reader-first document architecture* suitable for sustained reading. Own chapter/section hierarchy and argument allocation. Do not decide new strategy, validate an entire research domain, edit DOCX files or design presentation slides.

## Preconditions
- An audience/reader job, requested document medium or long-form intent, scope and acceptable level of detail.
- Supported claims or a domain/evidence pack with revision/as-of and uncertainty, or clearly identified gaps.
- Awareness of adjacent `report-composer` (chat-native semantic composition) and `presentation-storyline` (slides, not long documents).

## Procedure
1. State the reader's governing question and intended outcome. Distinguish decision record, comprehensive analysis, due diligence, technical reference and research paper. If a two-page brief is enough, return a shorter structure and do not inflate it.
2. Map existing `finding_id/claim_id/option_id` to the draft thesis and reader questions. Preserve status: proposed is not approved, user-provided is not independently verified.
3. Create a provisional chapter tree with `section_id, heading, purpose, reader_question, main_point, evidence_ids, suggested_exhibit_ids, method_or_limitation, detail_level, transitions`. Ensure siblings differ in purpose, not merely wording.
4. Select a structure deliberately: executive answer → decision rationale → alternatives → implementation; problem/method/findings/discussion; architecture context/options/trade-offs; or other context-specific progression. Never impose PESTEL/SWOT/TOWS unless the underlying analysis warrants it.
5. Decide which information belongs in body, sidebars, methodology, footnotes/bibliography and appendices. Provide a credible source plan for all material figures and quotations; missing sources remain visibly marked.
6. Plan charts, tables, decision matrices and diagrams as semantic `exhibit_spec` slots; delegate rendering to `visual-output-design` with supported data. No synthetic numbers for visual balance.
7. Draft a provisional executive summary *from* supported main findings and identified choices; revisit it after substantive drafting changes, never introduce unaudited recommendations.
8. Test the horizontal chapter reading flow and vertical support within key sections, including contradictions, missing alternatives, weakest evidence and readability at the requested length. Do not challenge/change upstream strategic decisions without an `UPSTREAM_REVIEW_REQUIRED` handoff.
9. Send a `ReportArchitecture` with gaps and gates to drafting/authoring. Do not assert file generation.

## Decision rules
- Outline changes are communication decisions; material recommendation changes require the source domain to adjudicate.
- Dense technical content can be correct for a reference document; forced brevity is not universally good.
- A missing analytic result is not an invitation to invent it; request/route missing research.
- Never route an explicit slide-deck request here unless a long-form report is *also* requested.

## Inputs
`ReportBrief`, compatible `DomainResult` or user-provided findings, source ledger, depth guidance, intended media and language.

## Output contract
`ReportArchitecture{reader_job,profile,source_result_refs[],provisional_thesis,chapter_tree:[{section_id,level,heading,reader_question,purpose,main_point,claim_ids[],finding_ids[],option_ids[],evidence_ids[],exhibit_specs[],reader_transition,detail_level,appendix_rule}],executive_summary_basis[],methodology_plan,citation_plan,unresolved_evidence_gaps[],upstream_challenges[],drafting_instructions}`.

## Evidence and failure
If substantive support is missing, describe missing evidence and permissible provisional structure, not validated findings. If a domain recommendation conflicts with new evidence, return `UPSTREAM_REVIEW_REQUIRED`, not a silently rewritten option. A source-only plan is not DOCX/PDF output.

## Quality checks
- [ ] The outline supports the actual reading/decision job, not a ritual table of contents.
- [ ] Material conclusions keep domain IDs, evidence, status and limitations.
- [ ] No duplicated report-composer/chat pipeline or slide ghost-deck logic.
- [ ] Long-form depth and exhibit placements are justified, not padded.
