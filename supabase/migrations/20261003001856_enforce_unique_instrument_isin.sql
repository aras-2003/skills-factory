-- DDL-only reconstruction from the applied migration ledger. Seed/operational DML is intentionally omitted.
-- Reconstruction scope: docs/governance/iterations/iteration-04-supabase-grants-2026-10-26.md.

create unique index if not exists ux_instruments_isin_nonnull
on public.instruments(isin)
where isin is not null;
