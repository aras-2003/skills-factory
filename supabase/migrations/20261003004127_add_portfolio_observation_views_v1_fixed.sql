create or replace view public.latest_valid_snapshot_pair with (security_invoker = true) as
with ranked as (
  select
    snapshot_id,
    as_of_date,
    snapshot_reason,
    source_id,
    created_at,
    row_number() over (order by as_of_date desc, created_at desc) as rn
  from public.portfolio_snapshots
  where is_valid
)
select
  (max(snapshot_id::text) filter (where rn=1))::uuid as current_snapshot_id,
  max(as_of_date) filter (where rn=1) as current_as_of_date,
  (max(snapshot_id::text) filter (where rn=2))::uuid as prior_snapshot_id,
  max(as_of_date) filter (where rn=2) as prior_as_of_date
from ranked
where rn <= 2;

create or replace view public.portfolio_position_changes with (security_invoker = true) as
with pair as (
  select * from public.latest_valid_snapshot_pair
),
current_agg as (
  select
    ps.instrument_id,
    sum(coalesce(ps.market_value,0)) as market_value,
    sum(coalesce(ps.portfolio_weight,0)) as portfolio_weight
  from public.position_snapshots ps
  join pair p on ps.snapshot_id=p.current_snapshot_id
  group by ps.instrument_id
),
prior_agg as (
  select
    ps.instrument_id,
    sum(coalesce(ps.market_value,0)) as market_value,
    sum(coalesce(ps.portfolio_weight,0)) as portfolio_weight
  from public.position_snapshots ps
  join pair p on ps.snapshot_id=p.prior_snapshot_id
  group by ps.instrument_id
)
select
  p.current_snapshot_id,
  p.current_as_of_date,
  p.prior_snapshot_id,
  p.prior_as_of_date,
  coalesce(c.instrument_id,pr.instrument_id) as instrument_id,
  i.ticker,
  i.name,
  pr.market_value as prior_market_value,
  c.market_value as current_market_value,
  case when pr.market_value is null or c.market_value is null then null
       else c.market_value-pr.market_value end as market_value_change,
  pr.portfolio_weight as prior_weight,
  c.portfolio_weight as current_weight,
  case when pr.portfolio_weight is null or c.portfolio_weight is null then null
       else c.portfolio_weight-pr.portfolio_weight end as weight_change,
  case
    when pr.instrument_id is null then 'NEW'
    when c.instrument_id is null then 'EXITED'
    when abs(coalesce(c.portfolio_weight,0)-coalesce(pr.portfolio_weight,0)) < 0.000001
         and abs(coalesce(c.market_value,0)-coalesce(pr.market_value,0)) < 0.01 then 'UNCHANGED'
    when coalesce(c.portfolio_weight,0) > coalesce(pr.portfolio_weight,0) then 'WEIGHT_UP'
    when coalesce(c.portfolio_weight,0) < coalesce(pr.portfolio_weight,0) then 'WEIGHT_DOWN'
    else 'VALUE_CHANGED'
  end as observed_state
from pair p
full join current_agg c on true
full join prior_agg pr on pr.instrument_id=c.instrument_id
join public.instruments i on i.instrument_id=coalesce(c.instrument_id,pr.instrument_id);

comment on view public.portfolio_position_changes is
'Observation-only latest-vs-prior valid snapshot comparison. Establishes observed change, never causal attribution.';

revoke all on public.latest_valid_snapshot_pair, public.portfolio_position_changes from public, anon, authenticated;
grant select on public.latest_valid_snapshot_pair, public.portfolio_position_changes to service_role;
