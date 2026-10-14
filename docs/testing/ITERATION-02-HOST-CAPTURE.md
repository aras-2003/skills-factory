# Iteration 2 — executable host capture integration

Source implementation for #149/#240/#251/#253; semantic source disposition for #287 is below. This is a runtime handoff, not a runtime PASS.

## Actual interfaces

`scripts/eval/iteration02_cua_capture.mjs` executes against the documented `cua_repl` Tab/App interfaces. It does not start an alternative browser driver, inspect hidden application state or guess a provider API. In a host where native App APIs are disabled, Desktop execution is BLOCKED at runtime; browser/Work uses the documented Tab API. This environmental limit does not imply native Desktop was executed.

Initialize the host through its advertised entry point and read its returned documentation. Select the exact approved synthetic session and installed provider. Obtain an actual runtime_info observation matching the pinned release-manifest, with `observation_source` and timestamp. Build the request from the input-only handoff (including the original trailing newline), never from evaluator assertions. Channels are browser, work, desktop; Production is refused.

Import the module in the host's JavaScript REPL, then call `executeAndArchive(privateRoot, target, request, installedIdentity, approval, controls)`. For browser/Work, `controls.input` is a prompt locator obtained from a fresh UI snapshot. For native Desktop, the adapter uses documented paste/Return and AX observation. `controls.observeCompletion` is a provider-specific callback that reads the visible response and returns `{state:'complete', response}` only after actual completion. No timeout auto-resubmits a prompt. An atomic attempt directory is reserved before submission; success and failure both prevent an automatic second submission.

The adapter stores original before/after screenshots and accessible text, exact response, input/candidate identity, observation time and hash references. Only approved synthetic data are submitted. Raw captures stay private; do not push them to this public repository. Screenshot capture is not visual validation, and a visible response alone does not attest hidden tool calls. An independent observer must provide raw MCP tool receipts separately.

`iteration02_host_capture_intake.py --package <input-pack> --host-capture <capture.json> --output <private-report.json>` binds actual Work/Desktop captures to the same immutable lock checked by the existing runners. It verifies the frozen input and actual archived bytes. Its only successful result is HOST_CAPTURE_BOUND_REVIEW_REQUIRED; it never assigns model PASS.

## Native Site format and browser binding

`iteration02_site_native_receipt.py` unwraps structuredContent or the native JSON text block without rewriting it. It validates native unsigned tool receipts and canonical output SHA, separately binds observed worker source and embedded Lab manifest, and rejects ZIP-for-payload substitutions. Browser/chart and route-to-child validators accept `receipt_profile: site-native-v1` with a hash-bound `site_runtime_info_path`/`site_runtime_info_sha256` file. Legacy synthetic fixture format remains supported separately.

For chart checks save the actual native output and its exact SVG; save `data` separately as tool_output. Correlation is the SHA-256 of the original raw native tool export, not an invented provider call ID. Native output digest is over canonical full output before tool_receipt, rather than JSON file whitespace or only the data object. Client evidence must independently reference the same export and actual screenshot. Unsigned structural correspondence still requires independent review.

`iteration02_flow_capture.collect` builds all four parity records from real raw tool traces, actual structured semantic results, client observations and screenshots. It calculates hashes rather than accepting handwritten digest labels. Missing architecture execution, actual chart display or either source layer blocks parity. It uses the existing canonical parity bridge; there is no second campaign or evaluator.

## Semantic routing development (#287)

Source remediation is already integrated: investment requests route through Investment OS, exact child load precedes specialist reasoning, workflow Entry criteria bound four previously identified adjacent-domain workflows, and research/preview requests cannot authorize writes (#303/#346). Governance, proofreading and arithmetic stay outside Investment OS. A route receipt is never child execution. The existing all-component campaign covers 64 skills/19 workflows and keeps human semantic assessment separate from source fixtures.

No additional source defect is inferred from a REVIEW_REQUIRED static signal alone. #243/#256/#311 retain historical verdicts for exact-version runtime adjudication; any newly confirmed source defect requires a linked fix. The current source handoff is executable on documented host surfaces, with disabled or missing provider capabilities reported at runtime. This is not an independent human review or a claim that all domain semantics have passed.
