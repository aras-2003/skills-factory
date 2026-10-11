# Report OS — long-form document production (candidate source)

**Status:** proposed / draft. No installed package, authoring tool or runtime creation/export validation is implied by these source files.

Report OS produces deliberate **long-form, editable and paginated** analytical documents when requested. It does **not** redo substantive Strategy/OAF/Commerce/Investing work, override source conclusions or become a general research engine.

| Component | Scope | Boundary |
| --- | --- | --- |
| [report-document-architecture](report-document-architecture/SKILL.md) | Reading flow, hierarchy, chapters and evidence allocation | Not new subject analysis; not slide ghost deck |
| [report-document-authoring](report-document-authoring/SKILL.md) | Professional DOCX/Google Docs/PDF authoring under current verified connector/tool capabilities | Not chat-native report composition; no phantom file |
| [report-document-review](report-document-review/SKILL.md) | Independent content/page-level/layout/round-trip QA and targeted revision | Not Strategy domain approval; not unsupported tool receipts |

Workflow: [report-production](../../workflows/report-production/WORKFLOW.md). Shared contract: [Analysis → Artifacts](../../docs/architecture/content-to-artifact-contract.md).

**Reuse**: `report-composer` for semantic/report flow and chat reporting; `visual-output-design` for evidence-bound exhibits; source-domain analysis for the substance. We deliberately did **not** add a redundant report-brief skill, new global evidence validator, bespoke chart renderer or generic PDF writer to the initial candidate. Split further only if evaluated use cases establish distinct triggers and independent value.
