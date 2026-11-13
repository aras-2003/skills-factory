"""Quarantine and inventory external skills without executing their contents.

The intake command creates evidence and a read-only quarantine copy. It never
installs a skill, changes the provenance registry, or promotes a candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
import zlib
import unicodedata
from contextlib import closing
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Callable, Iterable


TOOL_VERSION = "1.0.0"
SCHEMA_VERSION = 1
DECISIONS = {"APPROVED", "REVIEW_REQUIRED", "REJECTED", "UNKNOWN"}
MAX_ARCHIVE_BYTES = 50_000_000
MAX_MEMBER_BYTES = 10_000_000
MAX_TOTAL_BYTES = 100_000_000
MAX_MEMBERS = 2_000
MAX_COMPRESSION_RATIO = 200
MAX_FRONTMATTER_BYTES = 1_000_000
GITHUB_HOSTS = {"api.github.com", "codeload.github.com"}
GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,37}[A-Za-z0-9])?/[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9])?$")
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
LICENSE_NAMES = {"license", "license.md", "license.txt", "licence", "licence.md", "copying", "notice"}
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".pdf", ".woff", ".woff2", ".ttf", ".otf", ".mp3", ".mp4"}
VCS_METADATA_NAMES = {".git", ".hg", ".svn"}
SENSITIVE_NAMES = {".npmrc", ".pypirc", ".netrc", ".aws", ".ssh", "credentials", "credentials.json", "secrets.json", "id_rsa", "id_ed25519"}


class IntakeError(ValueError):
    """An input is unsafe, incomplete, or cannot be represented reliably."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def canonical_digest(value: Any) -> str:
    return sha256(canonical_json(value))


def validate_github_identity(repository: str, commit: str, subdir: str | None = None) -> tuple[str, str, str | None]:
    if not isinstance(repository, str) or not GITHUB_REPO_RE.fullmatch(repository):
        raise IntakeError("invalid GitHub repository identity")
    if not isinstance(commit, str) or not FULL_COMMIT_RE.fullmatch(commit.lower()):
        raise IntakeError("remote source requires a full 40-character commit SHA")
    normalized_subdir = normalize_relative_path(subdir) if subdir else None
    return repository, commit.lower(), normalized_subdir


def normalize_relative_path(raw: str) -> str:
    if not raw or "\x00" in raw or "\\" in raw or ":" in raw or unicodedata.normalize("NFC", raw) != raw or any(unicodedata.category(char) == "Cf" for char in raw):
        raise IntakeError("unsafe relative path")
    member = PurePosixPath(raw)
    windows_member = PureWindowsPath(raw)
    if member.is_absolute() or windows_member.is_absolute() or windows_member.drive:
        raise IntakeError("unsafe relative path")
    parts = raw.split("/")
    reserved = {"con", "prn", "aux", "nul", *(f"com{index}" for index in range(1, 10)), *(f"lpt{index}" for index in range(1, 10))}
    if any(part in {"", ".", ".."} or part.endswith((" ", ".")) or part.casefold().split(".", 1)[0] in reserved or any(ord(char) < 32 or ord(char) == 127 for char in part) for part in parts):
        raise IntakeError("unsafe relative path")
    if any(part.casefold() in VCS_METADATA_NAMES or part.casefold() in SENSITIVE_NAMES or part.casefold().startswith(".env") or PurePosixPath(part).suffix.casefold() in {".pem", ".key", ".p12", ".pfx"} for part in parts):
        raise IntakeError("source contains VCS metadata or a sensitive credential file")
    if re.search(r"%(?:2e|2f|5c)", raw, re.I):
        raise IntakeError("encoded path separators and dot segments are not allowed")
    normalized = member.as_posix()
    if normalized != raw:
        raise IntakeError("non-canonical relative path")
    return normalized


def _validate_url(url: str, hosts: set[str]) -> None:
    parsed = urllib.parse.urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise IntakeError("remote URL contains an invalid port") from exc
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").lower() not in hosts
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or parsed.fragment
    ):
        raise IntakeError("remote URL is outside the HTTPS provider allowlist")


class GitHubRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow only the known GitHub API-to-codeload redirect path."""

    max_redirections = 3
    max_repeats = 2

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        _validate_url(newurl, GITHUB_HOSTS)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _read_response(opener: Any, url: str, limit: int, *, timeout: int = 15, expected_host: str | None = None, expected_path: str | None = None) -> bytes:
    _validate_url(url, GITHUB_HOSTS)
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "skills-factory-external-intake/1"},
    )
    try:
        response = opener.open(request, timeout=timeout)
        with closing(response):
            final_url = response.geturl() if hasattr(response, "geturl") else url
            _validate_url(final_url, GITHUB_HOSTS)
            final = urllib.parse.urlsplit(final_url)
            if expected_host and (final.hostname or "").lower() != expected_host:
                raise IntakeError("remote redirect changed the expected provider host")
            if expected_path and final.path.casefold() != expected_path.casefold():
                raise IntakeError("remote redirect changed the pinned repository path")
            status = getattr(response, "status", 200)
            if status != 200:
                raise IntakeError("remote provider returned a non-success status")
            data = response.read(limit + 1)
    except urllib.error.HTTPError as exc:
        raise IntakeError(f"remote provider returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise IntakeError("remote provider request failed") from exc
    if len(data) > limit:
        raise IntakeError("remote response exceeds configured size limit")
    return data


def github_opener() -> Any:
    return urllib.request.build_opener(GitHubRedirectHandler())


def fetch_github_source(repository: str, commit: str, subdir: str | None = None, *, opener: Any = None) -> tuple[dict[str, Any], dict[str, bytes]]:
    repository, commit, subdir = validate_github_identity(repository, commit, subdir)
    opener = opener or github_opener()
    owner, repo = repository.split("/", 1)
    base = f"https://api.github.com/repos/{urllib.parse.quote(owner, safe='')}/{urllib.parse.quote(repo, safe='')}"
    metadata_path = f"/repos/{owner}/{repo}/commits/{commit}"
    metadata_url = f"https://api.github.com{metadata_path}"
    archive_url = f"{base}/zipball/{commit}"
    try:
        metadata = json.loads(_read_response(opener, metadata_url, 1_000_000, expected_host="api.github.com", expected_path=metadata_path).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntakeError("remote commit metadata is invalid") from exc
    if not isinstance(metadata, dict) or not isinstance(metadata.get("sha"), str) or metadata["sha"].lower() != commit:
        raise IntakeError("provider commit identity does not match the requested pin")
    commit_data = metadata.get("commit") or {}
    if not isinstance(commit_data, dict):
        raise IntakeError("remote commit author metadata is invalid")
    author_data = commit_data.get("author") or {}
    api_author = metadata.get("author") or {}
    if not isinstance(author_data, dict) or not isinstance(api_author, dict):
        raise IntakeError("remote commit author metadata is invalid")
    author = {
        "state": "PROVIDER_COMMIT_METADATA" if author_data.get("name") or api_author.get("login") else "UNKNOWN",
        "name": author_data.get("name") or None,
        "login": api_author.get("login") or None,
        "commit_sha": commit,
    }
    archive_bytes = _read_response(
        opener,
        archive_url,
        MAX_ARCHIVE_BYTES,
        expected_host="codeload.github.com",
        expected_path=f"/{owner}/{repo}/legacy.zip/{commit}",
    )
    files = inventory_zip(archive_bytes, subdir=subdir, strip_github_root=True)
    source = {
        "type": "github_repository",
        "repository": repository,
        "commit": commit,
        "subdir": subdir,
        "source_url": f"https://github.com/{repository}/tree/{commit}" + ("/" + "/".join(urllib.parse.quote(part, safe="-._~") for part in subdir.split("/")) if subdir else ""),
        "source_digest": sha256(archive_bytes),
        "author": author,
    }
    return source, files


def _validate_member_tree(paths: Iterable[tuple[str, bool]]) -> None:
    kinds: dict[str, str] = {}
    folded: dict[str, str] = {}
    component_spellings: dict[str, str] = {}
    for path, is_dir in paths:
        if path in kinds or path.casefold() in folded:
            raise IntakeError("duplicate normalized archive path")
        kinds[path] = "directory" if is_dir else "file"
        folded[path.casefold()] = path
        parts = path.split("/")
        for index in range(1, len(parts) + 1):
            prefix = "/".join(parts[:index])
            prior = component_spellings.setdefault(prefix.casefold(), prefix)
            if prior != prefix:
                raise IntakeError("archive paths collide on case-insensitive filesystems")
    for path, kind in kinds.items():
        parts = path.split("/")
        for index in range(1, len(parts)):
            parent = "/".join(parts[:index])
            if kinds.get(parent) == "file" or kinds.get(folded.get(parent.casefold(), parent)) == "file":
                raise IntakeError("archive path has a file/directory conflict")
        path_folded = path.casefold()
        if kind == "file" and any(other.casefold().startswith(path_folded + "/") for other in kinds):
            raise IntakeError("archive path has a file/directory conflict")


def inventory_zip(archive_bytes: bytes, *, subdir: str | None = None, strip_github_root: bool = False) -> dict[str, bytes]:
    if len(archive_bytes) > MAX_ARCHIVE_BYTES:
        raise IntakeError("archive exceeds compressed-size limit")
    selected_subdir = normalize_relative_path(subdir) if subdir else None
    try:
        archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
    except (zipfile.BadZipFile, OSError) as exc:
        raise IntakeError("invalid ZIP archive") from exc

    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_MEMBERS:
            raise IntakeError("archive exceeds member-count limit")
        raw_names: list[tuple[zipfile.ZipInfo, str, bool]] = []
        roots: set[str] = set()
        for info in infos:
            is_dir = info.is_dir()
            raw = info.filename[:-1] if is_dir else info.filename
            path = normalize_relative_path(raw)
            roots.add(path.split("/", 1)[0])
            mode = (info.external_attr >> 16) & 0xFFFF
            member_type = stat.S_IFMT(mode)
            allowed_types = {0, stat.S_IFREG} if not is_dir else {0, stat.S_IFDIR}
            if member_type not in allowed_types:
                raise IntakeError("archive contains a link or unsupported file type")
            if info.flag_bits & 0x1:
                raise IntakeError("encrypted archive member is not auditable")
            if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                raise IntakeError("archive uses an unsupported compression method")
            if info.file_size < 0 or info.compress_size < 0 or info.file_size > MAX_MEMBER_BYTES:
                raise IntakeError("archive member exceeds size limit")
            if info.file_size and (not info.compress_size or info.file_size / info.compress_size > MAX_COMPRESSION_RATIO):
                raise IntakeError("archive member exceeds compression-ratio limit")
            raw_names.append((info, path, is_dir))

        if strip_github_root and (len(roots) != 1 or not raw_names):
            raise IntakeError("remote archive does not have one canonical repository root")
        root = next(iter(roots)) if strip_github_root else None
        members: list[tuple[zipfile.ZipInfo, str, bool]] = []
        for info, path, is_dir in raw_names:
            if root:
                if path == root:
                    continue
                if not path.startswith(root + "/"):
                    raise IntakeError("remote archive has inconsistent root paths")
                path = path[len(root) + 1 :]
            if not path:
                continue
            members.append((info, normalize_relative_path(path), is_dir))
        _validate_member_tree((path, is_dir) for _, path, is_dir in members)

        total_size = 0
        output: dict[str, bytes] = {}
        for info, path, is_dir in members:
            if is_dir:
                continue
            total_size += info.file_size
            if total_size > MAX_TOTAL_BYTES:
                raise IntakeError("archive exceeds expanded-size limit")
            try:
                with archive.open(info, "r") as stream:
                    data = stream.read(info.file_size + 1)
            except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError, zlib.error) as exc:
                raise IntakeError("archive member failed integrity validation") from exc
            if len(data) != info.file_size:
                raise IntakeError("archive member size does not match its metadata")
            if selected_subdir:
                prefix = selected_subdir + "/"
                if not path.startswith(prefix):
                    continue
                path = path[len(prefix) :]
                if not path:
                    continue
            output[path] = data
        if not output:
            raise IntakeError("archive contains no files for the selected source path")
        _validate_file_paths(output)
        return dict(sorted(output.items()))


def _validate_file_paths(files: dict[str, bytes]) -> None:
    if len(files) > MAX_MEMBERS:
        raise IntakeError("source exceeds file-count limit")
    total = 0
    folded: set[str] = set()
    for path, data in files.items():
        normalized = normalize_relative_path(path)
        if normalized != path or path.casefold() in folded:
            raise IntakeError("duplicate or non-canonical source path")
        folded.add(path.casefold())
        if len(data) > MAX_MEMBER_BYTES:
            raise IntakeError("source file exceeds size limit")
        total += len(data)
        if total > MAX_TOTAL_BYTES:
            raise IntakeError("source exceeds expanded-size limit")
    _validate_member_tree((path, False) for path in files)


def _read_local_file(path: Path, *, max_bytes: int = MAX_MEMBER_BYTES) -> bytes:
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink > 1 or before.st_size > max_bytes:
        raise IntakeError("local source contains a link, special file, or oversized file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise IntakeError("local source changed or could not be opened safely") from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise IntakeError("local source changed during inventory")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise IntakeError("local source exceeds configured size limit")
        after = os.fstat(descriptor)
        if (opened.st_size, opened.st_mtime_ns, opened.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise IntakeError("local source changed during inventory")
        data = b"".join(chunks)
        if len(data) != before.st_size:
            raise IntakeError("local source changed during inventory")
        return data
    finally:
        os.close(descriptor)


def inventory_directory(directory: Path, *, subdir: str | None = None) -> dict[str, bytes]:
    directory = Path(directory)
    try:
        if directory.is_symlink() or not directory.is_dir():
            raise IntakeError("local source is not a real directory")
        root = directory.resolve(strict=True)
    except OSError as exc:
        raise IntakeError("local source directory is unavailable") from exc
    selected = root
    if subdir:
        for part in PurePosixPath(normalize_relative_path(subdir)).parts:
            selected = selected / part
            if selected.is_symlink():
                raise IntakeError("selected source path contains a symbolic link")
    if selected.is_symlink() or not selected.is_dir():
        raise IntakeError("selected source path is not a real directory")
    selected = selected.resolve(strict=True)
    if selected != root and root not in selected.parents:
        raise IntakeError("selected source path escapes its directory")
    files: dict[str, bytes] = {}
    total = 0
    directory_snapshots: list[tuple[Path, int, int]] = []
    entry_count = 0
    stack = [selected]
    while stack:
        current = stack.pop()
        before_dir = current.lstat()
        directory_snapshots.append((current, before_dir.st_mtime_ns, before_dir.st_ino))
        try:
            entries = []
            with os.scandir(current) as stream:
                for entry in stream:
                    entry_count += 1
                    if entry_count > MAX_MEMBERS:
                        raise IntakeError("local source exceeds entry-count limit")
                    entries.append(entry)
            entries.sort(key=lambda item: item.name, reverse=True)
        except OSError as exc:
            raise IntakeError("local source directory cannot be inventoried") from exc
        for entry in entries:
            relative = Path(entry.path).relative_to(selected).as_posix()
            normalize_relative_path(relative)
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise IntakeError("local source changed during inventory") from exc
            if stat.S_ISLNK(info.st_mode):
                raise IntakeError("local source contains a symbolic link")
            if stat.S_ISDIR(info.st_mode):
                stack.append(Path(entry.path))
            elif stat.S_ISREG(info.st_mode):
                if info.st_nlink > 1:
                    raise IntakeError("local source contains a hard-linked file")
                data = _read_local_file(Path(entry.path))
                files[relative] = data
                total += len(data)
                if total > MAX_TOTAL_BYTES:
                    raise IntakeError("local source exceeds expanded-size limit")
            else:
                raise IntakeError("local source contains a special file")
            if len(files) > MAX_MEMBERS:
                raise IntakeError("local source exceeds file-count limit")
    for directory_path, mtime_ns, inode in directory_snapshots:
        after_dir = directory_path.lstat()
        if not stat.S_ISDIR(after_dir.st_mode) or (after_dir.st_mtime_ns, after_dir.st_ino) != (mtime_ns, inode):
            raise IntakeError("local source directory changed during inventory")
    if not files:
        raise IntakeError("local source contains no files")
    _validate_file_paths(files)
    return dict(sorted(files.items()))


def _inventory_rows(files: dict[str, bytes]) -> list[dict[str, Any]]:
    _validate_file_paths(files)
    return [{"path": path, "size_bytes": len(data), "sha256": sha256(data)} for path, data in sorted(files.items())]


def _license_paths(files: dict[str, bytes]) -> list[dict[str, str]]:
    return [
        {"path": path, "sha256": sha256(data)}
        for path, data in sorted(files.items())
        if PurePosixPath(path).name.casefold() in LICENSE_NAMES
    ]


def _skill_frontmatter_findings(files: dict[str, bytes]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path, data in sorted(files.items()):
        if PurePosixPath(path).name != "SKILL.md":
            continue
        if len(data) > MAX_FRONTMATTER_BYTES:
            findings.append({"path": path, "code": "SKILL_FRONTMATTER_TOO_LARGE"})
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            findings.append({"path": path, "code": "SKILL_INVALID_UTF8"})
            continue
        lines = text.splitlines()
        if not lines or lines[0] != "---":
            findings.append({"path": path, "code": "SKILL_FRONTMATTER_MISSING"})
            continue
        try:
            end = next(index for index in range(1, len(lines)) if lines[index] == "---")
        except StopIteration:
            findings.append({"path": path, "code": "SKILL_FRONTMATTER_UNCLOSED"})
            continue
        try:
            import yaml
            from yaml.tokens import AliasToken, AnchorToken
        except ImportError:
            findings.append({"path": path, "code": "SAFE_YAML_PARSER_UNAVAILABLE"})
            continue
        frontmatter = "\n".join(lines[1:end])
        try:
            if len(frontmatter.encode("utf-8")) > MAX_FRONTMATTER_BYTES:
                raise IntakeError("frontmatter exceeds size limit")
            if any(isinstance(token, (AliasToken, AnchorToken)) for token in yaml.scan(frontmatter)):
                findings.append({"path": path, "code": "SKILL_FRONTMATTER_ALIAS_NOT_ALLOWED"})
                continue
            parsed = yaml.safe_load(frontmatter)
        except Exception:
            findings.append({"path": path, "code": "SKILL_FRONTMATTER_INVALID"})
            continue
        if not isinstance(parsed, dict) or not isinstance(parsed.get("name"), str) or not parsed.get("name", "").strip() or not isinstance(parsed.get("description"), str) or not parsed.get("description", "").strip():
            findings.append({"path": path, "code": "SKILL_FRONTMATTER_REQUIRED_FIELDS_MISSING"})
    if not any(PurePosixPath(path).name == "SKILL.md" for path in files):
        findings.append({"path": "", "code": "SKILL_FILE_MISSING"})
    return findings


def _review_hints(files: dict[str, bytes]) -> list[str]:
    hints: set[str] = set()
    patterns = (
        ("PROMPT_OVERRIDE", re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|system)\s+instructions|reveal\s+(?:the\s+)?(?:system\s+)?prompt|ignore\s+the\s+user", re.I)),
        ("CREDENTIAL_ACCESS", re.compile(r"os\.environ|process\.env|\$env:|api[_ -]?key|access[_ -]?token|private[_ -]?key", re.I)),
        ("NETWORK_ACTIVITY", re.compile(r"\bcurl\b|\bwget\b|requests\.(?:get|post|put)|httpx\.|fetch\s*\(|urllib\.request", re.I)),
        ("DESTRUCTIVE_OPERATION", re.compile(r"rm\s+-rf|shutil\.rmtree|\bunlink\s*\(|\bdelete\s+all\b|format\s+[a-z]:", re.I)),
        ("UNEXPECTED_WRITE_ACTIVITY", re.compile(r"write_text\s*\(|write_bytes\s*\(|writeFile(?:Sync)?\s*\(|os\.(?:remove|unlink)\s*\(|open\s*\([^\n]+,[^\n]*['\"](?:w|a|x)" , re.I)),
        ("TOOL_PERMISSION_DECLARATION", re.compile(r"(?im)^\s*(?:allowed-tools|tools)\s*:")),
    )
    for path, data in files.items():
        suffix = PurePosixPath(path).suffix.casefold()
        if suffix in ASSET_SUFFIXES or b"\x00" in data[:4096]:
            hints.add("EMBEDDED_OR_BINARY_ASSET")
        text = data.decode("utf-8", errors="ignore")
        if PurePosixPath(path).name.casefold() in {"requirements.txt", "pyproject.toml", "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"}:
            hints.add("DEPENDENCY_OR_LIFECYCLE_REVIEW")
        for code, pattern in patterns:
            if pattern.search(text):
                hints.add(code)
    return sorted(hints)


def scan_quarantined_files(files: dict[str, bytes], *, scan_fn: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Run the existing static scanner on an isolated temp tree; never run content."""
    if scan_fn is None:
        try:
            if str(Path(__file__).resolve().parent) not in sys.path:
                sys.path.insert(0, str(Path(__file__).resolve().parent))
            from scan_skills import scan as scan_fn  # type: ignore[no-redef]
        except Exception:
            return {"status": "NOT_RUN", "findings": [], "errors": ["existing static scanner unavailable"]}
    with tempfile.TemporaryDirectory(prefix="sf-intake-scan-") as temp_name:
        root = Path(temp_name)
        for area in ("skills", "scripts/security"):
            (root / area).mkdir(parents=True, exist_ok=True)
        (root / "scripts/security/waivers.yaml").write_text("waivers: []\n", encoding="utf-8")
        target = root / "skills/external"
        target.mkdir(parents=True)
        for relative, data in files.items():
            path = target.joinpath(*PurePosixPath(relative).parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        try:
            findings, errors = scan_fn(root, today=None)
        except Exception as exc:
            return {"status": "BLOCKED", "findings": [], "errors": [f"static scanner failed ({type(exc).__name__})"]}
    rows = [
        {"rule_id": item.rule_id, "severity": item.severity, "path": item.path.removeprefix("skills/external/"), "line": item.line, "fingerprint": item.fingerprint, "suppressed": item.suppressed}
        for item in findings
    ]
    blocked = bool(errors) or any(item.severity == "high" and not item.suppressed for item in findings)
    return {"status": "BLOCKED" if blocked else "REVIEW_REQUIRED", "findings": rows, "errors": [str(error) for error in errors]}


def _source_inventory_digest(rows: list[dict[str, Any]]) -> str:
    return canonical_digest(rows)


def build_receipt(source: dict[str, Any], files: dict[str, bytes], *, scan_fn: Callable[..., Any] | None = None, known_receipts: Iterable[dict[str, Any]] = ()) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = _inventory_rows(files)
    inventory_sha = _source_inventory_digest(rows)
    license_evidence = _license_paths(files)
    scan_report = scan_quarantined_files(files, scan_fn=scan_fn)
    format_findings = _skill_frontmatter_findings(files)
    known_receipts = list(known_receipts)
    skill_hashes = [row["sha256"] for row in rows if PurePosixPath(row["path"]).name == "SKILL.md"]
    duplicate_skill_paths: dict[str, list[str]] = {}
    for row in rows:
        if PurePosixPath(row["path"]).name == "SKILL.md":
            duplicate_skill_paths.setdefault(row["sha256"], []).append(row["path"])
    duplicate_skill_paths = {digest: paths for digest, paths in sorted(duplicate_skill_paths.items()) if len(paths) > 1}
    if format_findings and scan_report["status"] != "BLOCKED":
        scan_report["status"] = "REVIEW_REQUIRED"
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "source": source,
        "inventory_sha256": inventory_sha,
        "files": rows,
        "skill_paths": [row["path"] for row in rows if PurePosixPath(row["path"]).name == "SKILL.md"],
        "author_provenance": source.get("author") or {"state": "UNKNOWN", "name": None, "login": None, "commit_sha": None},
        "license_evidence": license_evidence,
        "license_decision": "REVIEW_REQUIRED" if license_evidence else "UNKNOWN",
        "security_review": scan_report,
        "format_findings": format_findings,
        "review_hints": _review_hints(files),
        "duplicate_inventory_matches": sorted({
            inventory_sha
            for existing in known_receipts
            if _known_receipt_matches(existing, inventory_sha)
        }),
        "duplicate_skill_content_matches": sorted({
            digest
            for existing in known_receipts
            for digest in skill_hashes
            if digest in _receipt_skill_hashes(existing)
        }),
        "duplicate_skill_paths": duplicate_skill_paths,
        "authorization_state": "NOT_AUTHORIZED",
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "inventory_sha256": inventory_sha,
        "files": rows,
        "pinned": True,
        "upstream_commit_pinned": source.get("type") == "github_repository" and bool(source.get("commit")),
        "license_decision": receipt["license_decision"],
        "authorization_state": "NOT_AUTHORIZED",
    }
    return receipt, manifest


def _known_receipt_matches(receipt: dict[str, Any], inventory_sha: str) -> bool:
    rows = receipt.get("files")
    if not isinstance(rows, list) or receipt.get("inventory_sha256") != inventory_sha:
        return False
    if not all(isinstance(row, dict) and isinstance(row.get("path"), str) and isinstance(row.get("size_bytes"), int) and 0 <= row["size_bytes"] <= MAX_MEMBER_BYTES and isinstance(row.get("sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", row["sha256"]) for row in rows):
        return False
    try:
        _validate_member_tree((normalize_relative_path(row["path"]), False) for row in rows)
    except IntakeError:
        return False
    return _source_inventory_digest(sorted(rows, key=lambda item: item["path"])) == inventory_sha


def _receipt_skill_hashes(receipt: dict[str, Any]) -> set[str]:
    if not _known_receipt_matches(receipt, str(receipt.get("inventory_sha256", ""))):
        return set()
    return {
        row["sha256"]
        for row in receipt["files"]
        if PurePosixPath(row["path"]).name == "SKILL.md"
    }


def receipt_digest(receipt: dict[str, Any]) -> str:
    return canonical_digest(receipt)


def validate_review_authorization(receipt: dict[str, Any], review: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(review, dict):
        return False, ["review must be a JSON object"]
    if review.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported review schema")
    if review.get("receipt_sha256") != receipt_digest(receipt):
        errors.append("review is not bound to this receipt digest")
    if review.get("inventory_sha256") != receipt.get("inventory_sha256"):
        errors.append("review inventory digest does not match")
    source = receipt.get("source") or {}
    reviewed_source = review.get("source") or {}
    if not isinstance(reviewed_source, dict):
        reviewed_source = {}
        errors.append("review source identity must be an object")
    if reviewed_source.get("repository") != source.get("repository") or reviewed_source.get("commit") != source.get("commit"):
        errors.append("review source identity does not match")
    if not isinstance(review.get("reviewer"), str) or not review.get("reviewer", "").strip():
        errors.append("reviewer identity is required")
    if not isinstance(review.get("rationale"), str) or not review.get("rationale", "").strip():
        errors.append("review rationale is required")
    try:
        from datetime import datetime
        reviewed_at = datetime.fromisoformat(str(review.get("reviewed_at", "")).replace("Z", "+00:00"))
        if reviewed_at.tzinfo is None:
            raise ValueError
    except ValueError:
        errors.append("reviewed_at must be an ISO-8601 timestamp with timezone")
    for key in ("license_decision", "security_decision"):
        if review.get(key) not in DECISIONS:
            errors.append(f"{key} is invalid")
    if review.get("license_decision") == "APPROVED" and not str(review.get("license_evidence_reference", "")).strip():
        errors.append("approved license requires an evidence reference")
    if review.get("security_decision") == "APPROVED" and not str(review.get("security_evidence_reference", "")).strip():
        errors.append("approved security review requires an evidence reference")
    if review.get("license_decision") != "APPROVED" or review.get("security_decision") != "APPROVED":
        errors.append("license and security decisions must both be explicitly APPROVED")
    return not errors, errors


def _ensure_quarantine_root(path: Path) -> Path:
    path = Path(path).expanduser().absolute()
    existed = path.exists()
    try:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        info = path.lstat()
    except OSError as exc:
        raise IntakeError("quarantine root is unavailable") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise IntakeError("quarantine root must be a real directory")
    resolved = path.resolve(strict=True)
    if not existed:
        try:
            resolved.chmod(0o700)
        except OSError:
            pass
    return resolved


def _existing_quarantine_matches(target: Path, files: dict[str, bytes]) -> bool:
    if target.is_symlink() or not target.is_dir():
        return False
    found: dict[str, bytes] = {}
    for path in target.rglob("*"):
        relative = path.relative_to(target).as_posix()
        if path.is_symlink():
            return False
        if path.is_file():
            found[relative] = path.read_bytes()
        elif not path.is_dir():
            return False
    return found == files


def write_quarantine(quarantine_root: Path, files: dict[str, bytes], inventory_sha: str, *, source_root: Path | None = None) -> Path:
    _validate_file_paths(files)
    if not re.fullmatch(r"[a-f0-9]{64}", inventory_sha):
        raise IntakeError("invalid inventory digest")
    if _source_inventory_digest(_inventory_rows(files)) != inventory_sha:
        raise IntakeError("inventory digest does not match quarantine files")
    if source_root is not None:
        source = Path(source_root).resolve(strict=True)
        requested_root = Path(quarantine_root).expanduser().absolute().resolve(strict=False)
        if requested_root == source or source in requested_root.parents or requested_root in source.parents:
            raise IntakeError("quarantine and source paths must be separate")
    root = _ensure_quarantine_root(quarantine_root)
    target = root / inventory_sha
    if target.exists() or target.is_symlink():
        if _existing_quarantine_matches(target, files):
            return target
        raise IntakeError("existing quarantine entry does not match the pinned inventory")
    staging = root / f".staging-{uuid.uuid4().hex}"
    staging.mkdir(mode=0o700)
    try:
        for relative, data in sorted(files.items()):
            path = staging.joinpath(*PurePosixPath(relative).parts)
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
            path.chmod(0o400)
        for directory in sorted((p for p in staging.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            directory.chmod(0o500)
        staging.chmod(0o500)
        try:
            staging.rename(target)
        except FileExistsError:
            if not _existing_quarantine_matches(target, files):
                raise IntakeError("concurrent quarantine entry does not match the pinned inventory")
            staging.chmod(0o700)
            shutil.rmtree(staging)
    except Exception:
        try:
            staging.chmod(0o700)
            for directory in staging.rglob("*"):
                if directory.is_dir() and not directory.is_symlink():
                    directory.chmod(0o700)
                elif directory.is_file() and not directory.is_symlink():
                    directory.chmod(0o600)
            shutil.rmtree(staging, ignore_errors=True)
        except OSError:
            pass
        raise
    return target


def _write_output(path: Path, data: bytes) -> None:
    path = Path(path).expanduser().absolute()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise IntakeError("receipt/manifest output cannot be a symbolic link")
    if path.exists():
        if not path.is_file() or path.read_bytes() != data:
            raise IntakeError("receipt/manifest output already exists with different content")
        return
    temp = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _load_known_receipts(paths: list[Path]) -> list[dict[str, Any]]:
    results = []
    for path in paths:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IntakeError("known receipt cannot be read as JSON") from exc
        if not isinstance(value, dict):
            raise IntakeError("known receipt must be a JSON object")
        results.append(value)
    return results


def intake(args: argparse.Namespace) -> dict[str, Any]:
    source_root: Path | None = None
    if args.source:
        source_path = Path(args.source).expanduser()
        if source_path.is_dir():
            source_root = source_path.resolve(strict=True)
            files = inventory_directory(source_path, subdir=args.subdir)
            source = {
                "type": "local_directory",
                "locator": source_path.name,
                "subdir": normalize_relative_path(args.subdir) if args.subdir else None,
                "source_digest": _source_inventory_digest(_inventory_rows(files)),
                "commit": None,
                "author": {"state": "UNKNOWN", "name": None, "login": None, "commit_sha": None},
            }
        else:
            if source_path.is_symlink() or not source_path.is_file():
                raise IntakeError("local source must be a regular directory or ZIP file")
            archive_bytes = _read_local_file(source_path, max_bytes=MAX_ARCHIVE_BYTES)
            files = inventory_zip(archive_bytes, subdir=args.subdir)
            source = {
                "type": "local_bundle",
                "locator": source_path.name,
                "subdir": normalize_relative_path(args.subdir) if args.subdir else None,
                "source_digest": sha256(archive_bytes),
                "commit": None,
                "author": {"state": "UNKNOWN", "name": None, "login": None, "commit_sha": None},
            }
    else:
        source, files = fetch_github_source(args.github_repo, args.commit, args.subdir)
    if not any(PurePosixPath(path).name == "SKILL.md" for path in files):
        raise IntakeError("selected source contains no SKILL.md")

    quarantine_root = Path(args.quarantine).expanduser().absolute()
    output_paths = [Path(args.receipt).expanduser().absolute(), Path(args.manifest).expanduser().absolute()]
    if output_paths[0].resolve(strict=False) == output_paths[1].resolve(strict=False):
        raise IntakeError("receipt and manifest paths must be different")
    quarantine_resolved = quarantine_root.resolve(strict=False)
    for output in output_paths:
        output_resolved = output.resolve(strict=False)
        if output_resolved == quarantine_resolved or quarantine_resolved in output_resolved.parents:
            raise IntakeError("receipt and manifest must be outside the quarantine tree")
    if source_root:
        source_resolved = source_root.resolve(strict=True)
        for output in [quarantine_root, *output_paths]:
            resolved = output.resolve(strict=False)
            if resolved == source_resolved or source_resolved in resolved.parents or resolved in source_resolved.parents:
                raise IntakeError("outputs must not be written into the local source tree")

    known = _load_known_receipts([Path(item) for item in args.known_receipt])
    receipt, manifest = build_receipt(source, files, known_receipts=known)
    quarantine = write_quarantine(quarantine_root, files, receipt["inventory_sha256"], source_root=source_root)
    _write_output(Path(args.receipt), canonical_json(receipt))
    _write_output(Path(args.manifest), canonical_json(manifest))
    result = {
        "status": "QUARANTINED_BLOCKED" if receipt["security_review"]["status"] == "BLOCKED" else "QUARANTINED_REVIEW_REQUIRED",
        "receipt_sha256": receipt_digest(receipt),
        "inventory_sha256": receipt["inventory_sha256"],
        "quarantine": str(quarantine),
        "authorization_state": "NOT_AUTHORIZED",
    }
    if args.review:
        try:
            review = json.loads(Path(args.review).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IntakeError("review record cannot be read as JSON") from exc
        authorized, errors = validate_review_authorization(receipt, review)
        result["review_validation"] = "EXPLICIT_APPROVALS_VALID_NO_IMPORT_ACTION" if authorized else "NOT_AUTHORIZED"
        result["review_errors"] = errors
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inventory and quarantine untrusted skill sources; never install or execute them.")
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--source", help="local directory or ZIP bundle")
    sources.add_argument("--github-repo", help="GitHub repository as owner/name; requires --commit")
    parser.add_argument("--commit", help="full immutable Git commit SHA for --github-repo")
    parser.add_argument("--subdir", help="optional relative skill directory inside the source")
    parser.add_argument("--quarantine", required=True, help="isolated directory for read-only candidate bytes")
    parser.add_argument("--receipt", required=True, help="new or identical existing receipt JSON path")
    parser.add_argument("--manifest", required=True, help="new or identical existing pinned manifest JSON path")
    parser.add_argument("--known-receipt", action="append", default=[], help="receipt to use for exact duplicate detection; repeatable")
    parser.add_argument("--review", help="explicit reviewer record to validate against this exact receipt")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if bool(args.github_repo) != bool(args.commit):
        parser.error("--github-repo and --commit must be supplied together")
    try:
        result = intake(args)
    except (IntakeError, OSError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    except Exception as exc:
        print(json.dumps({"status": "REFUSED", "reason": f"internal intake error ({type(exc).__name__})"}, ensure_ascii=False, sort_keys=True))
        return 3
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
