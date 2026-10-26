BEGIN;

CREATE TABLE public.sf_future_table_probe (id integer PRIMARY KEY);
CREATE SEQUENCE public.sf_future_sequence_probe;
CREATE FUNCTION public.sf_future_function_probe()
RETURNS integer
LANGUAGE sql
IMMUTABLE
AS $$ SELECT 1 $$;

DO $$
BEGIN
  IF has_table_privilege('anon', 'public.sf_future_table_probe', 'SELECT')
     OR has_table_privilege('anon', 'public.sf_future_table_probe', 'INSERT')
     OR has_table_privilege('anon', 'public.sf_future_table_probe', 'UPDATE')
     OR has_table_privilege('anon', 'public.sf_future_table_probe', 'DELETE')
     OR has_table_privilege('anon', 'public.sf_future_table_probe', 'TRUNCATE')
     OR has_table_privilege('anon', 'public.sf_future_table_probe', 'REFERENCES')
     OR has_table_privilege('anon', 'public.sf_future_table_probe', 'TRIGGER')
     OR has_table_privilege('authenticated', 'public.sf_future_table_probe', 'SELECT')
     OR has_table_privilege('authenticated', 'public.sf_future_table_probe', 'INSERT')
     OR has_table_privilege('authenticated', 'public.sf_future_table_probe', 'UPDATE')
     OR has_table_privilege('authenticated', 'public.sf_future_table_probe', 'DELETE')
     OR has_table_privilege('authenticated', 'public.sf_future_table_probe', 'TRUNCATE')
     OR has_table_privilege('authenticated', 'public.sf_future_table_probe', 'REFERENCES')
     OR has_table_privilege('authenticated', 'public.sf_future_table_probe', 'TRIGGER')
     OR has_table_privilege('service_role', 'public.sf_future_table_probe', 'SELECT')
     OR has_table_privilege('service_role', 'public.sf_future_table_probe', 'INSERT')
     OR has_table_privilege('service_role', 'public.sf_future_table_probe', 'UPDATE')
     OR has_table_privilege('service_role', 'public.sf_future_table_probe', 'DELETE')
     OR has_table_privilege('service_role', 'public.sf_future_table_probe', 'TRUNCATE')
     OR has_table_privilege('service_role', 'public.sf_future_table_probe', 'REFERENCES')
     OR has_table_privilege('service_role', 'public.sf_future_table_probe', 'TRIGGER') THEN
    RAISE EXCEPTION 'future table received an implicit grant';
  END IF;

  IF has_sequence_privilege('anon', 'public.sf_future_sequence_probe', 'USAGE')
     OR has_sequence_privilege('anon', 'public.sf_future_sequence_probe', 'SELECT')
     OR has_sequence_privilege('authenticated', 'public.sf_future_sequence_probe', 'USAGE')
     OR has_sequence_privilege('authenticated', 'public.sf_future_sequence_probe', 'SELECT')
     OR has_sequence_privilege('service_role', 'public.sf_future_sequence_probe', 'USAGE')
     OR has_sequence_privilege('service_role', 'public.sf_future_sequence_probe', 'SELECT') THEN
    RAISE EXCEPTION 'future sequence received an implicit grant';
  END IF;

  IF has_function_privilege('anon', 'public.sf_future_function_probe()', 'EXECUTE')
     OR has_function_privilege('authenticated', 'public.sf_future_function_probe()', 'EXECUTE')
     OR has_function_privilege('service_role', 'public.sf_future_function_probe()', 'EXECUTE') THEN
    RAISE EXCEPTION 'future function received an implicit grant';
  END IF;
END $$;

DROP FUNCTION public.sf_future_function_probe();
DROP SEQUENCE public.sf_future_sequence_probe;
DROP TABLE public.sf_future_table_probe;
COMMIT;
