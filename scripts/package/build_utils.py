from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import yaml

RUNTIME_DIRS = ("references", "scripts", "assets", "agents")
EXCLUDED_NAMES = {"__pycache__", ".DS_Store"}
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".rubric.yaml")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def assert_source_revision(expected: str, actual: str) -> None:
    if not expected or not actual:
        raise ValueError("source revisions must be non-empty")
    if expected != actual:
        raise RuntimeError(f"source moved from {expected} to {actual}; refusing stale publication")


def source_revision(root: Path) -> str:
    override = os.environ.get("SOURCE_REVISION")
    if override:
        return override
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
    except Exception:
        return "unknown"


def load_versions(root: Path) -> dict:
    data = yaml.safe_load((root / "release" / "package.yaml").read_text(encoding="utf-8")) or {}
    return data


def ensure_source_valid(root: Path) -> None:
    validator = root / "scripts" / "validate" / "validate_all.py"
    if not validator.is_file():
        return
    result = subprocess.run(
        [sys.executable, str(validator)],
        cwd=root,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode:
        detail = (result.stdout + "\n" + result.stderr).strip()
        raise ValueError("source validation failed before build:\n" + detail)


def package_version(root: Path, key: str) -> str:
    data = load_versions(root)
    section = data.get(key) or {}
    version = section.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError(f"release/package.yaml: missing {key}.version")
    return version


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_tree(path: Path) -> str:
    h = hashlib.sha256()
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = item.relative_to(path).as_posix().encode()
        h.update(len(rel).to_bytes(4, "big"))
        h.update(rel)
        data = item.read_bytes()
        h.update(len(data).to_bytes(8, "big"))
        h.update(data)
    return h.hexdigest()


SAFE_ARTIFACT_ROOTS = ("plugins", "dist", ".tmp")


def _absolute_without_resolve(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def validate_output_path(root: Path, output: Path) -> Path:
    root_lexical = _absolute_without_resolve(root)
    output_lexical = _absolute_without_resolve(output)

    try:
        relative = output_lexical.relative_to(root_lexical)
    except ValueError as exc:
        raise ValueError(f"output must stay inside repository: {output_lexical}") from exc

    if not relative.parts:
        raise ValueError(f"unsafe output path: {output_lexical}")

    current = root_lexical
    for part in relative.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError(f"output path traverses symlink: {current}")

    root_resolved = root_lexical.resolve(strict=False)
    output_resolved = output_lexical.resolve(strict=False)
    try:
        resolved_relative = output_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"output escapes repository after resolution: {output_lexical}") from exc

    if len(resolved_relative.parts) < 2 or resolved_relative.parts[0] not in SAFE_ARTIFACT_ROOTS:
        allowed = ", ".join(f"{name}/<artifact>" for name in SAFE_ARTIFACT_ROOTS)
        raise ValueError(f"unsafe output path: {output_lexical}; allowed roots: {allowed}")

    git_dir = (root_resolved / ".git").resolve(strict=False)
    try:
        output_resolved.relative_to(git_dir)
    except ValueError:
        pass
    else:
        raise ValueError(f"unsafe output path inside .git: {output_lexical}")

    return output_resolved


@contextmanager
def atomic_output(root: Path, output: Path) -> Iterator[Path]:
    output = validate_output_path(root, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.stage-", dir=output.parent))
    backup = output.parent / f".{output.name}.backup"
    if backup.exists():
        shutil.rmtree(backup)
    try:
        yield stage
        if output.exists():
            output.rename(backup)
        try:
            stage.rename(output)
        except Exception:
            if backup.exists() and not output.exists():
                backup.rename(output)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise


def include_runtime_file(rel: Path) -> bool:
    if any(part in EXCLUDED_NAMES for part in rel.parts):
        return False
    if rel.parts and rel.parts[0] == "tests":
        return False
    if rel.name.startswith(".") and rel.name != ".well-known":
        return False
    if any(rel.name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES):
        return False
    return True


def copy_runtime_support(src_skill: Path, dst_skill: Path) -> list[str]:
    inventory: list[str] = []
    for dirname in RUNTIME_DIRS:
        source = src_skill / dirname
        if not source.exists():
            continue
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            if path.is_symlink():
                raise ValueError(f"runtime support symlinks are not allowed: {path}")
            rel = path.relative_to(src_skill)
            if not include_runtime_file(rel):
                continue
            target = dst_skill / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            inventory.append(rel.as_posix())
    return inventory


def package_runtime_mcp(
    root: Path,
    stage: Path,
    *,
    mode: str = "local",
    remote_url: str | None = None,
) -> list[dict]:
    if mode not in {"local", "remote"}:
        raise ValueError(f"unsupported MCP packaging mode: {mode}")
    if mode == "remote" and not remote_url:
        raise ValueError("remote MCP packaging requires a non-empty HTTPS URL")
    if mode == "remote" and not remote_url.startswith("https://"):
        raise ValueError("remote MCP URL must use HTTPS")

    source_dir = root / "runtime" / "mcp"
    config_src = source_dir / "mcp.json"
    renderer_src = source_dir / "chart_renderer.py"
    investment_src = source_dir / "investment_runtime.py"
    server_src = source_dir / "server.py"
    cloud_src = source_dir / "cloud_server.py"
    catalog_src = source_dir / "skill_catalog.py"
    if not all(path.is_file() for path in (config_src, renderer_src, investment_src, server_src, cloud_src, catalog_src)):
        raise ValueError("runtime MCP sources are incomplete")

    config = json.loads(config_src.read_text(encoding="utf-8"))
    servers = config.get("mcpServers")
    if not isinstance(servers, dict):
        raise ValueError("runtime/mcp/mcp.json must declare mcpServers")
    for required in ("skills-factory-runtime",):
        if required not in servers:
            raise ValueError(f"runtime/mcp/mcp.json must declare {required}")

    if mode == "remote":
        servers = {
            name: {"type": "http", "url": remote_url}
            for name in servers
        }
        portable_config = {
            "$schema": config.get("$schema"),
            "mcpServers": servers,
        }
        write_json(stage / "mcp.json", portable_config)
        write_json(stage / ".mcp.json", {"mcpServers": servers})
        mcp_out = None
    else:
        shutil.copyfile(config_src, stage / "mcp.json")
        mcp_out = stage / "mcp"
        mcp_out.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(renderer_src, mcp_out / "chart_renderer.py")
        shutil.copyfile(investment_src, mcp_out / "investment_runtime.py")
        shutil.copyfile(server_src, mcp_out / "server.py")
        shutil.copyfile(cloud_src, mcp_out / "cloud_server.py")
        shutil.copyfile(catalog_src, mcp_out / "skill_catalog.py")
        write_json(stage / ".mcp.json", {"mcpServers": servers})

    tree_digest = (
        sha256_tree(mcp_out)
        if mcp_out
        else sha256_bytes(json.dumps(servers, sort_keys=True).encode("utf-8"))
    )
    return [{
        "name": "skills-factory-runtime",
        "kind": "mcp-server",
        "runtime_class": "skills-factory-runtime",
        "tools": [
            "runtime_info",
            "list_skills",
            "load_skill",
            "route_investment_request",
            "render_bar_chart",
            "render_line_chart",
        ],
        "content_sha256": tree_digest,
        "transport": "streamable-http" if mode == "remote" else "stdio",
    }]


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


CAPABILITY_DIMENSIONS = ("network", "filesystem", "shell_exec", "credentials", "external_actions")


def capability_assessment(root: Path, component: str) -> dict:
    contract = yaml.safe_load((root / "release/capability-contract.yaml").read_text(encoding="utf-8")) or {}
    if contract.get("contract_id") != "repository-side-v1" or contract.get("schema_version") != "1.0":
        raise ValueError("unsupported repository capability contract")
    declaration = (contract.get("component_declarations") or {}).get(component)
    if declaration is None:
        return {"status": "UNASSESSED", "requirements": {name: "unassessed" for name in CAPABILITY_DIMENSIONS}}
    requirements = declaration.get("requirements") if isinstance(declaration, dict) else None
    if not isinstance(requirements, dict) or set(requirements) != set(CAPABILITY_DIMENSIONS):
        raise ValueError(f"{component}: invalid capability contract declaration")
    dimensions = contract.get("dimensions") or {}
    for name, value in requirements.items():
        if value not in dimensions.get(name, []):
            raise ValueError(f"{component}: invalid {name} capability {value!r}")
    return {"status": "UNASSESSED" if "unassessed" in requirements.values() else "DECLARED", "requirements": dict(requirements)}


def capability_contract_metadata() -> dict:
    return {"contract_id": "repository-side-v1", "assessment_semantics": "UNASSESSED is not equivalent to no permissions"}
