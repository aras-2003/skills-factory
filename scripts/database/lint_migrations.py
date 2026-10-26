from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "supabase" / "migrations"


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def grants_for(sql: str, name: str, privilege: str) -> bool:
    grants = re.findall(
        r"\bgrant\s+([^;]+?)\s+on\s+([^;]+?)\s+to\s+service_role\b",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for privileges, target in grants:
        if name.lower() in target.lower() and privilege.lower() in privileges.lower():
            return True
        if "all tables in schema public" in target.lower() and privilege.lower() in privileges.lower():
            return True
        if "all functions in schema public" in target.lower() and privilege.lower() in privileges.lower():
            return True
    return False


def revoked_from_clients(sql: str, name: str) -> bool:
    revokes = re.findall(
        r"\brevoke\s+all\s+on\s+([^;]+?)\s+from\s+([^;]+)",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for target, grantees in revokes:
        low = grantees.lower()
        if "anon" in low and "authenticated" in low and ("public" in low):
            if name.lower() in target.lower():
                return True
            if "all tables in schema public" in target.lower():
                return True
            if "all functions in schema public" in target.lower():
                return True
    return False


def main() -> int:
    files = sorted(MIGRATIONS.glob("*.sql"))
    if not files:
        fail("No database migrations found.")
    if any(not re.fullmatch(r"\d{14}_[a-z0-9_]+\.sql", path.name) for path in files):
        fail("Every migration filename must use the timestamp_name.sql format.")

    for path in files:
        sql = path.read_text(encoding="utf-8")
        scrubbed = re.sub(r"--[^\n]*|/\*[\s\S]*?\*/|\$[A-Za-z_0-9]*\$[\s\S]*?\$[A-Za-z_0-9]*\$", " ", sql)
        if re.search(r"\b(?:insert\s+into|update\s+[\w.]+|delete\s+from|truncate\s+table|merge\s+into)\b", scrubbed, re.IGNORECASE):
            fail(f"{path.name}: migration contains top-level data modification; keep private portfolio rows out of migrations.")
        if re.search(r"\b(?:copy\s+[^;]+\s+from\s+program|pg_read_file|pg_ls_dir|lo_import|dblink_exec)\b", sql, re.IGNORECASE):
            fail(f"{path.name}: server-side file or remote execution is forbidden.")
        if re.search(r"\bgrant\b[^;]*\bto\s+(?:public|anon|authenticated)\b", sql, re.IGNORECASE):
            fail(f"{path.name}: public/anon/authenticated grants are forbidden for private Investment OS data.")

        objects = re.findall(
            r"\bcreate\s+(?:or\s+replace\s+)?table\s+(?:if\s+not\s+exists\s+)?public\.([a-z_][a-z0-9_]*)",
            sql,
            re.IGNORECASE,
        )
        objects += re.findall(
            r"\bcreate\s+(?:or\s+replace\s+)?view\s+public\.([a-z_][a-z0-9_]*)",
            sql,
            re.IGNORECASE,
        )
        functions = re.findall(
            r"\bcreate\s+(?:or\s+replace\s+)?function\s+public\.([a-z_][a-z0-9_]*)",
            sql,
            re.IGNORECASE,
        )

        for name in objects:
            if not grants_for(sql, name, "select"):
                fail(f"{path.name}: public object {name} has no same-migration service_role grant.")
            if not revoked_from_clients(sql, name):
                fail(f"{path.name}: public object {name} has no same-migration revoke for PUBLIC/anon/authenticated.")

        for name in functions:
            if not grants_for(sql, name, "execute"):
                fail(f"{path.name}: function {name} has no same-migration service_role EXECUTE grant.")
            if not revoked_from_clients(sql, name):
                fail(f"{path.name}: function {name} has no same-migration revoke for PUBLIC/anon/authenticated.")

        view_definitions = re.findall(
            r"\bcreate\s+(?:or\s+replace\s+)?view\s+public\.([a-z_][a-z0-9_]*)([\s\S]*?\bas\s)",
            sql,
            re.IGNORECASE,
        )
        for name, definition in view_definitions:
            if not re.search(r"security_invoker\s*=\s*true", definition, re.IGNORECASE):
                fail(f"{path.name}: view {name} must be created with security_invoker=true.")

    defaults = (MIGRATIONS / "20261026170000_secure_public_data_api_defaults.sql")
    if not defaults.is_file():
        fail("Missing future-object default-privilege migration.")
    default_sql = re.sub(r"\s+", " ", defaults.read_text(encoding="utf-8").lower())
    for required in (
        "alter default privileges for role postgres in schema public",
        "revoke all on tables from public, anon, authenticated, service_role",
        "grant select, insert, update, delete on tables to service_role",
        "revoke all on sequences from public, anon, authenticated, service_role",
        "grant usage, select on sequences to service_role",
        "revoke execute on functions from anon, authenticated, service_role",
    ):
        if required not in default_sql:
            fail(f"Default-privilege migration is missing: {required}")
    if "alter default privileges for role postgres revoke execute on functions from public" not in default_sql:
        fail("Global PUBLIC EXECUTE default for postgres-created functions must be revoked globally.")

    print(f"Validated {len(files)} migrations: private grants, same-migration object ACLs, and view security.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
