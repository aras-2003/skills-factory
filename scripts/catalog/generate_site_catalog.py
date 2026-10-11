from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def collect_workflow_sources(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted((root / "workflows").rglob("WORKFLOW.md"))
    }


def _workflow_summary(text: str) -> str:
    lines = text.splitlines()
    in_purpose = False
    heading = ""
    topics: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.casefold() == "## purpose":
            in_purpose = True
            continue
        if in_purpose and stripped.startswith("## "):
            break
        if not in_purpose or not stripped:
            continue
        if not heading and not stripped.startswith(("#", "-", "*")):
            heading = " ".join(stripped.split()).rstrip(":")
        elif stripped.startswith(("-", "*")):
            topic = stripped[1:].strip()
            if topic:
                topics.append(" ".join(topic.split()))
        elif heading:
            break
    if not heading:
        return ""
    if topics:
        return heading + " " + "; ".join(topics) + "."
    return heading


def split_markdown_row(line: str) -> list[str]:
    """Split a pipe table row while keeping escaped pipes inside cells."""
    cells = re.split(r"(?<!\\)\|", line.strip())
    if cells and not cells[0].strip():
        cells = cells[1:]
    if cells and not cells[-1].strip():
        cells = cells[:-1]
    return [cell.replace(r"\|", "|").strip() for cell in cells]


def parse_package_manifest(text: str) -> dict[str, dict[str, str]]:
    """Read package identities without adding a YAML dependency."""
    packages: dict[str, dict[str, str]] = {}
    for key, label in (("package", "production"), ("lab", "lab")):
        match = re.search(
            rf"(?ms)^{re.escape(key)}:\s*\n(.*?)(?=^[^ \t]|\Z)",
            text,
        )
        if not match:
            raise ValueError(f"Missing {key} package metadata")
        section = match.group(1)
        name = re.search(r"(?m)^  name:\s*([^\n#]+)", section)
        version = re.search(r"(?m)^  version:\s*['\"]?([^'\"\s#]+)", section)
        if not name or not version:
            raise ValueError(f"Missing name or version for {key} package")
        packages[label] = {"name": name.group(1).strip(), "version": version.group(1).strip()}
    return packages


def build_catalog(
    markdown: str,
    package_manifest: str,
    source_revision: str,
    workflow_registry: str = "workflows: []\n",
    capability_contract: str = "contract_id: repository-side-v1\ncomponent_declarations: {}\n",
    workflow_sources: dict[str, str] | None = None,
) -> dict[str, object]:
    contract = yaml.safe_load(capability_contract) or {}
    if contract.get("contract_id") not in {None, "repository-side-v1"}:
        raise ValueError("Unsupported capability contract in site catalog input")
    declarations = contract.get("component_declarations") or {}
    if not isinstance(declarations, dict):
        raise ValueError("Capability contract component_declarations must be a mapping")
    def assessment(name: str) -> str:
        item = declarations.get(name)
        if not isinstance(item, dict):
            return "UNASSESSED"
        requirements = item.get("requirements")
        expected = {"network", "filesystem", "shell_exec", "credentials", "external_actions"}
        if not isinstance(requirements, dict) or set(requirements) != expected:
            return "UNASSESSED"
        if any(not isinstance(value, str) or value == "unassessed" for value in requirements.values()):
            return "UNASSESSED"
        return "DECLARED"

    skills: list[dict[str, str]] = []
    for line in markdown.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = split_markdown_row(line)
        if len(cells) != 6 or cells[0] == "Skill" or set("".join(cells)) <= {"-", ":", " "}:
            continue
        name, domain, maturity, version, description, source = cells
        if not all((name, domain, maturity, description, source)):
            raise ValueError(f"Invalid catalog row for {name or '(unnamed skill)'}")
        if source.startswith("/") or ".." in Path(source).parts:
            raise ValueError(f"Unsafe source path for {name}: {source}")
        skills.append({
            "name": name,
            "domain": domain,
            "maturity": maturity,
            "version": version,
            "description": description,
            "source": source,
            "source_status": "present",
            "capability_assessment": assessment(name),
        })
    if not skills:
        raise ValueError("CATALOG.md did not contain any skill rows")
    revision = source_revision.strip()
    if not revision:
        raise ValueError("Source revision is required for version provenance")
    registry = yaml.safe_load(workflow_registry) or {}
    workflows: list[dict[str, object]] = []
    registered_sources: set[str] = set()
    for item in registry.get("workflows") or []:
        if not isinstance(item, dict) or not item.get("name"):
            raise ValueError("Invalid workflow registry entry")
        workflow_path = str(item.get("workflow") or "")
        if not workflow_path or workflow_path.startswith("/") or ".." in Path(workflow_path).parts:
            raise ValueError(f"Unsafe workflow source path for {item.get('name')}")
        if workflow_sources is not None and workflow_path not in workflow_sources:
            raise ValueError(f"Missing workflow source for {item.get('name')}: {workflow_path}")
        registered_sources.add(workflow_path)
        dependencies = item.get("dependencies") or {}
        workflows.append({
            "name": str(item["name"]),
            "source": workflow_path,
            "source_status": "present",
            "runtime_registration": "registered",
            "maturity": str((item.get("metadata") or {}).get("maturity") or "unknown"),
            "version": str((item.get("metadata") or {}).get("version") or "unknown"),
            "description": " ".join(str(item.get("description") or "").split()),
            "declared_channels": dict(sorted((item.get("channels") or {}).items())),
            "required_dependencies": sorted(str(x) for x in dependencies.get("required") or []),
            "optional_dependencies": sorted(
                str(x.get("name")) for x in dependencies.get("optional") or []
                if isinstance(x, dict) and x.get("name")
            ),
            "capability_assessment": assessment(str(item["name"])),
        })
    for workflow_path, content in sorted((workflow_sources or {}).items()):
        if workflow_path in registered_sources:
            continue
        if not workflow_path.startswith("workflows/") or not workflow_path.endswith("/WORKFLOW.md") or ".." in Path(workflow_path).parts:
            raise ValueError(f"Unsafe unregistered workflow source path: {workflow_path}")
        workflow_name = Path(workflow_path).parent.name
        workflows.append({
            "name": workflow_name,
            "source": workflow_path,
            "source_status": "present",
            "runtime_registration": "not_registered",
            "maturity": "unknown",
            "version": "unknown",
            "description": _workflow_summary(content),
            "declared_channels": {},
            "required_dependencies": [],
            "optional_dependencies": [],
            "capability_assessment": assessment(workflow_name),
        })
    workflows.sort(key=lambda item: str(item["name"]))
    statuses = [item["capability_assessment"] for item in skills + workflows]
    overall_assessment = "UNASSESSED" if not any(status == "DECLARED" for status in statuses) else (
        "ASSESSED" if all(status == "DECLARED" for status in statuses) else "PARTIALLY_DECLARED"
    )
    return {
        "metadata": {
            "packages": parse_package_manifest(package_manifest),
            "source_revision": revision[:12],
            "capability_contract": "repository-side-v1",
            "capability_assessment": overall_assessment,
            "runtime_installation": "NOT_OBSERVED",
            "availability_semantics": "Source maturity and declared channels do not prove package inclusion or installed runtime availability.",
            "source_workflow_count": len(workflows),
            "registered_workflow_count": sum(item["runtime_registration"] == "registered" for item in workflows),
        },
        "skills": skills,
        "workflows": workflows,
    }


def current_revision() -> str:
    revision = os.environ.get("GITHUB_SHA") or os.environ.get("SOURCE_REVISION")
    if revision:
        return revision[:12]
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "--short=12", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> int:
    source = ROOT / "CATALOG.md"
    package_source = ROOT / "release" / "package.yaml"
    output = ROOT / "docs" / "catalog.json"
    catalog = build_catalog(
        source.read_text(encoding="utf-8"),
        package_source.read_text(encoding="utf-8"),
        current_revision(),
        (ROOT / "workflows" / "runtime-registry.yaml").read_text(encoding="utf-8"),
        (ROOT / "release" / "capability-contract.yaml").read_text(encoding="utf-8"),
        collect_workflow_sources(ROOT),
    )
    output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated site catalog with {len(catalog['skills'])} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
