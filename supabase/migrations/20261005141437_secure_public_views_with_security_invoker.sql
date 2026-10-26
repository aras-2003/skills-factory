alter view public.draft_theses set (security_invoker = true);

alter view public.latest_valid_snapshot_pair set (security_invoker = true);

alter view public.portfolio_position_changes set (security_invoker = true);

alter view public.portfolio_exposure_source_coverage set (security_invoker = true);
