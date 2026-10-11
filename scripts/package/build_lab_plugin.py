from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import yaml

from build_utils import atomic_output, capability_assessment, capability_contract_metadata, ensure_source_valid, package_runtime_mcp, package_version, sha256_tree, source_revision, write_json
from build_plugin import copy_skill
from workflow_entrypoints import add_workflow_entrypoints, load_registry


PLUGIN_NAME = "skills-factory-lab"
PLUGIN_VERSION = "0.2.1"

def discover_all_skills(root: Path) -> list[Path]:
    """Return every source skill; Lab/MCP exposure is independent of maturity."""
    return [path.parent for path in sorted((root / "skills").rglob("SKILL.md"))]


def add_runtime_eval_fixtures(root: Path, package_root: Path) -> int:
    registry = root / "evals" / "runtime-fixtures.yaml"
    if not registry.exists():
        return 0

    data = yaml.safe_load(registry.read_text(encoding="utf-8")) or {}
    targets = data.get("targets") or {}
    if not isinstance(targets, dict):
        raise ValueError("evals/runtime-fixtures.yaml: targets must be a mapping")

    copied = 0
    manifest: list[dict[str, str]] = []
    inputs_root = package_root / "executor-inputs"
    for target, cases in targets.items():
        target_dir = package_root / "skills" / target
        if not target_dir.exists():
            continue
        for case in cases or []:
            if not isinstance(case, dict):
                raise ValueError(f"evals/runtime-fixtures.yaml: {target} entries must be mappings")
            case_id = str(case.get("id") or "").strip()
            input_rel = str(case.get("input") or "").strip()
            rubric_rel = str(case.get("rubric") or "").strip()
            mode = str(case.get("mode") or "").strip()
            if not case_id or not input_rel or not rubric_rel or mode not in {"explicit", "natural-routing"}:
                raise ValueError(f"evals/runtime-fixtures.yaml: invalid case for {target}: {case}")

            src = root / input_rel
            rubric = root / rubric_rel
            if not src.exists():
                raise FileNotFoundError(f"Missing runtime eval input: {src}")
            if not rubric.exists():
                raise FileNotFoundError(f"Missing runtime eval rubric: {rubric}")
            if not src.name.endswith(".input.md"):
                raise ValueError(f"Runtime eval input must use .input.md suffix: {src}")
            if not rubric.name.endswith(".rubric.yaml"):
                raise ValueError(f"Runtime eval rubric must use .rubric.yaml suffix: {rubric}")

            dst = inputs_root / target / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
            manifest.append(
                {
                    "target": target,
                    "case_id": case_id,
                    "mode": mode,
                    "input": dst.relative_to(package_root).as_posix(),
                    "input_sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
                }
            )
    if manifest:
        # Keep the runner index beside, not inside, model-loadable skill content.
        (package_root / "executor-inputs.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "purpose": "executor input index; evaluator rubrics are not packaged",
                    "cases": sorted(manifest, key=lambda item: (item["target"], item["case_id"])),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return copied


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="plugins/skills-factory-lab")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    ensure_source_valid(root)
    out = root / args.output

    all_skills = discover_all_skills(root)
    if not all_skills:
        raise SystemExit("No source skills found; refusing to build empty lab plugin")

    with atomic_output(root, out) as stage:
        skills_out = stage / "skills"
        skills_out.mkdir(parents=True)

        skill_capabilities: dict[str, dict] = {}
        for skill_dir in all_skills:
            item = copy_skill(skill_dir, skills_out)
            skill_capabilities[item["name"]] = item

        available_names = {p.name for p in skills_out.iterdir() if p.is_dir()}
        workflow_names = add_workflow_entrypoints(
            root, "all", skills_out, channel="lab", available_names=available_names
        )

        runtime_eval_fixtures = add_runtime_eval_fixtures(root, stage)

        registry_by_name = {
            str(item.get("name")): item
            for item in load_registry(root)
            if isinstance(item, dict) and item.get("name")
        }
        capabilities: list[dict] = []
        for name, item in skill_capabilities.items():
            final_dir = skills_out / name
            final_inventory = sorted(
                p.relative_to(final_dir).as_posix()
                for p in final_dir.rglob("*")
                if p.is_file()
            )
            refreshed = dict(item)
            refreshed["inventory"] = final_inventory
            refreshed["content_sha256"] = sha256_tree(final_dir)
            capabilities.append(refreshed)

        for name in workflow_names:
            registry_item = registry_by_name.get(name)
            if registry_item is None:
                raise ValueError(f"workflow registry item missing after packaging: {name}")
            metadata = registry_item.get("metadata") or {}
            final_dir = skills_out / name
            capabilities.append(
                {
                    "name": name,
                    "kind": "workflow",
                    "maturity": metadata.get("maturity"),
                    "version": metadata.get("version"),
                    "inventory": sorted(
                        p.relative_to(final_dir).as_posix()
                        for p in final_dir.rglob("*")
                        if p.is_file()
                    ),
                    "content_sha256": sha256_tree(final_dir),
                    "capability_assessment": capability_assessment(root, name),
                }
            )

        version = package_version(root, "lab")
        interface = {
            "displayName": "Skills Factory Lab",
            "shortDescription": "Candidate skills for runtime evaluation and discovery.",
            "longDescription": "A self-contained non-production Lab/MCP package built from main for isolated behavioral testing. It exposes every source skill and registered workflow regardless of maturity. Do not enable it in the same session as the production plugin because duplicate capability names may compete.",
            "websiteURL": "https://aras-2003.github.io/skills-factory/",
            "brandColor": "#C6812C",
            "brandColorDark": "#F0C982",
            "logo": "./assets/brand-mark.svg",
            "composerIcon": "./assets/brand-mark.svg",
        }
        manifest = {
            "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "name": PLUGIN_NAME,
            "version": version,
            "description": "Isolated Lab/MCP package with every source skill and registered workflow, across all maturity statuses, for controlled behavioral testing.",
            "skills": "./skills/",
            "author": {"name": "Arkadiusz Kamrowski"},
            "repository": "https://github.com/aras-2003/skills-factory",
            "keywords": ["skills", "lab", "candidate", "oaf", "career"],
            "extensions": {
                "com.openai": {
                    "interface": interface
                }
            }
        }
        logo_source = root / "docs" / "assets" / "brand-mark.svg"
        if not logo_source.is_file():
            raise FileNotFoundError(f"Missing plugin brand asset: {logo_source}")
        assets_out = stage / "assets"
        assets_out.mkdir(parents=True, exist_ok=True)
        shutil.copy2(logo_source, assets_out / "brand-mark.svg")
        write_json(stage / "plugin.json", manifest)
        runtime_tools = package_runtime_mcp(root, stage)
        compat_dir = stage / ".codex-plugin"
        compat_dir.mkdir(parents=True)
        write_json(
            compat_dir / "plugin.json",
            {
                "name": PLUGIN_NAME,
                "version": version,
                "description": manifest["description"],
                "skills": "./skills/",
                "mcpServers": "./.mcp.json",
                "interface": interface,
            },
        )
        revision = source_revision(root)
        fixture_registry = yaml.safe_load((root / "evals" / "runtime-fixtures.yaml").read_text(encoding="utf-8")) or {}
        fixture_targets = set((fixture_registry.get("targets") or {}).keys())
        packaged_names = {item["name"] for item in capabilities}
        fixture_status = [
            {
                "target": target,
                "status": "packaged" if target in packaged_names else "error",
            }
            for target in sorted(fixture_targets)
        ]
        if any(item["status"] == "error" for item in fixture_status):
            missing = [item["target"] for item in fixture_status if item["status"] == "error"]
            raise ValueError("runtime fixture target not packaged in lab: " + ", ".join(missing))

        write_json(
            stage / "capabilities.json",
            {
                "schema_version": "1.0",
                "channel": "lab",
                "source_revision": revision,
                "capability_contract": capability_contract_metadata(),
                "session_rule": "Use this isolated Lab without the production plugin in the same runtime session.",
                "capabilities": sorted(capabilities, key=lambda x: x["name"]),
                "runtime_fixture_targets": fixture_status,
                "runtime_tools": runtime_tools,
            },
        )
        digest = sha256_tree(stage)
        write_json(
            stage / "release-manifest.json",
            {
                "schema_version": "1.0",
                "release_id": f"{version}+{revision[:12]}",
                "package": PLUGIN_NAME,
                "version": version,
                "channel": "lab",
                "source_revision": revision,
                "capability_contract": capability_contract_metadata(),
                "payload_content_sha256": digest,
                "components": [
                    {
                        "name": item["name"],
                        "kind": item["kind"],
                        "maturity": item.get("maturity"),
                        "version": item.get("version"),
                        "content_sha256": item.get("content_sha256"),
                        "capability_assessment": item.get("capability_assessment"),
                    }
                    for item in sorted(capabilities, key=lambda x: x["name"])
                ],
            },
        )

    print(
        f"Packaged {len(all_skills)} skills across all maturity statuses + "
        f"{len(workflow_names)} workflow entrypoints across all maturity statuses + "
        f"{runtime_eval_fixtures} runtime eval inputs into {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
