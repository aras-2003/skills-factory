#!/usr/bin/env python3
"""Desktop TEST adapter controller for source-locked external campaign cases.

This launches a pinned local *adapter executable*, never ChatGPT Desktop itself.
Adapter stdout is untrusted until independently reviewed with provider traces.
The operator must separately enforce OS/container network and secret isolation.
Site/browser/Production are deliberately not dispatchable here.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path

from iteration02_local_runner import (
    MAX_PROMPT_BYTES, MAX_RESPONSE_BYTES, RunBlocked, _inside, _regular,
    sha, verify_adapter,
)

MAX_OBSERVATION_AGE = dt.timedelta(hours=48)


def _json_regular(path: Path, field: str) -> dict:
    if not _regular(path):
        raise RunBlocked(f"{field}: requires regular file, never symlink")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as error:
        raise RunBlocked(f"{field}: malformed JSON ({type(error).__name__})") from error
    if not isinstance(data, dict):
        raise RunBlocked(f"{field}: must be JSON object")
    return data


def verify_external_case(package: Path, case_id: str, attempt: int) -> tuple[dict, dict, bytes]:
    lock = _json_regular(package / "external-lock.json", "external handoff")
    if (lock.get("kind") != "external_test_inputs_only"
            or lock.get("runtime_evidence") != "NOT_RUN"
            or lock.get("provider_calls_executed") is not False
            or lock.get("release_approved") is not False):
        raise RunBlocked("external handoff must be unexecuted/unsigned baseline")
    source = lock.get("source_revision")
    payload = lock.get("payload_content_sha256")
    release = lock.get("release_id")
    from iteration02_local_runner import HEX40, HEX64, CASE
    if not isinstance(source, str) or not HEX40.fullmatch(source):
        raise RunBlocked("external source revision missing or malformed")
    if not isinstance(payload, str) or not HEX64.fullmatch(payload):
        raise RunBlocked("external payload content SHA missing or malformed")
    if not isinstance(release, str) or not release:
        raise RunBlocked("external candidate release missing")
    if not isinstance(case_id, str) or not CASE.fullmatch(case_id):
        raise RunBlocked("invalid external case ID")
    cases = lock.get("cases")
    if not isinstance(cases, list):
        raise RunBlocked("external cases must be list")
    rows = [c for c in cases if isinstance(c, dict) and c.get("case_id") == case_id]
    if len(rows) != 1:
        raise RunBlocked("missing or duplicate external case")
    item = rows[0]
    if item.get("channel") != "desktop" or item.get("provider_dispatch") != "BLOCKED_PENDING_APPROVAL_AND_INSTALLED_IDENTITY":
        raise RunBlocked("only pinned Desktop TEST cases allowed")
    count = item.get("repetitions")
    if type(attempt) is not int or type(count) is not int or not (1 <= attempt <= count):
        raise RunBlocked("invalid attempt for frozen case")
    for key in ("source_revision", "release_id", "payload_content_sha256"):
        if item.get(key) != lock.get(key):
            raise RunBlocked(f"external case {key} drift")
    rel = f"desktop/{case_id}.input.md"
    if item.get("input_path") != rel:
        raise RunBlocked("Desktop prompt path is not frozen")
    path = package / rel
    if not _inside(package / "desktop", path) or not _regular(path):
        raise RunBlocked("Desktop prompt path is untrusted/symlink")
    prompt = path.read_bytes()
    if not prompt or len(prompt) > MAX_PROMPT_BYTES or sha(prompt) != item.get("input_sha256"):
        raise RunBlocked("Desktop prompt digest/size mismatch")
    from iteration02_local_runner import HEX64
    if not isinstance(item.get("rubric_sha256"), str) or not HEX64.fullmatch(item["rubric_sha256"]):
        raise RunBlocked("rubric digest missing or invalid")
    return lock, item, prompt


def verify_installed_identity(identity_path: Path, lock: dict, *, now: dt.datetime | None = None) -> tuple[dict, str]:
    raw = _json_regular(identity_path, "Desktop installed identity")
    if raw.get("channel") != "desktop" or raw.get("attestation_status") != "verified":
        raise RunBlocked("Desktop installed identity not independently observed")
    for key in ("source_revision", "release_id", "payload_content_sha256"):
        if raw.get(key) != lock.get(key):
            raise RunBlocked(f"Desktop installed identity mismatch: {key}")
    from iteration02_local_runner import HEX64
    schema = raw.get("tool_schema_digest")
    if not isinstance(schema, str) or not HEX64.fullmatch(schema.removeprefix("sha256:")):
        raise RunBlocked("Desktop observed tool schema digest missing")
    reference = raw.get("observation_source")
    if not isinstance(reference, str) or not reference.strip():
        raise RunBlocked("Desktop observation source reference missing")
    timestamp = raw.get("observed_at")
    try:
        observed = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError) as error:
        raise RunBlocked("Desktop observation timestamp malformed") from error
    if observed.tzinfo is None:
        raise RunBlocked("Desktop observation timestamp missing timezone")
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None or observed > now or now - observed > MAX_OBSERVATION_AGE:
        raise RunBlocked("Desktop observation is stale or from the future")
    return raw, sha(identity_path.read_bytes())


def execute_desktop(
    package: Path, archive: Path, identity_path: Path, case_id: str,
    attempt: int, adapter: Path, adapter_sha256: str, *,
    approval_reference: str = "", approved: bool = False, timeout: int = 90,
    now: dt.datetime | None = None, invoke=subprocess.run,
) -> dict:
    if not approved or not isinstance(approval_reference, str) or not approval_reference.strip():
        raise RunBlocked("Desktop TEST execution needs explicit flag and scoped approval reference")
    if type(timeout) is not int or timeout < 1 or timeout > 120:
        raise RunBlocked("Desktop adapter timeout outside bounds")
    package, archive = package.resolve(), archive.resolve()
    if _inside(package, archive) or _inside(archive, package):
        raise RunBlocked("Desktop receipts must be outside input package")
    lock, item, prompt = verify_external_case(package, case_id, attempt)
    identity, identity_sha256 = verify_installed_identity(identity_path, lock, now=now)
    exe = verify_adapter(adapter, adapter_sha256)
    # Never let an existing symlink redirect evidence outside the archive.
    archive.mkdir(mode=0o700, parents=True, exist_ok=True)
    desktop_dir = archive / "desktop"
    if desktop_dir.is_symlink():
        raise RunBlocked("Desktop archive directory must not be symlink")
    desktop_dir.mkdir(mode=0o700, exist_ok=True)
    runs = desktop_dir / case_id
    if runs.is_symlink():
        raise RunBlocked("Desktop case archive directory must not be symlink")
    runs.mkdir(mode=0o700, exist_ok=True)
    target = runs / f"{attempt:03d}"
    try:
        target.mkdir(mode=0o700)
    except FileExistsError:
        if target.is_symlink() or not target.is_dir():
            raise RunBlocked("previous Desktop attempt has unsafe directory")
        record_path = target / "record.json"
        previous = _json_regular(record_path, "previous Desktop attempt")
        for key, expected in (
            ("source_revision", lock["source_revision"]),
            ("release_id", lock["release_id"]),
            ("payload_content_sha256", lock["payload_content_sha256"]),
            ("case_id", case_id), ("attempt", attempt),
            ("adapter_sha256", adapter_sha256),
            ("input_sha256", item["input_sha256"]),
            ("rubric_sha256", item["rubric_sha256"]),
            ("installed_identity_sha256", identity_sha256),
            ("approval_reference", approval_reference),
        ):
            if previous.get(key) != expected:
                raise RunBlocked(f"prior Desktop receipt drift: {key}")
        if previous.get("status") == "ADAPTER_REPORTED_EXECUTED_REVIEW_REQUIRED":
            artifact = target / "adapter-response.json"
            if not _regular(artifact) or sha(artifact.read_bytes()) != previous.get("adapter_response_sha256"):
                raise RunBlocked("prior Desktop adapter output missing or altered")
            return {"status": "ALREADY_ARCHIVED_NO_REEXECUTION", "model_behavior_verdict": "NOT_EVALUATED"}
        return {"status": "PRIOR_BLOCKED_NO_REEXECUTION", "model_behavior_verdict": "NOT_EVALUATED"}

    # Only synthetic input and exact identity are forwarded; no evaluator rubric.
    request = {
        "schema_version": "1.0", "channel": "desktop",
        "case_id": case_id, "attempt": attempt, "prompt": prompt.decode("utf-8"),
        "input_sha256": item["input_sha256"], "source_revision": lock["source_revision"],
        "release_id": lock["release_id"], "payload_content_sha256": lock["payload_content_sha256"],
        "tool_schema_digest": identity["tool_schema_digest"],
    }
    command = (str(exe),)
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(target),
        "TMPDIR": str(target), "PYTHONNOUSERSITE": "1",
        "SKILLS_FACTORY_EVAL_MODE": "synthetic_desktop_test",
    }
    status, info, payload = "BLOCKED_ADAPTER", {}, None
    try:
        result = invoke(command, input=(json.dumps(request, ensure_ascii=False) + "\n").encode(),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        cwd=target, env=env, timeout=timeout, check=False)
        if result.returncode != 0 or len(result.stdout or b"") > MAX_RESPONSE_BYTES:
            raise RunBlocked("Desktop adapter nonzero exit or oversized response")
        response = json.loads((result.stdout or b"").decode("utf-8"))
        if not isinstance(response, dict):
            raise RunBlocked("Desktop adapter response is not an object")
        expected = {"case_id": case_id, "attempt": attempt, "source_revision": lock["source_revision"]}
        if any(response.get(k) != v for k, v in expected.items()):
            raise RunBlocked("Desktop adapter returned unrelated case/attempt/source")
        state, steps = response.get("execution_state"), response.get("steps")
        if state not in {"executed", "blocked", "awaiting_runner", "no_steps", "not_executed"}:
            raise RunBlocked("Desktop adapter execution state invalid")
        if (not isinstance(steps, list) or len(steps) > 100
                or any(not isinstance(x, dict)
                       or not isinstance(x.get("tool"), str) or not x["tool"].strip()
                       or not isinstance(x.get("status"), str) or not x["status"].strip()
                       for x in steps)):
            raise RunBlocked("Desktop adapter steps malformed or unbounded")
        if (state == "executed") != bool(steps):
            raise RunBlocked("Desktop adapter execution state inconsistent with steps")
        info = {"adapter_reported_state": state, "steps_reported": len(steps)}
        status = "ADAPTER_REPORTED_EXECUTED_REVIEW_REQUIRED" if steps else "ADAPTER_REPORTED_NOT_RUN"
        payload = result.stdout
    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired, UnicodeError) as error:
        info = {"failure_class": type(error).__name__}

    record = {
        "schema_version": "1.0", "kind": "iteration02_desktop_adapter_observation",
        "case_id": case_id, "attempt": attempt,
        "source_revision": lock["source_revision"], "release_id": lock["release_id"],
        "payload_content_sha256": lock["payload_content_sha256"],
        "input_sha256": item["input_sha256"], "rubric_sha256": item["rubric_sha256"],
        "installed_identity_sha256": identity_sha256, "adapter_sha256": adapter_sha256,
        "approval_reference": approval_reference,
        "status": status, "reported": info, "adapter_invoked": True,
        "provider_execution_authenticated": False,
        "evaluator_receipt": "NOT_RUN", "model_behavior_verdict": "NOT_EVALUATED",
        "client_display_state": "NOT_OBSERVED", "release_approved": False,
        "isolation": "OPERATOR_ASSERTED_NOT_ENFORCED_BY_SCRIPT",
    }
    if payload is not None:
        path = target / "adapter-response.json"
        with path.open("xb") as f:
            f.write(payload)
        path.chmod(0o600)
        record["adapter_response_sha256"] = sha(payload)
    with (target / "record.json.pending").open("x", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
    (target / "record.json.pending").rename(target / "record.json")
    (target / "record.json").chmod(0o600)
    return {"status": status, "record_path": str(target / "record.json"),
            "model_behavior_verdict": "NOT_EVALUATED"}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--external-pack", type=Path, required=True)
    p.add_argument("--archive-root", type=Path, required=True)
    p.add_argument("--installed-desktop-identity", type=Path, required=True)
    p.add_argument("--case-id", required=True)
    p.add_argument("--attempt", type=int, required=True)
    p.add_argument("--adapter", type=Path, required=True)
    p.add_argument("--adapter-sha256", required=True)
    p.add_argument("--approval-reference", required=True)
    p.add_argument("--approve-isolated-desktop-test", action="store_true")
    args = p.parse_args()
    try:
        out = execute_desktop(
            args.external_pack, args.archive_root, args.installed_desktop_identity,
            args.case_id, args.attempt, args.adapter, args.adapter_sha256,
            approval_reference=args.approval_reference,
            approved=args.approve_isolated_desktop_test,
        )
        print(json.dumps(out, sort_keys=True, indent=2))
        return int(out["status"] not in {
            "ADAPTER_REPORTED_EXECUTED_REVIEW_REQUIRED", "ALREADY_ARCHIVED_NO_REEXECUTION"
        })
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"status": "BLOCKED", "error": str(error),
                          "model_behavior_verdict": "NOT_EVALUATED"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
