#!/usr/bin/env python3
"""Bind synthetic Iteration 1 acceptance cases to an exact Lab; never execute them."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path("evals/campaigns/iteration-01-safety-governance-2026-10/campaign.json")
ISSUES = {160, 233, 234, 245, 246, 248, 249, 258, 291, 303}
CASE_ID = re.compile(r"^I01-[A-Z]+-[0-9]{3}$")
HEX40 = re.compile(r"^[a-f0-9]{40}$")
HEX64 = re.compile(r"^[a-f0-9]{64}$")
LEAK = re.compile(r"^##\s+(?:evaluator rubric|pass criteria|expected behavior|failure conditions)\b", re.I | re.M)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def validate(root: Path = ROOT) -> tuple[dict, list[str]]:
    data = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}, ["manifest must be a JSON object"]
    errors = []
    if data.get("campaign") != "iteration-01-safety-governance-2026-10":
        errors.append("invalid campaign identity")
    if data.get("source_status") != "PLANNED_NOT_EXECUTED" or data.get("execution_channel") != "lab":
        errors.append("test pack must be unexecuted isolated Lab")
    issues = data.get("issues")
    if not isinstance(issues, list) or len(issues) != 10 or {
        row.get("issue") for row in issues if isinstance(row, dict)
    } != ISSUES:
        errors.append("exact 10-Issue inventory required")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        return data, errors + ["missing cases"]
    seen: set[str] = set()
    covered: set[int] = set()
    for row in cases:
        if not isinstance(row, dict):
            errors.append("malformed case")
            continue
        cid = row.get("id")
        if not isinstance(cid, str) or not CASE_ID.fullmatch(cid) or cid in seen:
            errors.append(f"duplicate/malformed ID: {cid!r}")
            continue
        seen.add(cid)
        issue = row.get("issue")
        if type(issue) is not int or issue not in ISSUES:
            errors.append(f"{cid}: unknown Issue")
        else:
            covered.add(issue)
        if row.get("execution_state") != "NOT_RUN" or row.get("surface") != "lab":
            errors.append(f"{cid}: must be Lab NOT_RUN")
        if type(row.get("requires_isolated_test_store")) is not bool:
            errors.append(f"{cid}: missing TEST-store boolean")
        n = row.get("repetitions")
        if type(n) is not int or n < 1:
            errors.append(f"{cid}: invalid repetitions")
        prompt = row.get("input")
        if not isinstance(prompt, str) or not prompt.strip() or LEAK.search(prompt):
            errors.append(f"{cid}: missing input or rubric leak")
        assertions = row.get("assertions")
        if not isinstance(assertions, dict) or not all(
            isinstance(assertions.get(k), list) and assertions[k] and
            all(isinstance(t, str) and t.strip() for t in assertions[k])
            for k in ("must", "must_not")
        ):
            errors.append(f"{cid}: invalid evaluator assertions")
    if covered != ISSUES:
        errors.append(f"uncovered Issues: {sorted(ISSUES - covered)}")
    gates = data.get("manual_gates")
    if not isinstance(gates, list) or not gates or any(
        not isinstance(row, dict) or row.get("status") not in {"NOT_RUN", "BLOCKED"}
        for row in gates
    ):
        errors.append("manual gates must start NOT_RUN/BLOCKED")
    return data, errors


def prepare(lab: Path, out: Path, root: Path = ROOT) -> dict:
    cfg, errors = validate(root)
    if errors:
        raise ValueError("; ".join(errors))
    if not lab.is_dir():
        raise ValueError("exact-candidate Lab artifact missing")
    release = json.loads((lab / "release-manifest.json").read_text(encoding="utf-8"))
    plugin = json.loads((lab / "plugin.json").read_text(encoding="utf-8"))
    expected = os.environ.get("SOURCE_REVISION") or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    revision, payload = release.get("source_revision"), release.get("payload_content_sha256")
    if not isinstance(expected, str) or not HEX40.fullmatch(expected):
        raise ValueError("expected source revision must be 40 hex characters")
    if revision != expected or not isinstance(payload, str) or not HEX64.fullmatch(payload):
        raise ValueError("candidate Lab source/digest mismatch")
    if release.get("channel") != "lab" or plugin.get("name") != "skills-factory-lab":
        raise ValueError("wrong package channel")
    if not isinstance(release.get("release_id"), str) or not release["release_id"]:
        raise ValueError("missing candidate Lab release ID")
    if out.exists():
        raise ValueError("refusing to overwrite previous campaign evidence")
    out.mkdir(parents=True)
    inputs = out / "executor-inputs"
    inputs.mkdir()
    queue = ["# Iteration 1 unassisted executor queue", "",
             "Use ONLY the attached Lab version, never production.",
             "Do not provide the evaluator-only source manifest to the executor.",
             "All outcomes remain NOT_RUN until actual trace and independent evaluation.", ""]
    case_lock = []
    for case in cfg["cases"]:
        name = case["id"] + ".input.md"
        content = case["input"].rstrip() + "\n"
        (inputs / name).write_text(content, encoding="utf-8")
        case_lock.append({
            "id": case["id"], "issue": case["issue"],
            "input_path": "executor-inputs/" + name,
            "input_sha256": digest(content.encode("utf-8")),
            "rubric_sha256": digest(canonical(case["assertions"])),
            "repetitions": case["repetitions"],
            "requires_isolated_test_store": case["requires_isolated_test_store"],
            "execution_state": "NOT_RUN", "outcome": None,
        })
        queue.extend(["## " + case["id"], "", case["input"].rstrip(), ""])
    shutil.copytree(lab, out / "lab-plugin")
    if any(p.name.endswith(".rubric.yaml") for p in out.rglob("*") if p.is_file()):
        raise ValueError("rubric leaked into executor artifact")
    lock = {
        "schema_version": "1.0", "campaign": cfg["campaign"],
        "campaign_manifest_sha256": digest((root / MANIFEST).read_bytes()),
        "source_revision": revision, "release_id": release["release_id"],
        "lab_version": plugin.get("version"), "payload_content_sha256": payload,
        "cases": case_lock, "manual_gates": [
            {"id": g["id"], "status": g["status"], "issues": g["issues"]}
            for g in cfg["manual_gates"]
        ], "runtime_execution_state": "NOT_RUN", "outcome": None,
        "claim": "SOURCE_PACKAGING_ONLY_NOT_RUNTIME_PASS",
    }
    (out / "lock.json").write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "QUEUE.md").write_text("\n".join(queue) + "\n", encoding="utf-8")
    return lock


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "prepare"])
    parser.add_argument("--lab", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        data, errors = validate()
        if errors:
            for item in errors:
                print("[BLOCKER]", item)
            return 1
        if args.command == "validate":
            print("Iteration 1: STATIC_VALID; cases:", len(data["cases"]), "; runtime: NOT_RUN")
            return 0
        if not args.lab or not args.output:
            parser.error("prepare requires --lab and --output")
        lock = prepare(args.lab, args.output)
        print("Prepared", args.output, lock["source_revision"], "NOT_RUN")
        return 0
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print("[BLOCKER]", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
