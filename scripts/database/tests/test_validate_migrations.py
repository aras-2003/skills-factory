from __future__ import annotations

import unittest

from scripts.database import validate_migrations as validator


class MigrationValidationTests(unittest.TestCase):
    def test_repository_migrations_meet_the_locked_contract(self) -> None:
        self.assertEqual([], validator.validate())

    def test_sql_splitter_keeps_dollar_quoted_blocks_intact(self) -> None:
        parts = validator.split_sql(
            "CREATE FUNCTION public.example() RETURNS text AS $$ BEGIN RETURN 'a;b'; END $$ LANGUAGE plpgsql; "
            "GRANT EXECUTE ON FUNCTION public.example() TO service_role;"
        )
        self.assertEqual(2, len(parts))
        self.assertIn("'a;b'", parts[0])
        self.assertTrue(parts[1].startswith("GRANT EXECUTE"))

    def test_grant_parser_handles_table_lists_and_function_signatures(self) -> None:
        parsed = validator.parse_grants(
            "GRANT SELECT, INSERT ON TABLE public.one, public.two TO service_role; "
            "GRANT EXECUTE ON FUNCTION public.try_numeric(text) TO service_role;"
        )
        self.assertEqual({"SELECT", "INSERT"}, parsed["one"])
        self.assertEqual({"SELECT", "INSERT"}, parsed["two"])
        self.assertEqual({"EXECUTE"}, parsed["try_numeric"])

    def test_quoted_example_text_is_not_classified_as_migration_dml(self) -> None:
        statement = "COMMENT ON TABLE public.accounts IS 'insert into public.accounts';"
        code = validator.code_only(statement).strip()
        self.assertFalse(validator.DML_START.match(code))

    def test_cte_and_direct_data_mutation_are_rejected(self) -> None:
        for sql in ("INSERT INTO public.accounts DEFAULT VALUES;", "WITH doomed AS (SELECT 1) DELETE FROM public.accounts;"):
            with self.subTest(sql=sql):
                roots = [validator.code_only(item).strip() for item in validator.split_sql(sql)]
                self.assertTrue(any(validator.DML_START.match(root) for root in roots))

    def test_default_privilege_grants_are_rejected(self) -> None:
        sql = "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT ON TABLES TO service_role;"
        self.assertIsNotNone(validator.DEFAULT_GRANT.search(sql))

    def test_legacy_schema_revokes_are_safe_when_schema_was_already_removed(self) -> None:
        migration = sorted(validator.MIGRATIONS.glob("*.sql"))[-1].read_text(encoding="utf-8").lower()
        self.assertIn("if to_regnamespace('investment') is not null then", migration)
        self.assertIn("execute 'revoke all on all tables in schema investment", migration)


if __name__ == "__main__":
    unittest.main()
