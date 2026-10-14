#!/usr/bin/env python3
"""Offline Site promotion / rollback *plan* preflight, never a deployment action.

Inputs must be captured independently from the actual Site MCP and immutable
candidate package. A syntactically acceptable plan cannot authenticate those
inputs, approve production, or perform a publish/rollback.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def digest(value: object, size: int = 64) -> bool:
    return isinstance(value, str) and bool(
        (HEX40 if size == 40 else HEX64).fullmatch(value)
    )


def plan(candidate: object, site: object, rollback: object) -> dict:
    errors: list[str] = []
    if not isinstance(candidate, dict) or not isinstance(site, dict) or not isinstance(rollback, dict):
        return {"state": "BLOCKED_INPUT", "errors": ["three structured manifests required"],
                "publish_performed": False, "rollback_performed": False, "release_approved": False}

    src = candidate.get("source_revision")
    ver = candidate.get("release_id")
    payload = candidate.get("payload_content_sha256")
    if not digest(src, 40) or not digest(payload) or not isinstance(ver, str) or not ver:
        errors.append("candidate: exact source/release/payload missing")
    if candidate.get("channel") != "lab":
        errors.append("candidate: only signed-off Lab package can enter Site staging")

    if site.get("attestation_status") != "verified":
        errors.append("site: no verified installed identity")
    previous = site.get("lab_release")
    if not isinstance(previous, dict):
        errors.append("site: embedded Lab release missing")
        previous = {}
    prior_source = previous.get("source_revision")
    prior_id = previous.get("release_id")
    prior_payload = previous.get("payload_content_sha256")
    if not digest(prior_source, 40) or not isinstance(prior_id, str) or not prior_id:
        errors.append("site: prior installed Lab identity absent")
    # Hosted runtime uses artifact_sha256 for the package ZIP, not necessarily
    # the decoded payload_content_sha256; require true payload identity here.
    if not digest(prior_payload):
        errors.append("site: prior Lab *payload* digest unverified")
    when = site.get("observed_at")
    try:
        observed = dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
        if observed.tzinfo is None:
            raise ValueError("timezone required")
    except (ValueError, TypeError, AttributeError):
        errors.append("site: timestamp missing/without timezone")
    if not isinstance(site.get("observation_source"), str) or not site["observation_source"].strip():
        errors.append("site: independently captured receipt reference missing")
    if src == prior_source and ver == prior_id and payload == prior_payload:
        errors.append("candidate: already observed as installed (not a new deployment)")
    if not digest(rollback.get("artifact_sha256")):
        errors.append("rollback: exact immutable artifact digest required")
    if rollback.get("source_revision") != prior_source or rollback.get("release_id") != prior_id:
        errors.append("rollback: immutable artifact does not match observed installed release")
    if rollback.get("payload_content_sha256") != prior_payload:
        errors.append("rollback: payload digest does not match installed release")
    if not isinstance(rollback.get("immutable_artifact_reference"), str) or not rollback["immutable_artifact_reference"].strip():
        errors.append("rollback: immutable artifact locator required")
    return {
        "schema_version": "1.0", "kind": "offline_site_promotion_preflight",
        "state": "BLOCKED_INPUT" if errors else "PLAN_ONLY_REVIEW_REQUIRED",
        "errors": sorted(set(errors)),
        "candidate_source_revision": src,
        "candidate_release_id": ver,
        "candidate_payload_content_sha256": payload,
        "previous_source_revision": prior_source,
        "previous_release_id": prior_id,
        "previous_payload_content_sha256": prior_payload,
        "previous_rollback_artifact_sha256": rollback.get("artifact_sha256"),
        "observed_site_receipt_reference": site.get("observation_source"),
        "runtime_source_comparison": "DECLARED_METADATA_ONLY",
        "operator_approval": "NOT_OBTAINED",
        "publisher_permissions": "NOT_VERIFIED",
        "isolated_smoke": "NOT_RUN",
        "post_publish_attestation": "NOT_RUN",
        "rollback_drill": "NOT_RUN",
        "publish_performed": False,
        "rollback_performed": False,
        "release_approved": False,
        "note": "Must independently authenticate receipt, artifact and Site installer, approve separately, then collect post-publish + rollback receipts.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate-manifest", type=Path, required=True)
    p.add_argument("--observed-site", type=Path, required=True)
    p.add_argument("--rollback-manifest", type=Path, required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        report = plan(*[
            json.loads(path.read_text(encoding="utf-8"))
            for path in (args.candidate_manifest, args.observed_site, args.rollback_manifest)
        ])
    except (OSError, ValueError, UnicodeError, TypeError) as error:
        report = {"state": "BLOCKED_INPUT", "errors": [type(error).__name__],
                  "publish_performed": False, "rollback_performed": False, "release_approved": False}
    contents = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(contents, encoding="utf-8")
    else:
        print(contents, end="")
    return 0 if report["state"] == "PLAN_ONLY_REVIEW_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
