"""Build parity flow records from immutable raw provider/client artifacts.

Does not fabricate semantic normalization, client visibility or model execution.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from iteration02_browser_evidence import read_evidence
from iteration02_parity_capture_bridge import FLOW_NAMES, normalize
from iteration02_site_native_receipt import unwrap, verify_identity, verify_call


def collect(candidate: dict, identity: dict, plan: list, root: Path, *, channel: str,
            observation_source: str, observed_at: str) -> dict:
    identity = unwrap(identity)
    if channel == "site":
        verify_identity(identity, candidate)
    flows = []
    if not isinstance(plan, list) or {p.get("flow") for p in plan if isinstance(p, dict)} != set(FLOW_NAMES) or len(plan) != 4:
        raise ValueError("exactly four distinct observed flows required")
    for row in plan:
        trace, raw_trace = read_evidence(root, row.get("tool_trace_path"))
        result, raw_result = read_evidence(root, row.get("semantic_result_path"))
        if not isinstance(result, dict) or not result:
            raise ValueError("actual structured workflow result required")
        if row["flow"] == "architecture-review":
            if (trace.get("kind") != "cua_host_capture" or trace.get("execution_state") != "executed"
                    or trace.get("source_revision") != candidate.get("source_revision")
                    or result != {"text": trace.get("response")} or not trace.get("response")):
                raise ValueError("actual architecture host response required")
            provider, _ = read_evidence(root, row.get("provider_trace_path"))
            provider = verify_call(provider, "load_skill", identity["source_revision"])
            if provider.get("name") != "architecture-review":
                raise ValueError("architecture specialist load not observed")
        else:
            tools = {"routing":"route_investment_request", "bar-chart":"render_bar_chart", "line-chart":"render_line_chart"}
            output = verify_call(trace, tools[row["flow"]], identity["source_revision"])
            actual = ({k:output.get(k) for k in ("route","child_workflow")} if row["flow"] == "routing" else output.get("data"))
            if result != actual:
                raise ValueError("semantic projection differs from actual provider result")
        display = "not_applicable"
        if row["flow"].endswith("chart"):
            client, _ = read_evidence(root, row.get("client_observation_path"))
            screenshot = read_evidence(root, row.get("screenshot_path"), binary=True)
            if (not (screenshot.startswith(b"\x89PNG\r\n\x1a\n") or screenshot.startswith(b"\xff\xd8"))
                    or client.get("client_display_state") != "observed"
                    or client.get("observed_tool_trace_sha256") != hashlib.sha256(raw_trace).hexdigest()):
                raise ValueError("chart client visibility not independently observed/bound")
            display = "observed"
        flows.append({"flow": row["flow"], "execution_state": "executed",
                      "tool_trace_sha256": hashlib.sha256(raw_trace).hexdigest(),
                      "semantic_result_sha256": hashlib.sha256(json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest(),
                      "client_display_state": display,
                      "observed_lab_source_revision": candidate["source_revision"],
                      "observed_site_server_revision": identity["source_revision"] if channel == "site" else None})
    return normalize(candidate, identity, flows, label=channel,
                     observation_source=observation_source, observed_at=observed_at)
