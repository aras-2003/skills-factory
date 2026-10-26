#!/usr/bin/env bash
set -euo pipefail

: "${PGHOST:?PGHOST must point to a clean PostgreSQL database}"
: "${PGUSER:?PGUSER must be the database migration owner}"
: "${PGDATABASE:?PGDATABASE must name a disposable test database}"

psql --no-psqlrc --set ON_ERROR_STOP=1 --file supabase/tests/bootstrap.sql

for migration in supabase/migrations/*.sql; do
  psql --no-psqlrc --set ON_ERROR_STOP=1 --file "$migration"
done

psql --no-psqlrc --set ON_ERROR_STOP=1 --file supabase/tests/database_security.sql
