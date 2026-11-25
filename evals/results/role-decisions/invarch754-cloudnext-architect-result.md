# Architect decision — Cloud Next #754 runtime slice

Observed source SHA: `b5a0daf5ad9c61e55d28b04e476937038af9d943`.

Disposition: approve implementation of an explicit fixture-ID-only Cloud Next calculator. Input is limited to `{fixture_id, expected_canonical_source_revision}`; no arbitrary caller-supplied decision bundle or override. Resolve only content-bound, in-repository synthetic fixtures that pass build-time checks for `execution_mode=TEST`, `write_scope.mode=NONE`, strict UTC/precision, and synthetic identifiers/data. Label all returned results as synthetic and include fixture digest, rule version and canonical source revision. This approval is for source implementation only; deployment remains separately gated.

Keep the existing route/load behavior and security-review production output unchanged. Do not insert fake specialist/model evidence or make the test tool the production workflow default. A real user-supplied decision requires authenticated specialist outputs, source/policy/portfolio authentication, matched historical evaluation and approved mappings.

Quarantine before publishing: the merged Python engine allows an incomplete NOT_HELD snapshot to yield AVOID, can accept LIVE with explicit write scope in the synthetic-style evaluator, and has permissive timestamp parsing/cutoff precision gaps. The fixture allowlist must exclude affected cases; build and ingress checks must reject any fixture that is not synthetic, uses non-NONE write scope, contains real IDs/data, violates strict UTC precision, or is not bound to the expected digest. Add regression cases for these defects, but do not claim general Python/TypeScript parity outside the safe allowlisted fixtures.

Site readback: active Site v148 is archive-backed and `succeeded`, current mirror SHA `a03d52ba1fec9b6c38d990714a58475a7fb07c85`; canonical/Lab source remains `f08abcf81bace86cb60908d7945dbebeb0df6dbc` and no synthesis calculator is deployed. Access is `custom` with one owner allowlisted, zero other users/groups/editors/external visitors. Preserve that exact audience; do not relabel it owner-private.
