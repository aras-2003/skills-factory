DO $$
DECLARE
  bad_object text;
BEGIN
  IF has_schema_privilege('anon', 'public', 'USAGE')
     OR has_schema_privilege('authenticated', 'public', 'USAGE')
     OR NOT has_schema_privilege('service_role', 'public', 'USAGE') THEN
    RAISE EXCEPTION 'public schema usage does not match the server-only contract';
  END IF;

  IF to_regnamespace('investment') IS NOT NULL AND (
       has_schema_privilege('anon', 'investment', 'USAGE')
       OR has_schema_privilege('authenticated', 'investment', 'USAGE')
       OR has_schema_privilege('service_role', 'investment', 'USAGE')
     ) THEN
    RAISE EXCEPTION 'deprecated investment schema is accessible to a runtime role';
  END IF;

  SELECT c.relname INTO bad_object
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p') AND NOT c.relrowsecurity
  LIMIT 1;
  IF bad_object IS NOT NULL THEN
    RAISE EXCEPTION 'RLS is not enabled for public table %', bad_object;
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p', 'v', 'm')
      AND (
        has_table_privilege('anon', c.oid, 'SELECT')
        OR has_table_privilege('anon', c.oid, 'INSERT')
        OR has_table_privilege('anon', c.oid, 'UPDATE')
        OR has_table_privilege('anon', c.oid, 'DELETE')
        OR has_table_privilege('anon', c.oid, 'TRUNCATE')
        OR has_table_privilege('anon', c.oid, 'REFERENCES')
        OR has_table_privilege('anon', c.oid, 'TRIGGER')
        OR has_table_privilege('authenticated', c.oid, 'SELECT')
        OR has_table_privilege('authenticated', c.oid, 'INSERT')
        OR has_table_privilege('authenticated', c.oid, 'UPDATE')
        OR has_table_privilege('authenticated', c.oid, 'DELETE')
        OR has_table_privilege('authenticated', c.oid, 'TRUNCATE')
        OR has_table_privilege('authenticated', c.oid, 'REFERENCES')
        OR has_table_privilege('authenticated', c.oid, 'TRIGGER')
      )
  ) THEN
    RAISE EXCEPTION 'anon or authenticated has table/view privileges in public';
  END IF;

  IF EXISTS (
    WITH expected(table_name, can_select, can_insert, can_update, can_delete) AS (
      VALUES
        ('system_config', true, false, false, false),
        ('migration_runs', true, true, true, false),
        ('accounts', true, true, true, false),
        ('instruments', true, true, true, false),
        ('sources', true, true, false, false),
        ('transactions', true, true, false, false),
        ('portfolio_snapshots', true, true, false, false),
        ('position_snapshots', true, true, false, false),
        ('theses', true, true, false, false),
        ('thesis_versions', true, true, false, false),
        ('investment_policies', true, true, false, false),
        ('investment_policy_versions', true, true, false, false),
        ('market_themes', true, true, false, false),
        ('market_theme_versions', true, true, false, false),
        ('watchlist', true, true, true, false),
        ('opportunities', true, true, false, false),
        ('research_events', true, true, false, false),
        ('signals', true, true, false, false),
        ('decisions', true, true, false, false),
        ('decision_outcomes', true, true, false, false),
        ('evidence_links', true, true, false, false),
        ('instrument_exposures', true, true, true, false),
        ('legacy_sheet_rows', false, false, false, false),
        ('cutover_events', true, true, false, false),
        ('account_valuation_snapshots', true, true, false, false),
        ('ppk_fund_allocation_observations', true, true, false, false)
    )
    SELECT 1
    FROM expected e
    LEFT JOIN pg_namespace n ON n.nspname = 'public'
    LEFT JOIN pg_class c ON c.relname = e.table_name AND c.relnamespace = n.oid
    WHERE c.oid IS NULL
      OR has_table_privilege('service_role', c.oid, 'SELECT') IS DISTINCT FROM e.can_select
      OR has_table_privilege('service_role', c.oid, 'INSERT') IS DISTINCT FROM e.can_insert
      OR has_table_privilege('service_role', c.oid, 'UPDATE') IS DISTINCT FROM e.can_update
      OR has_table_privilege('service_role', c.oid, 'DELETE') IS DISTINCT FROM e.can_delete
      OR has_table_privilege('service_role', c.oid, 'TRUNCATE')
      OR has_table_privilege('service_role', c.oid, 'REFERENCES')
      OR has_table_privilege('service_role', c.oid, 'TRIGGER')
  ) THEN
    RAISE EXCEPTION 'service_role privileges differ from the least-privilege table map';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
      AND c.relname <> 'legacy_sheet_rows'
      AND NOT has_table_privilege('service_role', c.oid, 'SELECT')
  ) THEN
    RAISE EXCEPTION 'service_role is missing required SELECT on a canonical table';
  END IF;

  IF has_table_privilege('service_role', 'public.legacy_sheet_rows', 'SELECT')
     OR has_table_privilege('service_role', 'public.legacy_sheet_rows', 'INSERT')
     OR has_table_privilege('service_role', 'public.legacy_sheet_rows', 'UPDATE')
     OR has_table_privilege('service_role', 'public.legacy_sheet_rows', 'DELETE') THEN
    RAISE EXCEPTION 'legacy_sheet_rows must remain unavailable to the runtime role';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind IN ('v', 'm')
      AND NOT has_table_privilege('service_role', c.oid, 'SELECT')
  ) THEN
    RAISE EXCEPTION 'service_role is missing SELECT on a derived view';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND (
        has_function_privilege('anon', p.oid, 'EXECUTE')
        OR has_function_privilege('authenticated', p.oid, 'EXECUTE')
      )
  ) THEN
    RAISE EXCEPTION 'a public function is executable by anon/authenticated';
  END IF;
  IF NOT has_function_privilege('service_role', 'public.try_numeric(text)'::regprocedure, 'EXECUTE') THEN
    RAISE EXCEPTION 'service_role cannot execute the required numeric parser';
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND p.oid <> 'public.try_numeric(text)'::regprocedure
      AND has_function_privilege('service_role', p.oid, 'EXECUTE')
  ) THEN
    RAISE EXCEPTION 'service_role has an unapproved public function grant';
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind = 'S'
      AND (
        has_sequence_privilege('anon', c.oid, 'USAGE')
        OR has_sequence_privilege('anon', c.oid, 'SELECT')
        OR has_sequence_privilege('authenticated', c.oid, 'USAGE')
        OR has_sequence_privilege('authenticated', c.oid, 'SELECT')
      )
  ) THEN
    RAISE EXCEPTION 'anon/authenticated has sequence privileges';
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind = 'S'
      AND (
        has_sequence_privilege('service_role', c.oid, 'USAGE')
        OR has_sequence_privilege('service_role', c.oid, 'SELECT')
        OR has_sequence_privilege('service_role', c.oid, 'UPDATE')
      )
  ) THEN
    RAISE EXCEPTION 'service_role has unexpected access to a sequence';
  END IF;
END $$;
