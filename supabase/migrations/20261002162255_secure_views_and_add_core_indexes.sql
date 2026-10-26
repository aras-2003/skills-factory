-- Secure derived views so they respect caller RLS rather than owner privileges.
alter view public.current_policy set (security_invoker = true);

alter view public.current_positions set (security_invoker = true);

alter view public.current_theses set (security_invoker = true);

alter view public.current_watchlist set (security_invoker = true);

alter view public.decision_performance set (security_invoker = true);

alter view public.latest_portfolio_snapshot set (security_invoker = true);

alter view public.portfolio_exposures set (security_invoker = true);

-- The duplicate custom schema created during setup is not canonical.
-- Revoke client-role access instead of dropping it.
revoke all on schema investment from anon, authenticated;

revoke all on all tables in schema investment from anon, authenticated;

revoke all on all sequences in schema investment from anon, authenticated;

-- Common relational indexes for portfolio/research workloads.
create index if not exists idx_position_snapshots_snapshot_id on public.position_snapshots(snapshot_id);

create index if not exists idx_position_snapshots_account_id on public.position_snapshots(account_id);

create index if not exists idx_position_snapshots_instrument_id on public.position_snapshots(instrument_id);

create index if not exists idx_transactions_account_id on public.transactions(account_id);

create index if not exists idx_transactions_instrument_id on public.transactions(instrument_id);

create index if not exists idx_transactions_source_id on public.transactions(source_id);

create index if not exists idx_portfolio_snapshots_source_id on public.portfolio_snapshots(source_id);

create index if not exists idx_portfolio_snapshots_migration_run_id on public.portfolio_snapshots(migration_run_id);

create index if not exists idx_portfolio_snapshots_supersedes on public.portfolio_snapshots(supersedes_snapshot_id);

create index if not exists idx_research_events_instrument_id on public.research_events(instrument_id);

create index if not exists idx_research_events_theme_id on public.research_events(theme_id);

create index if not exists idx_research_events_thesis_id on public.research_events(thesis_id);

create index if not exists idx_signals_instrument_id on public.signals(instrument_id);

create index if not exists idx_signals_theme_id on public.signals(theme_id);

create index if not exists idx_signals_source_id on public.signals(source_id);

create index if not exists idx_opportunities_instrument_id on public.opportunities(instrument_id);

create index if not exists idx_decisions_instrument_id on public.decisions(instrument_id);

create index if not exists idx_decisions_thesis_version_id on public.decisions(thesis_version_id);

create index if not exists idx_decision_outcomes_decision_id on public.decision_outcomes(decision_id);

create index if not exists idx_evidence_links_source_id on public.evidence_links(source_id);

create index if not exists idx_exposures_instrument_id on public.instrument_exposures(instrument_id);

create index if not exists idx_exposures_source_id on public.instrument_exposures(source_id);

create index if not exists idx_watchlist_instrument_id on public.watchlist(instrument_id);

create index if not exists idx_watchlist_thesis_id on public.watchlist(thesis_id);

create index if not exists idx_theses_instrument_id on public.theses(instrument_id);

create index if not exists idx_thesis_versions_supersedes on public.thesis_versions(supersedes);

create index if not exists idx_market_theme_versions_theme_id on public.market_theme_versions(theme_id);

create index if not exists idx_policy_versions_supersedes on public.investment_policy_versions(supersedes);
