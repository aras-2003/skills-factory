from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath

import yaml

from build_utils import sha256_tree

FORBIDDEN_PARTS = {"tests", "__pycache__", "evals"}
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def validate_skill_text(text: str, label: str) -> list[str]:
    errors: list[str] = []
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        return [f"{label}: missing portable frontmatter"]
    end = text.find("\n---\n", 4)
    try:
        fm = yaml.safe_load(text[4:end]) or {}
    except Exception as exc:
        return [f"{label}: invalid YAML frontmatter: {exc}"]
    name = fm.get("name")
    description = fm.get("description")
    if not isinstance(name, str) or not (1 <= len(name) <= 64):
        errors.append(f"{label}: portable name must be 1..64 characters")
    if not isinstance(description, str) or not (1 <= len(description) <= 1024):
        errors.append(f"{label}: portable description must be 1..1024 characters")
    compatibility = fm.get("compatibility")
    if compatibility is not None and (not isinstance(compatibility, str) or len(compatibility) > 500):
        errors.append(f"{label}: portable compatibility must be <=500 characters")
    metadata = fm.get("metadata") or {}
    if not isinstance(metadata, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in metadata.items()
    ):
        errors.append(f"{label}: portable metadata must be string -> string")
    return errors


def _inventory(component_dir: Path) -> list[str]:
    return sorted(
        p.relative_to(component_dir).as_posix()
        for p in component_dir.rglob("*")
        if p.is_file()
    )


def validate_manifests(path: Path) -> list[str]:
    errors: list[str] = []
    release = path / "release-manifest.json"
    capabilities = path / "capabilities.json"
    if not release.is_file():
        errors.append(f"missing release-manifest.json in {path}")
    if not capabilities.is_file():
        errors.append(f"missing capabilities.json in {path}")
    if release.is_file() and capabilities.is_file():
        r = json.loads(release.read_text(encoding="utf-8"))
        c = json.loads(capabilities.read_text(encoding="utf-8"))
        if r.get("source_revision") != c.get("source_revision"):
            errors.append("release/capabilities source_revision mismatch")
        if r.get("capability_contract") != c.get("capability_contract"):
            errors.append("release/capabilities capability_contract mismatch")
        if not r.get("release_id"):
            errors.append("release manifest missing immutable release_id")

        if "capabilities" in c:
            capability_items = c.get("capabilities") or []
            release_items = r.get("components") or []
            release_by_name = {
                item.get("name"): item
                for item in release_items
                if isinstance(item, dict) and item.get("name")
            }
            for item in capability_items:
                if not isinstance(item, dict) or not item.get("name"):
                    errors.append("invalid capability manifest item")
                    continue
                name = item["name"]
                component_dir = path / "skills" / name
                if not component_dir.is_dir():
                    errors.append(f"{name}: capability directory missing")
                    continue
                actual_digest = sha256_tree(component_dir)
                if item.get("content_sha256") != actual_digest:
                    errors.append(f"{name}: capabilities content_sha256 mismatch")
                if "inventory" in item and item.get("inventory") != _inventory(component_dir):
                    errors.append(f"{name}: capabilities inventory mismatch")

                release_item = release_by_name.get(name)
                if release_item is None:
                    errors.append(f"{name}: missing from release manifest")
                    continue
                for field in ("kind", "maturity", "version", "content_sha256"):
                    if release_item.get(field) != item.get(field):
                        errors.append(f"{name}: release/capabilities {field} mismatch")
                if item.get("capability_assessment") != release_item.get("capability_assessment"):
                    errors.append(f"{name}: release/capabilities capability_assessment mismatch")
                assessment = item.get("capability_assessment")
                if assessment is not None:
                    required_dimensions = {"network", "filesystem", "shell_exec", "credentials", "external_actions"}
                    requirements = assessment.get("requirements") if isinstance(assessment, dict) else None
                    if not isinstance(requirements, dict) or set(requirements) != required_dimensions:
                        errors.append(f"{name}: invalid capability assessment dimensions")
                    elif assessment.get("status") not in {"DECLARED", "UNASSESSED"}:
                        errors.append(f"{name}: invalid capability assessment status")
                    elif assessment.get("status") == "UNASSESSED" and "unassessed" not in requirements.values():
                        errors.append(f"{name}: UNASSESSED status requires an unresolved capability dimension")
                    elif assessment.get("status") == "DECLARED" and "unassessed" in requirements.values():
                        errors.append(f"{name}: DECLARED status cannot hide unresolved capability dimensions")

            capability_names = {
                item.get("name") for item in capability_items if isinstance(item, dict) and item.get("name")
            }
            extra_release = sorted(set(release_by_name) - capability_names)
            if extra_release:
                errors.append("release manifest has unknown components: " + ", ".join(extra_release))
    return errors


def validate_tree(path: Path, allow_lab_evals: bool = False) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing artifact: {path}"]
    errors.extend(validate_manifests(path))
    for file in path.rglob("*"):
        if not file.is_file():
            continue
        rel = file.relative_to(path)
        if any(part in FORBIDDEN_PARTS for part in rel.parts):
            is_lab_eval = (
                allow_lab_evals
                and "evals" in rel.parts
                and "references" in rel.parts
                and (file.name.endswith(".input.md") or file.name == "INDEX.md")
            )
            if not is_lab_eval:
                errors.append(f"forbidden runtime content: {rel}")
        if file.name.endswith(".rubric.yaml"):
            errors.append(f"rubric leaked into runtime artifact: {rel}")
        if file.name == "SKILL.md":
            skill_text = file.read_text(encoding="utf-8")
            errors.extend(validate_skill_text(skill_text, str(rel)))
            if allow_lab_evals and "references/evals/" in skill_text.casefold():
                errors.append(f"{rel}: executor fixture paths must not appear in model-loadable skill text")
        if allow_lab_evals and file.name.endswith(".input.md") and "skills" in rel.parts:
            errors.append(f"{rel}: executor input must be stored outside model-loadable skills")
    if allow_lab_evals:
        index_path = path / "executor-inputs.json"
        if not index_path.is_file():
            errors.append("Lab artifact missing executor-inputs.json")
        else:
            try:
                index = json.loads(index_path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"executor-inputs.json: invalid JSON: {exc}")
                index = {}
            cases = index.get("cases") if isinstance(index, dict) else None
            if (
                not isinstance(index, dict)
                or index.get("schema_version") != "1.0"
                or not isinstance(cases, list)
            ):
                errors.append("executor-inputs.json: unsupported schema or missing cases")
                cases = []
            indexed_inputs: set[str] = set()
            for item in cases:
                if not isinstance(item, dict):
                    errors.append("executor-inputs.json: case must be an object")
                    continue
                rel_input = item.get("input")
                if (
                    not isinstance(rel_input, str)
                    or not rel_input.startswith("executor-inputs/")
                    or ".." in PurePosixPath(rel_input).parts
                    or "\\" in rel_input
                    or not rel_input.endswith(".input.md")
                    or rel_input in indexed_inputs
                ):
                    errors.append(f"executor-inputs.json: unsafe or duplicate input path {rel_input!r}")
                    continue
                indexed_inputs.add(rel_input)
                input_path = path / rel_input
                input_root = path / "executor-inputs"
                traversed = [input_path, input_root, *input_path.parents]
                if any(parent.is_symlink() for parent in traversed if parent != path):
                    errors.append(f"executor-inputs.json: symlinked executor path {rel_input}")
                    continue
                try:
                    input_path.resolve().relative_to(path.resolve())
                except ValueError:
                    errors.append(f"executor-inputs.json: executor path escapes artifact {rel_input}")
                    continue
                if not input_path.is_file():
                    errors.append(f"executor-inputs.json: missing executor input {rel_input}")
                    continue
                actual_digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
                if item.get("input_sha256") != actual_digest:
                    errors.append(f"executor-inputs.json: digest mismatch for {rel_input}")
                if "rubric" in item:
                    errors.append(f"executor-inputs.json: rubric path is forbidden for {rel_input}")
            actual_inputs = {
                file.relative_to(path).as_posix()
                for file in (path / "executor-inputs").rglob("*.input.md")
            } if (path / "executor-inputs").is_dir() else set()
            if actual_inputs != indexed_inputs:
                errors.append("executor-inputs.json: indexed inputs do not match packaged executor inputs")
    return errors


def _unique_by_name(items: list[dict], label: str, errors: list[str]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            errors.append(f"{label}: item must be a mapping")
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name:
            errors.append(f"{label}: item missing name")
            continue
        if name in result:
            errors.append(f"{label}: duplicate component name {name}")
            continue
        result[name] = item
    return result


def _zip_member_errors(zip_name: str, item_name: str, infos: list[zipfile.ZipInfo]) -> list[str]:
    errors: list[str] = []
    names = [info.filename for info in infos]
    if len(names) != len(set(names)):
        errors.append(f"{zip_name}: duplicate ZIP entries")
    if names != sorted(names):
        errors.append(f"{zip_name}: ZIP entries are not sorted")
    for info in infos:
        name = info.filename
        if info.is_dir():
            errors.append(f"{zip_name}: directory entries are not allowed: {name}")
            continue
        if "\\" in name or name.startswith("/"):
            errors.append(f"{zip_name}: unsafe ZIP entry name {name}")
            continue
        raw_parts = name.split("/")
        if any(part in {"", ".", ".."} for part in raw_parts):
            errors.append(f"{zip_name}: unsafe ZIP entry name {name}")
            continue
        posix = PurePosixPath(name)
        if posix.is_absolute() or not posix.parts or posix.parts[0] != item_name:
            errors.append(f"{zip_name}: ZIP entry outside matching top-level folder: {name}")
            continue
        if len(posix.parts) < 2:
            errors.append(f"{zip_name}: ZIP entry missing component-relative path: {name}")
    return errors


def _zip_content_digest(zf: zipfile.ZipFile, infos: list[zipfile.ZipInfo]) -> tuple[str, list[str]]:
    h = hashlib.sha256()
    inventory: list[str] = []
    for info in sorted(infos, key=lambda x: x.filename):
        parts = PurePosixPath(info.filename).parts
        rel = PurePosixPath(*parts[1:]).as_posix()
        inventory.append(rel)
        rel_bytes = rel.encode()
        h.update(len(rel_bytes).to_bytes(4, "big"))
        h.update(rel_bytes)
        data = zf.read(info)
        h.update(len(data).to_bytes(8, "big"))
        h.update(data)
    return h.hexdigest(), inventory


def validate_zips(path: Path) -> list[str]:
    errors: list[str] = []
    index_path = path / "index.json"
    capabilities_path = path / "capabilities.json"
    release_path = path / "release-manifest.json"
    if not index_path.is_file():
        return [f"missing index.json in {path}"]
    errors.extend(validate_manifests(path))
    if not capabilities_path.is_file() or not release_path.is_file():
        return errors

    index = json.loads(index_path.read_text(encoding="utf-8"))
    capabilities = json.loads(capabilities_path.read_text(encoding="utf-8"))
    release = json.loads(release_path.read_text(encoding="utf-8"))
    if index.get("source_revision") is None:
        errors.append("index.json missing source_revision")
    if index.get("source_revision") != capabilities.get("source_revision"):
        errors.append("index/capabilities source_revision mismatch")
    if index.get("source_revision") != release.get("source_revision"):
        errors.append("index/release source_revision mismatch")
    if index.get("package_version") != capabilities.get("package_version"):
        errors.append("index/capabilities package_version mismatch")
    if index.get("package_version") != release.get("version"):
        errors.append("index/release package version mismatch")
    contract = index.get("capability_contract")
    if not isinstance(contract, dict) or contract != capabilities.get("capability_contract") or contract != release.get("capability_contract"):
        errors.append("index/capabilities/release capability_contract mismatch")

    index_by_name = _unique_by_name(index.get("skills") or [], "index", errors)
    capabilities_by_name = _unique_by_name(capabilities.get("skills") or [], "capabilities", errors)
    release_by_name = _unique_by_name(release.get("components") or [], "release manifest", errors)
    if set(index_by_name) != set(capabilities_by_name):
        errors.append("index/capabilities component set mismatch")
    if set(index_by_name) != set(release_by_name):
        errors.append("index/release component set mismatch")
    if release.get("component_count") != len(index_by_name):
        errors.append("release component_count mismatch")

    zip_names: set[str] = set()
    for name, item in index_by_name.items():
        zip_name = item.get("zip")
        if not isinstance(zip_name, str) or not zip_name:
            errors.append(f"{name}: missing zip name")
            continue
        if zip_name in zip_names:
            errors.append(f"duplicate ZIP filename in index: {zip_name}")
        zip_names.add(zip_name)

        capability = capabilities_by_name.get(name)
        release_item = release_by_name.get(name)
        identity_fields = ("version", "maturity", "zip", "content_sha256", "archive_sha256", "inventory", "capability_assessment")
        if capability is not None:
            for field in identity_fields:
                if capability.get(field) != item.get(field):
                    errors.append(f"{name}: index/capabilities {field} mismatch")
        if release_item is not None:
            if release_item.get("kind") != item.get("kind"):
                errors.append(f"{name}: index/release kind mismatch")
            for field in identity_fields:
                if release_item.get(field) != item.get(field):
                    errors.append(f"{name}: index/release {field} mismatch")

        zp = path / zip_name
        if not zp.is_file():
            errors.append(f"missing ZIP {zip_name}")
            continue
        actual_archive_digest = hashlib.sha256(zp.read_bytes()).hexdigest()
        if item.get("archive_sha256") != actual_archive_digest:
            errors.append(f"{zip_name}: archive_sha256 mismatch")

        try:
            with zipfile.ZipFile(zp) as zf:
                infos = zf.infolist()
                member_errors = _zip_member_errors(zip_name, name, infos)
                errors.extend(member_errors)
                if member_errors:
                    continue
                actual_content_digest, actual_inventory = _zip_content_digest(zf, infos)
                if item.get("content_sha256") != actual_content_digest:
                    errors.append(f"{zip_name}: content_sha256 mismatch")
                if item.get("inventory") != actual_inventory:
                    errors.append(f"{zip_name}: inventory mismatch")

                skill_member = f"{name}/SKILL.md"
                skill_entries = [info for info in infos if info.filename == skill_member]
                if len(skill_entries) != 1:
                    errors.append(f"{zip_name}: expected exactly one {skill_member}")
                else:
                    skill_text = zf.read(skill_entries[0]).decode("utf-8")
                    errors.extend(validate_skill_text(skill_text, f"{zip_name}:{skill_member}"))
                    fm_end = skill_text.find("\n---\n", 4)
                    if skill_text.startswith("---\n") and fm_end >= 0:
                        fm = yaml.safe_load(skill_text[4:fm_end]) or {}
                        metadata = fm.get("metadata") or {}
                        if fm.get("name") != name:
                            errors.append(f"{zip_name}: SKILL.md name mismatch")
                        if str(metadata.get("version") or "") != str(item.get("version") or ""):
                            errors.append(f"{zip_name}: SKILL.md version mismatch")
                        if str(metadata.get("maturity") or "") != str(item.get("maturity") or ""):
                            errors.append(f"{zip_name}: SKILL.md maturity mismatch")

                for info in infos:
                    entry_name = info.filename
                    parts = PurePosixPath(entry_name).parts
                    if any(part in FORBIDDEN_PARTS for part in parts):
                        errors.append(f"{zip_name}: forbidden path {entry_name}")
                    if entry_name.endswith(".rubric.yaml"):
                        errors.append(f"{zip_name}: rubric leaked: {entry_name}")
                    if info.date_time != ZIP_TIMESTAMP:
                        errors.append(f"{zip_name}: non-deterministic timestamp on {entry_name}")
        except zipfile.BadZipFile as exc:
            errors.append(f"{zip_name}: invalid ZIP: {exc}")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--zips", action="store_true")
    parser.add_argument("--lab", action="store_true", help="allow isolated executor-inputs/*.input.md in the Lab package")
    args = parser.parse_args()
    errors = validate_zips(args.path) if args.zips else validate_tree(args.path, allow_lab_evals=args.lab)
    for error in errors:
        print(f"[BLOCKER] {error}")
    if not errors:
        print(f"Artifact validation: OK ({args.path})")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
