"""Build a small Promptfoo view from canonical routing inputs and rubrics."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import yaml

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SELECTED_CASES = (
    "investment-portfolio-synthetic-smoke-en",
    "investment-opportunity-natural-pl",
    "copyedit-no-skill-en",
)


def main() -> None:
    registry = yaml.safe_load((ROOT / "evals/routing/registry.yaml").read_text(encoding="utf-8"))
    entries = {case["id"]: case for case in registry["cases"]}
    config = yaml.safe_load((HERE / "promptfooconfig.yaml").read_text(encoding="utf-8"))
    source_revision = os.environ.get("SOURCE_REVISION", "").strip()
    if not source_revision:
        source_revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
            source_revision = "working-tree-dirty"
    config["providers"][0]["config"]["server"]["env"] = {
        "SKILLS_FACTORY_ENVIRONMENT": "promptfoo-smoke",
        "SKILLS_FACTORY_SOURCE_REVISION": source_revision,
    }
    candidate_root = os.environ.get("SKILLS_FACTORY_MCP_ROOT", "").strip()
    if candidate_root:
        candidate_path = Path(candidate_root)
        if not candidate_path.is_absolute():
            candidate_path = ROOT / candidate_path
        server_path = candidate_path.resolve() / "mcp/server.py"
        if not server_path.is_file():
            raise SystemExit(f"candidate MCP server not found: {server_path}")
        config["providers"][0]["config"]["server"]["args"] = [str(server_path)]
    tests = []
    for case_id in SELECTED_CASES:
        case = entries[case_id]
        prompt_text = (ROOT / case["input"]).read_text(encoding="utf-8")
        rubric = yaml.safe_load((ROOT / case["rubric"]).read_text(encoding="utf-8"))
        if rubric.get("mode") != "natural-routing":
            raise SystemExit(f"unexpected source rubric mode: {case_id}")
        expected = rubric.get("expected_target") == "investment-os-review"
        assertions = [
            {
                "type": "contains",
                "value": '"is_investment_request":' + str(expected).lower(),
            }
        ]
        if expected:
            selected = rubric.get("required_selected_capabilities", [])
            if len(selected) != 1:
                raise SystemExit(f"smoke case must identify one expected capability: {case_id}")
            assertions.extend(
                [
                    {"type": "contains", "value": '"child_workflow":"' + selected[0] + '"'},
                    {"type": "contains", "value": '"execution_state":"routed_only"'},
                    {"type": "contains", "value": '"workflow_executed":false'},
                ]
            )
        else:
            assertions.append({"type": "contains", "value": '"route":"not_applicable"'})
        tests.append(
            {
                "description": case_id,
                "vars": {"prompt": json.dumps({"tool": "route_investment_request", "args": {"user_request": prompt_text}}, ensure_ascii=False)},
                "assert": assertions,
            }
        )
    runtime_assertions = [
        {
            "type": "contains",
            "value": '"runtime_name":"Skills Factory runtime"',
        }
    ]
    if candidate_root:
        runtime_assertions.append(
            {"type": "contains", "value": '"package_integrity_status":"verified"'}
        )
    tests.append(
        {
            "description": "runtime_info contract",
            "vars": {"prompt": json.dumps({"tool": "runtime_info", "args": {}})},
            "assert": runtime_assertions,
        }
    )
    config["tests"] = tests
    (HERE / ".tmp/promptfooconfig.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
