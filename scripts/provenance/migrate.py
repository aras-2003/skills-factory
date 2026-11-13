from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from catalog import migration_audit, migrate_registry, registry_errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reconcile the provenance registry with current skill/workflow source files."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the canonical registry differs from deterministic reconciliation",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    path = root / "provenance" / "registry.yaml"
    audit_path = root / "provenance" / "migration-audit.json"
    current = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None
    reconciled = migrate_registry(root)
    errors = registry_errors(reconciled, root)
    if errors:
        for error in errors:
            print(f"[BLOCKER] {error}")
        return 1
    output = yaml.safe_dump(reconciled, sort_keys=False, allow_unicode=True, width=120)
    if args.check:
        audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.is_file() else None
        if current != reconciled or audit != migration_audit(reconciled):
            print("[BLOCKER] provenance registry or audit is stale; run scripts/provenance/migrate.py")
            return 1
        print(f"Provenance registry: OK ({len(reconciled['records'])} source records)")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output, encoding="utf-8")
    audit_path.write_text(
        json.dumps(migration_audit(reconciled), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Updated provenance registry and audit with {len(reconciled['records'])} source records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
