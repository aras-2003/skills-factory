-- DDL-only reconstruction from the applied migration ledger. Seed/operational DML is intentionally omitted.
-- Reconstruction scope: docs/governance/iterations/iteration-04-supabase-grants-2026-10-26.md.

alter table public.accounts add column if not exists legacy_ref text;

create unique index if not exists accounts_legacy_ref_uq on public.accounts(legacy_ref) where legacy_ref is not null;

alter table public.instruments add column if not exists legacy_ref text;

create unique index if not exists instruments_legacy_ref_uq on public.instruments(legacy_ref) where legacy_ref is not null;

alter table public.sources add column if not exists legacy_ref text;

create unique index if not exists sources_legacy_ref_uq on public.sources(legacy_ref) where legacy_ref is not null;

alter table public.opportunities add column if not exists legacy_ref text;

create unique index if not exists opportunities_legacy_ref_uq on public.opportunities(legacy_ref) where legacy_ref is not null;

alter table public.research_events add column if not exists legacy_ref text;

create unique index if not exists research_events_legacy_ref_uq on public.research_events(legacy_ref) where legacy_ref is not null;

alter table public.signals add column if not exists legacy_ref text;

create unique index if not exists signals_legacy_ref_uq on public.signals(legacy_ref) where legacy_ref is not null;

alter table public.investment_policies add column if not exists legacy_ref text;

create unique index if not exists investment_policies_legacy_ref_uq on public.investment_policies(legacy_ref) where legacy_ref is not null;

alter table public.portfolio_snapshots add column if not exists legacy_ref text;

create unique index if not exists portfolio_snapshots_legacy_ref_uq on public.portfolio_snapshots(legacy_ref) where legacy_ref is not null;
