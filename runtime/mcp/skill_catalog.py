"""Load the packaged Skills Factory catalog shared by Lab and remote MCP."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import yaml


_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_REFERENCE_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".csv"}


def packaged_release_identity() -> dict[str, Any]:
    """Expose actual installed manifest fields; never substitute ZIP hashes."""
    path = _plugin_root() / "release-manifest.json"
    if not path.is_file() or path.is_symlink():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return {}
    fields = ("channel", "version", "release_id", "source_revision", "payload_content_sha256")
    if not isinstance(value, dict) or any(not isinstance(value.get(k), str) or not value[k] for k in fields):
        return {}
    if not re.fullmatch(r"[0-9a-f]{40}", value["source_revision"]) or not re.fullmatch(r"[0-9a-f]{64}", value["payload_content_sha256"]):
        return {}
    return {k: value[k] for k in fields}


def _plugin_root() -> Path:
    configured = os.environ.get("PLUGIN_ROOT", "").strip()
    if configured:
        return Path(configured).resolve()
    current = Path(__file__).resolve()
    for candidate in (current.parent, *current.parents):
        if (candidate / "skills").is_dir():
            return candidate
    return current.parents[2]


def skills_root() -> Path:
    configured = os.environ.get("SKILLS_FACTORY_SKILLS_ROOT", "").strip()
    root = Path(configured).resolve() if configured else _plugin_root() / "skills"
    if not root.is_dir():
        raise RuntimeError(f"Skills catalog is unavailable: {root}")
    return root


def _frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    marker = text.find("\n---", 4)
    if marker < 0:
        return {}, text
    metadata = yaml.safe_load(text[4:marker]) or {}
    return metadata if isinstance(metadata, dict) else {}, text


def _tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        relative_path = item.relative_to(path)
        # This digest describes the host-loadable skill surface, not isolated
        # executor fixtures or repository-side evaluator material.
        if {"evals", "tests"}.intersection(relative_path.parts):
            continue
        relative = relative_path.as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        content = (
            _public_instructions(item.read_text(encoding="utf-8")).encode("utf-8")
            if relative_path.name == "SKILL.md"
            else item.read_bytes()
        )
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


def _public_instructions(text: str) -> str:
    """Strip Lab-only fixture indexes from legacy packaged skill text."""
    lines: list[str] = []
    for line in text.splitlines():
        if line.strip().casefold() == "## lab runtime eval inputs":
            break
        if "references/evals/" in line.casefold():
            continue
        lines.append(line)
    return "\n".join(lines).rstrip()


def _entry(skill_dir: Path) -> dict[str, Any]:
    metadata, _ = _frontmatter(skill_dir / "SKILL.md")
    nested = metadata.get("metadata") or {}
    name = str(metadata.get("name") or skill_dir.name)
    return {
        "name": name,
        "directory": skill_dir.relative_to(skills_root()).as_posix(),
        "domain": skill_dir.parent.name,
        "kind": "skill",
        "description": str(metadata.get("description") or ""),
        "version": str(nested.get("version") or "unknown"),
        "maturity": str(nested.get("maturity") or "unknown"),
        "content_sha256": _tree_digest(skill_dir),
    }


def entries() -> list[dict[str, Any]]:
    result = []
    for skill_dir in sorted(p.parent for p in skills_root().rglob("SKILL.md")):
        result.append(_entry(skill_dir))
    return result


def catalog_digest(items: list[dict[str, Any]] | None = None) -> str:
    items = items if items is not None else entries()
    payload = "\n".join(
        f"{item['name']}:{item['content_sha256']}" for item in sorted(items, key=lambda x: x["name"])
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def list_skills() -> dict[str, Any]:
    items = entries()
    return {
        "catalog_name": "Skills Factory Lab parity catalog",
        "evidence_boundary": {
            "scope": "Packaged capabilities only; not historical backlog or GitHub Project membership/acceptance.",
            "reconciliation": "For a source/backlog count mismatch, request the exact source revision and both ID sets. Report only verified set differences; counts alone cannot identify the missing ID. Keep source mapping, live Project fields/dependencies and runtime acceptance separate.",
            "unverified_revision": "If a required source revision is unavailable, mark that comparison BLOCKED_SOURCE_REVISION and ask for it; never guess the authoritative version.",
        },
        "catalog_digest": catalog_digest(items),
        "source_revision": os.environ.get("SKILLS_FACTORY_SOURCE_REVISION", "unattested"),
        "channel": os.environ.get("SKILLS_FACTORY_CHANNEL", "unknown"),
        "skills": [
            {key: value for key, value in item.items() if key != "directory"}
            for item in sorted(items, key=lambda x: x["name"])
        ],
    }


def load_skill(skill_name: str) -> dict[str, Any]:
    if not isinstance(skill_name, str) or not _SAFE_NAME.fullmatch(skill_name):
        raise ValueError("skill_name must be a simple packaged skill name")
    matches = [item for item in entries() if item["name"] == skill_name]
    if not matches:
        raise ValueError(f"skill is not present in the packaged Lab catalog: {skill_name}")
    item = matches[0]
    skill_dir = skills_root() / item["directory"]
    _, instructions = _frontmatter(skill_dir / "SKILL.md")
    instructions = _public_instructions(instructions)
    references = []
    reference_root = skill_dir / "references"
    if reference_root.is_dir() and not reference_root.is_symlink():
        for path in sorted(reference_root.rglob("*")):
            if (
                not path.is_file()
                or path.is_symlink()
                or path.suffix.lower() not in _REFERENCE_SUFFIXES
                or "evals" in path.relative_to(reference_root).parts
            ):
                continue
            references.append(
                {
                    "path": path.relative_to(skill_dir).as_posix(),
                    "content": path.read_text(encoding="utf-8"),
                }
            )
    return {
        **{key: value for key, value in item.items() if key != "directory"},
        "execution_mode": "host_model_executes_loaded_instructions",
        "instructions": instructions,
        "reference_files": references,
        "content_sha256": item["content_sha256"],
        "source_revision": os.environ.get("SKILLS_FACTORY_SOURCE_REVISION", "unattested"),
    }
