-- DDL-only reconstruction from the applied migration ledger. Seed/operational DML is intentionally omitted.
-- Reconstruction scope: docs/governance/iterations/iteration-04-supabase-grants-2026-10-26.md.

create view public.investment_account_exposure_inventory_v1 with (security_invoker=true) as
select a.provider,a.account_type,a.tax_wrapper,v.as_of_date,v.market_value,v.currency,'ACCOUNT_VALUATION'::text as basis
from public.accounts a join public.account_valuation_snapshots v on v.account_id=a.account_id
union all
select a.provider,a.account_type,a.tax_wrapper,s.as_of_date::date,sum(p.market_value),
min(p.currency),'POSITION_SNAPSHOT'::text
from public.accounts a join public.current_positions p on p.account_id=a.account_id
join public.portfolio_snapshots s on s.snapshot_id=p.snapshot_id
where a.tax_wrapper is distinct from 'PPK'
group by a.provider,a.account_type,a.tax_wrapper,s.as_of_date;

revoke all on table public.investment_account_exposure_inventory_v1 from public, anon, authenticated, service_role;
grant select on table public.investment_account_exposure_inventory_v1 to service_role;
