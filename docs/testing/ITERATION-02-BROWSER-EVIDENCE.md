# Iteration 02 — Browser / Site MCP-to-client evidence intake

Scope: #251, #253, #254; route-only Site test #149. Source contract only.
Script: `scripts/eval/iteration02_browser_evidence.py`.

## Inputs

Provide the **original unexecuted** external handoff `external-lock.json`
for the same candidate, a JSON array of per-attempt observations and a separate
directory holding exact tool trace, selected tool response, client observation
and client screenshot. Chart scenarios additionally need the render artifact.

Each observation has these fields:

- `case_id`, `attempt`, `channel` (`site` or `browser`), exact
  `source_revision`, `release_id`, `payload_content_sha256`,
  `input_sha256`, `rubric_sha256` from the unmodified external lock.
- `execution_state: executed`, `decision: REVIEW_REQUIRED`, timezone-aware
  `observed_at`, `observation_source`, `approval_reference`, distinct
  `executor` and `evaluator`, and a stable `correlation_id`.
- `trace`, `client`, `capture`, `tool_output`: each an object containing
  `path` relative to the evidence root and exact `sha256` digest.
- For chart cases `I02-251-browser-mcp`, `I02-253-parity` and
  `I02-254-charts`, an additional `chart` artifact path/SHA-256 is mandatory.

The tool trace is a JSON object repeating locked case/attempt/source/release/
payload/input and correlation IDs, plus nonempty `tool_calls` with unique
`id`, `tool_name`, `execution_state: executed` and `output_sha256`.
The selected tool call must correspond to the actual saved `tool_output` bytes.
Chart calls additionally contain `chart_payload_sha256` and
`normalized_data_sha256`. The saved chart PNG hash and client observation
must agree with both digests. Normalized data is produced by the independent
test runner; the validator does not calculate it from pixels.

The client JSON repeats the same locked identifiers and correlation ID, with
`observed_tool_call_id`, `client_display_state: observed` and nonempty
`accessible_text`. A saved PNG `capture` is mandatory even for route-only
Site cases. Merely storing a file whose header resembles PNG is **not proof
that a human actually saw the correct chart**.

## Example command

~~~bash
python scripts/eval/iteration02_browser_evidence.py \
  --external-lock ./external-handoff/external-lock.json \
  --observations ./observations.json \
  --evidence-root ./recorded-browser-evidence \
  --output ./browser-structural-review.json
~~~

## Decision boundary

- `INVALID_EVIDENCE` rejects missing, tampered, stale, mismatched, or unsafe
  artifacts, including symlink/path traversal, absent client capture,
  duplicate tool IDs, missing execution steps, and wrong normalized chart data.
- `NO_EXECUTION_EVIDENCE` means no observations; **not FAIL/PASS**.
- `STRUCTURAL_EVIDENCE_REVIEW_REQUIRED` verifies only the integrity and
  cross-references of **caller-supplied** files, not their authenticity.

Independent assessor must compare the original provider tool log,
accessible client/UI rendering, actual chart labels and values, claimed
authorization, execution state and normalized data against the frozen rubric.
Do not promote to runtime PASS, mark an Issue Done, or publish to Site based
on this structural validator. TEST fixtures in source CI are synthetic only.
