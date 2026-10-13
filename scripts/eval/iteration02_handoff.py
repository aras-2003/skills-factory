#!/usr/bin/env python3
"""Build a read-only, source-locked Iteration 2 executor-only Lab test package."""
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
MANIFEST = Path("evals/campaigns/iteration-02-runtime-2026-10/campaign.json")
ISSUES = {149, 240, 242, 243, 247, 250, 251, 252, 253, 254, 256, 257, 259, 286, 287, 289, 290, 311}
CHANNELS = {"lab", "site", "browser", "desktop", "production"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^I02-[0-9]{3}-[a-z0-9-]+$")


def digest(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def canonical(item) -> bytes:
    return json.dumps(item, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def validate(root: Path = ROOT) -> tuple[dict, list[str]]:
    try:
        raw = (root / MANIFEST).read_bytes()
        cfg = json.loads(raw)
    except (OSError, ValueError):
        return {}, ["missing/malformed campaign manifest"]
    if not isinstance(cfg, dict):
        return {}, ["manifest must be an object"]
    errors = []
    if cfg.get("campaign") != "iteration-02-runtime-2026-10" or cfg.get("stage") != "DRAFT_NOT_LOCKED":
        errors.append("campaign stage/identity invalid")
    all_issues = cfg.get("legacy_issues")
    if not isinstance(all_issues, list) or len(all_issues) != len(ISSUES) or set(
        x for x in all_issues if type(x) is int
    ) != ISSUES or any(type(x) is not int for x in all_issues):
        errors.append("exact 18-Issue inventory required")
    cases = cfg.get("cases")
    if not isinstance(cases, list):
        return cfg, errors + ["cases list missing"]
    seen, covered = set(), set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("malformed case")
            continue
        cid = case.get("id")
        if not isinstance(cid, str) or not ID.fullmatch(cid) or cid in seen:
            errors.append(f"invalid/duplicate ID {cid!r}")
            continue
        seen.add(cid)
        n = case.get("issue")
        if type(n) is not int or n not in ISSUES:
            errors.append(f"{cid}: unknown Issue")
        else:
            covered.add(n)
        if case.get("channel") not in CHANNELS:
            errors.append(f"{cid}: unsupported channel")
        if type(case.get("repetitions")) is not int or case["repetitions"] < 1:
            errors.append(f"{cid}: invalid repetitions")
        if case.get("execution_state") != "NOT_RUN":
            errors.append(f"{cid}: premature runtime state")
        prompt = case.get("input")
        if not isinstance(prompt, str) or not prompt.strip() or re.search(r"(?im)^##? (?:evaluator|pass criteria|rubric)", prompt):
            errors.append(f"{cid}: invalid input or evaluator leak")
        a = case.get("assertions")
        if not isinstance(a, dict) or any(
            not isinstance(a.get(key), list) or not a[key] or any(
                not isinstance(v, str) or not v.strip() for v in a[key]
            ) for key in ("must", "must_not")
        ):
            errors.append(f"{cid}: missing private assertions")
    if covered != ISSUES:
        errors.append(f"uncovered issues: {sorted(ISSUES - covered)}")
    gates = cfg.get("manual_gates")
    if not isinstance(gates, list) or any(
        not isinstance(gate, dict) or gate.get("status") not in {"BLOCKED", "NOT_RUN"}
        for gate in gates
    ):
        errors.append("manual gates must remain blocked/not-run")
    return cfg, errors


def prepare(lab: Path, out: Path, root: Path = ROOT) -> dict:
    config, errors = validate(root)
    if errors:
        raise ValueError("; ".join(errors))
    if not lab.is_dir():
        raise ValueError("exact Lab candidate missing")
    release = json.loads((lab / "release-manifest.json").read_text(encoding="utf-8"))
    expected_sha = os.environ.get("SOURCE_REVISION") or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if not isinstance(expected_sha, str) or not HEX40.fullmatch(expected_sha):
        raise ValueError("expected SHA is not exact 40-hex")
    if release.get("source_revision") != expected_sha or not isinstance(release.get("payload_content_sha256"), str) or not HEX64.fullmatch(release["payload_content_sha256"]) or release.get("channel") != "lab":
        raise ValueError("candidate Lab release/source/payload mismatch")
    if not isinstance(release.get("release_id"), str) or not release["release_id"]:
        raise ValueError("candidate release ID missing")
    if out.exists():
        raise ValueError("refusing to overwrite previous tester evidence")
    out.mkdir(parents=True)
    src = out / "executor-inputs"
    src.mkdir()
    lock_cases = []
    for case in config["cases"]:
        cid = case["id"]
        entry = {
            "id": cid, "issue": case["issue"], "channel": case["channel"],
            "repetitions": case["repetitions"], "execution_state": "NOT_RUN",
            "outcome": None,
            "rubric_sha256": digest(canonical(case["assertions"])),
        }
        if case["channel"] == "lab":
            prompt = case["input"].strip() + "\n"
            name = f"{cid}.input.md"
            (src / name).write_text(prompt, encoding="utf-8")
            entry.update({"input_path": "executor-inputs/" + name,
                          "input_sha256": digest(prompt.encode("utf-8")),
                          "dispatch": "LAB_ONLY_PENDING_EXECUTOR"})
        else:
            entry.update({"input_path": None, "input_sha256": digest(case["input"].encode("utf-8")),
                          "dispatch": "BLOCKED_NEEDS_SEPARATE_PROVIDER_AND_APPROVAL"})
        lock_cases.append(entry)
    shutil.copytree(lab, out / "lab-plugin")
    if any(p.name.endswith((".rubric.yaml", ".rubric.yml")) for p in out.rglob("*") if p.is_file()):
        raise ValueError("evaluator rubric file leaked into executor package")
    lock = {
        "schema_version": "1.0", "campaign": config["campaign"],
        "manifest_sha256": digest((root / MANIFEST).read_bytes()),
        "source_revision": expected_sha, "release_id": release["release_id"],
        "payload_content_sha256": release["payload_content_sha256"],
        "cases": lock_cases, "manual_gates": [
            {"id": x["id"], "status": x["status"]} for x in config["manual_gates"]
        ],
        "runtime_execution_state": "NOT_RUN", "outcome": None,
        "release_approved": False, "claim": "TEST_PACKAGE_ONLY_NOT_RUNTIME_PASS"
    }
    (out / "lock.json").write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "README.md").write_text(
        "# Iteration 2 executor pack — NOT_RUN\n\n"
        "Run only lab inputs against the exact packaged Lab in disposable sessions.\n"
        "Browser, Site, Desktop and Production cases are NOT embedded for execution;\n"
        "they require separate authorization, observed identity and independent receipts.\n"
        "Do not show source-only evaluator assertions to the executor.\n",
        encoding="utf-8",
    )
    return lock


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "prepare"))
    parser.add_argument("--lab", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        config, errors = validate()
        if errors:
            print("\n".join("[BLOCKED] " + x for x in errors))
            return 1
        if args.command == "validate":
            print("ITERATION_02_SOURCE_VALID", len(config["cases"]), "cases; runtime NOT_RUN")
            return 0
        if args.lab is None or args.output is None:
            parser.error("prepare requires --lab and --output")
        result = prepare(args.lab, args.output)
        print("PREPARED", result["source_revision"], "runtime NOT_RUN")
        return 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as e:
        print("[BLOCKED]", type(e).__name__, str(e)[:200])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
