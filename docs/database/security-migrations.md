# Investment OS database migrations and access tests

The canonical relational schema is `public`. Application migrations are owned by
the PostgreSQL `postgres` role. Runtime database access is server-side through
`service_role`; `anon` and `authenticated` have no access to Investment OS data.
RLS remains enabled as a second deny-by-default layer. A view exposed to the
Data API must be created with `security_invoker = true`.

## Migration source boundary

The 19 historical schema migrations were recovered from the production migration
ledger after a read-only metadata review. Only schema, access-control and view
definition code was added. Three bootstrap/configuration `INSERT` statements and
one existing-row deduplication `WITH` statement were intentionally omitted;
no portfolio rows, operational values or credentials were added. The recovered
files therefore support schema and privilege replay, not data reconciliation.
The production migration ledger already records those historical versions.
Do not apply the reconstructed history to production or treat its omitted
backfills/seeds as completed.

If a local workflow needs canonical bootstrap metadata, it must use synthetic
test fixtures in the disposable test database. Production data stays out of
the migration repository.

## Clean PostgreSQL security replay

`scripts/database/replay_migrations.sh` expects a disposable, empty PostgreSQL
database and the `postgres` migration owner. It creates Supabase-compatible
test roles, simulates the prior broad object defaults, replays the schema
migrations, and runs negative/positive role checks. It never targets either
Supabase project.

The replay verifies:

- new tables and views receive same-migration `service_role` grants;
- `anon` and `authenticated` cannot use the `public` schema or read/write
  private records;
- server-side `service_role` can perform the expected table operations;
- RLS is enabled on every public base table;
- public views use invoker security;
- new table, sequence and function defaults stay private unless a migration
  grants a capability explicitly.

This local/CI test is not a PostgREST or `supabase-js` receipt and does not
restore the paused `investment-os-test` project. Keep issue #387 open until the
isolated Supabase runtime path and its access behavior are verified.
