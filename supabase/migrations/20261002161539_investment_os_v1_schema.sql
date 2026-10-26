create schema if not exists investment;

create table if not exists investment.system_config (
  key text primary key,
  value jsonb not null,
  updated_at timestamptz not null default now()
);

create table if not exists investment.accounts (
  account_id uuid primary key default gen_random_uuid(),
  provider text not null,
  account_type text,
  currency text not null default 'PLN',
  tax_wrapper text,
  active boolean not null default true,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists investment.instruments (
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
  updated_at timestamptz not null default now()
);

create unique index if not exists instruments_isin_uq
on investment.instruments(isin) where isin is not null;

create unique index if not exists instruments_xtb_symbol_uq
on investment.instruments(xtb_symbol) where xtb_symbol is not null;

create table if not exists investment.sources (
  source_id uuid primary key default gen_random_uuid(),
  source_type text,
  title text not null,
  publisher text,
  url_or_drive_ref text,
  published_date date,
  accessed_at timestamptz not null default now(),
  primary_or_secondary text,
  content_hash text,
  notes text
);

create table if not exists investment.transactions (
  transaction_id uuid primary key default gen_random_uuid(),
  account_id uuid references investment.accounts(account_id),
  instrument_id uuid references investment.instruments(instrument_id),
  trade_date date not null,
  action text not null,
  quantity numeric,
  price numeric,
  currency text,
  fees numeric,
  source_id uuid references investment.sources(source_id),
  imported_at timestamptz not null default now(),
  external_id text
);

create unique index if not exists transactions_external_id_uq
on investment.transactions(external_id) where external_id is not null;

create table if not exists investment.portfolio_snapshots (
  snapshot_id uuid primary key default gen_random_uuid(),
  as_of_date timestamptz not null,
  snapshot_reason text,
  source_id uuid references investment.sources(source_id),
  is_complete boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists investment.position_snapshots (
  position_snapshot_id uuid primary key default gen_random_uuid(),
  snapshot_id uuid not null references investment.portfolio_snapshots(snapshot_id) on delete cascade,
  account_id uuid references investment.accounts(account_id),
  instrument_id uuid not null references investment.instruments(instrument_id),
  quantity numeric,
  cost_basis numeric,
  market_price numeric,
  market_value numeric,
  portfolio_weight numeric,
  currency text
);

create table if not exists investment.theses (
  thesis_id uuid primary key default gen_random_uuid(),
  instrument_id uuid not null references investment.instruments(instrument_id),
  horizon text,
  created_at timestamptz not null default now()
);

create table if not exists investment.thesis_versions (
  thesis_version_id uuid primary key default gen_random_uuid(),
  thesis_id uuid not null references investment.theses(thesis_id),
  version integer not null,
  effective_date timestamptz not null,
  thesis text not null,
  assumptions jsonb not null default '[]'::jsonb,
  catalysts jsonb not null default '[]'::jsonb,
  risks jsonb not null default '[]'::jsonb,
  kill_criteria jsonb not null default '[]'::jsonb,
  state text,
  supersedes uuid references investment.thesis_versions(thesis_version_id),
  created_at timestamptz not null default now(),
  unique(thesis_id, version)
);

create table if not exists investment.watchlist (
  watchlist_id uuid primary key default gen_random_uuid(),
  instrument_id uuid not null references investment.instruments(instrument_id),
  status text,
  setup text,
  next_trigger text,
  thesis_id uuid references investment.theses(thesis_id),
  added_at timestamptz not null default now(),
  last_reviewed_at timestamptz,
  updated_at timestamptz not null default now()
);

create table if not exists investment.market_themes (
  theme_id uuid primary key default gen_random_uuid(),
  name text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists investment.market_theme_versions (
  theme_version_id uuid primary key default gen_random_uuid(),
  theme_id uuid not null references investment.market_themes(theme_id),
  as_of_date timestamptz not null,
  mechanism text,
  indicators jsonb not null default '[]'::jsonb,
  beneficiaries jsonb not null default '[]'::jsonb,
  losers jsonb not null default '[]'::jsonb,
  invalidation jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists investment.opportunities (
  opportunity_id uuid primary key default gen_random_uuid(),
  as_of_date timestamptz not null,
  instrument_id uuid references investment.instruments(instrument_id),
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

create table if not exists investment.research_events (
  research_id uuid primary key default gen_random_uuid(),
  as_of_date timestamptz not null,
  instrument_id uuid references investment.instruments(instrument_id),
  theme_id uuid references investment.market_themes(theme_id),
  research_type text,
  summary text not null,
  confidence text,
  thesis_id uuid references investment.theses(thesis_id),
  created_at timestamptz not null default now()
);

create table if not exists investment.signals (
  signal_id uuid primary key default gen_random_uuid(),
  as_of_date timestamptz not null,
  instrument_id uuid references investment.instruments(instrument_id),
  theme_id uuid references investment.market_themes(theme_id),
  signal_type text not null,
  value_or_state text,
  interpretation text,
  source_id uuid references investment.sources(source_id),
  source_date date,
  confidence text,
  created_at timestamptz not null default now()
);

create table if not exists investment.investment_policies (
  policy_id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now()
);

create table if not exists investment.investment_policy_versions (
  policy_version_id uuid primary key default gen_random_uuid(),
  policy_id uuid not null references investment.investment_policies(policy_id),
  version integer not null,
  effective_date timestamptz not null,
  objectives jsonb not null default '{}'::jsonb,
  constraints jsonb not null default '{}'::jsonb,
  bucket_rules jsonb not null default '{}'::jsonb,
  sizing_rules jsonb not null default '{}'::jsonb,
  concentration_rules jsonb not null default '{}'::jsonb,
  cash_rules jsonb not null default '{}'::jsonb,
  review_rules jsonb not null default '{}'::jsonb,
  rationale text,
  supersedes uuid references investment.investment_policy_versions(policy_version_id),
  created_at timestamptz not null default now(),
  unique(policy_id, version)
);

create table if not exists investment.decisions (
  decision_id uuid primary key default gen_random_uuid(),
  decision_time timestamptz not null,
  instrument_id uuid references investment.instruments(instrument_id),
  lifecycle_action text,
  price_context numeric,
  position_weight numeric,
  horizon text,
  thesis_version_id uuid references investment.thesis_versions(thesis_version_id),
  rationale text,
  sizing_rationale text,
  confidence text,
  invalidation text,
  created_at timestamptz not null default now()
);

create table if not exists investment.decision_outcomes (
  outcome_id uuid primary key default gen_random_uuid(),
  decision_id uuid not null references investment.decisions(decision_id),
  review_date date not null,
  thesis_quality text,
  timing_quality text,
  sizing_quality text,
  process_adherence text,
  outcome_summary text,
  lessons text,
  created_at timestamptz not null default now()
);

create table if not exists investment.evidence_links (
  evidence_link_id uuid primary key default gen_random_uuid(),
  source_id uuid not null references investment.sources(source_id),
  entity_type text not null,
  entity_id uuid not null,
  claim_key text,
  created_at timestamptz not null default now()
);

create table if not exists investment.instrument_exposures (
  exposure_id uuid primary key default gen_random_uuid(),
  instrument_id uuid not null references investment.instruments(instrument_id),
  as_of_date date not null,
  exposure_type text not null,
  exposure_key text not null,
  exposure_value numeric,
  source_id uuid references investment.sources(source_id)
);

create table if not exists investment.migration_runs (
  migration_run_id uuid primary key default gen_random_uuid(),
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  source_backend text not null,
  target_backend text not null,
  status text not null,
  source_ref text,
  reconciliation jsonb not null default '{}'::jsonb,
  notes text
);

create table if not exists investment.cutover_events (
  cutover_id uuid primary key default gen_random_uuid(),
  effective_at timestamptz not null,
  from_backend text not null,
  to_backend text not null,
  migration_run_id uuid references investment.migration_runs(migration_run_id),
  reconciliation_status text not null,
  notes text,
  created_at timestamptz not null default now()
);

create or replace view investment.latest_portfolio_snapshot as
select ps.*
from investment.portfolio_snapshots ps
where ps.snapshot_id = (
  select snapshot_id
  from investment.portfolio_snapshots
  where is_complete = true
  order by as_of_date desc, created_at desc
  limit 1
);

create or replace view investment.current_positions as
select p.*
from investment.position_snapshots p
join investment.latest_portfolio_snapshot s using (snapshot_id);

create or replace view investment.current_theses as
select distinct on (t.thesis_id)
  t.thesis_id, t.instrument_id, t.horizon,
  v.thesis_version_id, v.version, v.effective_date, v.thesis,
  v.assumptions, v.catalysts, v.risks, v.kill_criteria, v.state
from investment.theses t
join investment.thesis_versions v on v.thesis_id = t.thesis_id
order by t.thesis_id, v.effective_date desc, v.version desc;

create or replace view investment.current_policy as
select pv.*
from investment.investment_policy_versions pv
where pv.effective_date <= now()
order by pv.effective_date desc, pv.version desc
limit 1;

create or replace view investment.current_watchlist as
select w.*
from investment.watchlist w
where coalesce(w.status,'') not in ('REMOVED','REJECTED','CLOSED');

create or replace view investment.portfolio_exposures as
select
  p.snapshot_id,
  e.exposure_type,
  e.exposure_key,
  sum(coalesce(p.portfolio_weight,0) * coalesce(e.exposure_value,0)) as weighted_exposure
from investment.current_positions p
join investment.instrument_exposures e on e.instrument_id = p.instrument_id
where e.as_of_date = (
  select max(e2.as_of_date)
  from investment.instrument_exposures e2
  where e2.instrument_id = e.instrument_id
    and e2.exposure_type = e.exposure_type
    and e2.exposure_key = e.exposure_key
)
group by p.snapshot_id, e.exposure_type, e.exposure_key;

create or replace view investment.decision_performance as
select
  d.decision_id,
  d.decision_time,
  d.instrument_id,
  d.lifecycle_action,
  d.position_weight,
  d.horizon,
  o.outcome_id,
  o.review_date,
  o.thesis_quality,
  o.timing_quality,
  o.sizing_quality,
  o.process_adherence,
  o.outcome_summary,
  o.lessons
from investment.decisions d
left join investment.decision_outcomes o on o.decision_id = d.decision_id;
