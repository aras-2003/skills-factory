create table if not exists public.ppk_fund_allocation_observations (
 observation_id uuid primary key default gen_random_uuid(),
 account_id uuid not null references public.accounts(account_id),
 as_of_date date not null,
 exposure_class text not null,
 reported_pct numeric(10,4) not null,
 source_url text not null,
 evidence_status text not null,
 notes text,
 created_at timestamptz not null default now(),
 unique(account_id,as_of_date,exposure_class,source_url)
);

alter table public.ppk_fund_allocation_observations enable row level security;

revoke all on public.ppk_fund_allocation_observations from public, anon, authenticated;

grant select, insert, update, delete on public.ppk_fund_allocation_observations to service_role;
