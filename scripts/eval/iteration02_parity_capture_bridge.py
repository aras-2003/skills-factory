#!/usr/bin/env python3
"""Normalize separately captured Work/Site MCP runtime_info for parity review.

This is an OFFLINE evidence adapter, never a provider client or an attestation
authority. Site server SHA and embedded Lab SHA are distinct. A Site ZIP hash
MUST NOT be promoted to decoded payload_content_sha256. No behavior PASS.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

FLOW_NAMES = ("routing", "architecture-review", "bar-chart", "line-chart")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha(value: object, length: int = 64) -> bool:
    if not isinstance(value, str):
        return False
    return bool((HEX40 if length == 40 else HEX64).fullmatch(value))


def time_ok(value: object) -> bool:
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except (AttributeError, ValueError, TypeError):
        return False


def normalize(candidate: object, identity: object, flow_evidence: object, *,
              label: str, observation_source: str, observed_at: str) -> dict:
    errors = []
    if not isinstance(candidate, dict) or not isinstance(identity, dict) or not isinstance(flow_evidence, list):
        return {"status": "BLOCKED_INPUT", "errors": ["candidate, identity and flows required"],
                "provider_authenticity": "NOT_INDEPENDENTLY_VERIFIED", "runtime_execution": "NOT_EXECUTED_BY_ADAPTER"}
    if label not in ("work", "site"):
        errors.append("label must be work or site")
    if not isinstance(observation_source, str) or not observation_source.strip() or not time_ok(observed_at):
        errors.append("observation source and offset-aware time required")
    for name, length in (("source_revision", 40), ("payload_content_sha256", 64)):
        if not sha(candidate.get(name), length):
            errors.append(f"candidate {name} missing")
    if not isinstance(candidate.get("release_id"), str) or not candidate["release_id"]:
        errors.append("candidate Lab release_id missing")

    if label == "site":
        if identity.get("channel") != "site" or identity.get("identity_source") != "site_environment":
            errors.append("Site runtime identity not observed from Site environment")
        site_sha = identity.get("source_revision")
        if not sha(site_sha, 40):
            errors.append("Site server source revision missing")
        embedded = identity.get("lab_release")
        if not isinstance(embedded, dict):
            embedded = {}
            errors.append("Site embedded Lab release absent")
        receipt = identity.get("tool_receipt")
        if (not isinstance(receipt, dict) or receipt.get("tool_name") != "runtime_info"
                or receipt.get("execution_state") != "executed" or receipt.get("status") != "SUCCESS"
                or receipt.get("source_revision") != site_sha):
            errors.append("unsigned Site tool receipt absent or server source mismatch")
        if identity.get("attestation_status") != "verified":
            errors.append("Site identity unattested")
        # A Site worker release_id belongs to the Site server, NEVER the Lab.
        lab_source = embedded.get("source_revision")
        lab_id = embedded.get("release_id")
        payload = embedded.get("payload_content_sha256")
        catalog = embedded.get("catalog_digest")
        if not sha(embedded.get("artifact_sha256")):
            errors.append("Site embedded ZIP SHA missing")
        if not sha(payload):
            errors.append("Site embedded decoded payload SHA absent; ZIP SHA is not payload")
        if not isinstance(lab_id, str) or not lab_id:
            errors.append("Site embedded Lab release_id missing; Site server release_id is different")
    else:
        site_sha = None
        if identity.get("channel") != "lab":
            errors.append("Work observation is not Lab")
        if identity.get("attestation_status") != "verified":
            errors.append("Work Lab identity unattested")
        lab_source = identity.get("source_revision")
        lab_id = identity.get("release_id")
        payload = identity.get("payload_content_sha256")
        catalog = identity.get("catalog_digest")
    if lab_source != candidate.get("source_revision") or not sha(lab_source, 40):
        errors.append("observed embedded Lab source does not equal candidate")
    if lab_id != candidate.get("release_id"):
        errors.append("observed Lab release ID does not equal candidate")
    if payload != candidate.get("payload_content_sha256") or not sha(payload):
        errors.append("observed decoded Lab payload does not equal candidate")
    if not sha(catalog):
        errors.append("observed Lab catalog digest invalid")

    digest = identity.get("tool_schema_digest")
    if not isinstance(digest, str) or not sha(digest.removeprefix("sha256:")):
        errors.append("observed tool schema digest invalid")
    caps = identity.get("capabilities")
    if not isinstance(caps, list) or any(not isinstance(c, str) or not c for c in caps) or len(caps) != len(set(caps)):
        errors.append("invalid installed tool capabilities")
    seen = set()
    normalized_flows = []
    for row in flow_evidence:
        if not isinstance(row, dict) or row.get("flow") not in FLOW_NAMES:
            errors.append("unrecognized flow receipt")
            continue
        flow_name = row["flow"]
        if flow_name in seen:
            errors.append(f"duplicate flow receipt {flow_name}")
        seen.add(flow_name)
        if row.get("execution_state") != "executed" or not sha(row.get("tool_trace_sha256")) or not sha(row.get("semantic_result_sha256")):
            errors.append(f"{flow_name} missing real execution/normalized output digests")
        if flow_name.endswith("chart") and row.get("client_display_state") != "observed":
            errors.append(f"{flow_name} missing client-visible result")
        if row.get("observed_lab_source_revision") != lab_source:
            errors.append(f"{flow_name} does not bind installed Lab source")
        if label == "site" and row.get("observed_site_server_revision") != site_sha:
            errors.append(f"{flow_name} does not bind Site server source")
        normalized_flows.append({
            key: row.get(key) for key in
            ("flow", "execution_state", "tool_trace_sha256", "semantic_result_sha256", "client_display_state")
        })
    for missing in set(FLOW_NAMES) - seen:
        errors.append(f"missing observed flow: {missing}")
    return {
        "schema_version": "1.0", "kind": "offline_work_site_parity_input_adapter",
        "status": "BLOCKED_EVIDENCE" if errors else "STRUCTURAL_MATCH_PENDING_INDEPENDENT_REVIEW",
        "errors": sorted(set(errors)), "label": label,
        "source_revision": lab_source, "release_id": lab_id,
        "payload_content_sha256": payload, "catalog_digest": catalog,
        "tool_schema_digest": digest, "capabilities": caps, "flows": normalized_flows,
        "attestation_status": identity.get("attestation_status"),
        "observed_at": observed_at, "observation_source": observation_source,
        "site_runtime_source_revision": site_sha,
        "provider_authenticity": "NOT_INDEPENDENTLY_VERIFIED",
        "runtime_execution": "NOT_EXECUTED_BY_ADAPTER", "release_approved": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--runtime-info", type=Path, required=True)
    p.add_argument("--flow-evidence", type=Path, required=True)
    p.add_argument("--channel", choices=("work", "site"), required=True)
    p.add_argument("--observation-source", required=True)
    p.add_argument("--observed-at", required=True)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    try:
        report = normalize(*[json.loads(path.read_text(encoding="utf-8"))
                             for path in (a.candidate, a.runtime_info, a.flow_evidence)],
                           label=a.channel, observation_source=a.observation_source,
                           observed_at=a.observed_at)
    except (ValueError, OSError, TypeError, UnicodeError):
        report = {"status": "BLOCKED_INPUT", "errors": ["invalid supplied JSON"],
                  "runtime_execution": "NOT_EXECUTED_BY_ADAPTER", "release_approved": False}
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["status"] == "STRUCTURAL_MATCH_PENDING_INDEPENDENT_REVIEW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
