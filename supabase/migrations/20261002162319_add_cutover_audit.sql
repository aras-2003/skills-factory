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

revoke all on public.cutover_events from public, anon, authenticated;
grant select, insert, update, delete on public.cutover_events to service_role;
