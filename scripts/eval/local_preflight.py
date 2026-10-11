#!/usr/bin/env python3
"""Run deterministic local eval-source preflight; never execute model/browser cases."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKS = (
    ("fixture_isolation", "scripts/eval/validate_isolation.py"),
    ("natural_routing_fixtures", "scripts/eval/validate_routing.py"),
    ("case_schema", "scripts/validate/validate_tests.py"),
)


def preflight(root: Path, *, runner=subprocess.run) -> dict:
    checks = []
    for name, rel in CHECKS:
        command = [sys.executable, rel]
        try:
            result = runner(
                command, cwd=root, check=False, capture_output=True, text=True, timeout=180
            )
            status = "PASS" if result.returncode == 0 else "FAIL"
            detail = (result.stdout or "") + (result.stderr or "")
            checks.append({"name": name, "status": status, "exit_code": result.returncode,
                           "output": detail.strip()})
        except (OSError, subprocess.TimeoutExpired) as exc:
            checks.append({"name": name, "status": "BLOCKED",
                           "exit_code": None, "output": type(exc).__name__})
    return {
        "schema_version": "1.0",
        "kind": "offline_eval_preflight",
        "execution_scope": "local_static_only",
        "runtime_case_execution": "NOT_RUN",
        "runtime_compatibility": "NOT_VERIFIED",
        "overall_status": "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL",
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = preflight(args.root.resolve())
    output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
