#!/usr/bin/env python3
"""Generate a read-only Investment capability source inventory.

Source metadata and workflow channel declarations are reported separately from
installed runtime evidence. This command never writes by default.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "validate"))
from common import load_yaml, split_frontmatter  # noqa: E402

SOURCE_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
WORKFLOW_CHANNELS = ("plugin", "lab", "chatgpt-zip")


def _source_record(records: dict[str, dict[str, Any]], source: str, *, kind: str, name: str, data: bytes) -> dict:
    record = records.get(source)
    if record is None:
        raise ValueError(f"missing provenance record for {source}")
    if record.get("kind") != kind or record.get("name") != name:
        raise ValueError(f"provenance identity mismatch for {source}")
    digest = hashlib.sha256(data).hexdigest()
    if record.get("source_sha256") != digest:
        raise ValueError(f"stale provenance SHA-256 for {source}")
    return record


def collect_inventory(root: Path, source_revision: str) -> dict[str, Any]:
    if not SOURCE_REVISION_RE.fullmatch(source_revision):
        raise ValueError("source_revision must be a full 40-character Git commit SHA")

    provenance_data = load_yaml(root / "provenance" / "registry.yaml")
    if not isinstance(provenance_data, dict) or not isinstance(provenance_data.get("records"), list):
        raise ValueError("provenance registry must contain a records list")
    records: dict[str, dict[str, Any]] = {}
    for record in provenance_data["records"]:
        if not isinstance(record, dict):
            raise ValueError("invalid provenance record")
        source = record.get("source")
        if not isinstance(source, str) or source in records:
            raise ValueError(f"missing or duplicate provenance source: {source}")
        records[source] = record

    skills: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for path in sorted((root / "skills" / "investing").glob("*/SKILL.md")):
        source = path.relative_to(root).as_posix()
        raw = path.read_bytes()
        frontmatter, _ = split_frontmatter(raw.decode("utf-8"))
        name = frontmatter.get("name")
        metadata = frontmatter.get("metadata")
        if not isinstance(name, str) or not isinstance(metadata, dict):
            raise ValueError(f"missing name/metadata in {source}")
        if name in seen_names:
            raise ValueError(f"duplicate Investment skill name: {name}")
        seen_names.add(name)
        record = _source_record(records, source, kind="skill", name=name, data=raw)
        skills.append({
            "kind": "skill",
            "name": name,
            "source": source,
            "version": str(metadata.get("version", "")),
            "maturity": str(metadata.get("maturity", "")),
            "source_sha256": record["source_sha256"],
            "provenance": str(record.get("classification", "UNKNOWN")),
            "declared_channels": "NOT_DECLARED_PER_SKILL",
        })

    registry = load_yaml(root / "workflows" / "runtime-registry.yaml")
    if not isinstance(registry, dict) or not isinstance(registry.get("workflows"), list):
        raise ValueError("runtime registry must contain a workflows list")
    workflows: list[dict[str, Any]] = []
    seen_workflows: set[str] = set()
    for row in registry["workflows"]:
        if not isinstance(row, dict):
            raise ValueError("invalid runtime workflow row")
        name = row.get("name")
        if not isinstance(name, str) or not name.startswith("investment-"):
            continue
        if name in seen_workflows:
            raise ValueError(f"duplicate Investment workflow name: {name}")
        seen_workflows.add(name)
        source = row.get("workflow")
        if not isinstance(source, str) or not source.startswith("workflows/investment-") or ".." in Path(source).parts:
            raise ValueError(f"invalid source path for {name}")
        path = root / source
        if not path.is_file():
            raise ValueError(f"registered workflow source missing for {name}: {source}")
        raw = path.read_bytes()
        record = _source_record(records, source, kind="workflow", name=name, data=raw)
        metadata = row.get("metadata")
        if not isinstance(metadata, dict):
            raise ValueError(f"missing registry metadata for {name}")
        channels = row.get("channels")
        if not isinstance(channels, dict):
            raise ValueError(f"missing channel declarations for {name}")
        workflows.append({
            "kind": "workflow",
            "name": name,
            "source": source,
            "version": str(metadata.get("version", "")),
            "maturity": str(metadata.get("maturity", "")),
            "source_sha256": record["source_sha256"],
            "provenance": str(record.get("classification", "UNKNOWN")),
            "declared_channels": {channel: channels.get(channel, "unknown") for channel in WORKFLOW_CHANNELS},
        })

    if not skills:
        raise ValueError("no Investment skill sources found")
    if not workflows:
        raise ValueError("no registered Investment workflows found")
    return {
        "source_revision": source_revision,
        "runtime_installation": "NOT_OBSERVED_BY_STATIC_SOURCE_GENERATOR",
        "skill_count": len(skills),
        "workflow_count": len(workflows),
        "skills": skills,
        "workflows": workflows,
    }


def render_markdown(inventory: dict[str, Any]) -> str:
    lines = [
        f"# Investment capability source inventory — {inventory['source_revision']}",
        "",
        f"Source inventory: {inventory['skill_count']} Investing skills and {inventory['workflow_count']} registered Investment workflows.",
        "Runtime installation/execution: **NOT_OBSERVED by this static generator**. Source-declared channels do not prove an installed runtime.",
        "",
        "| Kind | Capability | Source | Version | Maturity | Source SHA-256 | Provenance | Channel declaration |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in [*inventory["skills"], *inventory["workflows"]]:
        channels = row["declared_channels"]
        if isinstance(channels, dict):
            channel_text = ", ".join(f"{key}={channels[key]}" for key in WORKFLOW_CHANNELS)
        else:
            channel_text = channels
        lines.append(
            f"| {row['kind']} | {row['name']} | `{row['source']}` | {row['version']} | "
            f"{row['maturity']} | `{row['source_sha256']}` | {row['provenance']} | {channel_text} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--output", type=Path, help="optional output path; omit for stdout")
    args = parser.parse_args(argv)
    try:
        output = render_markdown(collect_inventory(args.repo_root, args.source_revision))
    except (OSError, ValueError) as exc:
        print(f"BLOCKED_SOURCE: {exc}", file=sys.stderr)
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
