"""Build a byte-verified index of the seven public strategy reference ZIPs.

The verifier reads members directly from ZIP files; it never extracts them or
copies third-party source into the repository.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import stat
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from zipfile import BadZipFile, ZipFile


ARCHIVES = (
    {
        "id": "oria-21-strategy",
        "filename": "21-strategy-skills-for-claude-skills.zip",
        "sha256": "8a1c43d39328927ce58fba294010ab1f977e903fe2fe0f7e02c321e8c21a96b7",
        "source_url": "https://www.oria.one/resources/21-strategy-skills-for-claude",
        "archive_url": "https://www.oria.one/resources/21-strategy-skills-for-claude-skills.zip",
        "license_status": "No license file in archive; webpage describes a free download but grants no identified redistribution license.",
    },
    {
        "id": "oria-tier-one-strategy",
        "filename": "tier-one-strategy-skills-for-claude-skills.zip",
        "sha256": "fcc70c0a7460fdb421cdd2a384c47c4c6b453c3c99ce30c41fcacb6de0827e69",
        "source_url": "https://www.oria.one/resources/tier-one-strategy-skills-for-claude",
        "archive_url": "https://www.oria.one/resources/tier-one-strategy-skills-for-claude-skills.zip",
        "license_status": "No license file in archive; webpage describes a free download but grants no identified redistribution license.",
    },
    {
        "id": "oria-excel-strategy",
        "filename": "excel-inspired-claude-skills-strategy-skills.zip",
        "sha256": "e7a2a8a12f4eb97f8e3e4ac042d499424917ae9ba57a3911e5ce73557574f221",
        "source_url": "https://www.oria.one/resources/excel-inspired-claude-skills-strategy",
        "archive_url": "https://www.oria.one/resources/excel-inspired-claude-skills-strategy-skills.zip",
        "license_status": "No license file in archive; webpage describes a free download but grants no identified redistribution license.",
    },
    {
        "id": "mckinsey-skills-community",
        "filename": "mckinsey_skills-main.zip",
        "sha256": "fcc531bb6015d9482f40b3cd3e0b54b760f0a6acdb4e3b5477a32b7744f19285",
        "source_url": "https://github.com/callmeramzo/mckinsey_skills",
        "archive_url": "https://github.com/callmeramzo/mckinsey_skills/archive/refs/heads/main.zip",
        "source_commit": "5023cc979fa88dc4c64f804f12aa9682d330606f",
        "license_status": "No license file in archive; reference-only, no verbatim reuse. Not an official McKinsey publication.",
    },
    {
        "id": "mckinsey-bcg-community",
        "filename": "mckinsey-bcg-consulting-main.zip",
        "sha256": "d6365ef2783139227b2ef1301672cab78c958ffbfa920e9dcd6bd5230fdaba38",
        "source_url": "https://github.com/MichaelRochonnn/mckinsey-bcg-consulting",
        "archive_url": "https://github.com/MichaelRochonnn/mckinsey-bcg-consulting/archive/refs/heads/main.zip",
        "source_commit": "3ca573be6ae3b216c959cbb865c4eaf7d62fd0bb",
        "license_status": "No license file in archive; reference-only, no verbatim reuse. Not an official McKinsey or BCG publication.",
    },
    {
        "id": "business-consulting-mit",
        "filename": "business-consulting-main.zip",
        "sha256": "e47518d78bd5d987b51f03159b7ad77973893dbe771acbcb3b9bef77ea609ea9",
        "source_url": "https://github.com/abinauv/business-consulting",
        "archive_url": "https://github.com/abinauv/business-consulting/archive/refs/heads/main.zip",
        "source_commit": "8808ffb170bd4f8d8fadcc7e107cc9d124837570",
        "license_status": "MIT; archive includes LICENSE. Preserve notice if reproducing substantial portions. Not an official McKinsey publication.",
    },
    {
        "id": "consultant-mit",
        "filename": "consultant-main.zip",
        "sha256": "af3eb3252085b6c49d6f6aba4af5fe45ed00e676c82ce976c321ab5c401f76b7",
        "source_url": "https://github.com/yoichiojima-2/consultant",
        "archive_url": "https://github.com/yoichiojima-2/consultant/archive/refs/heads/main.zip",
        "source_commit": "9a1ea0e2dac27be0b7448677ac47db4b2044b4af",
        "license_status": "MIT; archive includes LICENSE. Preserve notice if reproducing substantial portions. Not an official Accenture or Bain publication.",
    },
)


class CorpusError(ValueError):
    pass


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inspect_archive(path, expected):
    archive_bytes = path.read_bytes()
    actual_archive_sha = _digest(archive_bytes)
    if actual_archive_sha != expected["sha256"]:
        raise CorpusError(f"{expected['filename']}: SHA-256 mismatch")
    files = []
    seen = set()
    try:
        with ZipFile(path) as archive:
            uncompressed_total = 0
            for info in archive.infolist():
                if info.is_dir():
                    continue
                member = PurePosixPath(info.filename)
                windows_member = PureWindowsPath(info.filename)
                if (
                    member.is_absolute()
                    or windows_member.is_absolute()
                    or windows_member.drive
                    or "\\" in info.filename
                    or any(part in {"", ".", ".."} for part in info.filename.split("/"))
                    or not member.parts
                ):
                    raise CorpusError(f"{expected['filename']}: unsafe member path")
                if info.filename in seen:
                    raise CorpusError(f"{expected['filename']}: duplicate member path")
                seen.add(info.filename)
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise CorpusError(f"{expected['filename']}: symbolic-link member is not allowed")
                if info.flag_bits & 0x1:
                    raise CorpusError(f"{expected['filename']}: encrypted member is not auditable")
                uncompressed_total += info.file_size
                if info.file_size > 10_000_000 or uncompressed_total > 100_000_000:
                    raise CorpusError(f"{expected['filename']}: archive exceeds audit size limits")
                data = archive.read(info)
                files.append({
                    "archive_id": expected["id"],
                    "archive_sha256": actual_archive_sha,
                    "path": info.filename,
                    "size_bytes": info.file_size,
                    "sha256": _digest(data),
                    "extension": PurePosixPath(info.filename).suffix.lower(),
                })
    except BadZipFile as exc:
        raise CorpusError(f"{expected['filename']}: invalid ZIP archive") from exc
    licenses = [
        row for row in files
        if PurePosixPath(row["path"]).name.lower() in {"license", "license.md", "license.txt", "licence", "copying", "notice"}
    ]
    skills = [row for row in files if PurePosixPath(row["path"]).name.lower() == "skill.md"]
    return {
        **expected,
        "archive_sha256_verified": True,
        "archive_size_bytes": len(archive_bytes),
        "file_count": len(files),
        "markdown_count": sum(row["extension"] == ".md" for row in files),
        "skill_md_count": len(skills),
        "license_files": [{"path": row["path"], "sha256": row["sha256"]} for row in licenses],
    }, files


def build(source_dir, manifest_path, index_path):
    summaries, all_files = [], []
    for item in ARCHIVES:
        summary, files = inspect_archive(source_dir / item["filename"], item)
        summaries.append(summary)
        all_files.extend(files)
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "corpus_sha256_verified_against": "docs/strategy-os/external-source-register-2026-10-26.md",
        "source_handling": "Archives were retrieved from their listed public source URLs and hash-verified. ZIP members were read in place, never extracted. Third-party archive contents are not redistributed in this repository.",
        "archives": summaries,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with index_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["archive_id", "archive_sha256", "path", "size_bytes", "sha256", "extension"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(all_files, key=lambda row: (row["archive_id"], row["path"])))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True, help="Directory containing the seven hash-pinned ZIP files")
    parser.add_argument("--manifest", required=True, help="Output JSON manifest path")
    parser.add_argument("--index", required=True, help="Output CSV per-file SHA-256 index path")
    args = parser.parse_args()
    try:
        manifest = build(Path(args.source_dir), Path(args.manifest), Path(args.index))
    except (OSError, CorpusError) as exc:
        parser.error(str(exc))
    print(json.dumps({"archives": len(manifest["archives"]), "files": sum(item["file_count"] for item in manifest["archives"]), "verified": True}))


if __name__ == "__main__":
    main()
