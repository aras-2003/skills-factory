#!/usr/bin/env python3
"""Fail closed on mutable third-party GitHub Actions references."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

PIN = re.compile(r"^[0-9a-fA-F]{40}$")
DOCKER_PIN = re.compile(r"^docker://[^\s@]+@sha256:[0-9a-fA-F]{64}$")


def action_refs(node: object):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "uses":
                yield value
            else:
                yield from action_refs(value)
    elif isinstance(node, list):
        for child in node:
            yield from action_refs(child)


def validate_workflow(path: Path) -> list[str]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"{path}: unreadable or invalid workflow: {exc}"]
    errors: list[str] = []
    for ref in action_refs(document):
        if not isinstance(ref, str) or not ref.strip():
            errors.append(f"{path}: uses must be a nonempty literal action reference")
            continue
        if ref.startswith("./"):
            continue
        if ref.startswith("docker://"):
            if not DOCKER_PIN.fullmatch(ref):
                errors.append(f"{path}: mutable container reference: {ref}")
            continue
        if "@" not in ref:
            errors.append(f"{path}: action reference missing immutable SHA: {ref}")
            continue
        action, sha = ref.rsplit("@", 1)
        if not action or not PIN.fullmatch(sha):
            errors.append(f"{path}: action must use full 40-hex commit SHA: {ref}")
    return errors


def validate_directory(root: Path) -> list[str]:
    folder = root / ".github" / "workflows"
    if not folder.is_dir():
        return [f"{folder}: workflow directory absent"]
    paths = sorted(set(folder.glob("*.yml")) | set(folder.glob("*.yaml")))
    if not paths:
        return [f"{folder}: no workflow files found"]
    return [error for path in paths for error in validate_workflow(path)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    errors = validate_directory(args.root)
    for error in errors:
        print(f"[BLOCKER] {error}")
    if not errors:
        print("GitHub Actions dependency pins: OK (all external references immutable)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
