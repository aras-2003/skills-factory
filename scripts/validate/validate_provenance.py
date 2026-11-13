from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from provenance.catalog import load_registry, migration_audit, registry_digest  # noqa: E402


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    try:
        registry = load_registry(root)
        audit = json.loads((root / "provenance" / "migration-audit.json").read_text(encoding="utf-8"))
        if audit != migration_audit(registry):
            raise ValueError("provenance/migration-audit.json does not match canonical source inventory")
    except Exception as exc:
        print(f"[BLOCKER] provenance registry: {exc}")
        return 1
    counts: dict[str, int] = {}
    for row in registry["records"]:
        key = f"{row['kind']}:{row['classification']}"
        counts[key] = counts.get(key, 0) + 1
    print(json.dumps({"status": "VALID", "record_count": len(registry["records"]), "registry_sha256": registry_digest(registry), "classifications": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
