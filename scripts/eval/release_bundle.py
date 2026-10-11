"""Prepare an additive, source-bound release campaign; never execute model tests."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import zipfile

import yaml
from validate_isolation import FORBIDDEN_INPUT_HEADINGS

ROOT = Path(__file__).resolve().parents[2]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def prepare(output: Path, lab: Path, root: Path = ROOT) -> dict:
    output = output.resolve()
    if output == root.resolve() or root.resolve() in output.parents:
        raise ValueError("campaign output must be outside the source checkout")
    if output.exists() and any(output.iterdir()):
        raise ValueError("use a new empty output; preserve prior receipts")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root, text=True).strip():
        raise ValueError("commit source changes before freezing a campaign")
    manifest = json.loads((lab / "release-manifest.json").read_text())
    if manifest["source_revision"] != revision or manifest["channel"] != "lab":
        raise ValueError("Lab/source identity mismatch")
    packaged = {c["name"] for c in manifest["components"]}
    output.mkdir(parents=True, exist_ok=True)
    cases = []

    def add(cid, target, text, rubric, source, lane):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("missing executor input: " + cid)
        if FORBIDDEN_INPUT_HEADINGS.search(text):
            raise ValueError("evaluator heading in executor input: " + cid)
        stem = f"{len(cases) + 1:04d}"
        inp = output / "executor" / (stem + ".input.md")
        inp.parent.mkdir(parents=True, exist_ok=True)
        inp.write_text(text.strip() + "\n")
        rub = output / "evaluator" / (stem + ".rubric.json")
        write_json(rub, rubric)
        cases.append({"id": cid, "target": target, "lane": lane, "source": source,
                      "input": inp.relative_to(output).as_posix(),
                      "rubric": rub.relative_to(output).as_posix(),
                      "input_sha256": digest(inp.read_bytes()), "rubric_sha256": digest(rub.read_bytes()),
                      "status": "NOT_RUN", "outcome": None,
                      "surface": "cloud-host" if target in packaged else "source-sandbox",
                      "fixture_review": "REQUIRED", "integration_evidence": "NOT_RUN"})

    # Only input bytes go to executors; target, expectations and verdicts stay controller-side.
    for path in sorted([*(root / "skills").rglob("tests/cases.yaml"),
                        *(root / "workflows").rglob("tests/cases.yaml")]):
        target = path.parent.parent.name
        for row in yaml.safe_load(path.read_text())["cases"]:
            add("authored-" + target + "-" + row["id"], target, row["input"],
                {"expected": row["expected"], "case": row["case"]},
                path.relative_to(root).as_posix(), "authored")
    targets = {}
    for target, rows in yaml.safe_load((root / "evals/runtime-fixtures.yaml").read_text())["targets"].items():
        targets.update({row["input"]: target for row in rows})
    for path in sorted((root / "evals").rglob("*.input.md")):
        rubric_path = path.with_name(path.name.replace(".input.md", ".rubric.yaml"))
        if not rubric_path.is_file():
            continue
        rubric = yaml.safe_load(rubric_path.read_text())
        rel = path.relative_to(root).as_posix()
        target = targets.get(rel) or rubric.get("target") or rubric.get("expected_target") or "REVIEW_TARGET"
        add("external-" + rel.replace("/", "--"), target, path.read_text(), rubric, rel, "existing-runtime")
    for target in sorted(packaged):
        add("load-" + target, target,
            f"Use Skills Factory Cloud Next runtime_info and load_skill for {target}. Return actual tool results and references. Do not execute the skill or write external records.",
            {"must": ["exact Site and Lab identity match the observed candidate baseline",
                      "instructions and references match the frozen Lab artifact"],
             "must_not": ["evaluator/tests leakage", "claim loading executed the workflow"]},
            "release-manifest.json", "loader-parity")
    source_files = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    source_hashes = {rel: digest((root / rel).read_bytes()) for rel in source_files if rel and (root / rel).is_file()}
    lock = {"schema_version": "1.0", "campaign": "release-bundle-2026-10-10",
            "source_revision": revision, "source_files": source_hashes,
            "lab_manifest": manifest, "lab_manifest_sha256": digest((lab / "release-manifest.json").read_bytes()),
            "runtime_identity": "AWAITING_CANDIDATE_DEPLOYMENT_ATTESTATION", "runtime_execution": "NOT_RUN"}
    write_json(output / "lock.json", lock)
    write_json(output / "queue.json", {"campaign": lock["campaign"], "cases": cases})
    with zipfile.ZipFile(output / "executor-inputs.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for case in cases:
            path = output / case["input"]
            info = zipfile.ZipInfo(path.name, date_time=(2026, 10, 10, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    summary = {"cases": len(cases), "targets": len({c["target"] for c in cases}),
               "lab_entrypoints": len(packaged), "runtime_executed": 0,
               "by_lane": {lane: sum(c["lane"] == lane for c in cases) for lane in sorted({c["lane"] for c in cases})},
               "manual_fixture_review_required": True}
    write_json(output / "summary.json", summary)
    validate(output, root)
    return summary


def validate(output: Path, root: Path = ROOT) -> None:
    lock = json.loads((output / "lock.json").read_text())
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if revision != lock["source_revision"]:
        raise ValueError("source revision changed; create a new campaign")
    for rel, expected in lock["source_files"].items():
        path = root / rel
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError("source content drift: " + rel)
    cases = json.loads((output / "queue.json").read_text())["cases"]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("empty queue or duplicate IDs")
    with zipfile.ZipFile(output / "executor-inputs.zip") as archive:
        if set(archive.namelist()) != {Path(c["input"]).name for c in cases}:
            raise ValueError("executor archive inventory mismatch")
        for case in cases:
            for field in ("input", "rubric"):
                path = output / case[field]
                if digest(path.read_bytes()) != case[field + "_sha256"]:
                    raise ValueError("fixture digest mismatch")
            inp = output / case["input"]
            if FORBIDDEN_INPUT_HEADINGS.search(inp.read_text()) or archive.read(inp.name) != inp.read_bytes():
                raise ValueError("executor isolation/content failure")
            if case["status"] != "NOT_RUN" or case["outcome"] is not None:
                raise ValueError("preparation must not fabricate runtime results")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "validate"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lab", type=Path)
    args = parser.parse_args()
    if args.operation == "validate":
        validate(args.output)
        print("Release campaign integrity and executor isolation: OK; runtime NOT_RUN")
    else:
        if args.lab is None:
            parser.error("prepare requires --lab")
        print(json.dumps(prepare(args.output, args.lab), indent=2))
