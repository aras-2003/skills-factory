create or replace view public.portfolio_exposure_source_coverage with (security_invoker = true) as
with latest_exposure as (
  select
    e.instrument_id,
    max(e.as_of_date) as latest_exposure_date,
    array_agg(distinct e.exposure_type order by e.exposure_type) as exposure_types,
    count(*) as exposure_rows
  from public.instrument_exposures e
  group by e.instrument_id
)
select
  cp.account_id,
  cp.instrument_id,
  i.ticker,
  cp.portfolio_weight,
  case when le.instrument_id is not null then true else false end as has_exposure_metadata,
  le.latest_exposure_date,
  le.exposure_types,
  coalesce(le.exposure_rows,0) as exposure_rows
from public.current_positions cp
join public.instruments i on i.instrument_id=cp.instrument_id
left join latest_exposure le on le.instrument_id=cp.instrument_id;

comment on view public.portfolio_exposure_source_coverage is
'Portfolio-weight coverage of instruments that have any source-backed exposure metadata. This is source coverage only, not decomposition completeness. Do not sum heterogeneous exposure rows to infer completeness.';

revoke all on public.portfolio_exposure_source_coverage from public, anon, authenticated;
grant select on public.portfolio_exposure_source_coverage to service_role;
