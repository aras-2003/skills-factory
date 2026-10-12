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
 "catalog_digest":"<64-hex>", "tool_schema_digest":"<64-hex>",
 "capabilities":["runtime_info","load_skill","render_bar_chart"],
 "flows":[{"flow":"routing","execution_state":"executed",
           "tool_trace_sha256":"<64-hex>", "semantic_result_sha256":"<64-hex>",
           "client_display_state":"not_applicable"}]}
```

Include **four flows** in each: `routing`, `architecture-review`,
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
