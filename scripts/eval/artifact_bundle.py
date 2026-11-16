"""Bind downloaded QA artifacts to a candidate and fixture, without asserting PASS."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

MANIFEST = "artifact-manifest.json"


def inventory(directory: Path) -> dict[str, str]:
    result = {}
    for file in sorted(directory.rglob("*")):
        if file.is_symlink():
            raise ValueError("Artifact bundle must not contain symlinks")
        if file.is_file() and file.relative_to(directory).as_posix() != MANIFEST:
            result[file.relative_to(directory).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    if not result:
        raise ValueError("Artifact bundle is empty")
    return result


def pack(directory: Path, candidate: str, fixture: str | None = None) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", candidate):
        raise ValueError("Candidate must be an exact source commit SHA")
    if fixture is not None and not re.fullmatch(r"[0-9a-f]{64}", fixture):
        raise ValueError("Fixture must be a SHA-256 digest")
    return {"schema_version": "1.0", "candidate_source_revision": candidate,
            "fixture_sha256": fixture, "files": inventory(directory), "runtime_pass_claim": False}


def verify(directory: Path, candidate: str, fixture: str | None = None) -> dict:
    data = json.loads((directory / MANIFEST).read_text(encoding="utf-8"))
    expected = pack(directory, candidate, fixture)
    if data != expected:
        raise ValueError("Artifact candidate, fixture, manifest or file digests do not match")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("pack", "verify"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--fixture-sha256")
    args = parser.parse_args()
    if args.command == "pack":
        path = args.directory / MANIFEST
        if path.exists():
            raise ValueError("Existing artifact manifest is immutable; create a new bundle")
        path.write_text(json.dumps(pack(args.directory, args.candidate, args.fixture_sha256), indent=2) + "\n")
    else:
        verify(args.directory, args.candidate, args.fixture_sha256)
    print("Artifact identity/integrity verified; behavioral acceptance is separate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
