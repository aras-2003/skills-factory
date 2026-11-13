from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

from build_utils import (
    atomic_output,
    capability_assessment,
    capability_contract_metadata,
    copy_runtime_support,
    ensure_source_valid,
    package_version,
    sha256_tree,
    source_revision,
    write_json,
)
from portable import read_frontmatter, render_portable_skill
from workflow_entrypoints import load_registry
from skill_interface import repository_root, skill_domain, write_skill_interface

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from provenance.catalog import (  # noqa: E402
    enrich_capabilities,
    load_registry as load_provenance_registry,
    provenance_metadata,
)


ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ZIP_MODE = 0o100644 << 16


def discover_skills(root: Path, maturity: str) -> list[Path]:
    selected: list[Path] = []
    for skill_md in sorted((root / "skills").rglob("SKILL.md")):
        fm, _ = read_frontmatter(skill_md)
        metadata = fm.get("metadata") or {}
        if metadata.get("maturity") == maturity:
            selected.append(skill_md.parent)
    return selected


def _zip_bytes(files: list[tuple[str, bytes]]) -> bytes:
    import io

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for arcname, data in sorted(files, key=lambda x: x[0]):
            info = zipfile.ZipInfo(arcname, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = ZIP_MODE
            info.create_system = 3
            zf.writestr(info, data)
    return buf.getvalue()


def _write_deterministic_zip(source_dir: Path, zip_path: Path, top_level: str) -> None:
    files: list[tuple[str, bytes]] = []
    for path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
        arcname = (Path(top_level) / path.relative_to(source_dir)).as_posix()
        files.append((arcname, path.read_bytes()))
    zip_path.write_bytes(_zip_bytes(files))


def build_skill_bundle(skill_dir: Path, output_dir: Path) -> dict:
    fm, _ = read_frontmatter(skill_dir / "SKILL.md")
    name = fm.get("name")
    metadata = fm.get("metadata") or {}
    if not isinstance(name, str) or not name:
        raise ValueError(f"{skill_dir}: missing skill name")

    staging = output_dir / "_staging" / name
    staging.mkdir(parents=True, exist_ok=False)
    (staging / "SKILL.md").write_text(
        render_portable_skill(skill_dir / "SKILL.md"),
        encoding="utf-8",
    )
    inventory = ["SKILL.md"] + copy_runtime_support(skill_dir, staging)
    root = repository_root(skill_dir)
    inventory.extend(
        write_skill_interface(
            root, staging, name=name, description=str(fm.get("description") or ""),
            domain=skill_domain(root, skill_dir),
        )
    )

    files: list[tuple[str, bytes]] = []
    for path in sorted(p for p in staging.rglob("*") if p.is_file()):
        rel = (Path(name) / path.relative_to(staging)).as_posix()
        files.append((rel, path.read_bytes()))

    archive = _zip_bytes(files)
    zip_path = output_dir / f"{name}.zip"
    zip_path.write_bytes(archive)
    content_digest = sha256_tree(staging)
    archive_digest = hashlib.sha256(archive).hexdigest()
    return {
        "name": name,
        "kind": "skill",
        "version": str(metadata.get("version", "unknown")),
        "maturity": str(metadata.get("maturity", "unknown")),
        "description": str(fm.get("description", "")).strip(),
        "zip": zip_path.name,
        "content_sha256": content_digest,
        "archive_sha256": archive_digest,
        "inventory": sorted(inventory),
        "capability_assessment": capability_assessment(root, name),
    }


def workflow_channel_status(root: Path, maturity: str) -> list[dict]:
    rows: list[dict] = []
    for item in load_registry(root):
        metadata = item.get("metadata") or {}
        if metadata.get("maturity") != maturity:
            continue
        channels = item.get("channels") or {}
        deps = item.get("dependencies") or {}
        rows.append(
            {
                "name": str(item.get("name")),
                "kind": "workflow",
                "status": str(channels.get("chatgpt-zip") or "unavailable"),
                "required_dependencies": list(deps.get("required") or []),
                "optional_dependencies": [
                    str(x.get("name"))
                    for x in (deps.get("optional") or [])
                    if isinstance(x, dict) and x.get("name")
                ],
                "capability_assessment": capability_assessment(root, str(item.get("name"))),
            }
        )
    return sorted(rows, key=lambda x: x["name"])


def build(root: Path, output_dir: Path, maturity: str, allow_empty: bool = False) -> dict:
    ensure_source_valid(root)
    selected = discover_skills(root, maturity)
    if not selected and not allow_empty:
        raise ValueError(f"No skills with maturity={maturity!r}; refusing to build empty package set")

    revision = source_revision(root)
    version = package_version(root, "package")
    provenance_registry = load_provenance_registry(root)
    provenance_meta = provenance_metadata(provenance_registry)

    with atomic_output(root, output_dir) as stage:
        bundles = [build_skill_bundle(skill_dir, stage) for skill_dir in selected]
        enrich_capabilities(bundles, provenance_registry)
        workflows = workflow_channel_status(root, maturity)
        enrich_capabilities(workflows, provenance_registry)
        index = {
            "format": "chatgpt-personal-skills",
            "schema_version": "1.0",
            "channel": "chatgpt-zip",
            "package_version": version,
            "source_revision": revision,
            "capability_contract": capability_contract_metadata(),
            **provenance_meta,
            "maturity": maturity,
            "skills": bundles,
            "workflows": workflows,
        }
        staging = stage / "_staging"
        if staging.exists():
            import shutil
            shutil.rmtree(staging)
        write_json(stage / "index.json", index)

        payload_digest = sha256_tree(stage)
        write_json(
            stage / "release-manifest.json",
            {
                "schema_version": "1.0",
                "release_id": f"{version}+{revision[:12]}",
                "package": "skills-factory",
                "version": version,
                "channel": "chatgpt-zip",
                "source_revision": revision,
                "capability_contract": capability_contract_metadata(),
                **provenance_meta,
                "payload_content_sha256": payload_digest,
                "component_count": len(bundles),
                "components": [
                    {
                        "name": x["name"],
                        "kind": x["kind"],
                        "version": x["version"],
                        "maturity": x["maturity"],
                        "zip": x["zip"],
                        "content_sha256": x["content_sha256"],
                        "archive_sha256": x["archive_sha256"],
                        "inventory": x["inventory"],
                        "capability_assessment": x["capability_assessment"],
                        "provenance": x["provenance"],
                    }
                    for x in bundles
                ],
            },
        )
        write_json(
            stage / "capabilities.json",
            {
                "schema_version": "1.0",
                "channel": "chatgpt-zip",
                "package_version": version,
                "source_revision": revision,
                "capability_contract": capability_contract_metadata(),
                **provenance_meta,
                "skills": [
                    {
                        "name": x["name"],
                        "status": "supported",
                        "version": x["version"],
                        "maturity": x["maturity"],
                        "zip": x["zip"],
                        "content_sha256": x["content_sha256"],
                        "archive_sha256": x["archive_sha256"],
                        "inventory": x["inventory"],
                        "capability_assessment": x["capability_assessment"],
                        "provenance": x["provenance"],
                    }
                    for x in bundles
                ],
                "workflows": workflows,
            },
        )

    return {
        "skills": len(selected),
        "version": version,
        "source_revision": revision,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--maturity", default="production")
    parser.add_argument("--output", default="dist/chatgpt-skills")
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    output_dir = root / args.output
    result = build(root, output_dir, args.maturity, allow_empty=args.allow_empty)
    print(
        f"Packaged {result['skills']} skills as {result['version']} "
        f"from {result['source_revision']} into {output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
