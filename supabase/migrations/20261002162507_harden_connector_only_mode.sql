alter function public.try_numeric(text) set search_path = pg_catalog, public;

drop index if exists public.idx_position_snapshots_instrument_id;

drop index if exists public.idx_position_snapshots_snapshot_id;
