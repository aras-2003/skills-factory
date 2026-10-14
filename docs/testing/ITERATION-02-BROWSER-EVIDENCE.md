# Iteration 02 — Chat browser chart evidence binder (#251, #253, #254)

This is a **read-only offline evidence checker**. It does not open a browser,
invoke MCP, test private users, capture images or certify client display.

## Protocol

Use exact `external-lock.json` from the Iteration 2 external handoff artifact,
plus an independent TEST client capture object. Its `case_id` must be one of
`I02-251-browser-mcp`, `I02-253-parity`, or `I02-254-charts`. The capture
contains the exact locked source/release/payload/input digest, fresh UTC or
offset-aware timestamp, installed identity observation reference, chat
reference and capture source. All data must be synthetic/approved.

For each chart observation store three separate immutable *source files*
inside an evidence root: raw MCP tool receipt JSON, screenshot PNG, and
captured accessible/semantic chart JSON. Capture `tool_receipt_sha256`,
`screenshot_sha256` and `accessibility_sha256` over original file bytes.
Connect chart-tool and client records with a nonempty correlation ID in
`correlation_id`, `tool_call_correlation_id`, and
`client_capture_correlation_id` — all three must agree. The tool receipt
itself will normally report `client_display_state: not_observable`; only
the client capture can independently report an observed display.

Example capture shape (values are illustrative, not a real executed test):

~~~json
{
  "case_id": "I02-254-charts",
  "source_revision": "<40-hex>",
  "release_id": "<exact Lab release>",
  "payload_content_sha256": "<64-hex>",
  "input_sha256": "<locked input SHA>",
  "installed_attestation": "verified",
  "installed_observation_reference": "<immutable TEST receipt URL/ID>",
  "capture_source": "<independent TEST browser observer>",
  "chat_reference": "<specific TEST chat URL/ID>",
  "captured_at": "2026-10-13T12:00:00Z",
  "chart_checks": [
    {"kind":"bar", "correlation_id":"bar-call-1",
     "tool_call_correlation_id":"bar-call-1",
     "client_capture_correlation_id":"bar-call-1",
     "client_display_state":"observed",
     "tool_receipt_path":"bar-tool.json",
     "tool_receipt_sha256":"<raw file SHA>",
     "screenshot_path":"bar.png",
     "screenshot_sha256":"<raw file SHA>",
     "accessibility_path":"bar-accessible.json",
     "accessibility_sha256":"<raw file SHA>",
     "expected_data":{"title":"Signed bar fixture",
                      "labels":["negative","zero","positive"],
                      "values":[-5,0,3]}},
    {"kind":"line", "correlation_id":"line-call-1",
     "tool_call_correlation_id":"line-call-1",
     "client_capture_correlation_id":"line-call-1",
     "client_display_state":"observed",
     "tool_receipt_path":"line-tool.json",
     "tool_receipt_sha256":"<raw file SHA>",
     "screenshot_path":"line.png",
     "screenshot_sha256":"<raw file SHA>",
     "accessibility_path":"line-accessible.json",
     "accessibility_sha256":"<raw file SHA>",
     "expected_data":{"title":"Signed line fixture",
                      "x_labels":["before","after"],
                      "series_names":["synthetic"],
                      "series_values":[[-2,0]]}}
  ]
}
~~~

Run only **after** real TEST browser capture:

~~~bash
python scripts/eval/iteration02_browser_evidence.py \
  --external-lock external-lock.json \
  --capture browser-capture.json \
  --evidence-root ./captured-files \
  --output browser-evidence-review.json
~~~

Output `BLOCKED_EVIDENCE` means evidence integrity/identity/values are
incomplete. `STRUCTURALLY_CORRELATED_INDEPENDENT_REVIEW_REQUIRED` is
**not** runtime PASS or a claim that the screenshot is authentic.
Independent reviewer must authenticate the raw provider trace,
capture tools, accessible tree, screenshot/client visibility and
correlation with the actual installed candidate.

For #254, both signed chart probes (bar [-5,0,3] and line [-2,0])
are required. This binder does not replace routing/child MCP evidence
for #251, or all four Work↔Site parity flows for #253.
Never use it as an unattended browser runner or production deployment gate.

## Route → child load evidence (I02-251 and I02-253)

An additional offline script, iteration02_route_evidence.py, correlates the
source-locked raw route_investment_request MCP receipt with the selected
load_skill child receipt and a shared independently recorded browser
correlation ID. Router must report workflow_execution_state=not_executed
and response_policy=load_child_workflow_then_follow; a load alone must
**never** be treated as completed child workflow/model behavior.

The capture JSON identifies exact case_id, source/release/payload/input
digests, chat_reference, installed_identity_reference, correlation_id,
router_correlation_id and child_correlation_id; router_raw_path and
child_raw_path reference separate JSON files, with matching raw SHA256.
Run with --external-lock, --capture, --evidence-root and --output.

ROUTE_AND_LOAD_STRUCTURALLY_LINKED_REVIEW_REQUIRED still requires a
separately authenticated TEST provider execution trace, observed final
answer, independent evaluator and the full Work↔Site parity suite. The
script only detects mismatches and never certifies actual child execution.

## Artifact-byte binding added for combined Iteration 2 candidate

Each `chart_checks` row must also carry `tool_output_path`,
`tool_output_sha256`, `chart_payload_path`, and `chart_payload_sha256`.
The raw `tool_output` is a JSON data object; the validator compares its
labels, signed numbers, series and title against both expected frozen
values in the capture and the accessible client observation.

`tool_receipt` must include the exact `release_id`, `payload_content_sha256`,
`correlation_id`, `output_sha256`, and `chart_payload_sha256`.
Those digests MUST match the actual saved tool-output JSON bytes and saved
PNG chart bytes; capture-level digests alone are not sufficient.

Substitute artifact files, missing chart PNGs, wrong tool-call correlation
or values changed on either tool/client side yield BLOCKED_EVIDENCE.
Source CI uses synthetic fixtures, not actual Chat UI or MCP traces.

**Still unverified:** a genuine tool-output receipt, screenshot visual
correctness, accessibility provenance, real installed runtime, and
independent evaluator signature. Structural matching is not behavioral PASS.

## Observed Site MCP SVG vs offline PNG evidence compatibility (2026-10-13)

Site MCP `render_bar_chart` was observed returning an **SVG artifact** and
an unsigned tool receipt with `artifact_state: rendered` and
`client_display_state: not_observable`. The source-only validator accepts
`chart_payload_format: svg` **or** `png`, with a matching `.svg`/`.png`
artifact path and SHA-256 of the **actual saved bytes**. SVG inputs are
parsed without external entity fetch; DTD, entity declarations, scripts,
foreignObject, event handlers, and linked external resources are rejected.
Chart **client screenshots still must be PNG** and must independently
show the rendered result; neither a well-formed SVG nor matching JSON
proves a client actually displayed it.

The site's runtime `tool_receipt.source_revision` can identify Site server
code, separately from its embedded Lab `source_revision`. Always record
both in provider identity receipts; do not silently equate the two.
An unsigned Site tool receipt alone does not prove the provider executed
the candidate model nor that the screenshot is authentic.
