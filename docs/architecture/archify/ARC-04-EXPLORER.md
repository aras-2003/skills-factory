# ARC-04 — Skills Factory investment workflow explorer

Issue #377; parent #373. Uses the canonical IR from ARC-02 and isolated renderer from ARC-03.

## Scope

- Extracts an intentional, representative slice of 13 existing investment skills and 7 workflow entrypoints from immutable Git objects.
- Records each skill/workflow, explicit tool identifier, data field, documented route/dependency and failure-gate statement with exact source path, revision and line.
- Archives the complete extracted graph as `explorer-model.json` and renders two readable representative workflow views (`investment-security-review` and `investment-theme-discovery`) with the pinned Archify version through the ARC-03 isolated adapter. Each visual view includes direct documented skill/workflow/data lineage and the selected workflow's gate state; full tool/data references remain in the complete graph artifact.
- Traversal reports documented forward reachability. Cycle detection reports directed cycles among skill/workflow references.
- A missing failure-gate statement is an explicit unknown process node. Workflow gate execution is always `NOT_RUN` unless a correlated runtime receipt is supplied; this source-only renderer supplies none.

## Evidence and limits

The graph represents references written in the pinned source revision. Workflow-to-child edges mean documented conditional routing, not proof of runtime invocation. Tool and data nodes mean a literal source reference, not a successful call or a verified data read. Unsupported relationships remain unknown. Cycle output is diagnostic and does not claim execution order.

The smoke test verifies exact source lines against Git objects, renders the model in the ARC-03 container, runs the upstream browser-check, and archives the complete graph, model digest, gate report, traversal, cycle report, both rendered sample views and renderer receipts. It uses source text only; no private portfolio data is queried or rendered. Runtime execution remains NOT_RUN until separately tested in a correlated runtime.

## Validation

- `python3 -m unittest discover -s tests/architecture -p 'test_*.py' -v`
- `PYTHONPATH=. python3 scripts/architecture/run_skills_factory_explorer_smoke.py --upstream <exact-Archify-checkout> --output-dir <fresh-empty-directory>`
- CI artifact includes rendered HTML plus finalize, sandbox, provenance and explorer-summary receipts.
