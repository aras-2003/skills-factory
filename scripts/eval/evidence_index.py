"""Generate a public-safe index of existing receipts; never rewrite or promote them."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess

import receipt

ROOT = Path(__file__).resolve().parents[2]
SAFE_ID = re.compile(r"[A-Za-z0-9_.+/-]{1,200}\Z")
SAFE_REVISION = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def _parse_timestamp(value: object) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(dt.timezone.utc)


def _utc_text(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _candidate_source_revision(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--verify", "HEAD^{commit}"], cwd=root,
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _candidate_commit_time(root: Path) -> tuple[str | None, str]:
    """Use the exact checked-out candidate commit's committer time as the age anchor."""
    revision = _candidate_source_revision(root)
    if revision is None:
        return None, "CANDIDATE_COMMIT_TIME_UNAVAILABLE"
    try:
        raw = subprocess.check_output(
            ["git", "show", "-s", "--format=%cI", revision], cwd=root,
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None, "CANDIDATE_COMMIT_TIME_UNAVAILABLE"
    parsed = _parse_timestamp(raw)
    if parsed is None:
        return None, "CANDIDATE_COMMIT_TIME_UNAVAILABLE"
    return _utc_text(parsed), "git_commit_committer_timestamp"


def _age_projection(timestamp: object, as_of_utc: str | None, basis: str) -> dict:
    parsed = _parse_timestamp(timestamp)
    if timestamp is None or timestamp == "":
        state = "MISSING_TIMESTAMP"
    elif parsed is None:
        state = "MALFORMED_TIMESTAMP"
    elif as_of_utc is None:
        state = "AS_OF_UNAVAILABLE"
    else:
        as_of = _parse_timestamp(as_of_utc)
        if as_of is None:
            state = "AS_OF_UNAVAILABLE"
        elif parsed > as_of:
            state = "FUTURE_TIMESTAMP"
        else:
            return {"evaluation_timestamp_utc": _utc_text(parsed),
                    "age_days": round((as_of - parsed).total_seconds() / 86400, 6),
                    "age_state": "KNOWN", "age_as_of_utc": _utc_text(as_of),
                    "age_basis": basis}
    return {"evaluation_timestamp_utc": _utc_text(parsed) if parsed is not None else None,
            "age_days": None, "age_state": state, "age_as_of_utc": as_of_utc,
            "age_basis": basis}


def safe_id(value):
    return value if isinstance(value, str) and SAFE_ID.fullmatch(value) else None


def build_index(root: Path) -> dict:
    rows = []
    candidate_revision = _candidate_source_revision(root)
    as_of_utc, age_basis = _candidate_commit_time(root)
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
            timestamp = data["evaluation"].get("timestamp_utc")
            source_revision = data.get("source_revision")
            evidence_scope = data.get("evidence_scope")
            projected_revision = source_revision if isinstance(source_revision, str) and SAFE_REVISION.fullmatch(source_revision) else None
            revision_state = ("MISSING" if source_revision is None else
                              "MALFORMED" if projected_revision is None else
                              "UNKNOWN" if candidate_revision is None else
                              "MATCH" if projected_revision == candidate_revision else "MISMATCH")
            rows.append({
                "receipt_path": path.relative_to(root).as_posix(),
                "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "case_id": safe_id(data["case"].get("id")),
                "component": safe_id(data["component"].get("name")),
                "version": safe_id(data["component"].get("version")),
                "recorded_status": recorded,
                **_age_projection(timestamp, as_of_utc, age_basis),
                "source_revision": projected_revision,
                "source_revision_state": revision_state,
                "evidence_scope": evidence_scope if evidence_scope in receipt.VALID_EVIDENCE_SCOPES else None,
                "receipt_validation": "FAIL" if errors else "PASS",
                "component_identity_matches": identity_matches,
                "compatibility": "NOT_VERIFIED",  # Host/tools/dependencies need separate review.
            })
        except (ValueError, KeyError, TypeError, AttributeError, OSError):
            rows.append({"receipt_path": path.relative_to(root).as_posix(),
                         "evaluation_timestamp_utc": None, "age_days": None,
                         "age_state": "RECEIPT_UNREADABLE", "age_as_of_utc": as_of_utc,
                         "age_basis": age_basis, "source_revision": None,
                         "source_revision_state": "UNKNOWN", "evidence_scope": None,
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
