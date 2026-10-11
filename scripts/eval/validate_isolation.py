from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from common import load_registry, repo_root

FORBIDDEN_INPUT_HEADINGS = re.compile(
    r"^##\s+(PASS(?:\s+criteria)?|Expected routing|Expected route|Expected output properties|Expected behavior(?:s)?|Failure conditions|Test objective|Evaluator(?:-only)? rubric|Evaluator instructions|Scoring rubric)\b",
    re.IGNORECASE | re.MULTILINE,
)


def validate_registry(root: Path) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for target, cases in load_registry(root).items():
        if not isinstance(cases, list) or not cases:
            errors.append(f"{target}: fixture list must be non-empty")
            continue
        for case in cases:
            if not isinstance(case, dict):
                errors.append(f"{target}: each fixture must be a mapping")
                continue
            cid = str(case.get("id") or "").strip()
            mode = str(case.get("mode") or "").strip()
            input_rel = str(case.get("input") or "").strip()
            rubric_rel = str(case.get("rubric") or "").strip()
            if not cid:
                errors.append(f"{target}: missing case id")
            elif cid in seen_ids:
                errors.append(f"duplicate case id: {cid}")
            seen_ids.add(cid)
            if mode not in {"explicit", "natural-routing"}:
                errors.append(f"{target}/{cid}: invalid mode {mode!r}")
            if not input_rel.endswith(".input.md"):
                errors.append(f"{target}/{cid}: input must end in .input.md")
            if not rubric_rel.endswith(".rubric.yaml"):
                errors.append(f"{target}/{cid}: rubric must end in .rubric.yaml")
            input_path = root / input_rel
            rubric_path = root / rubric_rel
            if not input_path.is_file():
                errors.append(f"{target}/{cid}: missing input {input_rel}")
                continue
            if not rubric_path.is_file():
                errors.append(f"{target}/{cid}: missing rubric {rubric_rel}")
                continue
            if FORBIDDEN_INPUT_HEADINGS.search(input_path.read_text(encoding="utf-8")):
                errors.append(f"{target}/{cid}: executor input leaks evaluator headings")
            rubric_text = rubric_path.read_text(encoding="utf-8").lower()
            if "assertions:" not in rubric_text:
                errors.append(f"{target}/{cid}: rubric has no assertions")
    return errors


def validate_artifact(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"artifact does not exist: {path}"]
    for p in path.rglob("*"):
        if not p.is_file():
            continue
        if p.name.endswith(".rubric.yaml"):
            errors.append(f"rubric leaked into executor artifact: {p}")
        if p.name.endswith(".input.md") and FORBIDDEN_INPUT_HEADINGS.search(p.read_text(encoding="utf-8")):
            errors.append(f"packaged executor input leaks evaluator headings: {p}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path)
    args = parser.parse_args()
    root = repo_root()
    errors = validate_registry(root)
    if args.artifact:
        errors.extend(validate_artifact(args.artifact.resolve()))
    for err in errors:
        print(f"[BLOCKER] {err}")
    if not errors:
        print("Eval isolation: OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
