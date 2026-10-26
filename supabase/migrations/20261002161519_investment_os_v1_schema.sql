create extension if not exists pgcrypto;

create table if not exists public.system_config (
  key text primary key,
  value jsonb not null,
  updated_at timestamptz not null default now()
);

create table if not exists public.migration_runs (
  migration_run_id uuid primary key default gen_random_uuid(),
  source_type text not null,
  source_ref text not null,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  status text not null default 'RUNNING' check (status in ('RUNNING','SUCCESS','FAILED','SUPERSEDED')),
  reconciliation jsonb,
  notes text
);

create table if not exists public.accounts (
  account_id uuid primary key default gen_random_uuid(),
  provider text not null,
  account_type text,
  currency text,
  tax_wrapper text,
  active boolean not null default true,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.instruments (
  instrument_id uuid primary key default gen_random_uuid(),
  ticker text,
  isin text,
  name text not null,
  asset_type text,
  exchange text,
  currency text,
  xtb_symbol text,
  xtb_status text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (isin),
  unique (xtb_symbol)
);

create table if not exists public.sources (
  source_id uuid primary key default gen_random_uuid(),
  source_type text,
  title text,
  publisher text,
  url_or_drive_ref text,
  published_date date,
  accessed_at timestamptz,
  primary_or_secondary text,
  content_hash text,
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists public.transactions (
  transaction_id uuid primary key default gen_random_uuid(),
  external_transaction_id text,
  account_id uuid references public.accounts(account_id),
  instrument_id uuid references public.instruments(instrument_id),
  trade_date timestamptz not null,
  action text not null,
  quantity numeric,
  price numeric,
  currency text,
  fees numeric,
  source_id uuid references public.sources(source_id),
  imported_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb
);

create unique index if not exists transactions_external_id_uq
  on public.transactions(external_transaction_id)
  where external_transaction_id is not null;

create table if not exists public.portfolio_snapshots (
  snapshot_id uuid primary key default gen_random_uuid(),
  as_of_date timestamptz not null,
  snapshot_reason text,
  source_id uuid references public.sources(source_id),
  migration_run_id uuid references public.migration_runs(migration_run_id),
  is_valid boolean not null default true,
  supersedes_snapshot_id uuid references public.portfolio_snapshots(snapshot_id),
  created_at timestamptz not null default now()
);

create table if not exists public.position_snapshots (
  position_snapshot_id uuid primary key default gen_random_uuid(),
  snapshot_id uuid not null references public.portfolio_snapshots(snapshot_id) on delete cascade,
  account_id uuid references public.accounts(account_id),
  instrument_id uuid references public.instruments(instrument_id),
  quantity numeric,
  cost_basis numeric,
  market_price numeric,
  market_value numeric,
  portfolio_weight numeric,
  currency text,
  metadata jsonb not null default '{}'::jsonb
);

create table if not exists public.theses (
  thesis_id uuid primary key default gen_random_uuid(),
  instrument_id uuid references public.instruments(instrument_id),
  horizon text,
  created_at timestamptz not null default now()
);

create table if not exists public.thesis_versions (
  thesis_version_id uuid primary key default gen_random_uuid(),
  thesis_id uuid not null references public.theses(thesis_id),
  version integer not null,
  effective_date date not null,
  thesis text not null,
  assumptions jsonb not null default '[]'::jsonb,
  catalysts jsonb not null default '[]'::jsonb,
  risks jsonb not null default '[]'::jsonb,
  kill_criteria jsonb not null default '[]'::jsonb,
  state text,
  supersedes uuid references public.thesis_versions(thesis_version_id),
  created_at timestamptz not null default now(),
  unique(thesis_id, version)
);

create table if not exists public.investment_policies (
  policy_id uuid primary key default gen_random_uuid(),
  name text not null default 'Default Investment Policy',
  created_at timestamptz not null default now()
);

create table if not exists public.investment_policy_versions (
  policy_version_id uuid primary key default gen_random_uuid(),
  policy_id uuid not null references public.investment_policies(policy_id),
  version integer not null,
  effective_date date not null,
  objectives jsonb not null default '{}'::jsonb,
  constraints jsonb not null default '{}'::jsonb,
  bucket_rules jsonb not null default '{}'::jsonb,
  sizing_rules jsonb not null default '{}'::jsonb,
  concentration_rules jsonb not null default '{}'::jsonb,
  cash_rules jsonb not null default '{}'::jsonb,
  review_rules jsonb not null default '{}'::jsonb,
  rationale text,
  supersedes uuid references public.investment_policy_versions(policy_version_id),
  created_at timestamptz not null default now(),
  unique(policy_id, version)
);

create table if not exists public.market_themes (
  theme_id uuid primary key default gen_random_uuid(),
  name text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists public.market_theme_versions (
  theme_version_id uuid primary key default gen_random_uuid(),
  theme_id uuid not null references public.market_themes(theme_id),
  as_of_date date not null,
  mechanism text,
  indicators jsonb not null default '[]'::jsonb,
  beneficiaries jsonb not null default '[]'::jsonb,
  losers jsonb not null default '[]'::jsonb,
  invalidation jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.watchlist (
  watchlist_id uuid primary key default gen_random_uuid(),
  instrument_id uuid not null references public.instruments(instrument_id),
  status text,
  setup text,
  next_trigger text,
  thesis_id uuid references public.theses(thesis_id),
  added_at timestamptz not null default now(),
  last_reviewed_at timestamptz,
  updated_at timestamptz not null default now(),
  unique(instrument_id)
);

create table if not exists public.opportunities (
  opportunity_id uuid primary key default gen_random_uuid(),
  as_of_date date not null,
  instrument_id uuid references public.instruments(instrument_id),
  setup text,
  fundamental_change text,
  valuation_change text,
  market_trend_change text,
  materiality text,
  main_risk text,
  xtb_status text,
  next_step text,
  status text,
  created_at timestamptz not null default now()
);

create table if not exists public.research_events (
  research_id uuid primary key default gen_random_uuid(),
  as_of_date date not null,
  instrument_id uuid references public.instruments(instrument_id),
  theme_id uuid references public.market_themes(theme_id),
  research_type text,
  summary text not null,
  confidence text,
  thesis_id uuid references public.theses(thesis_id),
  created_at timestamptz not null default now()
);

create table if not exists public.signals (
  signal_id uuid primary key default gen_random_uuid(),
  as_of_date date not null,
  instrument_id uuid references public.instruments(instrument_id),
  theme_id uuid references public.market_themes(theme_id),
  signal_type text not null,
  value_or_state text,
  interpretation text,
  source_id uuid references public.sources(source_id),
  source_date date,
  confidence text,
  created_at timestamptz not null default now()
);

create table if not exists public.decisions (
  decision_id uuid primary key default gen_random_uuid(),
  decision_time timestamptz not null,
  instrument_id uuid references public.instruments(instrument_id),
  lifecycle_action text,
  price_context text,
  position_weight numeric,
  horizon text,
  thesis_version_id uuid references public.thesis_versions(thesis_version_id),
  rationale text,
  sizing_rationale text,
  confidence text,
  invalidation text,
  created_at timestamptz not null default now()
);

create table if not exists public.decision_outcomes (
  outcome_id uuid primary key default gen_random_uuid(),
  decision_id uuid not null references public.decisions(decision_id),
  review_date date not null,
  thesis_quality text,
  timing_quality text,
  sizing_quality text,
  process_adherence text,
  outcome_summary text,
  lessons text,
  created_at timestamptz not null default now()
);

create table if not exists public.evidence_links (
  evidence_link_id uuid primary key default gen_random_uuid(),
  source_id uuid not null references public.sources(source_id),
  entity_type text not null,
  entity_id uuid not null,
  claim_key text,
  created_at timestamptz not null default now()
);

create table if not exists public.instrument_exposures (
  exposure_id uuid primary key default gen_random_uuid(),
  instrument_id uuid not null references public.instruments(instrument_id),
  as_of_date date not null,
  exposure_type text not null,
  exposure_key text not null,
  exposure_value numeric,
  source_id uuid references public.sources(source_id),
  created_at timestamptz not null default now()
);

create table if not exists public.legacy_sheet_rows (
  legacy_row_id uuid primary key default gen_random_uuid(),
  migration_run_id uuid not null references public.migration_runs(migration_run_id),
  sheet_name text not null,
  row_number integer not null,
  row_data jsonb not null,
  imported_at timestamptz not null default now(),
  unique(migration_run_id, sheet_name, row_number)
);

create index if not exists idx_position_snapshots_snapshot on public.position_snapshots(snapshot_id);

create index if not exists idx_position_snapshots_instrument on public.position_snapshots(instrument_id);

create index if not exists idx_transactions_instrument_date on public.transactions(instrument_id, trade_date);

create index if not exists idx_signals_instrument_date on public.signals(instrument_id, as_of_date);

create index if not exists idx_research_instrument_date on public.research_events(instrument_id, as_of_date);

create index if not exists idx_opportunities_instrument_date on public.opportunities(instrument_id, as_of_date);

create index if not exists idx_decisions_instrument_time on public.decisions(instrument_id, decision_time);

create index if not exists idx_exposures_instrument_date on public.instrument_exposures(instrument_id, as_of_date);

create index if not exists idx_thesis_versions_thesis_version on public.thesis_versions(thesis_id, version desc);

create index if not exists idx_policy_versions_policy_version on public.investment_policy_versions(policy_id, version desc);

create or replace view public.latest_portfolio_snapshot
with (security_invoker = true)
as
select ps.*
from public.portfolio_snapshots ps
where ps.is_valid
order by ps.as_of_date desc, ps.created_at desc
limit 1;

create or replace view public.current_positions
with (security_invoker = true)
as
select p.*
from public.position_snapshots p
join public.latest_portfolio_snapshot l on l.snapshot_id = p.snapshot_id;

create or replace view public.current_theses
with (security_invoker = true)
as
select distinct on (t.thesis_id)
  t.thesis_id, t.instrument_id, t.horizon,
  tv.thesis_version_id, tv.version, tv.effective_date, tv.thesis,
  tv.assumptions, tv.catalysts, tv.risks, tv.kill_criteria, tv.state, tv.created_at
from public.theses t
join public.thesis_versions tv on tv.thesis_id = t.thesis_id
order by t.thesis_id, tv.version desc, tv.created_at desc;

create or replace view public.current_policy
with (security_invoker = true)
as
select ipv.*
from public.investment_policy_versions ipv
order by ipv.effective_date desc, ipv.version desc
limit 1;

create or replace view public.current_watchlist
with (security_invoker = true)
as
select w.*, i.ticker, i.name, i.xtb_symbol, i.xtb_status
from public.watchlist w
join public.instruments i using(instrument_id);

create or replace view public.portfolio_exposures
with (security_invoker = true)
as
select
  cp.snapshot_id,
  ie.exposure_type,
  ie.exposure_key,
  sum(coalesce(cp.portfolio_weight,0) * coalesce(ie.exposure_value,0)) as weighted_exposure
from public.current_positions cp
join public.instrument_exposures ie
  on ie.instrument_id = cp.instrument_id
 and ie.as_of_date = (
   select max(ie2.as_of_date)
   from public.instrument_exposures ie2
   where ie2.instrument_id = ie.instrument_id
     and ie2.exposure_type = ie.exposure_type
     and ie2.exposure_key = ie.exposure_key
 )
group by cp.snapshot_id, ie.exposure_type, ie.exposure_key;

create or replace view public.decision_performance
with (security_invoker = true)
as
select
  d.*,
  o.review_date,
  o.thesis_quality,
  o.timing_quality,
  o.sizing_quality,
  o.process_adherence,
  o.outcome_summary,
  o.lessons
from public.decisions d
left join lateral (
  select o.*
  from public.decision_outcomes o
  where o.decision_id = d.decision_id
  order by o.review_date desc, o.created_at desc
  limit 1
) o on true;

do $$
declare r record;
begin
  for r in
    select tablename from pg_tables where schemaname='public'
      and tablename in (
        'system_config','migration_runs','accounts','instruments','sources','transactions',
        'portfolio_snapshots','position_snapshots','theses','thesis_versions',
        'investment_policies','investment_policy_versions','market_themes','market_theme_versions',
        'watchlist','opportunities','research_events','signals','decisions','decision_outcomes',
        'evidence_links','instrument_exposures','legacy_sheet_rows'
      )
  loop
    execute format('alter table public.%I enable row level security', r.tablename);
  end loop;
end $$;

revoke all on all tables in schema public from public, anon, authenticated;

grant usage on schema public to service_role;

grant select, insert, update, delete on all tables in schema public to service_role;

grant usage, select on all sequences in schema public to service_role;
