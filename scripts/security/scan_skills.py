from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parents[2]
CODE_SUFFIXES = {".py", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts", ".ps1", ".json", ".toml", ".txt"}
TEXT_SUFFIXES = CODE_SUFFIXES | {".md", ".yaml", ".yml"}
KNOWN_RULES = {"SEC001", "SEC002", "SEC003", "SEC004", "SEC005", "SEC006", "SEC007", "SEC008", "SEC009", "SEC010"}
SCAN_AREAS = ("skills", "runtime", "scripts", "workflows", "templates", ".github/workflows")
EXCLUDED_PARTS = {"tests", "__pycache__", ".venv", ".tmp", "node_modules", "evals", ".git"}
SCANNER_SOURCE = Path("scripts/security/scan_skills.py")

# These are deliberately narrow static indicators. A finding requires review; this
# scanner does not prove exploitability and never executes inspected files.
LINE_RULES: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("SEC001", "high", re.compile(r"\b(?:curl|wget)\b[^\n|;]*\|\s*(?:sudo\s+)?(?:sh|bash)\b", re.I)),
    ("SEC002", "high", re.compile(r"\b(?:exec|eval)\s*\(\s*(?:base64\.)?b64decode\s*\(", re.I)),
    ("SEC003", "high", re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password|private[_-]?key)\b\s*[:=]\s*['\"](?!(?:your|replace|example|placeholder|changeme))[^'\"]{12,}['\"]")),
    ("SEC004", "high", re.compile(r"\b(?:subprocess\.(?:run|Popen|call)|os\.system)\s*\([^\n]*(?:shell\s*=\s*True|\|\s*(?:sh|bash))", re.I)),
)
NETWORK_RE = re.compile(r"\b(?:requests\.(?:post|put|patch)|httpx\.(?:post|put|patch)|urllib\.request\.urlopen|fetch\s*\()", re.I)
SECRET_READ_RE = re.compile(r"(?:os\.environ|getenv\s*\(|process\.env|\$env:)[^\n]*(?:secret|token|password|credential|api.?key|private.?key)", re.I)
OBFUSCATION_RE = re.compile(r"\b(?:base64\.b64decode|b64decode|atob\s*\(|fromhex\s*\(|marshal\.loads)\b", re.I)
DYNAMIC_EXEC_RE = re.compile(r"\b(?:exec|eval|compile)\s*\(|\b(?:subprocess\.(?:run|Popen|call)|os\.system)\b", re.I)
TOKEN_LITERAL_RE = re.compile(r"(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    path: str
    line: int
    message: str
    fingerprint: str
    suppressed: bool = False
    suppression_reason: str | None = None


def _fingerprint(rule_id: str, rel_path: str, line: str) -> str:
    normalized = " ".join(line.strip().split())
    return hashlib.sha256(f"{rule_id}\0{rel_path}\0{normalized}".encode()).hexdigest()


def _source_files(root: Path) -> Iterable[Path]:
    found: set[Path] = set()
    for area in SCAN_AREAS:
        base = root / area
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            rel = path.relative_to(root)
            if any(part in EXCLUDED_PARTS for part in rel.parts):
                continue
            if rel == SCANNER_SOURCE:
                continue
            if not path.is_file() and not path.is_symlink():
                continue
            if path.is_symlink() or path.suffix.lower() in TEXT_SUFFIXES or path.name in {"SKILL.md", "WORKFLOW.md"}:
                found.add(path)
    yield from sorted(found)


def _dependency_is_pinned(value: str) -> bool:
    requirement = value.split(";", 1)[0].strip()
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*(?:\[[^]]+\])?\s*==\s*[A-Za-z0-9][A-Za-z0-9.+!-]*", requirement):
        return True
    direct_url = requirement
    named_url = re.match(r"^[A-Za-z0-9][A-Za-z0-9_.-]*\s*@\s*(\S+)$", requirement)
    if named_url:
        direct_url = named_url.group(1)
    if direct_url.startswith(("http://", "https://", "git+https://", "git+ssh://")):
        return bool(re.search(r"@[0-9a-f]{40}(?:#|$)", direct_url, re.I) or re.search(r"#sha256=[0-9a-f]{64}$", direct_url, re.I))
    if requirement.startswith(("-e ", "--editable ")):
        target = requirement.split(maxsplit=1)[1]
        return not re.match(r"(?:git\+)?(?:https?|ssh)://", target, re.I)
    return False


def _scan_file(root: Path, path: Path) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"cannot inspect {path.relative_to(root).as_posix()}: {type(exc).__name__}") from exc
    rel = path.relative_to(root).as_posix()
    lines = text.splitlines()
    findings: list[Finding] = []
    # Bidi controls can reorder visible text. ZWJ/ZWNJ are intentionally excluded.
    bidi_controls = {0x061C, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069}
    for number, line in enumerate(lines, 1):
        if any(ord(char) in bidi_controls or (ord(char) == 0xFEFF and number > 1) for char in line):
            findings.append(Finding("SEC010", "medium", rel, number, _message("SEC010"), _fingerprint("SEC010", rel, line)))
        for rule_id, severity, pattern in LINE_RULES:
            if pattern.search(line):
                findings.append(Finding(rule_id, severity, rel, number, _message(rule_id), _fingerprint(rule_id, rel, line)))
        if TOKEN_LITERAL_RE.search(line) and not any(item.rule_id == "SEC003" and item.line == number for item in findings):
            findings.append(Finding("SEC003", "high", rel, number, _message("SEC003"), _fingerprint("SEC003", rel, line)))

    if path.name == "package.json":
        try:
            package = json.loads(text)
        except json.JSONDecodeError:
            package = {}
        scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
        if isinstance(scripts, dict) and any(key.lower() in {"preinstall", "install", "postinstall"} for key in scripts):
            line_number = next((i for i, line in enumerate(lines, 1) if re.search(r'"(?:preinstall|install|postinstall)"\s*:', line, re.I)), 1)
            evidence_line = lines[line_number - 1] if lines else ""
            findings.append(Finding("SEC007", "high", rel, line_number, _message("SEC007"), _fingerprint("SEC007", rel, evidence_line)))
    if path.name == "setup.py" and re.search(r"\b(?:subprocess|os\.system|exec|eval)\b", text):
        number = next((i for i, line in enumerate(lines, 1) if re.search(r"\b(?:subprocess|os\.system|exec|eval)\b", line)), 1)
        evidence_line = lines[number - 1] if lines else ""
        findings.append(Finding("SEC007", "high", rel, number, _message("SEC007"), _fingerprint("SEC007", rel, evidence_line)))
    if path.name.startswith("requirements") and path.suffix == ".txt":
        for number, line in enumerate(lines, 1):
            value = line.split("#", 1)[0].strip()
            if not value or value.startswith(("-r ", "-c ", "--index-url", "--extra-index-url", "--trusted-host")):
                continue
            if not _dependency_is_pinned(value):
                findings.append(Finding("SEC008", "medium", rel, number, _message("SEC008"), _fingerprint("SEC008", rel, value)))

    # Cross-line heuristic is intentionally a single file-level finding and needs human review.
    if SECRET_READ_RE.search(text) and NETWORK_RE.search(text):
        line_number = next((i for i, line in enumerate(lines, 1) if SECRET_READ_RE.search(line)), 1)
        evidence_line = lines[line_number - 1] if lines else ""
        findings.append(Finding("SEC005", "high", rel, line_number, _message("SEC005"), _fingerprint("SEC005", rel, evidence_line)))
    if OBFUSCATION_RE.search(text) and DYNAMIC_EXEC_RE.search(text) and not any(f.rule_id == "SEC002" for f in findings):
        line_number = next((i for i, line in enumerate(lines, 1) if OBFUSCATION_RE.search(line)), 1)
        evidence_line = lines[line_number - 1] if lines else ""
        findings.append(Finding("SEC006", "high", rel, line_number, _message("SEC006"), _fingerprint("SEC006", rel, evidence_line)))
    return findings


def _message(rule_id: str) -> str:
    return {
        "SEC001": "Remote content is piped directly to a shell.",
        "SEC002": "Decoded content is passed directly to dynamic execution.",
        "SEC003": "A credential-like value appears hard-coded.",
        "SEC004": "A shell-execution call uses a shell or command pipeline.",
        "SEC005": "Credential-bearing environment access and outbound requests occur in the same file.",
        "SEC006": "Obfuscation and dynamic execution occur in the same file.",
        "SEC007": "A package install lifecycle hook can execute code during installation.",
        "SEC008": "A skill dependency is not pinned to an exact version.",
        "SEC009": "A source symlink is not scanned because it can escape the skills tree.",
        "SEC010": "Bidirectional or unexpected invisible Unicode control requires review.",
    }[rule_id]


def _load_waivers(path: Path, today: date) -> tuple[dict[tuple[str, str, str], str], list[str]]:
    if not path.exists():
        return {}, []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        return {}, [f"cannot read security waivers: {exc}"]
    entries = data.get("waivers", []) if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return {}, ["security waivers must contain a waivers list"]
    allowed: dict[tuple[str, str, str], str] = {}
    errors: list[str] = []
    for index, entry in enumerate(entries):
        label = f"waivers[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be a mapping")
            continue
        rule_id, rel_path, fingerprint = entry.get("rule_id"), entry.get("path"), entry.get("fingerprint")
        reason, expires = entry.get("reason"), entry.get("expires")
        if not all(isinstance(v, str) and v.strip() for v in (rule_id, rel_path, fingerprint, reason)) or not isinstance(expires, (str, date)):
            errors.append(f"{label} requires rule_id, path, fingerprint, reason, and expires")
            continue
        if rule_id not in KNOWN_RULES or Path(rel_path).is_absolute() or ".." in Path(rel_path).parts:
            errors.append(f"{label} has an unknown rule or unsafe path")
            continue
        try:
            expiry = expires if isinstance(expires, date) else date.fromisoformat(expires)
        except ValueError:
            errors.append(f"{label} expires must be YYYY-MM-DD")
            continue
        if expiry < today:
            errors.append(f"{label} is expired ({expires})")
            continue
        key = (rule_id, rel_path, fingerprint)
        if key in allowed:
            errors.append(f"{label} duplicates a waiver")
            continue
        allowed[key] = reason.strip()
    return allowed, errors


def scan(root: Path = ROOT, *, today: date | None = None) -> tuple[list[Finding], list[str]]:
    current_date = today or date.today()
    waivers, errors = _load_waivers(root / "scripts/security/waivers.yaml", current_date)
    findings: list[Finding] = []
    if not (root / "skills").is_dir():
        return findings, errors + ["skills source directory is missing"]
    sources = list(_source_files(root))
    if not any(path.name == "SKILL.md" for path in sources):
        return findings, errors + ["no skill sources were found"]
    for path in sources:
        if path.is_symlink():
            rel = path.relative_to(root).as_posix()
            findings.append(Finding("SEC009", "high", rel, 0, _message("SEC009"), _fingerprint("SEC009", rel, "symlink")))
            continue
        try:
            findings.extend(_scan_file(root, path))
        except ValueError as exc:
            errors.append(str(exc))
    matched_waivers = {(item.rule_id, item.path, item.fingerprint) for item in findings} & set(waivers)
    for key in sorted(set(waivers) - matched_waivers):
        errors.append(f"waiver has no matching finding (stale or fingerprint mismatch): {key[0]} {key[1]}")
    findings = [
        Finding(
            **{
                **asdict(item),
                "suppressed": (item.rule_id, item.path, item.fingerprint) in waivers,
                "suppression_reason": waivers.get((item.rule_id, item.path, item.fingerprint)),
            }
        )
        for item in findings
    ]
    return findings, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Statically scan skill sources; scanned code is never executed.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--report", type=Path, help="write a JSON report to this path")
    args = parser.parse_args()
    findings, errors = scan(args.root.resolve())
    payload = {
        "schema_version": "1.0",
        "scanner": "skill-static-security",
        "scan_scope": list(SCAN_AREAS),
        "execution": "static-only; scanned code was not executed",
        "findings": [asdict(item) for item in findings],
        "errors": errors,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        for error in errors:
            print(f"[BLOCKER] {error}")
        for item in findings:
            state = "SUPPRESSED" if item.suppressed else "FINDING"
            suffix = f" — {item.suppression_reason}" if item.suppression_reason else ""
            print(f"[{state}] {item.severity} {item.rule_id} {item.path}:{item.line} {item.message}{suffix}")
        if not errors and not any(not item.suppressed and item.severity == "high" for item in findings):
            print(f"Skill security scan: OK ({len(findings)} finding(s), all reviewed or below gate)")
    return 1 if errors or any(not item.suppressed and item.severity == "high" for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
