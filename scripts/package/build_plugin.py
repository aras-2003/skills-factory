from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from build_utils import (
    atomic_output,
    copy_runtime_support,
    capability_assessment,
    capability_contract_metadata,
    ensure_source_valid,
    package_version,
    package_runtime_mcp,
    sha256_tree,
    source_revision,
    write_json,
)
from portable import read_frontmatter, render_portable_skill
from workflow_entrypoints import add_workflow_entrypoints, load_registry
from skill_interface import repository_root, skill_domain, write_skill_interface

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from provenance.catalog import (  # noqa: E402
    enrich_capabilities,
    load_registry as load_provenance_registry,
    provenance_metadata,
)

PLUGIN_NAME = "skills-factory"


def discover_skills(root: Path, maturity: str) -> list[Path]:
    skills = []
    for skill_md in sorted((root / "skills").rglob("SKILL.md")):
        fm, _ = read_frontmatter(skill_md)
        metadata = fm.get("metadata") or {}
        if metadata.get("maturity") == maturity:
            skills.append(skill_md.parent)
    return skills


def copy_skill(src: Path, dst_root: Path) -> dict:
    fm, _ = read_frontmatter(src / "SKILL.md")
    name = fm.get("name")
    metadata = fm.get("metadata") or {}
    if not isinstance(name, str) or not name:
        raise ValueError(f"{src}: missing skill name")
    dst = dst_root / name
    if dst.exists():
        raise ValueError(f"duplicate packaged skill name: {name}")
    dst.mkdir(parents=True)
    (dst / "SKILL.md").write_text(render_portable_skill(src / "SKILL.md"), encoding="utf-8")
    inventory = ["SKILL.md"] + copy_runtime_support(src, dst)
    root = repository_root(src)
    inventory.extend(
        write_skill_interface(
            root, dst, name=name, description=str(fm.get("description") or ""),
            domain=skill_domain(root, src),
        )
    )
    return {
        "name": name,
        "kind": "skill",
        "version": str(metadata.get("version", "unknown")),
        "maturity": str(metadata.get("maturity", "unknown")),
        "inventory": sorted(inventory),
        "content_sha256": sha256_tree(dst),
        "capability_assessment": capability_assessment(root, name),
    }


def build(
    root: Path,
    out: Path,
    maturity: str,
    allow_empty: bool = False,
    runtime_mode: str = "local",
    remote_mcp_url: str | None = None,
) -> dict:
    if runtime_mode not in {"local", "remote", "skills-only"}:
        raise ValueError(f"unsupported runtime mode: {runtime_mode}")
    if runtime_mode == "remote" and not remote_mcp_url:
        raise ValueError("--remote-mcp-url is required for --runtime-mode remote")
    ensure_source_valid(root)
    selected = discover_skills(root, maturity)
    if not selected and not allow_empty:
        raise ValueError(f"No skills with maturity={maturity!r}; refusing to build empty plugin")

    with atomic_output(root, out) as stage:
        skills_out = stage / "skills"
        skills_out.mkdir(parents=True)
        capabilities = [copy_skill(skill_dir, skills_out) for skill_dir in selected]
        available_names = {item["name"] for item in capabilities}
        workflow_names = add_workflow_entrypoints(
            root,
            maturity,
            skills_out,
            channel="plugin",
            available_names=available_names,
        )
        provenance_registry = load_provenance_registry(root)
        registry_by_name = {
            str(item.get("name")): item
            for item in load_registry(root)
            if isinstance(item, dict) and item.get("name")
        }
        capabilities.extend(
            {
                "name": name,
                "kind": "workflow",
                "maturity": maturity,
                "version": str((registry_by_name[name].get("metadata") or {}).get("version") or ""),
                "content_sha256": sha256_tree(skills_out / name),
                "capability_assessment": capability_assessment(root, name),
            }
            for name in workflow_names
        )
        enrich_capabilities(capabilities, provenance_registry)

        version = package_version(root, "package")
        manifest = {
            "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "name": PLUGIN_NAME,
            "version": version,
            "description": "Validated production skills for Arkadiusz Kamrowski workflows.",
            "skills": "./skills/",
            "author": {"name": "Arkadiusz Kamrowski"},
            "repository": "https://github.com/aras-2003/skills-factory",
            "keywords": ["skills", "productivity", "career", "strategy", "research"],
            "extensions": {
                "com.openai": {
                    "interface": {
                        "displayName": "Skills Factory",
                        "shortDescription": "Validated reusable workflows from the Skills Factory catalog.",
                        "longDescription": "A governed collection of production-ready reusable skills maintained in GitHub and packaged for ChatGPT/Codex."
                    }
                }
            }
        }
        write_json(stage / "plugin.json", manifest)
        runtime_tools = (
            package_runtime_mcp(root, stage, mode=runtime_mode, remote_url=remote_mcp_url)
            if runtime_mode in {"local", "remote"}
            else []
        )
        compat_dir = stage / ".codex-plugin"
        compat_dir.mkdir(parents=True)
        compat_manifest = {
            "name": PLUGIN_NAME,
            "version": version,
            "description": manifest["description"],
            "skills": "./skills/",
        }
        if runtime_mode in {"local", "remote"}:
            compat_manifest["mcpServers"] = "./.mcp.json"
        write_json(compat_dir / "plugin.json", compat_manifest)
        revision = source_revision(root)
        write_json(
            stage / "capabilities.json",
            {
                "schema_version": "1.0",
                "channel": "plugin",
                "runtime_mode": runtime_mode,
                "surface_support": {
                    "chat_web": True,
                    "chat_mobile": runtime_mode == "skills-only",
                    "work": True,
                    "desktop": True,
                },
                "source_revision": revision,
                "capability_contract": capability_contract_metadata(),
                **provenance_metadata(provenance_registry),
                "capabilities": sorted(capabilities, key=lambda x: x["name"]),
                "runtime_tools": runtime_tools,
            },
        )
        payload_digest = sha256_tree(stage)
        write_json(
            stage / "release-manifest.json",
            {
                "schema_version": "1.0",
                "release_id": f"{version}+{revision[:12]}",
                "package": PLUGIN_NAME,
                "version": version,
                "channel": "plugin",
                "runtime_mode": runtime_mode,
                "source_revision": revision,
                "capability_contract": capability_contract_metadata(),
                **provenance_metadata(provenance_registry),
                "payload_content_sha256": payload_digest,
                "components": [
                    {
                        "name": item["name"],
                        "kind": item["kind"],
                        "maturity": item.get("maturity"),
                        "version": item.get("version"),
                        "content_sha256": item.get("content_sha256"),
                        "capability_assessment": item.get("capability_assessment"),
                        "provenance": item.get("provenance"),
                    }
                    for item in sorted(capabilities, key=lambda x: x["name"])
                ],
            },
        )

    return {
        "skills": len(selected),
        "workflows": len(workflow_names),
        "version": package_version(root, "package"),
        "source_revision": source_revision(root),
        "runtime_mode": runtime_mode,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--maturity", default="production")
    parser.add_argument("--output", default="plugins/skills-factory")
    parser.add_argument("--allow-empty", action="store_true")
    parser.add_argument(
        "--runtime-mode",
        choices=("local", "remote", "skills-only"),
        default="local",
        help="local stdio MCP, remote HTTPS MCP, or skills-only for mobile-safe Chat",
    )
    parser.add_argument("--remote-mcp-url", help="HTTPS /mcp endpoint for remote runtime mode")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    out = root / args.output
    result = build(
        root,
        out,
        args.maturity,
        allow_empty=args.allow_empty,
        runtime_mode=args.runtime_mode,
        remote_mcp_url=args.remote_mcp_url,
    )
    print(
        f"Packaged {result['skills']} skills + {result['workflows']} workflow entrypoints "
        f"as {result['version']} from {result['source_revision']} into {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
