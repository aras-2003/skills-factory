# Scheduled Investment OS monitoring — server-side execution

## Decision identity

- Issue: #801, acceptance criteria MON-01–MON-07
- Decision ID: ISSUE-801-A3-01
- Architecture Impact: A3 (set in the native GitHub Project)
- Status: REVIEW_REQUIRED; implementation active under owner-approved one-time D2 WIP exception (2026-11-26)
- Baseline: 88cf9f314c90aa8c6d3a14c01c04ed64282e91c5
- Candidate SHA: NOT_CREATED
- Decision owner / independent reviewer: coordinator owns integration; independent review is pending against the candidate diff
- Related contracts: docs/SITES-PUBLISHING.md, docs/governance/SDLC-OPERATING-PROCESS.md, adapters/skills-factory-cloud-next/src/mcp-handler.ts, live Investment OS MSS 1.0 metadata

## Context and scope

The existing Scheduled Task remains the sole 11:00/23:00 Europe/Warsaw trigger. The requested change is server-side authenticated MCP execution that records canonical market monitoring results with idempotent slot claims, traceable evidence and verified cutover. No GitHub Actions runtime, extra cron, duplicate investment ledger, new trading/policy workflow, or client/browser write path is in scope.

The exact Scheduled Task caller identity, supported authentication handoff, private configuration/prompt revision, standing write authority, rollback handle and full live database migration history are not exposed in this repository or current tool surface. These are explicit unknowns, not assumptions.

## Evidence-backed component and consumer map

| Producer / interface | Consumer | Source path and evidence | Contract / status |
| --- | --- | --- | --- |
| Next Site MCP route | Cloud Next adapter | sites/skills-factory-site/app/mcp/route.ts | GET/POST/DELETE delegate to handleMcp; source-backed. |
| MCP request handler | Tool declarations and execution | adapters/skills-factory-cloud-next/src/mcp-handler.ts | tools/list, tools/call, generic Sites identity-presence check, receipt call. It does not establish Scheduled Task scope. |
| Canonical tool declarations | Site client console / WebMCP | adapters/skills-factory-cloud-next/src/cloud-tools.ts; consumed by sites/skills-factory-site/app/page.tsx | Shared file is in the browser dependency graph; it is unsafe for server credentials or write execution. |
| Canonical tool execution | MCP handler and client console | cloud-tools.ts, sites/skills-factory-site/lib/skills-factory-adapter/cloud-tools.ts | Existing calculations are client-safe. Synchronization/build relationship must be checked by the final consumer diff. |
| MCP receipt | MCP response | adapters/skills-factory-cloud-next/src/tool-receipt.ts | Unsigned digest and optional trace correlation; not proof of authorization, persistence or readback. |
| Site source synchronization | Generated Site adapter/runtime | sites/skills-factory-site/scripts/sync-site-source.mjs and docs/SITES-PUBLISHING.md | Official private publication flow; verify canonical SHA, mirror SHA, Site version and attestation separately. |
| Live MSS 1.0 and market tables/functions | Scheduled monitoring executor | Read-only live Supabase metadata inspected by the Architect; complete live DDL/migration mapping is not present in the pinned repository | Existing canonical model, observations, score runs/components and scoring function exist. Exact schema and grants must be captured from a trusted backend evidence source before migration. |
| Existing market ingesters | Source observations | Live Edge functions market-fred-ingest and market-sp500-ingest v2, confirmed in metadata | Existing components must be inventoried for approval, freshness and overlapping series before reuse; not permission to invoke new sources. |

Direct and transitive consumers are not proven complete because the live DB schema and the private Scheduled Task configuration are outside the repository. Keep those edges UNKNOWN until exact source-backed evidence is supplied.

## Trust boundaries and operations

- Scheduled Task identity must be verified at a trusted server boundary and authorized for one monitoring capability. A generic authenticated-user header or prompt instruction is insufficient.
- No service-role credential, database proxy, market data, portfolio identifier, private scheduler prompt or raw sensitive trace may enter the client bundle, browser WebMCP or public issue.
- New executor code, backend client and secret access must be server-only and unreachable from the client dependency graph.
- Reject unauthorized identity and stale source SHA before provider fetch or persistence. Reject missing credentials, malformed slot and unsupported sources closed.
- The existing receipt binds bytes, not authority or successful DB persistence. Final runtime evidence must correlate scheduler invocation, request/run id, slot, source revision, output digest and verified canonical readback.
- The current Site MCP tool surface does not expose a Scheduled Task trigger/management operation. Live scheduled invocation and cutover are NOT_RUN.
- No buy/sell/rebalance, policy or thesis write is permitted. Monitoring writes require a specific verified standing mandate and a narrowly scoped DB capability.

## Decision

- Selected composition: EXTEND the current authenticated Site MCP facade and COMPOSE it with existing canonical Investment OS storage/scoring components.
- Rationale: The issue and live metadata show canonical MSS 1.0 and market observations/score components already exist. A second MSS, score ledger, scheduler, or separate task system would duplicate ownership and violate the acceptance boundaries.
- Add a durable unique slot claim only if source inspection proves no suitable existing claim mechanism. Keep operational PENDING/RETRY/FAILED states out of score rows whose status contract represents score quality.
- Preserve MSS 1.0 model definition, versioned piecewise scoring function and existing preview/estimate views as compatibility surfaces. They are not a fresh fallback contract.
- Do not add an MCP capability to BROWSER_TOOLS or allow the Site console to execute monitoring writes.

## Proposed execution contract (requires scheduler and DB confirmation)

The verified Scheduled Task must provide a stable run identity, an explicit scheduled slot (local business date + 11:00/23:00 cycle), a pinned 40-hex source SHA, and an as-of timestamp. Server computes a stable slot/idempotency key; caller cannot supply arbitrary database object names, provider URLs, price limits or write destinations. Response should separate overall execution state from per-input terminal states and include provenance/freshness/coverage, persisted-run identity and readback status.

Exact names and schema are intentionally not declared until the real Scheduled Task payload, canonical live schema, and approved database invocation boundary have been inspected. Do not ship a guessed tool contract.

## Live database inspection (read-only, 2026-11-26)

The connected Supabase MCP identified the existing `investment-os` project as `ACTIVE_HEALTHY` on PostgreSQL 17.11. Read-only catalog queries confirmed the relevant live shapes and constraints without reading portfolio contents:

- `public.market_score_runs` stores `model_id`, `as_of_at`, `report_cycle`, score/coverage fields, optional `input_fingerprint`, and JSON metadata. Its only unique index/constraint is the `run_id` primary key; `report_cycle` has a check constraint but no unique slot key.
- `public.market_score_components` has primary key `(run_id, indicator_code)` and references existing runs, indicators, and observations.
- `public.market_observations` has unique key `(indicator_code, observation_date, source_provider, revision_number)` and records source, publication/retrieval time, quality status, and metadata.
- The only live public scoring function found by the targeted catalog query is `market_piecewise_score_v1(numeric, jsonb) -> numeric`.
- `service_role` has broad SELECT/INSERT/UPDATE/DELETE/TRUNCATE privileges on all three target tables; no row policies were returned for those tables. This is not a narrow scheduled-monitoring write boundary. Do not expose or reuse a service-role credential for the MCP caller; a reviewed, narrowly scoped server-side capability is required.

This evidence confirms that the canonical score tables exist and no slot claim is enforced by the `market_score_runs` unique indexes. It does not establish the missing Scheduled Task identity, task payload, standing write mandate, source approvals, or safe invocation role. No schema or data was changed.

## Data behavior and fallback

The live catalog confirms active MSS 1.0 and existing market data components. The current preview reads relative to CURRENT_DATE without a publication-age gate; the legacy estimate view embeds historical data. Neither satisfies deterministic live fallback or freshness. A live source registry sample had zero APPROVED zero-cost candidates for two required inputs; those inputs must be DATA_GAP until approved source mappings exist. A source marked candidate is not authorized.

Use only exact approved zero-cost sources with publication vintage at or before the slot. Preserve per-indicator source, source timestamp, as-of time, freshness result, coverage and derivation. Do not infer zero, stale-as-fresh, complete coverage, or VERIFIED status from missing evidence. Calculate MSS using the unchanged versioned definition/function and verify the persisted score and components by readback.

## Migration and recovery

1. Confirm the live Scheduled Task identity, payload fields, write authority, execution deadline/retry behavior and supported rollback mechanism without copying secrets or its raw prompt into public sources.
2. Complete the trusted live schema/consumer map: exact MSS 1.0 definition/function, approved source list, and existing ingester behavior. The relevant live run/observation/component columns, constraints, indexes, and grants were read-only inspected on 2026-11-26; no unique monitoring slot claim exists on `market_score_runs`.
3. Since no unique slot claim is enforced on the live `market_score_runs`, propose the smallest additive operational claim record with a unique slot key, expiring/recoverable claim token and no duplicated score/history fields. Review migration and concurrent-claim proof before applying it. Do not rely on broad `service_role` table privileges as the scheduled caller's authorization boundary.
4. Build a server-only MCP executor and validate source, date, slot and revision before network or write side effects. Bound retries and deadlines; make one provider failure isolated and all input statuses terminal.
5. Write canonical run and components transactionally. On timeout after commit, a repeat request must recover by the unique slot claim and readback rather than append a duplicate.
6. Publish privately through the existing Sites workflow. Confirm Site identity/version, canonical source SHA, mirror SHA and verified runtime attestation; then observe actual MCP invocation and readback in a non-cutover verification run.
7. Switch only the same existing Scheduled Task after exact-SHA runtime evidence and independent review pass. Keep the prior prompt/configuration available for immediate restoration.
8. Rollback restores the old task config and disables the new write capability; retain canonical history and receipts. Do not delete data or change market-source approval during rollback.

## Verification and handoff

The complete MON-01–MON-07 case design is in evals/results/role-decisions/issue-801/test-design.md; Architect advice is in evals/results/role-decisions/issue-801/architect-result.md. These are design evidence, not execution receipts. Every case remains NOT_RUN until its exact candidate/runtime evidence exists.

- Consumer regression must include the MCP route, handler, canonical tool/schema tests, Site client bundle exclusion, generated adapter sync, existing investment routing/ingesters and live readback.
- Required negative tests cover unauthenticated/wrong task identity, stale source SHA, missing secrets, unknown/paid source, source failures, exhausted retries and timeout after a successful database commit.
- Required concurrency tests use separate real database connections; mocks do not establish atomic slot claims.
- Site deployment, effective task identity, Site attestation, scheduler event, report receipt and canonical readback are distinct gates.
- Independent Architect decision review and independent candidate review are separate and pending.
- No runtime state migration is approved or applied. Any schema migration requires review of exact live DDL, rollback and canonical data compatibility.

## Unresolved risks / blockers

- Native Project active development WIP was already above the D2 cap (4 In progress / limit 2; 2 In review / limit 5). The owner explicitly approved a one-time exception for #801 on 2026-11-26; the Project item was moved to In progress and now shows 1/2. This exception is scoped only to #801 and does not authorize changing other work items or relaxing other D1-D8 gates.
- Exact Scheduled Task authentication contract, prompt/version, write mandate, retry semantics and rollback operation are unverified.
- The relevant live score/run/observation/component DDL and grants are now verified read-only, and those indexes expose no slot claim; the complete live migration history and existing ingester side-effect behavior still need reconciliation before a migration or write integration.
- Approved zero-cost sources are missing for two inputs; measured complete MSS fallback is not currently supportable under the existing allowlist.
- Current chat connector has no scheduled-task trigger/control; MON-01 and MON-07 runtime/cutover remain NOT_RUN.
- Candidate code, migration, CI, Site deployment, actual Scheduled Task E2E, rollback drill and independent candidate review do not yet exist.

Implementation is active under the approved WIP exception, but candidate construction of the live write path remains gated on verifying the private task/database contract. No production promotion is implied.
