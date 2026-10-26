-- DDL-only reconstruction from the applied migration ledger. Seed/operational DML is intentionally omitted.
-- Reconstruction scope: docs/governance/iterations/iteration-04-supabase-grants-2026-10-26.md.

create table if not exists public.cutover_events (
  cutover_id uuid primary key default gen_random_uuid(),
  effective_at timestamptz not null default now(),
  from_backend text not null,
  to_backend text not null,
  migration_run_id uuid references public.migration_runs(migration_run_id),
  reconciliation_status text not null,
  notes text,
  created_at timestamptz not null default now()
);

alter table public.cutover_events enable row level security;

create index if not exists idx_cutover_events_migration_run_id on public.cutover_events(migration_run_id);

alter table public.cutover_events enable row level security;
revoke all on table public.cutover_events from public, anon, authenticated, service_role;
grant select, insert on table public.cutover_events to service_role;
