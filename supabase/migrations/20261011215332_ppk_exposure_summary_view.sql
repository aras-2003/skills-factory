create or replace view public.ppk_exposure_summary with (security_invoker = true) as
select a.account_id,a.provider,a.legacy_ref as account_label,v.as_of_date,v.market_value,v.currency,v.contributions_total,
round(100*v.market_value/nullif(sum(v.market_value) over(partition by v.as_of_date),0),4) as ppk_internal_weight_pct,
'UNKNOWN_UNDERLYING_ALLOCATION'::text as lookthrough_status,
'PPK_TARGET_DATE_FUND_UNVERIFIED'::text as exposure_class
from public.accounts a join lateral (
select v1.* from public.account_valuation_snapshots v1
where v1.account_id=a.account_id order by v1.as_of_date desc,v1.created_at desc limit 1
) v on true where a.tax_wrapper='PPK';

revoke all on public.ppk_exposure_summary from public,anon,authenticated;

grant select on public.ppk_exposure_summary to service_role;
