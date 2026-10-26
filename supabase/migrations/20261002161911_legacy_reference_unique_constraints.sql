-- DDL-only reconstruction from the applied migration ledger. Seed/operational DML is intentionally omitted.
-- Reconstruction scope: docs/governance/iterations/iteration-04-supabase-grants-2026-10-26.md.

drop index if exists public.accounts_legacy_ref_uq;

drop index if exists public.instruments_legacy_ref_uq;

drop index if exists public.sources_legacy_ref_uq;

drop index if exists public.opportunities_legacy_ref_uq;

drop index if exists public.research_events_legacy_ref_uq;

drop index if exists public.signals_legacy_ref_uq;

drop index if exists public.investment_policies_legacy_ref_uq;

drop index if exists public.portfolio_snapshots_legacy_ref_uq;

alter table public.accounts drop constraint if exists accounts_legacy_ref_key;

alter table public.instruments drop constraint if exists instruments_legacy_ref_key;

alter table public.sources drop constraint if exists sources_legacy_ref_key;

alter table public.opportunities drop constraint if exists opportunities_legacy_ref_key;

alter table public.research_events drop constraint if exists research_events_legacy_ref_key;

alter table public.signals drop constraint if exists signals_legacy_ref_key;

alter table public.investment_policies drop constraint if exists investment_policies_legacy_ref_key;

alter table public.portfolio_snapshots drop constraint if exists portfolio_snapshots_legacy_ref_key;

alter table public.accounts add constraint accounts_legacy_ref_key unique(legacy_ref);

alter table public.instruments add constraint instruments_legacy_ref_key unique(legacy_ref);

alter table public.sources add constraint sources_legacy_ref_key unique(legacy_ref);

alter table public.opportunities add constraint opportunities_legacy_ref_key unique(legacy_ref);

alter table public.research_events add constraint research_events_legacy_ref_key unique(legacy_ref);

alter table public.signals add constraint signals_legacy_ref_key unique(legacy_ref);

alter table public.investment_policies add constraint investment_policies_legacy_ref_key unique(legacy_ref);

alter table public.portfolio_snapshots add constraint portfolio_snapshots_legacy_ref_key unique(legacy_ref);
