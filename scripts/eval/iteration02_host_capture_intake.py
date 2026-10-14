"""Ingest real cua_repl Work/Desktop captures against the canonical runner lock.

No UI calls, model verdict or client authenticity is invented by this intake.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from iteration02_local_runner import RunBlocked, verified_case, _regular
from iteration02_desktop_runner import verify_external_case
from iteration02_browser_evidence import read_evidence


def ingest(package: Path, capture_file: Path) -> dict:
    for node in (capture_file.absolute(), *capture_file.absolute().parents):
        if node.is_symlink():
            raise RunBlocked("symlink host capture path")
    if not _regular(capture_file):
        raise RunBlocked("regular host capture required")
    capture = json.loads(capture_file.read_text())
    if capture.get("kind") != "cua_host_capture":
        raise RunBlocked("unsupported host capture")
    channel = capture.get("channel")
    if channel == "desktop":
        lock, case, prompt = verify_external_case(package, capture.get("case_id"), capture.get("attempt"))
    elif channel == "work":
        lock, case, prompt = verified_case(package, capture.get("case_id"), capture.get("attempt"))
    else:
        raise RunBlocked("use browser evidence binder for browser lane")
    for key in ("source_revision", "release_id", "payload_content_sha256"):
        if capture.get(key) != lock.get(key):
            raise RunBlocked("host capture candidate drift: " + key)
    if capture.get("input_sha256") != hashlib.sha256(prompt).hexdigest():
        raise RunBlocked("host capture prompt drift")
    if (capture.get("execution_state") != "executed" or not capture.get("approval_reference")
            or not capture.get("installed_observation_source") or not capture.get("response")
            or capture.get("model_behavior_verdict") != "NOT_EVALUATED"):
        raise RunBlocked("unapproved or incomplete host capture")
    root = capture_file.parent
    for stage in ("before", "after"):
        item = capture.get("artifacts", {}).get(stage, {})
        for key in ("screenshot", "accessible"):
            contents = read_evidence(root, item.get(key + "_path"), binary=True)
            if hashlib.sha256(contents).hexdigest() != item.get(key + "_sha256"):
                raise RunBlocked("host artifact hash drift")
            if key == "screenshot" and not (contents.startswith(b"\x89PNG\r\n\x1a\n") or contents.startswith(b"\xff\xd8")):
                raise RunBlocked("invalid client screenshot")
        if not item.get("captured_at") or not item.get("client_reference"):
            raise RunBlocked("client timestamp/reference missing")
        try:
            stamp = dt.datetime.fromisoformat(item["captured_at"].replace("Z", "+00:00"))
            if stamp.tzinfo is None or not dt.timedelta(0) <= dt.datetime.now(dt.timezone.utc)-stamp <= dt.timedelta(hours=48):
                raise ValueError("stale/future capture")
        except (ValueError, TypeError, AttributeError) as error:
            raise RunBlocked("invalid client observation timestamp") from error
    return {"schema_version": "1.0", "kind": "runner_host_capture_intake",
            "case_id": capture["case_id"], "attempt": capture["attempt"],
            "channel": channel, "status": "HOST_CAPTURE_BOUND_REVIEW_REQUIRED",
            "capture_sha256": hashlib.sha256(capture_file.read_bytes()).hexdigest(),
            "source_revision": lock["source_revision"], "input_sha256": case["input_sha256"],
            "model_behavior_verdict": "NOT_EVALUATED", "release_approved": False,
            "provider_authenticity": "REQUIRES_INDEPENDENT_REVIEW"}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--package", type=Path, required=True)
    p.add_argument("--host-capture", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        report = ingest(args.package, args.host_capture)
    except (ValueError, OSError, TypeError, KeyError) as error:
        report = {"status": "BLOCKED_CAPTURE", "reason": str(error), "model_behavior_verdict": "NOT_EVALUATED"}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    return int(report["status"] == "BLOCKED_CAPTURE")


if __name__ == "__main__":
    raise SystemExit(main())
