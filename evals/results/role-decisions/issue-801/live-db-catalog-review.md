# Issue #801 live database catalog review

Status: bounded, read-only catalog observation; not a complete DDL or code-path audit.

- Canonical source baseline: `88cf9f314c90aa8c6d3a14c01c04ed64282e91c5`.
- Target: existing Supabase project named `investment-os`; returned status `ACTIVE_HEALTHY`, PostgreSQL 17.11. Project identifiers and all row contents are intentionally omitted.
- Observation window: completed no later than `2026-11-26T10:50:59Z`. Individual database MCP calls did not expose execution timestamps.
- Method: Supabase MCP read-only `SELECT` queries over `information_schema`, `pg_class`, `pg_namespace`, `pg_indexes`, `pg_policies`, `pg_proc`, `pg_trigger`, `pg_roles`, and `information_schema.role_table_grants`. No table rows, holdings, portfolio identifiers, or secrets were read. No schema or data writes were performed.
- Evidence limit: tool output is unsigned and was returned in the current task context; this sanitized transcription is not a cryptographic database attestation.

## Observed schema facts

- `public.market_score_runs`: columns include `run_id`, `model_id`, `calculated_at`, `as_of_at`, `report_cycle`, coverage/score fields, optional `input_fingerprint`, and JSON metadata. The only unique index/constraint observed is the primary key on `run_id`; `report_cycle` has a check constraint, not a unique slot constraint.
- `public.market_score_components`: primary key `(run_id, indicator_code)`; foreign keys to runs, indicators, and observations.
- `public.market_observations`: unique key `(indicator_code, observation_date, source_provider, revision_number)`; source, publication/retrieval time, quality, and metadata columns.
- `public.market_indicators`: primary key `indicator_code` and per-indicator freshness/configuration columns.
- Target-table indexes also include non-unique latest/comparison lookups; they do not enforce a unique monitoring slot.
- Row-level security is enabled and not forced on the three score/run/observation tables. The catalog query returned no row policies for them.
- `service_role` has `BYPASSRLS`; grants include SELECT, INSERT, UPDATE, DELETE, and TRUNCATE on the three target tables. Do not use this as the scheduled task's narrow authorization boundary.
- Targeted function-name lookup found `public.market_piecewise_score_v1(numeric, jsonb) -> numeric` as the public score function matching the search. A bounded name scan for `claim`, `lock`, `idempot`, or `schedule` returned no matching relations or routines in `public`/`investment`; the target-table trigger query returned no user triggers.

## Sanitized source-readiness observation

- Aggregate query against `public.market_free_data_readiness_v1`: `select count(*) as indicator_count, count(*) filter (where approved_free_count=0) as indicators_without_approved_free_source, count(*) filter (where approved_free_count>0) as indicators_with_approved_free_source, count(*) filter (where freshness='FRESH') as fresh_indicator_count from public.market_free_data_readiness_v1;`
- Result observed no later than `2026-11-26T10:50:59Z`: `indicator_count=2`, `indicators_without_approved_free_source=2`, `indicators_with_approved_free_source=0`, `fresh_indicator_count=0`.
- This is an aggregate only; no indicator names, source URLs, candidate records, observation values, or portfolio rows were read or retained. The query output is unsigned.

## What this does not prove

- It does not export full table/function DDL, inspect every routine body or every migration, or rule out advisory locks and claim logic under unrelated names.
- It does not establish the current Scheduled Task's identity, payload, write mandate, retries, rollback, or ability to call the Site MCP.
- It does not prove freshness or source approval. The earlier bounded source-registry observation is documented in `architect-result.md`; two required inputs lacked an approved zero-cost candidate there and remain `DATA_GAP` until approved mappings are established.
- It does not establish runtime execution, persistence, readback, or cutover. MON-01–MON-07 remain `NOT_RUN`.
