#!/usr/bin/env python3
"""Prepare source-locked EXTERNAL tester inputs without provider calls.

Lab executor ZIP intentionally excludes these cases. This exports separate
TEST-only handoff envelopes for Site/browser/Desktop/Production testers with
input SHA and rubric digest, never evaluator assertions or credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import iteration02_handoff as parent


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare(root: Path, lab_pack: Path, out: Path) -> dict:
    cfg, errors = parent.validate(root)
    if errors:
        raise ValueError("campaign blocked: " + "; ".join(errors))
    locked_path = lab_pack / "lock.json"
    if not locked_path.is_file() or locked_path.is_symlink():
        raise ValueError("source-locked Lab handoff required")
    lock = json.loads(locked_path.read_text(encoding="utf-8"))
    if not isinstance(lock, dict):
        raise ValueError("malformed Lab lock")
    sha_source = lock.get("source_revision")
    if not isinstance(sha_source, str) or not parent.HEX40.fullmatch(sha_source):
        raise ValueError("invalid locked source revision")
    if lock.get("manifest_sha256") != parent.digest((root / parent.MANIFEST).read_bytes()):
        raise ValueError("campaign manifest changed after source lock")
    if lock.get("runtime_execution_state") != "NOT_RUN" or lock.get("release_approved") is not False:
        raise ValueError("non-pristine Lab handoff")
    by_id = {}
    cases = lock.get("cases")
    if not isinstance(cases, list) or len(cases) != len(cfg["cases"]):
        raise ValueError("locked campaign case set differs from source")
    for row in cases:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or row["id"] in by_id:
            raise ValueError("invalid/duplicate locked case")
        by_id[row["id"]] = row
    if out.exists():
        raise ValueError("will not overwrite existing external tester evidence")
    output = []
    pending = []
    for case in cfg["cases"]:
        n, ch = case["id"], case["channel"]
        row = by_id.get(n)
        if row is None or row.get("channel") != ch or row.get("repetitions") != case["repetitions"]:
            raise ValueError("locked case identity/channel/repetitions mismatch")
        canonical_sha = parent.digest(parent.canonical(case["assertions"]))
        if row.get("rubric_sha256") != canonical_sha:
            raise ValueError("evaluator rubric digest changed")
        if ch == "lab":
            if row.get("dispatch") != "LAB_ONLY_PENDING_EXECUTOR":
                raise ValueError("lab dispatch was changed")
            continue
        if ch not in ("site", "browser", "desktop", "production"):
            raise ValueError("unsupported external surface")
        payload = case["input"].encode("utf-8")
        if row.get("input_path") is not None or sha(payload) != row.get("input_sha256"):
            raise ValueError("external input digest or Lab isolation mismatch")
        output.append((n, ch, payload, row))
    out.mkdir(parents=True)
    for n, ch, payload, row in output:
        folder = out / ch
        folder.mkdir(exist_ok=True)
        fname = n + ".input.md"
        with (folder / fname).open("xb") as f:
            f.write(payload)
        pending.append({
            "case_id": n, "channel": ch, "repetitions": row["repetitions"],
            "input_path": ch + "/" + fname, "input_sha256": sha(payload),
            "rubric_sha256": row["rubric_sha256"],
            "source_revision": sha_source, "release_id": lock.get("release_id"),
            "payload_content_sha256": lock.get("payload_content_sha256"),
            "execution_state": "NOT_RUN", "outcome": None,
            "provider_dispatch": "BLOCKED_PENDING_APPROVAL_AND_INSTALLED_IDENTITY",
            "client_display": "NOT_OBSERVED",
            "independent_evaluator": "NOT_RUN",
        })
    report = {
        "schema_version": "1.0", "kind": "external_test_inputs_only",
        "campaign": cfg["campaign"], "source_revision": sha_source,
        "release_id": lock.get("release_id"),
        "payload_content_sha256": lock.get("payload_content_sha256"),
        "locked_manifest_sha256": lock["manifest_sha256"],
        "cases": pending, "external_case_count": len(pending),
        "planned_attempts": sum(x["repetitions"] for x in pending),
        "provider_calls_executed": False, "runtime_evidence": "NOT_RUN",
        "publication_authorized": False, "release_approved": False,
        "note": "Four separate external surfaces; do not run or publish without each provider's specific approval and observed release identity.",
    }
    (out / "external-lock.json").write_text(
        json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "README.md").write_text(
        "# Iteration 02 EXTERNAL TEST INPUTS — NOT RUN\n\n"
        "Input-only and rubric-isolated. Not a script or permission to run on Site,"
        " browser, Desktop or Production. Each surface requires separate approval,"
        " exact installed source/release/payload, traces and independent evaluator.\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=parent.ROOT)
    p.add_argument("--lab-pack", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        report = prepare(args.root, args.lab_pack, args.output)
        print("EXTERNAL_INPUTS_ONLY_NOT_RUN", report["external_case_count"])
        return 0
    except (ValueError, OSError, TypeError, KeyError) as error:
        print("BLOCKED", type(error).__name__, str(error)[:200])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
