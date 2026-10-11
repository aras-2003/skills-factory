from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve()
EVAL = HERE.parents[1] / "eval"
sys.path.insert(0, str(EVAL))
import receipt as eval_receipt  # noqa: E402

MAX_EXCEPTION_DAYS = 30


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated frontmatter")
    data = yaml.safe_load(text[4:end]) or {}
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a mapping")
    return data, text[end + 5:]


def production_components(root: Path) -> dict[str, tuple[str, str, str]]:
    result: dict[str, tuple[str, str, str]] = {}
    for skill_file in sorted((root / "skills").rglob("SKILL.md")):
        fm, _ = split_frontmatter(skill_file.read_text(encoding="utf-8"))
        metadata = fm.get("metadata") or {}
        if metadata.get("maturity") == "production":
            result[str(fm["name"])] = (
                "skill",
                str(metadata.get("version") or ""),
                skill_file.relative_to(root).as_posix(),
            )

    registry = yaml.safe_load((root / "workflows" / "runtime-registry.yaml").read_text(encoding="utf-8")) or {}
    for item in registry.get("workflows") or []:
        if not isinstance(item, dict):
            continue
        metadata = item.get("metadata") or {}
        if metadata.get("maturity") == "production":
            result[str(item.get("name"))] = (
                "workflow",
                str(metadata.get("version") or ""),
                str(item.get("workflow") or ""),
            )
    return result


def _date(value: Any, label: str, errors: list[str]) -> dt.date | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{label}: missing date")
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label}: invalid ISO date {value!r}")
        return None


def _validate_verified_receipt(root: Path, name: str, version: str, rec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    raw = rec.get("receipt")
    if not isinstance(raw, str) or not raw:
        return [f"{name}: verified requires receipt"]
    receipt_path = root / raw
    if not receipt_path.is_file():
        return [f"{name}: verified receipt missing: {raw}"]
    try:
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{name}: verified receipt unreadable: {exc}"]

    # The receipt's source revision is the exact tested revision. A later evidence-only
    # commit may contain the receipt; current-version status is anchored by component
    # version/content identity, while source_revision remains immutable provenance.
    errors.extend(
        f"{name}: receipt {err}"
        for err in eval_receipt.validate_receipt_data(
            data,
            root=root,
            current_revision=str(data.get("source_revision") or ""),
        )
    )
    if data.get("evidence_scope") != "current-version":
        errors.append(f"{name}: verified receipt must have evidence_scope=current-version")
    if data.get("evaluation", {}).get("status") != "PASS":
        errors.append(f"{name}: verified receipt must be PASS")
    component = data.get("component", {})
    if component.get("name") != name:
        errors.append(f"{name}: verified receipt component name mismatch")
    if str(component.get("version") or "") != version:
        errors.append(f"{name}: verified receipt component version mismatch")
    return errors


def validate_record(
    root: Path,
    name: str,
    version: str,
    rec: dict[str, Any],
    *,
    review_by: dt.date,
    today: dt.date,
) -> list[str]:
    errors: list[str] = []
    status = rec.get("current_runtime_receipt")
    if status not in {"pending", "verified", "not-required"}:
        return [f"{name}: invalid current_runtime_receipt"]
    if not rec.get("maturity_disposition"):
        errors.append(f"{name}: missing maturity_disposition")
    severity_flag = rec.get("known_high_severity_failure", False)
    if not isinstance(severity_flag, bool):
        errors.append(f"{name}: known_high_severity_failure must be a boolean")
    if severity_flag is not False:
        errors.append(f"{name}: unresolved known high-severity failure blocks readiness disposition")

    if status == "verified":
        errors.extend(_validate_verified_receipt(root, name, version, rec))
        if rec.get("exception_owner") or rec.get("exception_expires"):
            errors.append(f"{name}: verified must not rely on an exception")

    elif status == "pending":
        for field in ("evidence_gap", "limitation"):
            if not rec.get(field):
                errors.append(f"{name}: pending evidence requires {field}")
        disposition = rec.get("maturity_disposition")
        if disposition == "retain-existing-pending-evidence-review":
            for field in ("exception_owner", "exception_expires"):
                if not rec.get(field):
                    errors.append(f"{name}: pending evidence requires {field}")
            expiry = _date(rec.get("exception_expires"), f"{name}: exception_expires", errors)
            if expiry is not None:
                if expiry < today:
                    errors.append(f"{name}: pending exception expired on {expiry.isoformat()}")
                if expiry > review_by:
                    errors.append(f"{name}: exception_expires must not exceed review_by")
                if (expiry - today).days > MAX_EXCEPTION_DAYS:
                    errors.append(f"{name}: pending exception exceeds {MAX_EXCEPTION_DAYS}-day limit")
        elif disposition == "lab-candidate-pending-runtime-validation":
            if rec.get("candidate_channel") != "lab":
                errors.append(f"{name}: Lab candidate must set candidate_channel=lab")
            if rec.get("exception_owner") or rec.get("exception_expires"):
                errors.append(f"{name}: Lab candidate must not rely on an exception")
            if rec.get("receipt"):
                errors.append(f"{name}: pending Lab candidate must not claim a runtime receipt")
        else:
            errors.append(f"{name}: pending has unsupported maturity_disposition")
    elif status == "not-required":
        if not rec.get("not_required_reason"):
            errors.append(f"{name}: not-required requires not_required_reason")
        if rec.get("exception_owner") or rec.get("exception_expires"):
            errors.append(f"{name}: not-required must not use an exception")
    return errors


def validate(root: Path, *, today: dt.date | None = None) -> list[str]:
    errors: list[str] = []
    today = today or dt.datetime.now(dt.timezone.utc).date()
    path = root / "release" / "production-readiness.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    records = data.get("components") or []
    if not isinstance(records, list):
        return ["components must be a list"]

    review_by = _date(data.get("review_by"), "review_by", errors)
    if review_by is None:
        review_by = today
    elif review_by < today:
        errors.append(f"review_by expired on {review_by.isoformat()}")

    actual = production_components(root)
    seen: dict[str, dict[str, Any]] = {}
    for rec in records:
        if not isinstance(rec, dict):
            errors.append("readiness record must be a mapping")
            continue
        name = str(rec.get("name") or "")
        if not name:
            errors.append("readiness record missing name")
            continue
        if name in seen:
            errors.append(f"duplicate readiness record: {name}")
        seen[name] = rec

    missing = sorted(set(actual) - set(seen))
    extra = sorted(set(seen) - set(actual))
    if missing:
        errors.append("missing production readiness records: " + ", ".join(missing))
    if extra:
        errors.append("readiness records for non-production components: " + ", ".join(extra))

    for name, (kind, version, source) in actual.items():
        rec = seen.get(name)
        if not rec:
            continue
        if rec.get("kind") != kind:
            errors.append(f"{name}: kind mismatch")
        if str(rec.get("version")) != version:
            errors.append(f"{name}: version mismatch ({rec.get('version')} != {version})")
        if rec.get("source") != source:
            errors.append(f"{name}: source mismatch")
        errors.extend(validate_record(root, name, version, rec, review_by=review_by, today=today))
    return errors


def main() -> int:
    root = HERE.parents[2]
    errors = validate(root)
    for error in errors:
        print(f"[BLOCKER] release/production-readiness.yaml: {error}")
    if not errors:
        print("Production readiness registry: OK")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
