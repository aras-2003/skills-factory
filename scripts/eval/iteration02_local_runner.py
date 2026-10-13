#!/usr/bin/env python3
"""Idempotent LAB-only controller for an explicitly approved isolated executor.

The runner executes an adapter process, NOT the Lab model itself. It captures
untrusted adapter output for a separate evaluator; NEVER assigns model PASS.
Production/Site/browser/Desktop lanes are always blocked in this controller.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
CASE = re.compile(r"^I02-[0-9]{3}-[a-z0-9-]+$")
ALLOWED_STATES = {"executed", "blocked", "awaiting_runner", "no_steps", "not_executed"}
MAX_PROMPT_BYTES = 256_000
MAX_RESPONSE_BYTES = 512_000


class RunBlocked(ValueError):
    """Fail closed instead of assuming a run happened."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inside(root: Path, child: Path) -> bool:
    return child.resolve().is_relative_to(root.resolve())


def _regular(path: Path) -> bool:
    try:
        return stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink()
    except OSError:
        return False


def verified_case(pack: Path, case_id: str, attempt: int) -> tuple[dict, dict, bytes]:
    """Freeze exact input, release and attempt before invoking any adapter."""
    if not isinstance(case_id, str) or not CASE.fullmatch(case_id):
        raise RunBlocked("invalid case ID")
    if type(attempt) is not int or attempt < 1:
        raise RunBlocked("invalid attempt number")
    manifest = pack / "lock.json"
    if not _regular(manifest):
        raise RunBlocked("missing/nonregular lock")
    lock = json.loads(manifest.read_text(encoding="utf-8"))
    if (not isinstance(lock, dict) or not HEX40.fullmatch(str(lock.get("source_revision", "")))
            or not HEX64.fullmatch(str(lock.get("payload_content_sha256", "")))
            or not isinstance(lock.get("release_id"), str)
            or not lock["release_id"]
            or lock.get("runtime_execution_state") != "NOT_RUN"
            or lock.get("release_approved") is not False):
        raise RunBlocked("unverified or malformed source-locked campaign")
    release_path = pack / "lab-plugin/release-manifest.json"
    if not _regular(release_path):
        raise RunBlocked("Lab release manifest missing")
    release = json.loads(release_path.read_text(encoding="utf-8"))
    for key in ("source_revision", "release_id", "payload_content_sha256"):
        if release.get(key) != lock.get(key):
            raise RunBlocked(f"Lab release mismatch {key}")
    if release.get("channel") != "lab":
        raise RunBlocked("candidate is not an isolated Lab package")
    cases = lock.get("cases")
    if not isinstance(cases, list):
        raise RunBlocked("malformed case inventory")
    found = [x for x in cases if isinstance(x, dict) and x.get("id") == case_id]
    if len(found) != 1:
        raise RunBlocked("missing/duplicate locked case")
    entry = found[0]
    if entry.get("channel") != "lab" or entry.get("dispatch") != "LAB_ONLY_PENDING_EXECUTOR":
        raise RunBlocked("external/unauthorized provider lane")
    repetitions = entry.get("repetitions")
    if type(repetitions) is not int or not 1 <= attempt <= repetitions:
        raise RunBlocked("attempt exceeds locked repetitions")
    rel = entry.get("input_path")
    if rel != f"executor-inputs/{case_id}.input.md":
        raise RunBlocked("case input not restricted to executor inputs")
    path = pack / rel
    if not _inside(pack / "executor-inputs", path) or not _regular(path):
        raise RunBlocked("untrusted or symlink case input")
    data = path.read_bytes()
    if not data or len(data) > MAX_PROMPT_BYTES or sha(data) != entry.get("input_sha256"):
        raise RunBlocked("case input digest/size mismatch")
    if not HEX64.fullmatch(str(entry.get("rubric_sha256", ""))):
        raise RunBlocked("missing evaluator-only rubric pin")
    # The package gives the evaluator only the rubric SHA, never its content.
    return lock, entry, data


def verify_adapter(executable: Path, pinned_digest: str) -> Path:
    if not isinstance(pinned_digest, str) or not HEX64.fullmatch(pinned_digest):
        raise RunBlocked("adapter SHA256 pin required")
    if not executable.is_absolute() or not _regular(executable):
        raise RunBlocked("adapter must be an absolute regular executable, no symlinks")
    if not os.access(executable, os.X_OK):
        raise RunBlocked("adapter is not executable")
    if sha(executable.read_bytes()) != pinned_digest:
        raise RunBlocked("adapter executable digest mismatch")
    return executable


def run_one(pack: Path, archive_root: Path, case_id: str, attempt: int,
            adapter: Path, adapter_sha256: str, *, authorized: bool = False,
            invoke=subprocess.run, timeout: int = 90) -> dict:
    """Reserve once, invoke a pinned executor, and archive untrusted observations."""
    if not authorized:
        raise RunBlocked("explicit --approve-isolated-lab-exec is required")
    if type(timeout) is not int or not 1 <= timeout <= 120:
        raise RunBlocked("timeout outside permitted bounds")
    pack = pack.resolve()
    archive_root = archive_root.resolve()
    if _inside(pack, archive_root) or _inside(archive_root, pack):
        raise RunBlocked("archives must be separate from immutable executor package")
    lock, item, prompt = verified_case(pack, case_id, attempt)
    executable = verify_adapter(adapter, adapter_sha256)
    # The controller cannot prove an OS sandbox. A separate disposable TEST
    # machine/container with denied secrets/network is REQUIRED by operator.
    archive_root.mkdir(parents=True, exist_ok=True)
    runs = archive_root / "runs" / case_id
    runs.mkdir(parents=True, exist_ok=True)
    run_dir = runs / f"{attempt:03d}"
    try:
        run_dir.mkdir(mode=0o700)  # atomic reservation: duplicate invocation never reruns
    except FileExistsError:
        recorded = run_dir / "record.json"
        if not _regular(recorded):
            raise RunBlocked("incomplete prior run; manual recovery required, no automatic retry")
        previous = json.loads(recorded.read_text(encoding="utf-8"))
        if (previous.get("source_revision") != lock["source_revision"]
                or previous.get("case_id") != case_id or previous.get("attempt") != attempt
                or previous.get("input_sha256") != item["input_sha256"]
                or previous.get("adapter_sha256") != adapter_sha256):
            raise RunBlocked("prior run identity mismatch; refuse overwrite")
        previous_status = previous.get("status")
        replay_status = ("ALREADY_ARCHIVED_NO_REEXECUTION"
                         if previous_status == "ADAPTER_REPORTED_EXECUTED_REVIEW_REQUIRED"
                         else "PRIOR_BLOCKED_NO_REEXECUTION")
        return {"status": replay_status, "record_path": recorded.as_posix(),
                "model_behavior_verdict": "NOT_EVALUATED"}

    request = {
        "schema_version": "1.0", "case_id": case_id, "attempt": attempt,
        "release_id": lock["release_id"], "source_revision": lock["source_revision"],
        "payload_content_sha256": lock["payload_content_sha256"],
        "input_sha256": item["input_sha256"],
        "prompt": prompt.decode("utf-8"),
    }
    request_data = (json.dumps(request, sort_keys=True, ensure_ascii=False) + "\n").encode()
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": str(run_dir), "TMPDIR": str(run_dir),
        "SKILLS_FACTORY_EVAL_MODE": "isolated_test",
        "PYTHONNOUSERSITE": "1",
    }
    status, reported, response_bytes = "BLOCKED_ADAPTER", {}, None
    try:
        result = invoke([str(executable)], input=request_data, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, cwd=run_dir, env=env, timeout=timeout,
                        check=False)
        if len(result.stdout or b"") > MAX_RESPONSE_BYTES:
            raise RunBlocked("adapter response exceeds output cap")
        if result.returncode != 0:
            raise RunBlocked("adapter nonzero exit")
        response = json.loads((result.stdout or b"").decode("utf-8"))
        if not isinstance(response, dict):
            raise RunBlocked("adapter response must be a JSON object")
        if response.get("case_id") != case_id or response.get("attempt") != attempt:
            raise RunBlocked("adapter case/attempt mismatch")
        if response.get("source_revision") != lock["source_revision"]:
            raise RunBlocked("adapter source revision mismatch")
        if response.get("execution_state") not in ALLOWED_STATES:
            raise RunBlocked("invalid adapter execution state")
        steps = response.get("steps")
        if not isinstance(steps, list) or any(not isinstance(s, dict) for s in steps):
            raise RunBlocked("adapter steps must be structured list")
        if response["execution_state"] == "executed" and not steps:
            raise RunBlocked("adapter claims executed but has no execution steps")
        if response["execution_state"] != "executed" and steps:
            raise RunBlocked("nonexecuted adapter must not invent steps")
        status = "ADAPTER_REPORTED_EXECUTED_REVIEW_REQUIRED" if steps else "ADAPTER_REPORTED_NOT_RUN"
        response_bytes = result.stdout
        # These are adapter-reported, unverified assertions, not runtime PASS.
        reported = {
            "execution_state": response["execution_state"],
            "steps_sha256": sha(json.dumps(steps, sort_keys=True).encode()),
            "response_sha256": sha(result.stdout),
            "steps_reported": len(steps),
        }
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired, TypeError) as exc:
        reported = {"failure_class": type(exc).__name__}
        status = "BLOCKED_ADAPTER"

    record = {
        "schema_version": "1.0", "kind": "iteration02_local_adapter_controller_receipt",
        "case_id": case_id, "attempt": attempt, "source_revision": lock["source_revision"],
        "release_id": lock["release_id"], "payload_content_sha256": lock["payload_content_sha256"],
        "input_sha256": item["input_sha256"], "rubric_sha256": item["rubric_sha256"],
        "adapter_sha256": adapter_sha256, "status": status, "reported": reported,
        "adapter_process_invoked": True, "provider_execution_attested": False,
        "independent_evaluator": "NOT_RUN", "model_behavior_verdict": "NOT_EVALUATED",
        "external_write_authorized": False, "release_approved": False,
        "operator_must_provide_isolated_test_machine": True,
    }
    # Preserve the exact bounded adapter response so an independent evaluator
    # can inspect actual bytes, not just a self-reported summary or digest.
    # Synthetic TEST data only. Private outputs require approved private storage.
    if response_bytes is not None:
        raw_path = run_dir / "adapter-response.json"
        with raw_path.open("xb") as handle:
            handle.write(response_bytes)
        raw_path.chmod(0o600)
        record["adapter_response_path"] = raw_path.name
    target = run_dir / "record.json"
    # Atomic snapshot. Never overwrite existing evidence.
    temp = run_dir / "record.json.pending"
    with temp.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, sort_keys=True, indent=2, ensure_ascii=False)
        handle.write("\n")
    temp.rename(target)
    target.chmod(0o600)
    return {"status": status, "record_path": target.as_posix(),
            "model_behavior_verdict": "NOT_EVALUATED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--adapter-sha256", required=True)
    parser.add_argument("--approve-isolated-lab-exec", action="store_true")
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()
    try:
        result = run_one(args.pack, args.archive_root, args.case_id, args.attempt,
                         args.adapter, args.adapter_sha256,
                         authorized=args.approve_isolated_lab_exec,
                         timeout=args.timeout)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] in {"ADAPTER_REPORTED_EXECUTED_REVIEW_REQUIRED",
                                         "ALREADY_ARCHIVED_NO_REEXECUTION"} else 1
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_behavior_verdict": "NOT_EVALUATED"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
