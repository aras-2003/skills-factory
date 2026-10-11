# Report OS — Document Semantic Model and Receipt (draft)

Cross-domain source rules: [Analysis → Artifact Contract](../../../docs/architecture/content-to-artifact-contract.md). These are model semantics, **not** a provider API or an assertion that Canva, Docs, Word or PDF connectors support every operation.

## Brief
`ReportBrief{brief_id,objective,audience,reader_task,decision_or_learning_outcome,scope,horizon,profile,reading_mode{DEEP_READ|EXECUTIVE_LEAVE_BEHIND|TECHNICAL_REFERENCE|WHITE_PAPER},language,length_guidance?,source_constraints,brand?,confidentiality,requested_formats[],editability_required,permissions,assumptions[],readiness}`.

## Sections and citations
`ReportModel{report_id,source_result_refs[],source_revision?,title,thesis?,method,executive_summary,sections:[{section_id,heading,level,purpose,reader_question,claim_ids[],source_finding_ids[],source_option_ids[],narrative_blocks[],table_ids[],exhibit_ids[],notes[],crossref_ids[],appendix?}],references:[{citation_id,source_locator,as_of?,license?}],figures[],tables[],annexes[],styles,revision_history[]}`.

Every factual claim is traceable to `DomainResult` or explicitly labeled user-provided, hypothesis, derived, disputed or unknown. Output must not silently revise a domain choice. Crossref/TOC generation must be real, not purely decorative.

## Artifacts and quality
`DocumentReceipt{run_id,source_revision,workflow_version,provider,capability_preflight,domain_validation_state,artifact_id?,native_docx_path_or_url?,google_docs_url?,pdf_path_or_url?,creation_receipts[],render_page_receipts[],export_receipts[],page_count?,pdf_page_count?,editability_observed,fonts,TOC_checks,link_checks,content_parity_checks,figure_manifest,review_findings[],fix_history[],client_display_state,delivery_status}`.

`ReviewFinding{finding_id,source_section_id,page_number?,severity{CRITICAL|MAJOR|MINOR},dimension{CONTENT|EVIDENCE|METHOD|STYLE|LAYOUT|EXPORT|RIGHTS},observed_evidence,remedy,owner,verification,closed}`.

**Do not conflate states**:
- `SOURCE_DOMAIN_VALIDATED` is an upstream domain assertion with its own receipt, not a byproduct of document polish.
- `DOCUMENT_MODEL_READY` means a semantic model exists, not an exported document.
- `DOCX_CREATED`, `DOCX_EDITABILITY_CHECKED`, `PAGES_RENDERED`, `LAYOUT_QA`, `PDF_CREATED`, `DOCX_PDF_PARITY`, `CLIENT_DISPLAY_OBSERVED` are independent observations.
- States per check: `NOT_RUN|PASS|FAIL|BLOCKED|UNVERIFIED`; an unavailable provider is `BLOCKED` rather than fictional success. The client's UI is `NOT_OBSERVABLE` unless independently observed.

## Reuse and compatibility
Report composer may provide its existing `sections, narrative, evidence, implication, visual_slots` semantics; long-document adapters add explicit heading hierarchy, pagination, bibliography and native output receipts. Presentation OS may consume the **same** source result independently, but does not use the paginated report as a required intermediary or automatically re-run the analysis.
