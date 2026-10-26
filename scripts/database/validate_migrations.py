#!/usr/bin/env python3
"""Validate the checked-in DDL-only Investment OS migration contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "supabase" / "migrations"

TABLE_ACCESS = {
    "system_config": {"SELECT"},
    "migration_runs": {"SELECT", "INSERT", "UPDATE"},
    "accounts": {"SELECT", "INSERT", "UPDATE"},
    "instruments": {"SELECT", "INSERT", "UPDATE"},
    "sources": {"SELECT", "INSERT"},
    "transactions": {"SELECT", "INSERT"},
    "portfolio_snapshots": {"SELECT", "INSERT"},
    "position_snapshots": {"SELECT", "INSERT"},
    "theses": {"SELECT", "INSERT"},
    "thesis_versions": {"SELECT", "INSERT"},
    "investment_policies": {"SELECT", "INSERT"},
    "investment_policy_versions": {"SELECT", "INSERT"},
    "market_themes": {"SELECT", "INSERT"},
    "market_theme_versions": {"SELECT", "INSERT"},
    "watchlist": {"SELECT", "INSERT", "UPDATE"},
    "opportunities": {"SELECT", "INSERT"},
    "research_events": {"SELECT", "INSERT"},
    "signals": {"SELECT", "INSERT"},
    "decisions": {"SELECT", "INSERT"},
    "decision_outcomes": {"SELECT", "INSERT"},
    "evidence_links": {"SELECT", "INSERT"},
    "instrument_exposures": {"SELECT", "INSERT", "UPDATE"},
    "legacy_sheet_rows": set(),
    "cutover_events": {"SELECT", "INSERT"},
    "account_valuation_snapshots": {"SELECT", "INSERT"},
    "ppk_fund_allocation_observations": {"SELECT", "INSERT"},
}

SECRET_PATTERNS = (
    re.compile(r"postgres(?:ql)?://[^\s:/]+:[^\s@]+@", re.I),
    re.compile(r"\bsb_secret_[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{30,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(
        r"\b(?:password|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
        re.I,
    ),
)
PUBLIC_CREATE = re.compile(
    r"^CREATE\s+(?:OR\s+REPLACE\s+)?(?P<kind>TABLE|VIEW|MATERIALIZED\s+VIEW|FUNCTION|SEQUENCE)\s+"
    r"(?:IF\s+NOT\s+EXISTS\s+)?(?P<schema>[A-Za-z_][\w]*)\.(?P<name>[A-Za-z_][\w]*)",
    re.I,
)
DML_START = re.compile(r"^(?:INSERT|UPDATE|DELETE|MERGE|TRUNCATE|COPY|WITH)\b", re.I)
GRANT = re.compile(
    r"^GRANT\s+(?P<privileges>[A-Z,\s]+?)\s+ON\s+(?:TABLE\s+)?(?P<objects>.+?)\s+TO\s+service_role\s*$",
    re.I | re.S,
)
DEFAULT_GRANT = re.compile(
    r"ALTER\s+DEFAULT\s+PRIVILEGES[\s\S]*?GRANT\s+[A-Z,\s]+\s+ON\s+(?:TABLES|SEQUENCES|FUNCTIONS)\s+TO\s+(?:PUBLIC|anon|authenticated|service_role)",
    re.I,
)


def split_sql(sql: str) -> list[str]:
    """Split SQL on semicolons outside strings, comments, and dollar blocks."""
    parts: list[str] = []
    start = 0
    index = 0
    state = "normal"
    dollar = ""
    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ""
        if state == "line_comment":
            if char == "\n":
                state = "normal"
            index += 1
            continue
        if state == "block_comment":
            if char == "*" and next_char == "/":
                state = "normal"
                index += 2
            else:
                index += 1
            continue
        if state == "single_quote":
            if char == "'" and next_char == "'":
                index += 2
                continue
            if char == "'":
                state = "normal"
            elif char == "\\":
                index += 2
                continue
            index += 1
            continue
        if state == "double_quote":
            if char == '"' and next_char == '"':
                index += 2
                continue
            if char == '"':
                state = "normal"
            index += 1
            continue
        if state == "dollar_quote":
            if sql.startswith(dollar, index):
                index += len(dollar)
                state = "normal"
            else:
                index += 1
            continue
        if char == "-" and next_char == "-":
            state = "line_comment"
            index += 2
            continue
        if char == "/" and next_char == "*":
            state = "block_comment"
            index += 2
            continue
        if char == "'":
            state = "single_quote"
            index += 1
            continue
        if char == '"':
            state = "double_quote"
            index += 1
            continue
        if char == "$":
            match = re.match(r"\$[A-Za-z_0-9]*\$", sql[index:])
            if match:
                dollar = match.group(0)
                state = "dollar_quote"
                index += len(dollar)
                continue
        if char == ";":
            parts.append(sql[start:index].strip())
            start = index + 1
        index += 1
    if sql[start:].strip():
        parts.append(sql[start:].strip())
    return [part for part in parts if part]


def code_only(sql: str) -> str:
    """Remove comments and ordinary string literals while retaining dollar bodies."""
    output: list[str] = []
    index = 0
    state = "normal"
    dollar = ""
    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ""
        if state == "line_comment":
            if char == "\n":
                state = "normal"
                output.append("\n")
            index += 1
            continue
        if state == "block_comment":
            if char == "*" and next_char == "/":
                state = "normal"
                index += 2
            else:
                index += 1
            continue
        if state == "single_quote":
            if char == "'" and next_char == "'":
                output.append(" ")
                index += 2
                continue
            if char == "'":
                state = "normal"
            output.append(" ")
            index += 1
            continue
        if state == "double_quote":
            if char == '"' and next_char == '"':
                output.append('""')
                index += 2
                continue
            if char == '"':
                state = "normal"
            output.append(char)
            index += 1
            continue
        if state == "dollar_quote":
            if sql.startswith(dollar, index):
                output.append(dollar)
                index += len(dollar)
                state = "normal"
            else:
                output.append(char)
                index += 1
            continue
        if char == "-" and next_char == "-":
            state = "line_comment"
            index += 2
            continue
        if char == "/" and next_char == "*":
            state = "block_comment"
            index += 2
            continue
        if char == "'":
            state = "single_quote"
            output.append(" ")
            index += 1
            continue
        if char == '"':
            state = "double_quote"
            output.append(char)
            index += 1
            continue
        if char == "$":
            match = re.match(r"\$[A-Za-z_0-9]*\$", sql[index:])
            if match:
                dollar = match.group(0)
                state = "dollar_quote"
                output.append(dollar)
                index += len(dollar)
                continue
        output.append(char)
        index += 1
    return "".join(output)


def parse_grants(sql: str) -> dict[str, set[str]]:
    grants: dict[str, set[str]] = {}
    for statement in split_sql(sql):
        code = code_only(statement).strip()
        function_grant = re.match(
            r"^GRANT\s+EXECUTE\s+ON\s+FUNCTION\s+public\.([A-Za-z_][\w]*)\s*\([^)]*\)\s+TO\s+service_role\s*$",
            code,
            re.I | re.S,
        )
        if function_grant:
            grants.setdefault(function_grant.group(1).lower(), set()).add("EXECUTE")
            continue
        match = GRANT.match(code)
        if not match:
            continue
        privileges = {item.strip().upper() for item in match.group("privileges").split(",")}
        objects = match.group("objects").strip()
        if objects.upper().startswith("ALL "):
            continue
        for item in objects.split(","):
            name = item.strip().lower()
            if name.startswith("public."):
                grants.setdefault(name.removeprefix("public."), set()).update(privileges)
    return grants


def validate() -> list[str]:
    errors: list[str] = []
    files = sorted(MIGRATIONS.glob("*.sql"))
    if len(files) != 20:
        errors.append(f"expected 20 migrations (19 reconstructed + 1 security migration), found {len(files)}")
    if any(not re.match(r"^\d{14}_[a-z0-9_]+\.sql$", file.name) for file in files):
        errors.append("migration filenames must use the Supabase 14-digit timestamp format")
    if [file.name for file in files] != sorted(file.name for file in files):
        errors.append("migrations are not lexically chronological")
    if not files or not files[-1].name.endswith("_explicit_private_data_api_grants.sql"):
        errors.append("the explicit private Data API grant migration must be last")

    grant_by_file: dict[Path, dict[str, set[str]]] = {}
    for path in files:
        sql = path.read_text(encoding="utf-8")
        grant_by_file[path] = parse_grants(sql)
        for pattern in SECRET_PATTERNS:
            if pattern.search(sql):
                errors.append(f"{path.relative_to(ROOT)} contains a credential-like value")
                break
        for statement in split_sql(sql):
            code = code_only(statement).strip()
            if DML_START.match(code):
                errors.append(f"{path.relative_to(ROOT)} contains disallowed DML")
                break
            dollar_bodies = re.findall(r"\$[A-Za-z_0-9]*\$([\s\S]*?)\$[A-Za-z_0-9]*\$", statement)
            if any(
                re.search(
                    r"\b(?:INSERT\s+INTO|DELETE\s+FROM|MERGE\s+INTO|TRUNCATE|COPY)\b|\bUPDATE\s+[A-Za-z_][\w.]*\s+SET\b",
                    body,
                    re.I,
                )
                for body in dollar_bodies
            ):
                errors.append(f"{path.relative_to(ROOT)} contains DML in a dollar-quoted code body")
                break
            if re.match(r"^CREATE\s+(?:OR\s+REPLACE\s+)?(?:FUNCTION|PROCEDURE)\b", code, re.I):
                body = code.split("AS", 1)[-1]
                if re.search(r"\b(?:INSERT\s+INTO|DELETE\s+FROM|MERGE\s+INTO|TRUNCATE|COPY)\b", body, re.I):
                    errors.append(f"{path.relative_to(ROOT)} contains DML in a routine body")
                    break
                if re.search(r"\bUPDATE\s+[A-Za-z_][\w.]*\s+SET\b", body, re.I):
                    errors.append(f"{path.relative_to(ROOT)} contains DML in a routine body")
                    break

    # Every public object creator must establish its access boundary in the same migration.
    for path in files:
        sql = path.read_text(encoding="utf-8")
        code = code_only(sql)
        grants = grant_by_file[path]
        for statement in split_sql(sql):
            match = PUBLIC_CREATE.match(code_only(statement).strip())
            if not match or match.group("schema").lower() != "public":
                continue
            kind = re.sub(r"\s+", " ", match.group("kind").upper())
            name = match.group("name").lower()
            if kind == "TABLE":
                expected = TABLE_ACCESS.get(name)
                if expected is None:
                    errors.append(f"{path.name} creates unclassified table public.{name}")
                    continue
                if grants.get(name, set()) != expected:
                    errors.append(
                        f"{path.name} must grant {sorted(expected)} on public.{name} in the creating migration; "
                        f"found {sorted(grants.get(name, set()))}"
                    )
                if not re.search(
                    rf"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?public\.{re.escape(name)}\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY",
                    code,
                    re.I,
                ) and not ("enable row level security" in sql.lower() and f"'{name}'" in sql.lower()):
                    errors.append(f"{path.name} does not enable RLS for public.{name}")
                if name not in ("legacy_sheet_rows",):
                    revoke = re.search(
                        rf"REVOKE\s+ALL\s+ON\s+TABLE\s+public\.{re.escape(name)}\s+FROM\s+PUBLIC\s*,\s*anon\s*,\s*authenticated\s*,\s*service_role",
                        code,
                        re.I,
                    )
                    baseline_revoke = re.search(
                        r"REVOKE\s+ALL\s+ON\s+ALL\s+TABLES\s+IN\s+SCHEMA\s+public\s+FROM\s+PUBLIC\s*,\s*anon\s*,\s*authenticated\s*,\s*service_role",
                        code,
                        re.I,
                    )
                    if not (revoke or baseline_revoke):
                        errors.append(f"{path.name} does not revoke public client access to public.{name}")
            elif kind in {"VIEW", "MATERIALIZED VIEW"}:
                if grants.get(name, set()) != {"SELECT"}:
                    errors.append(f"{path.name} must grant SELECT only on view public.{name}")
                if not re.search(
                    rf"REVOKE\s+ALL\s+ON\s+(?:TABLE\s+)?public\.{re.escape(name)}\s+FROM\s+PUBLIC\s*,\s*anon\s*,\s*authenticated\s*,\s*service_role",
                    code,
                    re.I,
                ):
                    errors.append(f"{path.name} does not revoke client access to view public.{name}")
            elif kind == "FUNCTION":
                if grants.get(name, set()) != {"EXECUTE"}:
                    errors.append(f"{path.name} must grant EXECUTE only on function public.{name}")
                if not re.search(
                    rf"REVOKE\s+ALL\s+ON\s+FUNCTION\s+public\.{re.escape(name)}\s*\([^)]*\)\s+FROM\s+PUBLIC\s*,\s*anon\s*,\s*authenticated\s*,\s*service_role",
                    code,
                    re.I,
                ):
                    errors.append(f"{path.name} does not revoke default function access to public.{name}")

    final_sql = files[-1].read_text(encoding="utf-8") if files else ""
    required_defaults = (
        "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public",
        "REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated, service_role",
        "REVOKE ALL ON SEQUENCES FROM PUBLIC, anon, authenticated, service_role",
        "REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC",
        "REVOKE EXECUTE ON FUNCTIONS FROM anon, authenticated, service_role",
    )
    for required in required_defaults:
        if required.lower() not in final_sql.lower():
            errors.append(f"final migration missing default-privilege gate: {required}")
    for statement in split_sql(final_sql):
        if DEFAULT_GRANT.match(code_only(statement).strip()):
            errors.append("final migration must not grant privileges to future objects by default")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: 20 chronological DDL-only migrations, least-privilege grants, RLS, and future defaults validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
