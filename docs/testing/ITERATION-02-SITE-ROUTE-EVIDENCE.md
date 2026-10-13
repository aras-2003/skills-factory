# Iteration 02 / #149 — Site MCP route-only evidence gate

Executable source: `scripts/eval/iteration02_site_route_evidence.py`.
TEST_ONLY offline structural checker. It reads **no user holdings or production
stores**, invokes no provider and never claims runtime PASS.

## Tester handoff

Use the pristine `external-lock.json` generated for this **exact** Lab
source revision. Case `I02-149-cloud-e2e` is Site-scoped, not Desktop, Lab
or Production. A capture JSON must include case, attempt, channel, source,
release, payload, prompt/rubric digests, scoped approval, independent
executor/evaluator, timezone-aware observation time and correlation ID.

Four immutable raw artifact references with relative paths and SHA-256:
`tool_receipt` (JSON), `tool_output` (JSON), `client_observation` (JSON),
and `screenshot` (PNG bytes). The original MCP tool-call ID, trace identity,
saved raw output hash, selected child and client observation must match.

**Critical route-only rule:** the raw selected child execution object must
be `{ "state": "not_executed", "steps": [] }`. Any executed child, missing
steps or ambiguous state blocks the case, even if the route choice is valid.

Example read-only assessment:

~~~bash
python scripts/eval/iteration02_site_route_evidence.py \
  --external-lock external-lock.json \
  --capture site-route-observation.json \
  --evidence-root captured-artifacts \
  --output route-structure-review.json
~~~

`STRUCTURAL_REVIEW_REQUIRED` only establishes internal file identity and
relationships. Human/independent evaluator must authenticate the original
Site MCP and Chat client traces, approve any real runtime execution and
inspect screenshot/accessible UI before acceptance. A synthetic fixture
passing source CI is not a live MCP or browser receipt.
