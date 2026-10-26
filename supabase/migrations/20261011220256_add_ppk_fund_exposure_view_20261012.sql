-- DDL-only reconstruction from the applied migration ledger. Seed/operational DML is intentionally omitted.
-- Reconstruction scope: docs/governance/iterations/iteration-04-supabase-grants-2026-10-26.md.

create or replace view public.ppk_fund_exposures with (security_invoker = true) as
select a.account_id, a.provider, a.legacy_ref as account_label,
a.metadata->>'fund_name' as fund_name,
v.as_of_date, v.market_value, v.currency, v.contributions_total,
round(v.market_value / nullif(sum(v.market_value) over(),0) * 100, 4) as share_of_ppk_pct,
'PPK_TARGET_DATE_MIXED'::text as asset_class,
'UNKNOWN'::text as verified_equity_pct,
'UNKNOWN'::text as verified_bond_pct,
'UNVERIFIED'::text as actual_allocation_status,
a.metadata->>'fund_source_url' as fund_source_url
from public.accounts a
join lateral (select x.* from public.account_valuation_snapshots x
  where x.account_id=a.account_id order by x.as_of_date desc,x.created_at desc limit 1) v on true
where a.tax_wrapper='PPK';

revoke all on public.ppk_fund_exposures from PUBLIC, anon, authenticated, service_role;

revoke all on table public.ppk_fund_exposures from public, anon, authenticated;
grant select on table public.ppk_fund_exposures to service_role;
