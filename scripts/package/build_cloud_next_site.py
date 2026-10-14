from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "sites" / "skills-factory-site"
ADAPTER = ROOT / "adapters" / "skills-factory-cloud-next"
IGNORED = shutil.ignore_patterns(
    ".git",
    ".next",
    ".sites-runtime",
    ".wrangler",
    "dist",
    "node_modules",
    "outputs",
    "__pycache__",
    "*.pyc",
    "*.tsbuildinfo",
    "*.tar.gz",
    ".env*",
)


def run(args: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    subprocess.run(args, cwd=cwd, env=env, check=True)


def deterministic_lab_archive(source: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"Lab artifact contains a symlink: {path.relative_to(source)}")
            if not path.is_file():
                continue
            name = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def generate_catalog(lab: Path, work_dir: Path) -> Path:
    generated_site = work_dir / "site"
    shutil.copytree(SITE, generated_site, ignore=IGNORED)
    lab_archive = work_dir / "skills-factory-lab.zip"
    deterministic_lab_archive(lab, lab_archive)
    run(
        [
            sys.executable,
            str(ADAPTER / "scripts" / "sync-lab-catalog.py"),
            str(lab),
            str(lab_archive),
            "--site-root",
            str(generated_site),
        ]
    )
    run(
        [
            "node",
            str(ADAPTER / "scripts" / "sync-lab-references.mjs"),
            str(lab),
            str(generated_site),
        ]
    )
    adapter_out = generated_site / "lib" / "skills-factory-adapter"
    adapter_out.mkdir(parents=True, exist_ok=True)
    for source in sorted(ADAPTER.joinpath("src").glob("*.ts")):
        shutil.copyfile(source, adapter_out / source.name)
    shutil.copyfile(generated_site / "lib" / "skill-catalog.ts", adapter_out / "skill-catalog.ts")
    return generated_site / "lib" / "skill-catalog.ts"


def source_revision() -> str:
    revision = os.environ.get("SOURCE_REVISION") or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if len(revision) != 40 or any(character not in "0123456789abcdef" for character in revision.lower()):
        raise ValueError("SOURCE_REVISION must be a full Git SHA.")
    return revision.lower()


def routing_contract_blob() -> str:
    blob = subprocess.check_output(
        ["git", "rev-parse", f"{source_revision()}:workflows/investment-os-review/WORKFLOW.md"],
        cwd=ROOT,
        text=True,
    ).strip()
    if not re.fullmatch(r"[a-f0-9]{40}", blob):
        raise ValueError("Could not resolve the canonical investment routing contract blob.")
    return blob


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify or refresh the Cloud Next adapter bundle from this commit's Lab build."
    )
    parser.add_argument("--lab-artifact", type=Path, help="Existing extracted Lab artifact; built when omitted.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Fail if the adapter bundle is stale (default).")
    group.add_argument("--write-generated", action="store_true", help="Write the generated adapter bundle into the Site workspace.")
    args = parser.parse_args()

    SITE.joinpath(".openai", "hosting.json").read_text(encoding="utf-8")
    scratch_root = ROOT / ".tmp"
    if scratch_root.is_symlink():
        raise ValueError("Refusing a symlink at the repository .tmp scratch path.")
    scratch_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cloud-next-catalog-", dir=scratch_root) as temporary:
        work_dir = Path(temporary)
        lab = args.lab_artifact.resolve() if args.lab_artifact else work_dir / "lab"
        if not args.lab_artifact:
            build_env = dict(os.environ)
            build_env["SOURCE_REVISION"] = source_revision()
            run([sys.executable, str(ROOT / "scripts" / "package" / "build_lab_plugin.py"), "--output", str(lab)], env=build_env)
        if not (lab / "release-manifest.json").is_file():
            raise FileNotFoundError(f"Lab artifact is missing a release manifest: {lab}")

        generated_catalog_path = generate_catalog(lab, work_dir)
        generated_site = generated_catalog_path.parents[1]
        adapter_generated = generated_site / "lib" / "skills-factory-adapter"
        adapter_provenance = (
            f'// Generated from this Skills Factory commit before the Site build.\n'
            f'export const CANONICAL_SOURCE_REVISION = "{source_revision()}" as const;\n'
            f'export const ROUTING_CONTRACT_BLOB_SHA = "{routing_contract_blob()}" as const;\n'
        ).encode()
        (adapter_generated / "canonical-provenance.ts").write_bytes(adapter_provenance)
        source_digests = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(ADAPTER.joinpath("src").glob("*.ts"))
        }
        adapter_manifest = {
            "schema_version": "1.0",
            "adapter": "skills-factory-cloud-next",
            "source_revision": source_revision(),
            "lab_release_id": json.loads((lab / "release-manifest.json").read_text(encoding="utf-8"))["release_id"],
            "source_files": source_digests,
        }
        (adapter_generated / "adapter-manifest.json").write_text(
            json.dumps(adapter_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        generated_files = {
            f"lib/skills-factory-adapter/{path.name}": path.read_bytes()
            for path in sorted(adapter_generated.iterdir()) if path.is_file()
        }
        if args.write_generated:
            for relative, content in generated_files.items():
                target = SITE / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            print("Generated the Cloud Next adapter bundle, catalog and source attestation from this Skills Factory build.")
            return 0
        stale = [relative for relative, content in generated_files.items()
                 if not (SITE / relative).is_file() or (SITE / relative).read_bytes() != content]
        if stale:
            raise SystemExit(
                "Cloud Next's generated adapter bundle or catalog is stale. Run "
                "python scripts/package/build_cloud_next_site.py --write-generated and include the result."
            )
        print("Cloud Next adapter bundle, catalog, references and provenance match this Skills Factory build.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
