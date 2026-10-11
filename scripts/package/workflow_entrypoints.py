from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

import yaml

from build_utils import include_runtime_file
from portable import portable_metadata
from skill_interface import workflow_domain, write_skill_interface


def load_registry(root: Path) -> list[dict]:
    path = root / "workflows" / "runtime-registry.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = data.get("workflows") or []
    if not isinstance(items, list):
        raise ValueError("workflows/runtime-registry.yaml: workflows must be a list")
    return items


def channel_supported(item: dict[str, Any], channel: str) -> bool:
    channels = item.get("channels") or {}
    if not isinstance(channels, dict):
        return False
    return channels.get(channel) == "supported"


def select_workflows(root: Path, maturity: str, channel: str = "plugin") -> list[dict]:
    selected = []
    for item in load_registry(root):
        metadata = item.get("metadata") or {}
        if (maturity == "all" or metadata.get("maturity") == maturity) and channel_supported(item, channel):
            selected.append(item)
    return selected


def dependency_names(item: dict[str, Any]) -> tuple[list[str], list[dict[str, str]]]:
    deps = item.get("dependencies") or {}
    required = deps.get("required") or []
    optional = deps.get("optional") or []
    if not isinstance(required, list) or not all(isinstance(x, str) for x in required):
        raise ValueError(f"{item.get('name')}: dependencies.required must be a list of names")
    if not isinstance(optional, list):
        raise ValueError(f"{item.get('name')}: dependencies.optional must be a list")
    normalized_optional: list[dict[str, str]] = []
    for entry in optional:
        if not isinstance(entry, dict):
            raise ValueError(f"{item.get('name')}: optional dependency must be a mapping")
        name = str(entry.get("name") or "").strip()
        on_missing = str(entry.get("on_missing") or "").strip()
        if not name or not on_missing:
            raise ValueError(f"{item.get('name')}: optional dependency needs name and on_missing")
        normalized_optional.append({"name": name, "on_missing": on_missing})
    return required, normalized_optional


def dependency_availability(item: dict[str, Any], available_names: set[str]) -> tuple[list[str], list[dict[str, str]]]:
    required, optional = dependency_names(item)
    missing_required = [name for name in required if name not in available_names]
    missing_optional = [entry for entry in optional if entry["name"] not in available_names]
    return missing_required, missing_optional


def build_entrypoint(
    root: Path,
    item: dict,
    skills_out: Path,
    available_names: set[str],
) -> str:
    name = item.get("name")
    workflow_rel = item.get("workflow")
    description = str(item.get("description") or "").strip()
    metadata = item.get("metadata") or {}

    if not name or not workflow_rel or not description:
        raise ValueError(f"Invalid workflow registry item: {item}")

    workflow = root / workflow_rel
    if not workflow.exists():
        raise FileNotFoundError(f"Missing workflow source: {workflow}")

    missing_required, missing_optional = dependency_availability(item, available_names)
    if missing_required:
        raise ValueError(
            f"{name}: required runtime dependencies unavailable in this package: "
            + ", ".join(sorted(missing_required))
        )

    dst = skills_out / name
    if dst.exists():
        raise ValueError(f"duplicate runtime skill/workflow name: {name}")

    refs = dst / "references"
    refs.mkdir(parents=True, exist_ok=True)
    shutil.copy2(workflow, refs / "WORKFLOW.md")
    source_refs = workflow.parent / "references"
    if source_refs.is_dir():
        for source in sorted(source_refs.rglob("*")):
            if not source.is_file():
                continue
            if source.is_symlink():
                raise ValueError(f"workflow support symlinks are not allowed: {source}")
            relative = source.relative_to(source_refs)
            package_relative = Path("references") / relative
            if (
                not include_runtime_file(package_relative)
                or any(part in {"tests", "evals"} for part in relative.parts)
            ):
                continue
            target = refs / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    fm = yaml.safe_dump(
        {
            "name": name,
            "description": description,
            "metadata": portable_metadata(metadata),
        },
        sort_keys=False,
        allow_unicode=True,
    ).strip()

    dependency_section = ""
    if missing_optional:
        rows = [
            "",
            "## Dependency availability",
            "",
            "The following optional branches are unavailable in this package. Do not simulate or claim execution of the missing specialist:",
            "",
        ]
        for entry in missing_optional:
            rows.append(f"- `{entry['name']}`: {entry['on_missing']}")
        rows.append("")
        dependency_section = "\n".join(rows)

    skill_md = f"""---
{fm}
---

# {name.replace('-', ' ').title()} Runtime Entrypoint

## Purpose

Expose a repository workflow to the skill runtime without duplicating its orchestration logic.

## Procedure

1. Load `references/WORKFLOW.md`.
2. Follow it as the authoritative orchestration procedure.
3. Route only to specialist skills that the workflow actually requires.
4. Preserve workflow gates, stop conditions and evidence discipline.
5. If an optional dependency is unavailable, apply the declared reduced-scope behavior below and explicitly disclose that the specialist did not run.
6. Do not replace the workflow with a generic best-practice answer.
{dependency_section}
## Output contract

Use the output contract defined in `references/WORKFLOW.md`.

## Quality checks

- [ ] The workflow source was loaded.
- [ ] Specialist skills were selected selectively.
- [ ] Required dependencies were available.
- [ ] Missing optional dependencies were disclosed and not simulated.
- [ ] Workflow stage order and gates were preserved.
- [ ] Evidence and uncertainty remain explicit.
- [ ] No extra domain was added merely for completeness.
"""
    (dst / "SKILL.md").write_text(skill_md, encoding="utf-8")
    write_skill_interface(
        root, dst, name=name, description=description,
        domain=workflow_domain(str(name)),
    )
    return name


def add_workflow_entrypoints(
    root: Path,
    maturity: str,
    skills_out: Path,
    *,
    channel: str = "plugin",
    available_names: set[str] | None = None,
) -> list[str]:
    selected = select_workflows(root, maturity, channel=channel)
    names = [str(item.get("name")) for item in selected]
    if available_names is None:
        available_names = {p.name for p in skills_out.iterdir() if p.is_dir()}
    effective_available = set(available_names) | set(names)
    built: list[str] = []
    for item in selected:
        built.append(build_entrypoint(root, item, skills_out, effective_available))
    return built
