"""Create an isolated, lineage-bound package proposal from #617 quarantine.

This command never fetches or executes candidate content and never writes under
canonical skills/ or workflows/. It requires explicit review bound to the exact
intake receipt and matcher report, then validates the copied package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "security"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validate"))
import external_skill_intake as intake  # noqa: E402
from common import load_json, split_frontmatter  # noqa: E402
from validate_skill import validate_skill  # noqa: E402

ALLOWED_DECISIONS = {"IMPORT", "EXTEND", "COMPOSE"}
HEX_64 = re.compile(r"^[a-f0-9]{64}$")
HEX_40 = re.compile(r"^[a-f0-9]{40}$")


class ProposalError(ValueError):
    """Unsafe, stale, or incomplete adaptation proposal input."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProposalError(f"{label} is unreadable JSON") from exc
    if not isinstance(value, dict):
        raise ProposalError(f"{label} must be a JSON object")
    return value


def _validate_source_pin(source: Any) -> None:
    if not isinstance(source, dict):
        raise ProposalError("receipt source identity is missing")
    if not HEX_64.fullmatch(str(source.get("source_digest", ""))):
        raise ProposalError("intake source requires a full source content digest")
    if source.get("type") == "github_repository":
        if not isinstance(source.get("repository"), str) or not HEX_40.fullmatch(str(source.get("commit", ""))):
            raise ProposalError("GitHub source requires repository and full immutable commit SHA")
    elif source.get("type") in {"local_directory", "local_bundle"}:
        if not HEX_64.fullmatch(str(source.get("source_digest", ""))):
            raise ProposalError("local source requires immutable source digest")
    else:
        raise ProposalError("unsupported or unpinned intake source type")


def _validate_receipt(receipt: dict[str, Any], quarantine: Path) -> tuple[str, list[dict[str, Any]], dict[str, bytes]]:
    if receipt.get("schema_version") != intake.SCHEMA_VERSION:
        raise ProposalError("unsupported intake receipt schema")
    inventory_sha = receipt.get("inventory_sha256")
    if not isinstance(inventory_sha, str) or not HEX_64.fullmatch(inventory_sha):
        raise ProposalError("intake receipt inventory digest is invalid")
    if not intake._known_receipt_matches(receipt, inventory_sha):
        raise ProposalError("intake receipt inventory rows or digest are invalid")
    _validate_source_pin(receipt.get("source"))
    security_review = receipt.get("security_review")
    if not isinstance(security_review, dict) or security_review.get("status") not in {"BLOCKED", "REVIEW_REQUIRED"}:
        raise ProposalError("intake security review state is missing or unsupported")
    if security_review.get("status") == "BLOCKED":
        raise ProposalError("blocked security intake cannot become a package proposal")
    if receipt.get("license_decision") not in {"APPROVED", "REVIEW_REQUIRED", "REJECTED", "UNKNOWN"}:
        raise ProposalError("intake license decision is missing or unsupported")
    if receipt.get("license_decision") == "REJECTED":
        raise ProposalError("rejected license intake cannot become a package proposal")
    skill_paths = receipt.get("skill_paths")
    if not isinstance(skill_paths, list) or len(skill_paths) != 1 or not isinstance(skill_paths[0], str):
        raise ProposalError("intake receipt must identify exactly one SKILL.md")
    skill_path = intake.normalize_relative_path(skill_paths[0])
    rows = receipt["files"]
    row_paths = {row["path"] for row in rows}
    if skill_path not in row_paths:
        raise ProposalError("intake SKILL.md is missing from inventory")

    try:
        info = quarantine.lstat()
    except OSError as exc:
        raise ProposalError("quarantine directory is unavailable") from exc
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise ProposalError("quarantine must be a real directory")
    quarantine = quarantine.resolve(strict=True)
    expected: dict[str, dict[str, Any]] = {row["path"]: row for row in rows}
    seen: set[str] = set()
    file_bytes: dict[str, bytes] = {}
    for path in quarantine.rglob("*"):
        relative = path.relative_to(quarantine).as_posix()
        if path.is_symlink():
            raise ProposalError("quarantine contains a symbolic link")
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode) or relative not in expected:
            raise ProposalError("quarantine contains an unexpected or special file")
        raw = path.read_bytes()
        row = expected[relative]
        if len(raw) != row["size_bytes"] or intake.sha256(raw) != row["sha256"]:
            raise ProposalError("quarantine bytes do not match the exact intake receipt")
        seen.add(relative)
        file_bytes[relative] = raw
    if seen != set(expected):
        raise ProposalError("quarantine file set is incomplete")

    skill_prefix = PurePosixPath(skill_path).parent.as_posix()
    if skill_prefix == ".":
        skill_prefix = ""
    package_rows = [row for row in rows if not skill_prefix or row["path"].startswith(skill_prefix + "/")]
    package_paths = [row["path"][len(skill_prefix) + 1:] if skill_prefix else row["path"] for row in package_rows]
    if "SKILL.md" not in package_paths:
        raise ProposalError("selected package does not contain its SKILL.md")
    return skill_path, [{**row, "package_path": package_path} for row, package_path in zip(package_rows, package_paths)], file_bytes


def _validate_review(review: dict[str, Any], receipt: dict[str, Any], matcher_report: dict[str, Any], receipt_sha: str, matcher_sha: str) -> None:
    if review.get("schema_version") != 1:
        raise ProposalError("adaptation review schema_version must be 1")
    if review.get("receipt_sha256") != receipt_sha or review.get("inventory_sha256") != receipt.get("inventory_sha256"):
        raise ProposalError("adaptation review is not bound to the exact intake receipt")
    if review.get("matcher_report_sha256") != matcher_sha:
        raise ProposalError("adaptation review is not bound to the exact matcher report")
    source = review.get("source")
    if not isinstance(source, dict) or source != receipt.get("source"):
        raise ProposalError("adaptation review source identity differs from intake receipt")
    if review.get("approved_decision") != matcher_report.get("decision"):
        raise ProposalError("adaptation review decision differs from matcher report")
    for key in ("reviewer", "rationale"):
        if not isinstance(review.get(key), str) or not review[key].strip():
            raise ProposalError(f"adaptation review requires {key}")
    try:
        timestamp = datetime.fromisoformat(str(review.get("reviewed_at", "")).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProposalError("adaptation review timestamp must be ISO-8601") from exc
    if timestamp.tzinfo is None:
        raise ProposalError("adaptation review timestamp must include timezone")


def _validation_failures(issues: list[Any]) -> list[str]:
    failures = []
    for issue in issues:
        message = str(issue)
        if issue.severity in {"blocker", "high"} or "Supporting files should live under" in message or "Empty optional directory should be removed" in message:
            failures.append(message)
    return failures


def _validate_matcher_report(report: dict[str, Any]) -> None:
    if report.get("schema_version") != 1:
        raise ProposalError("unsupported matcher report schema")
    if not isinstance(report.get("candidate_identity"), str) or not report["candidate_identity"].strip():
        raise ProposalError("matcher report candidate identity is missing")
    if report.get("decision") not in ALLOWED_DECISIONS:
        raise ProposalError("matcher report decision is not an adaptation decision")
    if report.get("human_review_required") is not True or report.get("escalation_required") is not False:
        raise ProposalError("matcher report has no resolved human-approved adaptation decision")
    if report.get("inventory_complete") is not True:
        raise ProposalError("matcher report does not use a complete capability inventory")
    if not isinstance(report.get("reason_codes"), list) or not report["reason_codes"]:
        raise ProposalError("matcher report has no decision rationale")
    matches = report.get("matched_capabilities")
    conflicts = report.get("conflicts")
    comparisons = report.get("comparisons")
    if not isinstance(matches, list) or not all(isinstance(value, str) for value in matches):
        raise ProposalError("matcher report matched capabilities are invalid")
    if not isinstance(conflicts, list) or conflicts:
        raise ProposalError("matcher report contains unresolved conflicts")
    if not isinstance(comparisons, list):
        raise ProposalError("matcher report comparison evidence is missing")
    if report["decision"] == "EXTEND" and len(matches) != 1:
        raise ProposalError("EXTEND requires exactly one matched capability")
    if report["decision"] == "COMPOSE" and len(matches) < 2:
        raise ProposalError("COMPOSE requires at least two matched capabilities")
    if report["decision"] == "IMPORT" and matches:
        raise ProposalError("IMPORT cannot include a matched existing capability")
    for comparison in comparisons:
        if not isinstance(comparison, dict) or not isinstance(comparison.get("identity"), str) or not isinstance(comparison.get("evidence"), dict):
            raise ProposalError("matcher report contains an invalid comparison record")
        if comparison.get("conflict") is not False:
            raise ProposalError("matcher report contains an unresolved comparison conflict")


def _package_digest(rows: list[dict[str, str]]) -> str:
    payload = json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def create_proposal(receipt_path: Path, quarantine_path: Path, matcher_report_path: Path, review_path: Path, output_path: Path, proposed_name: str | None = None) -> dict[str, Any]:
    receipt = _read_json(receipt_path, "intake receipt")
    matcher_report = _read_json(matcher_report_path, "matcher report")
    review = _read_json(review_path, "adaptation review")
    decision = matcher_report.get("decision")
    _validate_matcher_report(matcher_report)
    if decision not in ALLOWED_DECISIONS:
        raise ProposalError("matcher decision does not permit an adaptation proposal")
    receipt_sha = intake.receipt_digest(receipt)
    matcher_sha = hashlib.sha256((json.dumps(matcher_report, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")).hexdigest()
    _validate_review(review, receipt, matcher_report, receipt_sha, matcher_sha)
    skill_path, package_rows, file_bytes = _validate_receipt(receipt, quarantine_path)

    output = output_path.expanduser().absolute()
    if output.exists() or output.is_symlink():
        raise ProposalError("proposal output must not already exist")
    parent = output.parent
    try:
        parent_info = parent.lstat()
    except OSError as exc:
        raise ProposalError("proposal parent directory must already exist") from exc
    if not stat.S_ISDIR(parent_info.st_mode) or stat.S_ISLNK(parent_info.st_mode):
        raise ProposalError("proposal parent must be a real directory")
    resolved_parent = parent.resolve(strict=True)
    resolved_output = resolved_parent / output.name
    canonical_roots = [(REPO_ROOT / name).resolve() for name in ("skills", "workflows")]
    if any(_is_under(resolved_output, canonical) for canonical in canonical_roots):
        raise ProposalError("proposal output cannot be written under canonical skills/ or workflows/")
    quarantine_real = quarantine_path.resolve(strict=True)
    if _is_under(resolved_output, quarantine_real) or _is_under(quarantine_real, resolved_output):
        raise ProposalError("proposal output and quarantine must be separate")

    skill_file_row = next(row for row in package_rows if row["package_path"] == "SKILL.md")
    skill_bytes = file_bytes[skill_file_row["path"]]
    try:
        frontmatter, _ = split_frontmatter(skill_bytes.decode("utf-8"))
    except Exception as exc:
        raise ProposalError("candidate SKILL.md frontmatter cannot be parsed") from exc
    skill_name = proposed_name or frontmatter.get("name")
    if not isinstance(skill_name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_name):
        raise ProposalError("candidate SKILL.md requires a valid name or an explicit --name proposal")

    temporary = Path(tempfile.mkdtemp(prefix=".sf-adaptation-", dir=resolved_parent))
    package = temporary / skill_name
    package.mkdir()
    try:
        package_file_digests: list[dict[str, str]] = []
        for row in sorted(package_rows, key=lambda item: item["package_path"]):
            relative = intake.normalize_relative_path(row["package_path"])
            target = package.joinpath(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(file_bytes[row["path"]])
            package_file_digests.append({"path": relative, "sha256": intake.sha256(target.read_bytes())})

        schema = load_json(REPO_ROOT / "scripts/validate/schemas/skill.schema.json")
        issues = validate_skill(package, schema, root=REPO_ROOT)
        proposal = {
            "schema_version": 1,
            "status": "ADAPTATION_SEED",
            "decision": decision,
            "candidate_identity": matcher_report.get("candidate_identity"),
            "intake_receipt_sha256": receipt_sha,
            "intake_inventory_sha256": receipt["inventory_sha256"],
            "matcher_report_sha256": matcher_sha,
            "source": receipt["source"],
            "source_skill_path": skill_path,
            "author_provenance": receipt.get("author_provenance"),
            "license_decision": receipt.get("license_decision", "UNKNOWN"),
            "license_evidence": receipt.get("license_evidence", []),
            "security_review_status": (receipt.get("security_review") or {}).get("status", "UNKNOWN"),
            "local_modifications": {"status": "NOT_STARTED", "items": []},
            "review": {"reviewer": review["reviewer"], "reviewed_at": review["reviewed_at"], "rationale": review["rationale"]},
            "package_name": skill_name,
            "source_package_files": package_file_digests,
            "source_package_sha256": _package_digest(package_file_digests),
            "seed_validation_issues": [str(issue) for issue in issues],
            "package_files": package_file_digests,
            "package_sha256": _package_digest(package_file_digests),
            "validation_warnings": [str(issue) for issue in issues if issue.severity not in {"blocker", "high"}],
            "automatic_merge_or_publish": False,
            "release_eligible": False,
        }
        (temporary / "proposal.json").write_text(json.dumps(proposal, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, resolved_output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    return {"status": "ADAPTATION_SEED_CREATED", "proposal": str(resolved_output), "package_name": skill_name,
            "package_sha256": proposal["package_sha256"], "receipt_sha256": receipt_sha,
            "decision": decision, "license_decision": proposal["license_decision"], "release_eligible": False}



def finalize_proposal(proposal_path: Path, change_record_path: Path) -> dict[str, Any]:
    proposal = _read_json(proposal_path / "proposal.json", "proposal manifest")
    change_record = _read_json(change_record_path, "change record")
    if proposal.get("status") != "ADAPTATION_SEED":
        raise ProposalError("only an unfinalized adaptation seed can be finalized")
    package_name = proposal.get("package_name")
    if proposal_path.is_symlink() or not proposal_path.is_dir():
        raise ProposalError("proposal path must be a real directory")
    if not isinstance(package_name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", package_name):
        raise ProposalError("proposal package identity is invalid")
    manifest_path = proposal_path / "proposal.json"
    if manifest_path.is_symlink():
        raise ProposalError("proposal manifest cannot be a symbolic link")
    package = proposal_path / package_name
    if package.is_symlink() or not package.is_dir():
        raise ProposalError("proposal package directory is missing or unsafe")
    schema = load_json(REPO_ROOT / "scripts/validate/schemas/skill.schema.json")
    issues = validate_skill(package, schema, root=REPO_ROOT)
    blockers = _validation_failures(issues)
    if blockers:
        raise ProposalError("adapted package fails repository portability validation: " + "; ".join(blockers))

    current: list[dict[str, str]] = []
    for path in package.rglob("*"):
        if path.is_symlink():
            raise ProposalError("adapted package contains a symbolic link")
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ProposalError("adapted package contains a special file")
        relative = path.relative_to(package).as_posix()
        intake.normalize_relative_path(relative)
        current.append({"path": relative, "sha256": intake.sha256(path.read_bytes())})
    current.sort(key=lambda item: item["path"])
    original = {item["path"]: item["sha256"] for item in proposal.get("source_package_files", [])}
    now = {item["path"]: item["sha256"] for item in current}
    changed_paths = sorted(path for path in set(original) | set(now) if original.get(path) != now.get(path))
    if not changed_paths:
        raise ProposalError("adaptation has no local package changes to review")

    if change_record.get("schema_version") != 1 or change_record.get("intake_receipt_sha256") != proposal.get("intake_receipt_sha256"):
        raise ProposalError("change record is not bound to the original intake receipt")
    if change_record.get("source_package_sha256") != proposal.get("source_package_sha256") or change_record.get("matcher_report_sha256") != proposal.get("matcher_report_sha256"):
        raise ProposalError("change record is not bound to the exact source package and matcher report")
    reviewer, rationale = change_record.get("reviewer"), change_record.get("rationale")
    if not isinstance(reviewer, str) or not reviewer.strip() or not isinstance(rationale, str) or not rationale.strip():
        raise ProposalError("change record requires reviewer and rationale")
    try:
        reviewed_at = datetime.fromisoformat(str(change_record.get("reviewed_at", "")).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProposalError("change record timestamp must be ISO-8601") from exc
    if reviewed_at.tzinfo is None:
        raise ProposalError("change record timestamp must include timezone")
    items = change_record.get("changes")
    if not isinstance(items, list):
        raise ProposalError("change record changes must be a list")
    descriptions: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("rationale"), str) or not item["rationale"].strip():
            raise ProposalError("each local change requires a path and rationale")
        if item["path"] in descriptions:
            raise ProposalError("change record contains duplicate paths")
        descriptions[item["path"]] = {"path": item["path"], "rationale": item["rationale"],
                                        "change": "ADDED" if item["path"] not in original else ("REMOVED" if item["path"] not in now else "MODIFIED")}
    if set(descriptions) != set(changed_paths):
        raise ProposalError("change record must describe every added, modified and removed package path exactly")

    proposal.update({
        "status": "FINALIZED_SCOPED_PR_PROPOSAL",
        "local_modifications": {"status": "HUMAN_REVIEWED", "reviewer": reviewer, "reviewed_at": change_record["reviewed_at"],
                                 "rationale": rationale, "items": [descriptions[path] for path in changed_paths]},
        "package_files": current,
        "package_sha256": _package_digest(current),
        "validation_warnings": [str(issue) for issue in issues if issue.severity not in {"blocker", "high"}],
        "release_eligible": False,
    })
    temporary_fd, temporary_name = tempfile.mkstemp(prefix=".proposal-", suffix=".json", dir=proposal_path)
    try:
        with os.fdopen(temporary_fd, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(proposal, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        os.replace(temporary_name, manifest_path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise
    return {"status": proposal["status"], "proposal": str(proposal_path), "package_name": package_name,
            "package_sha256": proposal["package_sha256"], "change_count": len(changed_paths), "release_eligible": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare or finalize an isolated adaptation proposal; never merge or publish.")
    parser.add_argument("--finalize", action="store_true", help="finalize an authored proposal using a reviewed change record")
    parser.add_argument("--change-record", type=Path, help="required with --finalize")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--quarantine", type=Path)
    parser.add_argument("--matcher-report", type=Path)
    parser.add_argument("--review", type=Path, help="human review bound to exact receipt and matcher report")
    parser.add_argument("--output", type=Path, help="new proposal path below an existing real parent directory")
    parser.add_argument("--name", help="explicit proposed package name if upstream frontmatter needs renaming")
    args = parser.parse_args(argv)
    try:
        if args.finalize:
            if not args.output or not args.change_record:
                parser.error("--finalize requires --output (proposal directory) and --change-record")
            result = finalize_proposal(args.output, args.change_record)
        else:
            if not all((args.receipt, args.quarantine, args.matcher_report, args.review, args.output)):
                parser.error("preparation requires --receipt, --quarantine, --matcher-report, --review and --output")
            result = create_proposal(args.receipt, args.quarantine, args.matcher_report, args.review, args.output, proposed_name=args.name)
    except (ProposalError, intake.IntakeError, OSError, ValueError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
