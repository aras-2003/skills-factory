#!/usr/bin/env python3
"""Offline route→child MCP trace correlation for Chat browser TEST sessions.

Verifies frozen identifiers and raw receipts without claiming child execution.
The actual model/browser session and provenance must be independently reviewed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from iteration02_browser_evidence import read_evidence, sha

ROUTING_CASES = {"I02-251-browser-mcp", "I02-253-parity"}


def assess(lock: object, observation: object, root: Path) -> dict:
    problems: list[str] = []
    if not isinstance(lock, dict) or not isinstance(observation, dict):
        return {"status": "BLOCKED_TRACE", "problems": ["invalid lock/observation"],
                "execution": "NOT_PERFORMED_BY_VALIDATOR", "release_approved": False}
    cid = observation.get("case_id")
    cases = lock.get("cases")
    matched = [x for x in cases if isinstance(x, dict) and x.get("case_id") == cid] if isinstance(cases, list) else []
    if not isinstance(cid, str) or cid not in ROUTING_CASES or len(matched) != 1 or matched[0].get("channel") != "browser":
        problems.append("wrong/missing frozen browser case")
    if lock.get("runtime_evidence") != "NOT_RUN" or lock.get("release_approved") is not False:
        problems.append("nonpristine external lock")
    for key in ("source_revision", "release_id", "payload_content_sha256"):
        if observation.get(key) != lock.get(key) or not isinstance(observation.get(key), str) or not observation[key]:
            problems.append("candidate source/release mismatch: " + key)
    if len(matched) == 1 and observation.get("input_sha256") != matched[0].get("input_sha256"):
        problems.append("frozen prompt digest mismatch")
    if not isinstance(observation.get("chat_reference"), str) or not observation["chat_reference"].strip():
        problems.append("missing TEST client reference")
    if not isinstance(observation.get("installed_identity_reference"), str) or not observation["installed_identity_reference"].strip():
        problems.append("installed provider observation reference missing")
    corr = observation.get("correlation_id")
    if not isinstance(corr, str) or not corr.strip():
        problems.append("missing correlation ID")
    sources = []
    router, child = None, None
    for name in ("router", "child"):
        try:
            data, raw = read_evidence(root, observation.get(f"{name}_raw_path"))
        except (OSError, ValueError, UnicodeError, TypeError) as error:
            problems.append(f"{name} raw receipt missing/unsafe: {type(error).__name__}")
            continue
        if observation.get(f"{name}_raw_sha256") != sha(raw):
            problems.append(name + " receipt digest mismatch")
        if name == "router":
            router = data
        else:
            child = data
        sources.append({"stage": name, "receipt_sha256": sha(raw)})
    if router is not None:
        receipt = router.get("tool_receipt")
        if not isinstance(receipt, dict) or any([
            receipt.get("tool_name") != "route_investment_request",
            receipt.get("status") != "SUCCESS",
            receipt.get("execution_state") != "executed",
            receipt.get("source_revision") != lock.get("source_revision"),
            router.get("workflow_execution_state") != "not_executed",
            router.get("outcome") is not None,
            router.get("response_policy") != "load_child_workflow_then_follow",
            router.get("must_invoke_child_workflow") is not True,
        ]):
            problems.append("router receipt is not a route-only handoff on exact source")
        chosen = router.get("child_workflow")
        if not isinstance(chosen, str) or not chosen.strip():
            problems.append("router child name missing")
        else:
            if child is not None and child.get("name") != chosen:
                problems.append("loaded child differs from selected workflow")
    if child is not None:
        receipt = child.get("tool_receipt")
        if not isinstance(receipt, dict) or any([
            receipt.get("tool_name") != "load_skill",
            receipt.get("status") != "SUCCESS",
            receipt.get("execution_state") != "executed",
            receipt.get("source_revision") != lock.get("source_revision"),
        ]):
            problems.append("child load receipt is not an executed exact-source load_skill")
    if observation.get("router_correlation_id") != corr or observation.get("child_correlation_id") != corr:
        problems.append("router↔child correlation not observed")
    if observation.get("child_execution_claim") == "executed":
        # Loading a workflow alone is never proof that the model actually
        # followed instructions or performed a required child tool action.
        problems.append("child model execution cannot be inferred from load_skill")
    return {
        "schema_version": "1.0", "kind": "offline_browser_route_child_receipts",
        "status": "BLOCKED_TRACE" if problems else "ROUTE_AND_LOAD_STRUCTURALLY_LINKED_REVIEW_REQUIRED",
        "problems": sorted(set(problems)), "case_id": cid,
        "bound_receipts": sources,
        "child_model_execution": "NOT_VERIFIED",
        "final_answer_behavior": "NOT_EVALUATED",
        "observed_browser_provenance": "NOT_AUTHENTICATED",
        "execution": "NOT_PERFORMED_BY_VALIDATOR",
        "release_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-lock", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        lock = json.loads(args.external_lock.read_text(encoding="utf-8"))
        observation = json.loads(args.capture.read_text(encoding="utf-8"))
        result = assess(lock, observation, args.evidence_root)
    except (OSError, ValueError, UnicodeError, TypeError) as error:
        result = {"status": "BLOCKED_TRACE", "problems": [type(error).__name__], "release_approved": False}
    content = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return int(result["status"] != "ROUTE_AND_LOAD_STRUCTURALLY_LINKED_REVIEW_REQUIRED")


if __name__ == "__main__":
    raise SystemExit(main())
