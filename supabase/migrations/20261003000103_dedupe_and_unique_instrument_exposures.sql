-- DDL-only reconstruction from the applied migration ledger. Seed/operational DML is intentionally omitted.
-- Reconstruction scope: docs/governance/iterations/iteration-04-supabase-grants-2026-10-26.md.

create unique index if not exists ux_instrument_exposures_identity
on public.instrument_exposures (
  instrument_id,
  as_of_date,
  exposure_type,
  exposure_key,
  coalesce(source_id, '00000000-0000-0000-0000-000000000000'::uuid)
);
