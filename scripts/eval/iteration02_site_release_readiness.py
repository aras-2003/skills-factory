#!/usr/bin/env python3
"""Source-only Site release readiness preflight; never publishes or approves.

Normalizes the current Site MCP runtime_info shape, distinguishing Site runtime
source from the embedded Lab source. A ZIP artifact SHA is NOT a payload digest.
No network, browser, publisher or production actions are performed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def valid(value: object, *, short: bool = False) -> bool:
    return isinstance(value, str) and bool((HEX40 if short else HEX64).fullmatch(value))


def when(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return result.tzinfo is not None


def assess(candidate: object, installed_site: object, rollback: object) -> dict:
    blockers: list[str] = []
    if not all(isinstance(x, dict) for x in (candidate, installed_site, rollback)):
        return {"status": "BLOCKED_EVIDENCE", "blockers": ["candidate, Site and rollback objects required"],
                "publish_performed": False, "rollback_performed": False, "release_approved": False}
    lab = installed_site.get("lab_release")
    lab = lab if isinstance(lab, dict) else {}
    site_receipt = installed_site.get("tool_receipt")
    site_receipt = site_receipt if isinstance(site_receipt, dict) else {}

    if candidate.get("channel") != "lab":
        blockers.append("candidate must be an exact Lab artifact")
    for name, length in (("source_revision", 40), ("payload_content_sha256", 64)):
        if not valid(candidate.get(name), short=length == 40):
            blockers.append(f"candidate {name} invalid/missing")
    if not isinstance(candidate.get("release_id"), str) or not candidate.get("release_id"):
        blockers.append("candidate release_id missing")

    if installed_site.get("channel") != "site":
        blockers.append("Site runtime_info channel not site")
    if installed_site.get("attestation_status") != "verified" or installed_site.get("identity_source") != "site_environment":
        blockers.append("Site environment attestation not observed")
    if not valid(installed_site.get("source_revision"), short=True):
        blockers.append("Site runtime source_revision missing")
    if not isinstance(installed_site.get("release_id"), str) or not installed_site.get("release_id"):
        blockers.append("Site runtime release_id missing")
    schema = installed_site.get("tool_schema_digest")
    if not isinstance(schema, str) or not valid(schema.removeprefix("sha256:")):
        blockers.append("Site tool schema SHA-256 missing")
    if site_receipt.get("tool_name") != "runtime_info" or site_receipt.get("status") != "SUCCESS":
        blockers.append("Site runtime_info tool receipt missing or unsuccessful")
    if site_receipt.get("source_revision") != installed_site.get("source_revision"):
        blockers.append("Site tool receipt source differs from Site runtime source")
    if not when(site_receipt.get("completed_at")) or not when(installed_site.get("deployed_at")):
        blockers.append("Site runtime_info timing not offset-aware")

    if lab.get("channel") != "lab" or not valid(lab.get("source_revision"), short=True):
        blockers.append("embedded Lab exact source unavailable")
    if not valid(lab.get("catalog_digest")) or not valid(lab.get("artifact_sha256")):
        blockers.append("embedded Lab catalog or ZIP artifact digest unavailable")
    if candidate.get("source_revision") == lab.get("source_revision"):
        blockers.append("target Lab source already matches installed source")
    # Provider's Lab release_id may be omitted: version is NOT a release_id.
    previous_payload = lab.get("payload_content_sha256")
    if not valid(previous_payload):
        blockers.append("embedded Lab payload_content_sha256 missing; ZIP artifact_sha256 is NOT equivalent")

    if rollback.get("channel") != "lab":
        blockers.append("rollback manifest channel missing")
    if rollback.get("source_revision") != lab.get("source_revision"):
        blockers.append("rollback source does not match currently embedded Lab")
    if rollback.get("artifact_sha256") != lab.get("artifact_sha256") or not valid(rollback.get("artifact_sha256")):
        blockers.append("rollback ZIP digest does not match Site embedded Lab")
    if not valid(rollback.get("payload_content_sha256")) or rollback.get("payload_content_sha256") != previous_payload:
        blockers.append("rollback payload digest unavailable/mismatched")
    locator = rollback.get("immutable_artifact_reference")
    if (not isinstance(locator, str) or not locator.strip() or
            re.search(r"(?:/heads/|/latest(?:/|$)|\bmain\b)", locator, re.I)):
        blockers.append("immutable rollback artifact reference missing/ambiguous")
    if installed_site.get("runtime_release", {}).get("source_revision") != lab.get("source_revision") if isinstance(installed_site.get("runtime_release"), dict) else True:
        blockers.append("Site runtime_release and lab_release embedded sources disagree")

    return {
        "schema_version": "1.0", "kind": "read_only_site_promotion_readiness",
        "status": "BLOCKED_EVIDENCE" if blockers else "INPUTS_CONSISTENT_APPROVAL_REQUIRED",
        "blockers": sorted(set(blockers)),
        "site_runtime_source_revision": installed_site.get("source_revision"),
        "site_runtime_release_id": installed_site.get("release_id"),
        "current_embedded_lab_source_revision": lab.get("source_revision"),
        "current_embedded_lab_artifact_sha256": lab.get("artifact_sha256"),
        "candidate_lab_source_revision": candidate.get("source_revision"),
        "candidate_lab_release_id": candidate.get("release_id"),
        "candidate_lab_payload_content_sha256": candidate.get("payload_content_sha256"),
        "tool_schema_digest": schema,
        "provider_authenticity": "NOT_INDEPENDENTLY_VERIFIED",
        "reviewer_approval": "NOT_OBTAINED", "publisher_authorization": "NOT_OBTAINED",
        "canary_execution": "NOT_RUN", "post_deploy_identity": "NOT_RUN",
        "rollback_rehearsal": "NOT_RUN", "publish_performed": False,
        "rollback_performed": False, "release_approved": False,
        "note": "Verified-shaped caller data are not a signed provider attestation. Only approved Sites publishing tools may promote after separate owner/reviewer checks.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--site-runtime-info", type=Path, required=True)
    p.add_argument("--rollback", type=Path, required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        result = assess(*[
            json.loads(file.read_text(encoding="utf-8"))
            for file in (args.candidate, args.site_runtime_info, args.rollback)
        ])
    except (OSError, ValueError, UnicodeError, TypeError) as exc:
        result = {"status": "BLOCKED_EVIDENCE", "blockers": [type(exc).__name__],
                  "publish_performed": False, "rollback_performed": False,
                  "release_approved": False}
    encoded = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if result["status"] == "INPUTS_CONSISTENT_APPROVAL_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
