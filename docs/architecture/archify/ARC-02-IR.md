# ARC-02 — Canonical visualization intermediate representation v1

Issue #375; parent #373. **Source-side implementation only.** No renderer or runtime enabled.

`scripts/architecture/visualization_ir.py` accepts strict source-backed objects with schema_version=1, model_id, source_revision, nodes, edges. Each observed/proposed node and edge must provide explicit evidence with uri (`repo://` or `evidence://`), revision exactly matching model's source_revision and locator. Unknown elements are permitted but cannot claim evidence. Edges may never refer to missing nodes. An evidenced edge may not connect an unknown node.

`validate_model` rejects unknown attributes and unsupported enumerations. It sorts nodes/edges lexically; `canonical_json` and `model_digest` provide reproducible fingerprints independent of input ordering. This representation is distinct from Archify's rendering JSON and is not an OAF metamodel replacement.

## Scope limits / safety
- No inference of nodes/edges from labels, layouts, or LLM output.
- No remote fetching, code execution, persistence or rendering.
- No source authenticity guarantee: a URI + revision is an **asserted reference**, not a cryptographic attestation. A separate trusted loader must verify referenced locators against that revision before promoting evidence into authoritative model facts (planned integration).
- Does not yet verify semantic edge type compatibility (e.g., capability → application); ARC-02 requires domain-specific relation policy before closure.
- URI string validation is minimal allow-list and **not** a file-access authorization mechanism.

## Validation
Run `python3 -m unittest discover -s tests/architecture -p 'test_visualization_ir.py'`. CI evidence and actual results should be reported per exact commit; neither tests nor runtime have been executed in GitHub connector-only authoring environment.

## Follow-up for ARC-02 acceptance
Add schema/contract fixture files, source locator verifier bound to trusted repository revision, semantic edge type matrix for Skills Factory and OAF, tests for adversarial revisions/locators, and CI wiring. Do not claim Ready before tests and review.
