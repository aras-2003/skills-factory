# ARC-02 — Canonical, evidence-aware visualization IR v1

Issue #375; parent #373; PR #386. Source-only shared Python model, not Archify native JSON, OAF replacement, a renderer or an MCP tool.

## Contracts

- Only schema_version integer 1, model_id, immutable lowercase **40-character Git commit SHA** as source_revision, and explicit nodes/edges arrays.
- Allowed node types: skill, workflow, tool, capability, process, application, data, owner, unknown. Allowed edge types: requires, calls, produces, supports, owns, depends_on, flows_to, unknown.
- Each observed/proposed fact must contain at least one repo:// path with matching full revision and Lstart[-Lend] locator. Unknown states cannot claim evidence; unknown relation must have unknown type.
- Fail closed on duplicate IDs, dangling edges, extra attributes, unsupported enums, malformed line ranges, unsafe path segments and unsupported relationship direction/type pairs.
- Semantic compatibility is implemented as an explicit edge type-pair allow-list; it restricts expressibility, not factual correctness. The `depends_on` relation allows skill/workflow → data dependencies and workflow → process links so source-backed models can expose documented data lineage and process/failure gates. These relations do not attest successful data access or runtime gate execution.
- Sorting nodes, edges and evidence refs makes canonical_json and SHA-256 model_digest stable under input reordering.

## Authenticity boundary

validate_model checks structure and semantic *plausibility*, not truth or authority. **verify_sources(model, trusted_repo_root)** additionally reads Git objects at the declared commit SHA (not mutable working-tree files), requires a Git commit object and confirms every referenced UTF-8 line locator exists. It requires a locally trusted Git checkout and no network or tool permission escalation. It does NOT prove that the referenced lines entail the model claim. Human/domain evidence evaluation remains mandatory for claims affecting decisions.

Only repo:// sources are currently accepted. evidence:// external records are deliberately rejected until a trusted external evidence attestor is specified and tested. Paths must be repo-relative; no traversal or arbitrary URLs. No writeback, persistence, renderer or network operation exists in this module.

## Tests

`python3 -m unittest discover -s tests/architecture -p 'test_visualization_ir.py' -v`

Tests cover deterministic digests, allowed/forbidden semantic edges, no inferred links, stale revision, duplicate/dangling edges, malicious URI and locator input, exact commit lookup, missing Git blob and locator outside the referenced immutable source. A dedicated CI workflow `.github/workflows/ci-architecture-ir.yml` binds execution to the PR head SHA. CI completion and review are separate evidence.

## Release limitations

This does not by itself implement ARC-03 adapter, Archify rendering, runtime registration, or a general enterprise architecture metamodel. Merge is gated by the active 3a lock in PR #429, exact-head CI, and post-merge main checks. Codex self-review is disclosed and is not independent review.
