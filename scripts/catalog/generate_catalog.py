from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "validate"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import repo_root_from, split_frontmatter  # noqa: E402
from generate_site_catalog import build_catalog, collect_workflow_sources, current_revision  # noqa: E402
from provenance.catalog import load_registry, records_by_source  # noqa: E402


def main() -> int:
    root = repo_root_from(__file__)
    rows = []
    provenance_registry = load_registry(root)
    provenance_by_source = records_by_source(provenance_registry)

    for skill_file in sorted((root / "skills").rglob("SKILL.md")):
        frontmatter, _ = split_frontmatter(skill_file.read_text(encoding="utf-8"))
        rel = skill_file.parent.relative_to(root)
        parts = rel.parts
        domain = parts[1] if len(parts) > 1 else ""
        metadata = frontmatter.get("metadata") or {}
        rows.append(
            (
                frontmatter.get("name", ""),
                domain,
                " ".join(str(frontmatter.get("description", "")).split()),
                metadata.get("maturity", ""),
                metadata.get("version", ""),
                str(rel / "SKILL.md"),
                provenance_by_source[str(rel / "SKILL.md")]["classification"],
            )
        )

    out = [
        "# Skill Catalog",
        "",
        "> Generated from SKILL.md metadata and `provenance/registry.yaml`. Do not edit manually.",
        "",
        "| Skill | Domain | Maturity | Version | Description | Source | Provenance |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, domain, description, maturity, version, source, provenance in rows:
        safe = description.replace("|", "\\|")
        out.append(f"| {name} | {domain} | {maturity} | {version} | {safe} | {source} | {provenance} |")

    markdown = "\n".join(out) + "\n"
    catalog_path = root / "CATALOG.md"
    catalog_path.write_text(markdown, encoding="utf-8")

    # CATALOG.md and the website JSON are two published views of the same
    # skills/package metadata. Refresh both here so version changes cannot
    # leave the site data stale.
    site_path = root / "docs" / "catalog.json"
    previous_revision = ""
    if site_path.is_file():
        previous = json.loads(site_path.read_text(encoding="utf-8"))
        previous_revision = str((previous.get("metadata") or {}).get("source_revision") or "")
    package_manifest = (root / "release" / "package.yaml").read_text(encoding="utf-8")
    site_catalog = build_catalog(
        markdown,
        package_manifest,
        previous_revision or current_revision(),
        (root / "workflows" / "runtime-registry.yaml").read_text(encoding="utf-8"),
        (root / "release" / "capability-contract.yaml").read_text(encoding="utf-8"),
        collect_workflow_sources(root),
        provenance_registry,
    )
    site_path.write_text(
        json.dumps(site_catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated CATALOG.md and docs/catalog.json with {len(rows)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
