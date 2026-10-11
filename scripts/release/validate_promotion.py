from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate_promotion(root: Path, *, require_ancestor: bool = True) -> list[str]:
    errors: list[str] = []
    lab_path = root / "plugins/skills-factory-lab/release-manifest.json"
    lab_copy_path = root / "docs/lab-release.json"
    production_paths = [
        root / "plugins/skills-factory/release-manifest.json",
        root / "dist/chatgpt-skills/release-manifest.json",
    ]
    try:
        lab = _read_json(lab_path)
        lab_copy = _read_json(lab_copy_path)
        production = [_read_json(path) for path in production_paths]
    except ValueError as exc:
        return [str(exc)]

    source_revision = lab.get("source_revision")
    lab_release_id = lab.get("release_id")
    lab_digest = lab.get("payload_content_sha256")
    if not isinstance(source_revision, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", source_revision):
        errors.append("Lab manifest must identify a full 40-character source_revision")
        source_revision = None
    if not isinstance(lab_release_id, str) or not lab_release_id:
        errors.append("Lab manifest is missing release_id")
    if not isinstance(lab_digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", lab_digest):
        errors.append("Lab manifest is missing a SHA-256 payload digest")
    for field in ("source_revision", "release_id", "payload_content_sha256", "version"):
        if lab_copy.get(field) != lab.get(field):
            errors.append(f"docs/lab-release.json does not match Lab package field {field}")

    for path, manifest in zip(production_paths, production):
        if manifest.get("source_revision") != source_revision:
            errors.append(f"{path.relative_to(root)} was not built from the exact Lab source revision")
        if manifest.get("channel") not in {"plugin", "chatgpt-zip"}:
            errors.append(f"{path.relative_to(root)} has an unexpected release channel")

    evidence_path = root / "release/promotion-evidence.json"
    try:
        evidence = _read_json(evidence_path)
    except ValueError as exc:
        errors.append(str(exc))
        evidence = {}
    required_evidence = {
        "source_revision": source_revision,
        "lab_release_id": lab_release_id,
        "lab_payload_content_sha256": lab_digest,
        "status": "PASS",
    }
    for field, expected in required_evidence.items():
        if evidence.get(field) != expected:
            errors.append(f"promotion evidence {field} must match the exact Lab candidate")
    for field in ("run_id", "run_url", "observed_at"):
        if not isinstance(evidence.get(field), str) or not evidence[field].strip():
            errors.append(f"promotion evidence must include {field}")

    if require_ancestor and source_revision:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", source_revision, "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            errors.append("Lab-tested source revision is not an ancestor of this production promotion")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify exact Lab-to-production candidate identity.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    errors = validate_promotion(args.root.resolve())
    if errors:
        print("Production promotion blocked:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Production promotion identity and Lab runtime evidence verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
