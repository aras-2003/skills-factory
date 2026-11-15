"""Generate a public-safe index of existing receipts; never rewrite or promote them."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import receipt

ROOT = Path(__file__).resolve().parents[2]
SAFE_ID = re.compile(r"[A-Za-z0-9_.+/-]{1,200}\Z")


def safe_id(value):
    return value if isinstance(value, str) and SAFE_ID.fullmatch(value) else None


def build_index(root: Path) -> dict:
    rows = []
    for path in sorted((root / "evals/results").rglob("*.json")):
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not all(k in data for k in ("case", "component", "evaluation")):
                continue
            errors = receipt.validate_receipt_data(data, root=root,
                                                  current_revision=str(data.get("source_revision") or ""))
            version, digest = receipt.current_component_identity(root, data["component"]["name"])
            identity_matches = (version == data["component"].get("version") and
                                digest == data["component"].get("content_sha256"))
            recorded = data["evaluation"].get("status")
            if recorded not in receipt.VALID_STATUSES:
                recorded = "INVALID"
            rows.append({
                "receipt_path": path.relative_to(root).as_posix(),
                "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "case_id": safe_id(data["case"].get("id")),
                "component": safe_id(data["component"].get("name")),
                "version": safe_id(data["component"].get("version")),
                "recorded_status": recorded,
                "receipt_validation": "FAIL" if errors else "PASS",
                "component_identity_matches": identity_matches,
                "compatibility": "NOT_VERIFIED",  # Host/tools/dependencies need separate review.
            })
        except (ValueError, KeyError, TypeError, AttributeError, OSError):
            rows.append({"receipt_path": path.relative_to(root).as_posix(),
                         "receipt_validation": "FAIL", "compatibility": "NOT_VERIFIED"})
    return {"schema_version": "1.0", "kind": "derived_receipt_index", "receipts": rows,
            "runtime_pass_claim": False, "production_approved": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = build_index(args.root.resolve())
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Indexed {len(report['receipts'])} historical receipts; no runtime/release approval inferred")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
