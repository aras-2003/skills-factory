# Output policy router (OUT-02) — source-only candidate

This is a **small deterministic planner** for a semantic intent already classified by a host model, user, or higher-level workflow. It does **not** parse a natural-language request, execute a domain OS, author files, create GitHub/Canva/Docs content or certify an artifact.

## Source ownership
Strategy/OAF/Investing/Commerce etc. own the analytical result and approval. Report OS, Presentation OS, Interactive Experience OS and possible future spreadsheet adapter consume the **same immutable source result revision** and perform medium-specific communication/review.

Related: [OUT-01](https://github.com/aras-2003/skills-factory/issues/297) (cross-OS handoff), [OUT-02](https://github.com/aras-2003/skills-factory/issues/298) (this policy), [OUT-03](https://github.com/aras-2003/skills-factory/issues/299) (quality), [OUT-04](https://github.com/aras-2003/skills-factory/issues/300) (lifecycle), [SHEET-01](https://github.com/aras-2003/skills-factory/issues/301) (P2 discovery/P3 optional).

## Input contract (v0.1)

Supply JSON to `python -m scripts.output.route` on stdin. Here is a **planning example only** (capability states must reflect observed target-specific tooling, not marketplace or connection status):

```json
{
  "request_kind": "RENDER_EXISTING",
  "semantic_resolution": "RESOLVED",
  "source_result": {
    "result_id": "oaf:2026-operating-model",
    "revision": "rev-1",
    "domain": "oaf"
  },
  "requested_outputs": [
    {"kind": "report", "format": "docx"},
    {"kind": "presentation", "format": "canva"},
    {"kind": "interactive_web", "format": "html"}
  ],
  "capabilities": {
    "report:docx": "AVAILABLE",
    "presentation:canva": "AVAILABLE",
    "interactive_web:html": "AVAILABLE"
  },
  "publish_requested": false,
  "publish_authorized": false
}
```

- `request_kind`: `ANALYZE_ONLY`, `RENDER_EXISTING`, `ANALYZE_THEN_RENDER`, `EDIT_EXISTING`. `EDIT_EXISTING` additionally requires an explicit `artifact_ref`.
- `semantic_resolution`: `RESOLVED` or `AMBIGUOUS`. On ambiguity **ask a user question**, not guess by string matches.
- `requested_outputs`: explicit `kind`/`format` pairs, preserving order; duplicates removed. Chat-only analysis with no requested file produces only `chat:text`. When the user explicitly asks for both DOCX/PDF it returns two format entries, but the same content-domain report owner.
- `source_result`: stable `result_id, revision, domain` only. The eventual OUT-01 contract expands this to claims/evidence/option IDs; this v0.1 implementation does **not** validate source authenticity or domain correctness.
- `analysis_state` when source missing: `NOT_STARTED|IN_PROGRESS|UNAVAILABLE|UNKNOWN`. No implicit domain execution. Incomplete source → `WAITING_FOR_SOURCE/UPSTREAM` or `BLOCKED_UPSTREAM`.
- `capabilities` keys `kind:format` for create/export and `edit:kind:format` for `EDIT_EXISTING`, values `AVAILABLE|UNAVAILABLE|UNKNOWN`. No key = `UNKNOWN`. **Generation/read/export capability does not establish edit capability.** `AVAILABLE` means the specific operation is available, **not** that a deliverable was created or delivered.
- Spreadsheet: deliberately `DEFERRED_PRODUCT` despite any generic XLSX connector capability. P2 discovery / P3 optional.
- Hosted web: separately requires `publish_requested=true` and `publish_authorized=true`, and **still** returns a plan only. No deployment is executed.

## Output contract and state boundaries

`PLANNED` means policy outcome only, not runtime success. Each delegation has its own `route_state`, `execution_state=NOT_RUN` and `delivery_state=NOT_RUN`; no cross-format PASS inheritance.

| State | Meaning |
| --- | --- |
| READY_TO_DELEGATE | Sufficient policy prerequisites to attempt target specialist; no execution implied |
| WAITING_FOR_SOURCE | User asked to render an existing analysis pack, but no revision was provided |
| WAITING_UPSTREAM | Requested domain analysis has not completed |
| BLOCKED_UPSTREAM | Required source-domain capability/analysis unavailable or unknown |
| BLOCKED_CAPABILITY | Required concrete format operation is unavailable |
| UNVERIFIED_CAPABILITY | Tool state was not confirmed; availability cannot be presumed |
| DEFERRED_PRODUCT | Spreadsheet OS not implemented or authorized yet |
| BLOCKED_PUBLICATION_APPROVAL | Hosted website needs separate explicit permission |

Do not declare `DOCX_CREATED`, `PPTX_EXPORTED`, `WEB_RENDERED` or `PASS` from this script output. Even if a Canva account can be searched, that does not prove it can export PPTX. Follow the target OS's own preflight, construction, source integrity, native QA and export receipts.

## Validation and limitations

```bash
python -m unittest discover -s scripts/output/tests -p 'test_*.py'
```

This is **only a deterministic policy layer**: no model natural-routing E2E, no source pack authenticity check, no editor/browser runtime integration and no built artifact. New candidate E2E must be version-pinned and tested separately from frozen historical R18 sources.

The design intentionally avoids creating a new skill or runtime registry entry until the model-specific `Output Router` skill contract/near-miss tests have passed a dedicated review. The already existing `report-composer` and `visual-output-design` remain authoritative for chat reports and individual visuals.
