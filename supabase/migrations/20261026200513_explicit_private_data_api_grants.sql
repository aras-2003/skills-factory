-- Keep canonical Investment OS data server-side and opt in to access explicitly.
-- Supabase Data API table grants and RLS are separate controls; both are covered here.

REVOKE ALL ON SCHEMA public FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SCHEMA public TO service_role;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC, anon, authenticated, service_role;
DO $$
DECLARE
  column_grant record;
BEGIN
  FOR column_grant IN
    SELECT table_schema, table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = 'public'
  LOOP
    EXECUTE format(
      'REVOKE ALL (%I) ON TABLE %I.%I FROM PUBLIC, anon, authenticated, service_role',
      column_grant.column_name,
      column_grant.table_schema,
      column_grant.table_name
    );
  END LOOP;
END $$;
GRANT SELECT ON TABLE public.system_config, public.current_policy, public.current_positions,
  public.current_theses, public.current_watchlist, public.decision_performance, public.draft_theses,
  public.investment_account_exposure_inventory_v1, public.latest_portfolio_snapshot,
  public.latest_valid_snapshot_pair, public.portfolio_exposure_source_coverage,
  public.portfolio_exposures, public.portfolio_position_changes, public.ppk_exposure_summary,
  public.ppk_fund_exposures TO service_role;
GRANT SELECT, INSERT, UPDATE ON TABLE public.accounts, public.instruments, public.watchlist,
  public.instrument_exposures, public.migration_runs TO service_role;
GRANT SELECT, INSERT ON TABLE public.sources, public.transactions, public.portfolio_snapshots,
  public.position_snapshots, public.theses, public.thesis_versions, public.investment_policies,
  public.investment_policy_versions, public.market_themes, public.market_theme_versions,
  public.opportunities, public.research_events, public.signals, public.decisions,
  public.decision_outcomes, public.evidence_links, public.cutover_events,
  public.account_valuation_snapshots, public.ppk_fund_allocation_observations TO service_role;

REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC, anon, authenticated, service_role;

REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC, anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.try_numeric(text) TO service_role;

-- Some current installations have already removed the deprecated duplicate schema.
-- When present, keep it inaccessible to every runtime role.
DO $legacy_schema$
BEGIN
  IF to_regnamespace('investment') IS NOT NULL THEN
    EXECUTE 'REVOKE ALL ON SCHEMA investment FROM PUBLIC, anon, authenticated, service_role';
    EXECUTE 'REVOKE ALL ON ALL TABLES IN SCHEMA investment FROM PUBLIC, anon, authenticated, service_role';
    EXECUTE 'REVOKE ALL ON ALL SEQUENCES IN SCHEMA investment FROM PUBLIC, anon, authenticated, service_role';
    EXECUTE 'REVOKE ALL ON ALL FUNCTIONS IN SCHEMA investment FROM PUBLIC, anon, authenticated, service_role';
  END IF;
END $legacy_schema$;

-- Migrations execute as postgres. Future objects remain private unless their migration grants access.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated, service_role;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  REVOKE ALL ON SEQUENCES FROM PUBLIC, anon, authenticated, service_role;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres
  REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  REVOKE EXECUTE ON FUNCTIONS FROM anon, authenticated, service_role;
