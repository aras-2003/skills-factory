# Product Intelligence Center — Architect finding

Disposition: **REVIEW_REQUIRED**. Reuse the existing private Site and compose a bounded P0 around existing server-side Site/runtime facilities plus allowlisted, read-only GitHub REST data. Keep the change inside the Site application; do not change shared Cloud Next MCP contracts or tool declarations.

## P0 boundary

- Add a protected `/intelligence` view with source freshness, provenance and partial/unavailable states.
- Use actual GitHub issue/PR events and existing runtime identity/catalog reads. Distinguish opened issues, completed issues (excluding `not_planned`) and merged PRs; do not sum these unlike event types.
- Treat unmapped domains as unassigned. Distinguish a verified zero from missing or incomplete pages. Paginate, deduplicate, respect rate limits, and show stale last-known-good data as historical.
- Do not claim native Project V2 status/iteration from issue REST fields. Native iterations, detailed plan timeline, Supabase metrics, execution receipts, workflow telemetry, scheduling, new storage and writes remain outside P0 until a safe, supported reader is verified.

## Evidence and risks

- The deployed Site/MCP attestation at discovery was canonical SHA `538d800534cf7f7eca32640592a90d252f6dbada`; this proves the prior deployment only.
- The Site has a generic server-side connected-app wrapper, but no configured GitHub connector. GitHub egress from the Site Worker was not verified. A production integration must fail clearly if server-side GitHub access is unavailable; do not expose credentials to browser code.
- `runtime_info` and `list_skills` are available. Existing evaluation receipts are historical evidence, not live telemetry and not a runtime PASS.
- Supabase project metadata was verified, but no safe aggregate/read-only endpoint was identified; private records were not read.
- Start implementation only after fresh native Project metadata and WIP readback. Do not infer Architecture Impact assignment from issue text.

## Source-linked context

- Issue: https://github.com/aras-2003/skills-factory/issues/821
- Site source: `sites/skills-factory-site/`
- Adapter: `adapters/skills-factory-cloud-next/`
- Runbook: `docs/SITES-PUBLISHING.md`
- Architecture/testing records: `docs/architecture/SOFTWARE-ARCHITECTURE-DECISIONS.md`, `docs/architecture/TESTING-OBSERVABILITY.md`
