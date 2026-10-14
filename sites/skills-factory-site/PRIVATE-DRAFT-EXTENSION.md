# Private MCP draft extension

User-authorized private runtime testing adds 10 Presentation/Report draft skills and 2 draft workflow entrypoints to the unchanged official Lab 0.34.0 artifact (70 entries). Combined catalog: 82 entries. Production plugin membership and maturity are unchanged.

The explicit allowlist is `scripts/draft-components.json`. Source is the clean pinned GitHub main revision `9b457bd68bcd9ff00aece141dbf7f0864b88a723`. The generator rejects a different revision, modified tracked files, untracked inputs, duplicate names, non-draft skills and test/eval paths. It embeds only named instruction files, named workflow support contracts and the shared content-to-artifact contract; tests and evaluator rubrics are excluded.

Workflow entrypoints are generated wrappers pointing to `references/WORKFLOW.md`, with draft maturity and version 0.1.0. Repository-relative support links are rewritten to the embedded reference keys. All Presentation draft entries include the Canva connector contract; all extension entries include domain quality and shared artifact contracts. Embedding instructions does not supply authoring/export connectors or grant upload permissions.

Regeneration uses the existing validated Lab artifact, its unchanged ZIP and the pinned source checkout:

```text
python scripts/sync-lab-catalog.py <lab-artifact> <lab-zip> <clean-pinned-source>
```

`runtime_info` reports `lab_release` (70 original entries), `draft_extension` (12 names, source file hashes and NOT_RUN behavior status) and `runtime_release` (82 entries and combined catalog digest). `list_skills` returns the combined catalog with both provenance sections. Its `artifact_sha256` still identifies the original Lab ZIP; `artifact_scope: base_lab_only` makes that explicit. Extension hashes bind the host-loadable instruction/reference surface. `load_skill` keeps the source revision and explicit draft maturity.

Validation before publication: TypeScript, MCP contract suite, instruction/content hash consistency, supporting reference closure and exclusion of evaluator material. After publication: native deployment success, exact Site identity and all 82 live loads. Model behavior, native authoring, PDF/PPTX/DOCX round trips, page/slide rendering and quality benchmarks still need a separate campaign with actually callable providers, source materials and export/render tools. Missing required capabilities must produce a specific BLOCKED result; technical loader checks do not establish production readiness.
