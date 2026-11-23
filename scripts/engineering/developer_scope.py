"""Inspect a delegated developer's committed Git scope without modifying it.

This is a post-execution consistency check. It is not a filesystem sandbox or
an authorization mechanism, and a matching diff is not proof of task success.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
from typing import Any


_SHA = re.compile(r"[0-9a-f]{40}\Z")
_SPECIAL_MODES = {b"120000", b"160000"}  # symlink and gitlink


class _GitError(Exception):
    pass


def _git(repo: Path, *arguments: str) -> bytes:
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *arguments],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            timeout=30, env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise _GitError("git_unavailable") from exc
    if result.returncode:
        raise _GitError("git_command_failed")
    return result.stdout


def _path(value: Any, *, directory_allowed: bool) -> str:
    if not isinstance(value, str) or not value or "\0" in value or "\\" in value:
        raise ValueError("paths must be nonempty repository-relative paths")
    if value.startswith("/") or (value.endswith("/") and not directory_allowed):
        raise ValueError("paths must be repository-relative and unambiguous")
    body = value[:-1] if value.endswith("/") else value
    if not body or any(part in {"", ".", ".."} for part in body.split("/")):
        raise ValueError("paths must not contain empty, dot or parent components")
    return value


def _nul_records(raw: bytes) -> list[bytes]:
    if not raw:
        return []
    if not raw.endswith(b"\0"):
        raise _GitError("malformed_git_output")
    return raw[:-1].split(b"\0")


def _decode(value: bytes) -> str:
    return value.decode("utf-8", "surrogateescape")


def _changed(repo: Path, base: str, candidate: str) -> tuple[set[str], set[str]]:
    records = _nul_records(_git(repo, "diff", "--raw", "-z", "--no-renames", "--no-ext-diff",
                                "--ignore-submodules=none", base, candidate, "--"))
    if len(records) % 2:
        raise _GitError("malformed_git_output")
    paths: set[str] = set()
    special: set[str] = set()
    for index in range(0, len(records), 2):
        metadata = records[index].split()
        if len(metadata) != 5 or not metadata[0].startswith(b":") or metadata[4] not in {
            b"A", b"D", b"M", b"T"
        }:
            raise _GitError("malformed_git_output")
        path = _decode(records[index + 1])
        if not path:
            raise _GitError("malformed_git_output")
        paths.add(path)
        if metadata[0][1:] in _SPECIAL_MODES or metadata[1] in _SPECIAL_MODES:
            special.add(path)
    return paths, special


def _working_paths(repo: Path) -> list[str]:
    records = _nul_records(_git(repo, "-c", "status.renames=false", "status", "--porcelain=v1",
                                "-z", "--untracked-files=all", "--ignore-submodules=none"))
    paths = []
    for record in records:
        if len(record) < 4 or record[2:3] != b" ":
            raise _GitError("malformed_git_output")
        paths.append(_decode(record[3:]))
    return sorted(set(paths))


def _special_tree_paths(repo: Path, revision: str) -> set[str]:
    records = _nul_records(_git(repo, "ls-tree", "-r", "-z", "--full-tree", revision))
    paths = set()
    for record in records:
        metadata, separator, path = record.partition(b"\t")
        fields = metadata.split()
        if not separator or len(fields) != 3:
            raise _GitError("malformed_git_output")
        if fields[0] in _SPECIAL_MODES:
            paths.add(_decode(path))
    return paths


def verify_candidate_scope(
    repo: Path | str, *, base_sha: str, candidate_sha: str,
    writable_paths: list[str], reported_changed_paths: list[str],
) -> dict[str, Any]:
    """Compare a clean candidate's actual diff with grants and reported paths.

    A trailing slash grants a directory and its descendants; a path without it
    grants exactly that file. Changed symlinks and submodules fail closed. Dirty
    tracked/untracked work blocks verification; Git-ignored files are excluded.
    The verifier never follows links or authenticates the supplied task receipt.
    """
    if not isinstance(base_sha, str) or not _SHA.fullmatch(base_sha):
        raise ValueError("base_sha must be a full lowercase 40-character Git SHA")
    if not isinstance(candidate_sha, str) or not _SHA.fullmatch(candidate_sha):
        raise ValueError("candidate_sha must be a full lowercase 40-character Git SHA")
    if not isinstance(writable_paths, list) or not isinstance(reported_changed_paths, list):
        raise ValueError("writable_paths and reported_changed_paths must be lists")
    grants = [_path(path, directory_allowed=True) for path in writable_paths]
    reported = [_path(path, directory_allowed=False) for path in reported_changed_paths]
    if len(set(grants)) != len(grants) or len(set(reported)) != len(reported):
        raise ValueError("paths must not contain duplicates")

    result: dict[str, Any] = {
        "base_sha": base_sha, "candidate_sha": candidate_sha, "scope_status": "BLOCKED",
        "actual_changed_paths": [], "working_tree_paths": [], "violations": [],
    }
    root = Path(repo)
    try:
        top = Path(os.fsdecode(_git(root, "rev-parse", "--show-toplevel").strip())).resolve()
        if top != root.resolve():
            raise _GitError("repository_root_mismatch")
        for revision in (base_sha, candidate_sha):
            resolved = _git(root, "rev-parse", "--verify", revision + "^{commit}").decode("ascii").strip()
            if resolved != revision:
                raise _GitError("commit_identity_mismatch")
        head = _git(root, "rev-parse", "--verify", "HEAD").decode("ascii").strip()
        if head != candidate_sha:
            result["violations"].append("HEAD")
            return result
        result["working_tree_paths"] = _working_paths(root)
        if result["working_tree_paths"]:
            result["violations"].append("working_tree_dirty")
            return result
        try:
            _git(root, "merge-base", "--is-ancestor", base_sha, candidate_sha)
        except _GitError:
            result["violations"].append("candidate_not_descendant")
            return result
        actual, special = _changed(root, base_sha, candidate_sha)
        unsafe_roots = _special_tree_paths(root, base_sha) | _special_tree_paths(root, candidate_sha)
        for grant in grants:
            if any(grant.rstrip("/").startswith(path + "/") for path in unsafe_roots):
                raise ValueError("writable_paths must not traverse a symlink or submodule")
        result["actual_changed_paths"] = sorted(actual)
        violations = {
            path for path in actual
            if path in special or not any(
                path.startswith(grant) if grant.endswith("/") else path == grant
                for grant in grants
            )
        }
        if actual != set(reported):
            violations.add("reported_changed_paths_mismatch")
        result["violations"] = sorted(violations)
        result["scope_status"] = "FAIL" if violations else "PASS"
        return result
    except (_GitError, UnicodeDecodeError) as exc:
        result["violations"].append(str(exc) or "git_command_failed")
        return result
