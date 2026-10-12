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
