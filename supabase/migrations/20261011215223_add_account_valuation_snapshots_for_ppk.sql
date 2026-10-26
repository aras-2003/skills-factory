-- DDL-only reconstruction from the applied migration ledger. Seed/operational DML is intentionally omitted.
-- Reconstruction scope: docs/governance/iterations/iteration-04-supabase-grants-2026-10-26.md.

create table if not exists public.account_valuation_snapshots (
 valuation_id uuid primary key default gen_random_uuid(),
 account_id uuid not null references public.accounts(account_id),
 as_of_date date not null,
 market_value numeric(20,2) not null check(market_value>=0),
 currency text not null,
 contributions_total numeric(20,2),
 personal_contributions numeric(20,2),
 source_label text not null,
 metadata jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now(),
 unique(account_id,as_of_date,source_label)
);

create index if not exists account_valuation_snapshots_account_date_idx on public.account_valuation_snapshots(account_id,as_of_date desc);

alter table public.account_valuation_snapshots enable row level security;

revoke all on table public.account_valuation_snapshots from public, anon, authenticated, service_role;
grant select, insert on table public.account_valuation_snapshots to service_role;
