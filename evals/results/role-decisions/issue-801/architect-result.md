# Issue #801 Architect result

- Baseline: `88cf9f314c90aa8c6d3a14c01c04ed64282e91c5`
- Impact: A3
- Disposition: REVIEW_REQUIRED; advice only, no implementation or runtime test performed.
- Recommended composition: EXTEND the existing authenticated Cloud Next MCP facade and COMPOSE it with the canonical Investment OS database components. Keep the existing Scheduled Task as the sole trigger; do not add a cron or GitHub Actions runtime.

## Source-backed boundaries

- Site MCP route: `sites/skills-factory-site/app/mcp/route.ts` delegates to adapter `mcp-handler.ts`.
- MCP dispatch: `adapters/skills-factory-cloud-next/src/mcp-handler.ts` serves `tools/list` and `tools/call`; its current caller check only requires the Sites authenticated-user header to be present. That generic identity is not authorization for a scheduled write.
- Current tool declarations/execution: `adapters/skills-factory-cloud-next/src/cloud-tools.ts`. Site UI imports it in `sites/skills-factory-site/app/page.tsx`, so adding a write runner to that module would place server implementation in the client dependency graph. Keep the write executor, credentials and backend client in a server-only module; do not add the runner to browser tools/WebMCP.
- Existing receipt: `adapters/skills-factory-cloud-next/src/tool-receipt.ts` binds input/output digests and optional trace correlation. A successful generic receipt alone does not prove the canonical write; bind the scheduled run, slot, source revision and verified readback separately.
- Live Supabase metadata inspected by Architect: canonical MSS model 1.0, versioned scoring function, market observations, score runs/components, approved-source registry and existing market ingest components/functions already exist. They are not represented by the pinned repository migration set; do not duplicate them or treat the repo migrations as complete live-schema evidence.

## Critical operational findings

- Existing score runs expose the 11:00/23:00 cycle labels but have no unique scheduled-slot key. Existing score/component status constraints must not be repurposed for operational pending/retry states. Before fetching sources, claim each slot atomically in the canonical database; finalize existing score output transactionally and verify with a readback. Create a minimal coordination row only if a current claim mechanism is absent.
- Current preview logic uses current date without publication-age freshness gating. A legacy estimate view contains fixed historical data. Neither is a valid deterministic fresh fallback. Preserve both existing interfaces and MSS v1.0.
- Current source registry has no approved zero-cost candidates for two required inputs. Keep them DATA_GAP; never silently promote candidates or hardcoded estimates to verified evidence. Inventory existing authorized ingest mappings before calling any provider.
- A narrow Scheduled Task identity/capability is required. Supabase market-object privileges are broad; never pass a service key through the browser or expose a generic database proxy.

## Required proof and recovery

1. Identify the real existing Scheduled Task's authenticated caller contract, permitted scope, current prompt/configuration version and supported rollback path; do not copy its raw prompt or identifiers into the public issue.
2. Pin a source-backed consumer map and existing live database contracts before writing code or migrations.
3. Test unauthenticated/incorrect identity, missing secret, stale source SHA, duplicate/concurrent slot, timeout after write, bounded retry, per-input terminal states, unchanged MSS oracle, DATA_GAP behavior, no forbidden trade/policy/thesis writes, and exact readback.
4. Keep the scheduled task unchanged through private Site publication, deployment attestation and read-only/verification run. Cut over the same task only after observed tool invocation and report/readback evidence.
5. Roll back by restoring the previous task configuration and disabling the new write path. Preserve canonical records; do not delete or rewrite historical evidence.

## Evidence limits

- Architect advice was received as a separate child result. The collaboration surface does not expose an effective model/effort or exact start/end event timestamps; requested profile was `sf-architect` / `gpt-6.2-sol` / high.
- No files, database rows or runtime configuration were changed by the Architect. No authenticated scheduler call, Site deployment, live concurrency test, or cutover was run.
- Independent review of this decision against the eventual exact candidate diff remains required.
