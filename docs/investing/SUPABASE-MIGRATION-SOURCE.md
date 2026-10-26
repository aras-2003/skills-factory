# Investment OS Supabase migration source

## Authority and reconstruction boundary

The canonical schema is `public`; the historical `investment` schema is noncanonical and private. The production database held 19 applied migration entries, but their SQL files were absent from the repository. For Iteration 04, the source was reconstructed from `supabase_migrations.schema_migrations` with the owner's approval to read migration code.

The checked-in historical files preserve DDL and access-control statements only. Seed and operational DML were deliberately excluded, and no credentials or production row data were copied. A clean replay therefore creates an empty schema, not a copy of production state. Bootstrap/cutover rows must be supplied by a separately authorized deployment step and are not fixtures for this migration suite.

The reconstructed timestamps match the applied ledger. Supabase records applied migration versions, not a source checksum; do not infer that matching versions prove byte-for-byte equivalence. The source reconstruction is explicitly labeled in each file. Future migration changes must be authored from the repository, reviewed as code, and applied only through the approved release path.

## Access model

Only the server-side `service_role` has usage on `public`. `anon`, `authenticated`, and PostgreSQL `PUBLIC` receive no Data API table, view, sequence, or function access. RLS remains enabled on every public data table as defense in depth; private tables intentionally have no client policies. The deprecated `investment` schema has no runtime role access.

The service role receives only operations needed by the current Investment OS persistence contract:

| Object | Service role access |
| --- | --- |
| `system_config` | SELECT |
| `migration_runs`, `accounts`, `instruments`, `watchlist`, `instrument_exposures` | SELECT, INSERT, UPDATE |
| Event and version tables, `cutover_events`, valuation/allocation observations | SELECT, INSERT |
| `legacy_sheet_rows` | No runtime access; migration-owner access only |
| Derived views | SELECT |
| `try_numeric(text)` | EXECUTE |
| Sequences | No current application sequences; future use requires an explicit grant in the creating migration |

Future tables, sequences, and functions receive no default grants, including to `service_role`. Each migration must grant only the privileges its object and caller need. The static validator and disposable Supabase replay enforce this contract.

## Verification

Run `python scripts/database/validate_migrations.py` and `python -m unittest discover -s scripts/database/tests -p 'test_*.py'` for the source-level gate. The CI migration workflow starts a local Supabase stack, replays all checked-in migrations into an empty PostgreSQL 17 database, runs `supabase db lint`, asserts effective role privileges and future-object defaults, and verifies denied client versus allowed server Data API requests.

The remote `investment-os-test` project is a separate runtime check. Never link local CLI commands to production, never run `db push --linked` as part of ordinary CI, and never put a service-role key in source, artifacts, or logs.

## Release and recovery

The final migration changes ACLs and default ACLs only. It does not rewrite rows, disable RLS, or grant access to `anon` or `authenticated`. Before applying it to production, capture the current effective table/view, sequence, function, and `postgres` default ACLs as a deployment receipt. A rollback is forward-only: do not delete an applied migration or restore broad grants. If the server path is denied, pause rollout and add only the missing privilege to the exact object after confirming the persistence contract; preserve client-role denial. For broader recovery, use the pre-deploy ACL receipt to prepare and review a narrowly scoped forward migration. This forward-only recovery guidance is documented but has not been rehearsed against a restore.

The clean replay intentionally has no bootstrap/portfolio rows because migration DML was excluded. This is expected and must not be treated as a complete Investment OS data restore. Runtime checks exercise synthetic rows in disposable CI/local databases. The existing remote test project is data-bearing; its business rows were not read or changed during this verification. Only a temporary empty probe table was used for client-denial checks and then removed. No clean replay or restore was run against that existing project.
