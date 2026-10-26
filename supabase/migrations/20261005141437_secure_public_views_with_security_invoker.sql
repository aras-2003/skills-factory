-- DDL-only reconstruction from the applied migration ledger. Seed/operational DML is intentionally omitted.
-- Reconstruction scope: docs/governance/iterations/iteration-04-supabase-grants-2026-10-26.md.

alter view public.draft_theses set (security_invoker = true);

alter view public.latest_valid_snapshot_pair set (security_invoker = true);

alter view public.portfolio_position_changes set (security_invoker = true);

alter view public.portfolio_exposure_source_coverage set (security_invoker = true);
