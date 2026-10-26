-- DDL-only reconstruction from the applied migration ledger. Seed/operational DML is intentionally omitted.
-- Reconstruction scope: docs/governance/iterations/iteration-04-supabase-grants-2026-10-26.md.

alter function public.try_numeric(text) set search_path = pg_catalog, public;

drop index if exists public.idx_position_snapshots_instrument_id;

drop index if exists public.idx_position_snapshots_snapshot_id;
