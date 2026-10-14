# Iteration 2 — controlled MCP failure/renderer campaign

Engineering scope: #252, #254, #149, with #251/#253 runtime acceptance.
The `failure_injection.py` CLI generates **synthetic expectations** for five
failure classes. It never modifies Site, deploys a plugin, calls MCP, or
triggers production data access.

```bash
python scripts/eval/failure_injection.py --case permission_denied
python -m unittest discover -s scripts/eval/tests -p 'test_failure_injection.py'
python -m unittest discover -s scripts/package/tests -p 'test_chart_renderer.py'
python -m unittest discover -s scripts/package/tests -p 'test_cloud_runtime.py'
```

Failure classes: timeout, permission_denied, tool_unavailable, incompatible_schema,
renderer_unavailable. Each describes expected BLOCKED/FAIL *only as a fixture*.
Capture an actual runtime trace, exception category, exact installed release,
source/tool digests and side effects to evaluate behavior. Missing runner,
permission denial before execution or no steps is **NOT_RUN/BLOCKED**, never
behavioral FAIL. Execute on disposable TEST endpoints only; never induce faults
on production Site or user accounts.

Chart source contract: explicit finite values, nonempty string labels,
minimum two x-points for line charts, maximum bounds and valid units.
Test zeros/negative values with actual renderer outputs separately.
A successful PNG/SVG payload is `PAYLOAD_RENDERED`, not `CLIENT_RENDERED`.
For client success, require a fresh Chat screenshot/accessible client trace
with expected title/series/labels and rendering status. Preserve a renderer
not-available case that reports blocked rather than claiming visible chart.

Re-run #251's browser MCP suite and #149's Site publication route only when an
approved exact candidate is installed. All such provider cases are NOT_RUN in
source CI.

## Chart-schema compatibility with the currently connected Site

Local renderer validation is aligned to the Site MCP's observed input limits:
bar charts allow 1–60 rows, line charts 2–100 categorical x-points and 1–8
series; each finite numeric value is in the inclusive range −10¹²…10¹²;
textual labels have at most 80 characters and units at most 30.
These are **schema-equivalent source bounds**, not a claim of identical PNG/SVG
pixel output or client rendering across the two runtimes.

Negative tests cover invalid labels, control characters, NaN/Infinity,
out-of-range values, mismatched series lengths, dimension overflow and tool
failure receipts. Synthetic MCP exception injection is never counted as a
live provider error-path execution. Actual client display, missing renderer
handling and browser tool-call receipts still require exact-version E2E tests.
