from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_REL = Path("evals/campaigns/interactive-report-exhibits-2026-10/campaign.yaml")
EXPECTED_PATHS = {
    "skills/meta/report-composer/SKILL.md",
    "skills/meta/visual-output-design/SKILL.md",
    "skills/meta/visual-output-design/references/tool-routing.md",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config(root: Path = ROOT) -> dict:
    return yaml.safe_load((root / CONFIG_REL).read_text(encoding="utf-8")) or {}


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    cfg = load_config(root)
    if cfg.get("campaign") != "interactive-report-exhibits-2026-10":
        errors.append("unexpected campaign identity")
    if cfg.get("runtime_status") != "NOT_RUN" or cfg.get("release_approved") is not False:
        errors.append("candidate campaign must remain NOT_RUN and release_approved=false until evidence is reviewed")
    paths = cfg.get("out_of_scope_behavior_paths") or []
    if set(paths) != EXPECTED_PATHS or len(paths) != len(EXPECTED_PATHS):
        errors.append("campaign must declare only the exact report exhibit behavior paths")
    if any(not (root / rel).is_file() for rel in EXPECTED_PATHS):
        errors.append("one or more declared report exhibit behavior paths are missing")

    skills = cfg.get("candidate_skills") or {}
    if set(skills) != {"report-composer", "visual-output-design"}:
        errors.append("campaign must cover exactly report-composer and visual-output-design")
    for name, spec in skills.items():
        source = root / str(spec.get("source") or "")
        tests = root / str(spec.get("test_cases") or "")
        if not source.is_file() or not tests.is_file():
            errors.append(f"{name}: source or test cases are missing")
            continue
        text = source.read_text(encoding="utf-8")
        if f'version: "{spec.get("version")}"' not in text:
            errors.append(f"{name}: candidate version does not match source")
        try:
            suite = yaml.safe_load(tests.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            errors.append(f"{name}: invalid test case YAML: {exc}")
            continue
        cases = {str(c.get("id")): c for c in suite.get("cases", []) if isinstance(c, dict) and c.get("id")}
        required = list(map(str, spec.get("required_case_ids") or []))
        if len(required) < 6 or len(set(required)) != len(required):
            errors.append(f"{name}: at least six unique runtime cases are required")
            continue
        for case_id in required:
            case = cases.get(case_id)
            expected = (case or {}).get("expected") or {}
            if not case or not str(case.get("input") or "").strip():
                errors.append(f"{name}: missing executor input for {case_id}")
            if not isinstance(expected.get("should_trigger"), bool) or not expected.get("must") or not expected.get("must_not"):
                errors.append(f"{name}: {case_id} must have frozen positive/negative assertions")
    policy = cfg.get("evaluator_policy") or {}
    for key in ("executor_must_not_receive_rubrics", "runtime_model_and_surface_must_be_recorded", "runtime_receipts_required_before_release"):
        if policy.get(key) is not True:
            errors.append(f"evaluator policy must set {key}=true")
    return errors


def prepare(lab: Path, out: Path, root: Path = ROOT) -> None:
    errors = validate(root)
    if errors:
        raise ValueError("; ".join(errors))
    if not lab.is_dir():
        raise ValueError(f"Lab artifact is missing: {lab}")
    release = json.loads((lab / "release-manifest.json").read_text(encoding="utf-8"))
    plugin = json.loads((lab / "plugin.json").read_text(encoding="utf-8"))
    caps = json.loads((lab / "capabilities.json").read_text(encoding="utf-8"))
    expected_revision = os.environ.get("SOURCE_REVISION") or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    revision = str(release.get("source_revision") or "")
    if revision != expected_revision:
        raise ValueError("Lab package source revision does not match the checked-out candidate")
    capabilities = {str(item.get("name")): item for item in caps.get("capabilities", [])}
    cfg = load_config(root)
    for name, spec in cfg["candidate_skills"].items():
        capability = capabilities.get(name)
        if not capability or str(capability.get("version")) != str(spec["version"]) or not capability.get("content_sha256"):
            raise ValueError(f"Lab artifact does not contain the exact candidate skill: {name}")
    out.mkdir(parents=True, exist_ok=False)
    executor = out / "executor-inputs"
    executor.mkdir()
    definitions = []
    queue = ["# Interactive report exhibits — executor-only campaign", "", "Use a fresh session with the exact attached Lab artifact. Do not share evaluator assertions with the executor.", ""]
    for name, spec in cfg["candidate_skills"].items():
        test_doc = yaml.safe_load((root / spec["test_cases"]).read_text(encoding="utf-8")) or {}
        by_id = {str(c["id"]): c for c in test_doc.get("cases", []) if isinstance(c, dict) and c.get("id")}
        for case_id in spec["required_case_ids"]:
            case = by_id[case_id]
            filename = f"{name}--{case_id}.input.md"
            prompt = str(case["input"]).strip() + "\n"
            (executor / filename).write_text(prompt, encoding="utf-8")
            definitions.append({"skill": name, "case_id": case_id, "input": filename, "input_sha256": sha256(executor / filename)})
            queue.extend([f"## {name} / {case_id}", "", "```text", prompt.rstrip(), "```", ""])
    skill_ids = {name: {"version": cap.get("version"), "content_sha256": cap.get("content_sha256")} for name, cap in capabilities.items() if name in cfg["candidate_skills"]}
    lock = {
        "schema_version": "1.0", "campaign": cfg["campaign"], "campaign_definition_sha256": sha256(root / CONFIG_REL),
        "source_revision": revision, "runtime_status": "NOT_RUN", "release_approved": False,
        "package": {"name": plugin.get("name"), "version": plugin.get("version"), "release_id": release.get("release_id"), "payload_content_sha256": release.get("payload_content_sha256")},
        "skills": skill_ids, "executor_cases": sorted(definitions, key=lambda x: (x["skill"], x["case_id"])),
        "rubrics_in_executor_pack": False,
    }
    shutil.copytree(lab, out / "lab-plugin")
    (out / "lock.json").write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "QUEUE.md").write_text("\n".join(queue), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["validate", "prepare"])
    parser.add_argument("--lab", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "validate":
            errors = validate()
            for error in errors:
                print(f"[BLOCKER] {error}")
            if not errors:
                print("interactive report exhibit campaign: OK (13 executor cases; runtime NOT_RUN)")
            return int(bool(errors))
        if not args.lab or not args.output:
            parser.error("prepare requires --lab and --output")
        prepare(args.lab, args.output)
        print(args.output)
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"[BLOCKER] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
