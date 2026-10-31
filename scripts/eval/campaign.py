Warning: truncated output (original token count: 22899)
Total output lines: 1886

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
PACKAGE_DIR = ROOT / "scripts" / "package"
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from common import load_campaign_cases, load_supplemental_cases, sha256_file
import receipt
import validate_routing
import build_plugin
import artifact_validation

CONFIG_REL = Path("evals/campaigns/runtime-validation-2026-10-r20/campaign.yaml")
CONFIG = ROOT / CONFIG_REL
SEPARATE_META_CAMPAIGN_REL = Path("evals/campaigns/skill-release-review-2026-10/release-review-campaign.yaml")
SKILL_ENGINEERING_CAMPAIGN_REL = Path("evals/campaigns/skill-engineering-2026-10/engineering-campaign.yaml")
PRESENTATION_OS_CAMPAIGN_REL = Path("evals/campaigns/presentation-os-creative-direction-2026-10/source-coverage.yaml")
INTERACTIVE_REPORT_EXHIBIT_CAMPAIGN_REL = Path("evals/campaigns/interactive-report-exhibits-2026-10/campaign.yaml")
INTERFACE_DESIGN_CAMPAIGN_REL = Path("evals/campaigns/interface-design-2026-10/campaign.yaml")
EXPECTED_INTERACTIVE_REPORT_EXHIBIT_PATHS = {
    "skills/meta/report-composer/SKILL.md",
    "skills/meta/visual-output-design/SKILL.md",
    "skills/meta/visual-output-design/references/tool-routing.md",
}


def separately_validated_engineering_paths() -> set[str]:
    """Return behavior paths covered by the exact, repository-validated engineering campaign."""
    path = ROOT / SKILL_ENGINEERING_CAMPAIGN_REL
    if not path.is_file():
        return set()
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    declared = cfg.get("out_of_scope_behavior_paths") or []
    expected = {
        "skills/meta/skill-authoring/SKILL.md",
        "skills/meta/skill-test-design/SKILL.md",
        "skills/meta/skill-evaluation/SKILL.md",
        "workflows/skill-development/WORKFLOW.md",
        "release/package.yaml",
    }
    if cfg.get("campaign") != "skill-engineering-2026-10" or set(declared) != expected:
        return set()
    fixtures = yaml.safe_load((ROOT / "evals/runtime-fixtures.yaml").read_text(encoding="utf-8")) or {}
    targets = fixtures.get("targets") or {}
    declared_targets = cfg.get("runtime_targets") or {}
    for target in ("skill-authoring", "skill-test-design", "skill-evaluation"):
        skill = ROOT / f"skills/meta/{target}/SKILL.md"
        declared = declared_targets.get(target) or {}
        version = str(declared.get("version") or "")
        if not version or not skill.is_file() or f'version: "{version}"' not in skill.read_text(encoding="utf-8"):
            return set()
        fixture_cases = targets.get(target) or []
        fixture_ids = {str(case.get("id")) for case in fixture_cases}
        if set(declared.get("required_cases") or []) != fixture_ids:
            return set()
        if len(fixture_cases) < 2:
            return set()
        for case in fixture_cases:
            if not (ROOT / str(case.get("input") or "")).is_file() or not (ROOT / str(case.get("rubric") or "")).is_file():
                return set()
    workflow = ROOT / "workflows/skill-development"
    workflow_cases = workflow / "tests/cases.yaml"
    if not (workflow / "WORKFLOW.md").is_file() or not workflow_cases.is_file():
        return set()
    cases_doc = yaml.safe_load(workflow_cases.read_text(encoding="utf-8")) or {}
    repo_workflow = cfg.get("repository_workflow") or {}
    if (
        repo_workflow.get("path") != "workflows/skill-development/WORKFLOW.md"
        or repo_workflow.get("test_cases") != "workflows/skill-development/tests/cases.yaml"
        or len(cases_doc.get("cases") or []) < int(repo_workflow.get("minimum_cases") or 0)
    ):
        return set()
    package = yaml.safe_load((ROOT / "release/package.yaml").read_text(encoding="utf-8")) or {}
    lab = package.get("lab") or {}
    package_cfg = cfg.get("package") or {}
    required_drafts = package_cfg.get("required_draft_targets") or []
    if (
        package_cfg.get("lab_version_source") != "release/package.yaml#lab.version"
        or not isinstance(lab.get("version"), str)
        or not lab.get("version")
        or set(lab.get("draft_test_targets") or []) != set(required_drafts)
    ):
        return set()
    return expected


def separately_validated_presentation_paths(root: Path = ROOT) -> set[str]:
    """Return explicitly case-covered Presentation/Report OS Lab source paths."""
    path = root / PRESENTATION_OS_CAMPAIGN_REL
    if not path.is_file():
        return set()
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    expected_paths = {
        "skills/presentations/presentation-deck-review/SKILL.md",
        "skills/presentations/presentation-exhibit-design/SKILL.md",
        "skills/presentations/presentation-slide-authoring/SKILL.md",
        "skills/presentations/presentation-storyline/SKILL.md",
        "workflows/presentation-production/WORKFLOW.md",
        "workflows/presentation-production/references/artifact-contract.md",
        "workflows/presentation-production/references/creative-direction.md",
        "workflows/presentation-production/references/design-library-selection.md",
        "workflows/presentation-production/references/quality-standard.md",
        "skills/reports/report-document-architecture/SKILL.md",
        "skills/reports/report-document-authoring/SKILL.md",
        "skills/reports/report-document-review/SKILL.md",
        "workflows/report-production/WORKFLOW.md",
        "workflows/report-production/references/document-contract.md",
        "workflows/report-production/references/quality-standard.md",
        "workflows/runtime-registry.yaml",
    }
    declared_paths = cfg.get("out_of_scope_behavior_paths") or []
    if (
        cfg.get("campaign") != "presentation-os-creative-direction-2026-10"
        or set(declared_paths) != expected_paths
        or len(declared_paths) != len(expected_paths)
        or cfg.get("runtime_status") not in {"NOT_RUN", "PASS"}
        or any(not (root / item).is_file() for item in expected_paths)
    ):
        return set()
    for rel in expected_paths:
        if not rel.startswith(("skills/presentations/", "skills/reports/")) or not rel.endswith("/SKILL.md"):
            continue
        source = (root / rel).read_text(encoding="utf-8")
        if not source.startswith("---\n"):
            return set()
        end = source.find("\n---\n", 4)
        if end < 0:
            return set()
        metadata = (yaml.safe_load(source[4:end]) or {}).get("metadata") or {}
        if metadata.get("maturity") != "draft":
            return set()
    readme = root / "README.md"
    if not readme.is_file() or "Lab 0.35.1 and its bundled MCP expose every source skill and workflow regardless of maturity" not in readme.read_text(encoding="utf-8"):
        return set()
    registry = yaml.safe_load((root / "workflows/runtime-registry.yaml").read_text(encoding="utf-8")) or {}
    registered = {item.get("name"): item for item in registry.get("workflows", []) if isinstance(item, dict)}
    for workflow_name in ("skill-development", "presentation-production", "report-production"):
        workflow = registered.get(workflow_name)
        if (
            workflow is None
            or (workflow.get("metadata") or {}).get("maturity") != "draft"
            or (workflow.get("channels") or {}).get("lab") != "supported"
            or (workflow.get("channels") or {}).get("plugin") != "unavailable"
        ):
            return set()

    for suite in cfg.get("case_suites") or []:
        source = root / str(suite.get("path") or "")
        if not source.is_file():
            return set()
        cases_doc = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
        cases_by_id = {
            str(item.get("id")): item
            for item in cases_doc.get("cases", [])
            if isinstance(item, dict) and item.get(…18899 tokens truncated…"runtime"]
    ns = argparse.Namespace(
        case_id=args.case_id,
        status=args.status,
        evidence_scope="current-version",
        source_revision=lock["behavior_source_revision"],
        component=case["target"],
        component_version=source_version,
        component_digest=source_digest,
        provider=runtime["provider"],
        model_id=runtime["model_id"],
        reasoning=runtime["reasoning"],
        catalog=list(obs["catalog"]),
        tools=list(runtime.get("available_tools") or []),
        prompt=(ROOT / case["input"]).read_text(encoding="utf-8"),
        output=str(out_dest),
        tool_trace=str(trace_dest),
        reviewer=args.reviewer,
        assisted=args.assisted,
        runtime_artifact={
            "channel": required_channel,
            "package_name": obs["package"]["name"],
            "package_version": obs["package"]["version"],
            "release_id": obs["package"]["release_id"],
            "source_revision": obs["package"]["source_revision"],
            "payload_content_sha256": obs["package"]["payload_content_sha256"],
            "component_content_sha256": component["content_sha256"],
        },
        selection_findings=sel_errors,
        evidence_origin=str(getattr(args, "evidence_origin", "runtime")),
        note=args.note,
    )
    old = os.environ.get("SOURCE_REVISION")
    os.environ["SOURCE_REVISION"] = lock["behavior_source_revision"]
    try:
        rec = receipt.create_receipt(ns)
    finally:
        if old is None:
            os.environ.pop("SOURCE_REVISION", None)
        else:
            os.environ["SOURCE_REVISION"] = old
    path = dest / "receipt.json"
    path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def evidence_compatibility_profile(source_revision: str, root: Path = ROOT) -> str:
    active_revision = str(config(root).get("behavior_source_revision") or "")
    if source_revision == active_revision:
        return "active-r2"
    historical_campaign = HISTORICAL_RECEIPT_COMPATIBILITY.get(source_revision)
    if historical_campaign:
        historical_config = root / "evals" / "campaigns" / historical_campaign / "campaign.yaml"
        if not historical_config.is_file():
            raise ValueError(
                f"historical compatibility campaign is missing: {historical_campaign}"
            )
        if historical_campaign == "runtime-validation-2026-10":
            return "historical-r1"
        if historical_campaign == "runtime-validation-2026-10-r2":
            return "historical-r2"
        if historical_campaign == "runtime-validation-2026-10-r3":
            return "historical-r3"
        if historical_campaign == "runtime-validation-2026-10-r4":
            return "historical-r4"
        if historical_campaign == "runtime-validation-2026-10-r5":
            return "historical-r5"
        if historical_campaign == "runtime-validation-2026-10-r6":
            return "historical-r6"
        if historical_campaign == "runtime-validation-2026-10-r7":
            return "historical-r7"
        if historical_campaign == "runtime-validation-2026-10-r8":
            return "historical-r8"
        if historical_campaign == "runtime-validation-2026-10-r9":
            return "historical-r9"
        if historical_campaign == "runtime-validation-2026-10-r10":
            return "historical-r10"
        if historical_campaign == "runtime-validation-2026-10-r11":
            return "historical-r11"
        if historical_campaign == "runtime-validation-2026-10-r12":
            return "historical-r12"
        if historical_campaign == "runtime-validation-2026-10-r13":
            return "historical-r13"
        if historical_campaign == "runtime-validation-2026-10-r14":
            return "historical-r14"
        if historical_campaign == "runtime-validation-2026-10-r15":
            return "historical-r15"
        return "historical-r14"
    raise ValueError(f"unsupported evidence source revision: {source_revision}")


def validate_evidence() -> list[str]:
    root = ROOT / config()["evidence_root"]
    if not root.exists():
        return []
    errors = []
    for path in sorted(root.rglob("receipt.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        source_revision = str(data.get("source_revision") or "")
        try:
            compatibility = evidence_compatibility_profile(source_revision, root=ROOT)
        except ValueError as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue
        for err in receipt.validate_receipt_data(
            data, root=ROOT, current_revision=source_revision
        ):
            errors.append(f"{path.relative_to(ROOT)} [{compatibility}]: {err}")
    return errors


def main() -> int:
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("validate")
    q = s.add_parser("queue")
    q.add_argument("--output", type=Path)
    q.add_argument("--include-supplemental", action="store_true")
    prep = s.add_parser("prepare")
    prep.add_argument("--output", type=Path, default=ROOT / ".tmp/runtime-campaign")
    prep.add_argument("--production-plugin", type=Path, help="Reuse a production package built from this exact source.")
    prep.add_argument("--lab-plugin", type=Path, help="Reuse a Lab package built from this exact source.")
    lock_cmd = s.add_parser("validate-lock")
    lock_cmd.add_argument("--lock", required=True, type=Path)
    smoke = s.add_parser("verify-smoke")
    smoke.add_argument("--lock", required=True, type=Path)
    smoke.add_argument("--observed", required=True, type=Path)
    imp = s.add_parser("import-run")
    imp.add_argument("--case-id", required=True)
    imp.add_argument("--run-id", required=True)
    imp.add_argument("--lock", required=True)
    imp.add_argument("--smoke", required=True)
    imp.add_argument("--output", required=True)
    imp.add_argument("--trace", required=True)
    imp.add_argument("--status", required=True, choices=["REVIEW_REQUIRED", "PASS", "FAIL"])
    imp.add_argument("--reviewer", required=True)
    imp.add_argument("--assisted", action="store_true")
    imp.add_argument("--evidence-origin", choices=["runtime", "offline"], default="runtime")
    imp.add_argument("--note")
    s.add_parser("validate-evidence")
    args = p.parse_args()

    if args.cmd == "validate":
        errors = validate_campaign()
        for e in errors:
            print("[BLOCKER]", e)
        if not errors:
            print(f"Runtime campaign definition: OK ({len(load_campaign_cases(ROOT, config()["campaign"]))} core cases)")
        return 1 if errors else 0
    if args.cmd == "queue":
        text = queue_text(args.include_supplemental)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    if args.cmd == "prepare":
        prepare(args.output, production_plugin=args.production_plugin, lab_plugin=args.lab_plugin)
        print(args.output)
        return 0
    if args.cmd == "validate-lock":
        try:
            validate_lock_file(args.lock, root=ROOT)
        except ValueError as exc:
            print("[BLOCKER]", exc)
            return 1
        print("Campaign lock: OK")
        return 0
    if args.cmd == "verify-smoke":
        errors = verify_smoke(args.lock, args.observed)
        for e in errors:
            print("[BLOCKER]", e)
        if not errors:
            print("Runtime smoke evidence: OK")
        return 1 if errors else 0
    if args.cmd == "import-run":
        print(import_run(args))
        return 0
    errors = validate_evidence()
    for e in errors:
        print("[BLOCKER]", e)
    if not errors:
        print("Runtime campaign evidence: OK")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
