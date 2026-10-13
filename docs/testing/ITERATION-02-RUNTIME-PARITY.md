# Iteration 2 — Work Lab vs Site parity, source-only gate

This tool is a **read-only offline comparator**, not a web/browser/runner. It
covers ENG-14 #242, ENG-17 #247, E2E-01 #250 and E2E-04 #253 *partially*.
Never infer installed runtime capability from GitHub `main`, the catalog,
declared channel support or a successful build.

Collect **two independently observed, fresh receipts**, one from Work Lab and
one from the connected Site MCP, tied to the same candidate Lab source revision,
release ID and payload SHA-256. Adapt each provider's raw receipt into a normalized
JSON object with:

```json
{"attestation_status":"verified",
 "observed_at":"2026-10-13T00:00:00+02:00",
 "observation_source":"real provider tool output URL / immutable trace ID",
 "source_revision":"<40-hex>", "release_id":"<Lab release ID>",
 "payload_content_sha256":"<64-hex>",
 "catalog_digest":"<64-hex>", "tool_schema_digest":"sha256:<64-hex>",
 "capabilities":["runtime_info","load_skill","render_bar_chart"],
 "flows":[{"flow":"routing","execution_state":"executed",
           "tool_trace_sha256":"<64-hex>", "semantic_result_sha256":"<64-hex>",
           "client_display_state":"not_applicable"}]}
```

A tool schema digest with the public `sha256:` prefix or raw 64-hex form is accepted and normalized. Never accept another algorithm or infer actual capability from a source-only catalog.\n\nInclude **four flows** in each: `routing`, `architecture-review`,
`bar-chart`, `line-chart`. Chart receipts require actual client-visible
observation; a returned SVG/PNG payload alone is insufficient. The
`semantic_result_sha256` must be constructed from the same normalized,
data-bound outcome for both surfaces (not a screenshot byte comparison). Keep
all originals and correlation IDs with the assessor, never put rubrics in the
executor context. Input assertions are not proof that an action occurred.

```bash
python scripts/eval/runtime_parity.py \
  --candidate-lab-release .tmp/lab/release-manifest.json \
  --work-observation work-observed.json \
  --site-observation site-observed.json \
  --output .tmp/runtime-parity-report.json
```

`BLOCKED` means missing identity, tool traces, chart display or malformed evidence.
`MISMATCH` means candidate identity, tool schema, catalog or representative flow
contract diverges. `MATCH_PENDING_INDEPENDENT_REVIEW` is **not PASS**: the input
observations may be unauthenticated; an independent reviewer must inspect raw
provider logs, tool receipts, caller/user interface and model traces. This
tool never edits external systems and never authorizes publishing.

The current Site release may lag GitHub main; in that case the correct result
is **MISMATCH**, not a fabricated cross-channel parity PASS.

## Runtime identity and source consistency (new source gate)

The local MCP `runtime_info` now rejects non-40-hex source revisions, non-SHA-256
tool schema digests and timestamps without timezone. It exposes
`attestation_basis: unsigned_runtime_environment_fields_only` and
`installation_behavior_verified: false`. A well-formed `attestation_status:
verified` is **not cryptographic proof** of provider deployment or an observed
behavioral trace. Site Worker attestation is a distinct provider-origin claim.

`scripts/catalog/validate_runtime_registry_parity.py` checks all source
`WORKFLOW.md`, `SKILL.md`, `runtime-registry.yaml`,
`capability-contract.yaml` and `docs/catalog.json` without calling external
tools. Its best state is `SOURCE_PARITY_ONLY_REVIEW_REQUIRED`. A source-only
declaration does not grant network, credential, write or production permission.

`scripts/eval/r17_disposition.py` reads the immutable R17 transcript receipts,
checks their exact count/status and hashes, and emits the historical nine-FAIL
retest queue. R17's 36/9 summary is historical, not a new-version verdict;
Production-only exclusions remain separately blocked.
