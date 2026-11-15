from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from xml.parsers import expat
from pathlib import Path

from common import repo_root_from, split_frontmatter

ROOT = "skill_instructions"
ORDER = (
    "purpose",
    "guidelines",
    "steps",
    "decision_rules",
    "input_context",
    "output_contract",
    "failure_handling",
    "quality_checks",
    "examples",
    "references",
)
REQUIRED = {"purpose", "guidelines", "steps", "output_contract", "failure_handling"}
ALLOWED = set(ORDER)
PLACEHOLDER = re.compile(r"(?:\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b|lorem ipsum|\.{3,})", re.I)


class XmlValidationError(ValueError):
    pass


def _fail(path: str, line: int, message: str) -> None:
    raise XmlValidationError(f"{path}:{line}: {message}")


def validate_xml_body(body: str, path: str = "<body>") -> None:
    if len(body.encode("utf-8")) > 256_000:
        _fail(path, 1, "XML body exceeds the 256 KB limit")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)", body, re.I):
        line = body[:re.search(r"<!\s*(?:DOCTYPE|ENTITY)", body, re.I).start()].count("\n") + 1
        _fail(path, line, "DOCTYPE and ENTITY declarations are not allowed")
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        line = exc.position[0] if exc.position else 1
        _fail(path, line, f"malformed XML: {exc}")
    if root.tag != ROOT:
        _fail(path, 1, f"root element must be <{ROOT}>")
    if root.attrib != {"version": "1.0"}:
        _fail(path, 1, '<skill_instructions> requires only version="1.0"')
    source_lines: list[int] = []
    line_parser = expat.ParserCreate()
    line_parser.StartElementHandler = lambda _name, _attrs: source_lines.append(line_parser.CurrentLineNumber)
    line_parser.Parse(body, True)
    line_by_element = {
        id(element): line
        for element, line in zip(root.iter(), source_lines, strict=True)
    }

    def line_of(el: ET.Element) -> int:
        return line_by_element.get(id(el), 1)

    if root.text and root.text.strip():
        _fail(path, 1, f"<{ROOT}> must contain only its defined child sections")
    if len(root) > 32:
        _fail(path, 1, "too many top-level sections (maximum 32)")
    tags = [child.tag for child in root]
    seen: set[str] = set()
    for child in root:
        if child.tag not in ALLOWED:
            _fail(path, line_of(child), f"unknown top-level section <{child.tag}>")
        if child.tag in seen:
            _fail(path, line_of(child), f"duplicate top-level section <{child.tag}>")
        seen.add(child.tag)
    for tag in REQUIRED:
        if tags.count(tag) != 1:
            _fail(path, 1, f"required section <{tag}> must appear exactly once")
    expected_order = [tag for tag in ORDER if tag in tags]
    if tags != expected_order:
        _fail(path, 1, "sections are out of order; use the order shown in the grammar")

    def substantive(
        el: ET.Element, line: int | None = None, allowed_attributes: set[str] | None = None
    ) -> None:
        line = line or line_of(el)
        expected_attributes = allowed_attributes or set()
        if set(el.attrib) != expected_attributes:
            _fail(path, line, f"<{el.tag}> requires attributes {sorted(expected_attributes)}")
        if len(el):
            _fail(path, line, f"<{el.tag}> must contain text, not nested elements")
        text = (el.text or "").strip()
        if not text or PLACEHOLDER.search(text):
            _fail(path, line, f"<{el.tag}> must contain meaningful text, not be empty or a placeholder")

    for section in root:
        section_line = line_of(section)
        if section.tail and section.tail.strip():
            _fail(path, section_line, f"text is not allowed between top-level sections after <{section.tag}>")
        if section.attrib:
            _fail(path, section_line, f"<{section.tag}> does not allow attributes")
        if section.tag in {"guidelines", "steps", "decision_rules", "input_context", "quality_checks", "examples", "references"} and section.text and section.text.strip():
            _fail(path, section_line, f"<{section.tag}> must contain only its defined child elements")
        if section.tag in {"purpose", "output_contract", "failure_handling"}:
            substantive(section)
        elif section.tag in {"guidelines", "quality_checks"}:
            item_tag = "guideline" if section.tag == "guidelines" else "check"
            if len(section) == 0 or any(item.tag != item_tag or item.attrib for item in section):
                _fail(path, section_line, f"<{section.tag}> must contain one or more plain <{item_tag}> elements")
            for item in section:
                substantive(item)
        elif section.tag == "steps":
            if len(section) == 0 or any(item.tag != "step" or set(item.attrib) != {"id"} for item in section):
                _fail(path, section_line, "<steps> must contain one or more <step id=\"S1\"> elements")
            ids = [item.get("id", "") for item in section]
            if len(set(ids)) != len(ids) or any(not re.fullmatch(r"S[1-9][0-9]*", value) for value in ids):
                _fail(path, section_line, "step IDs must be unique and use S1, S2, …")
            for item in section:
                substantive(item, allowed_attributes={"id"})
        elif section.tag == "decision_rules":
            if len(section) == 0 or any(item.tag != "rule" or set(item.attrib) != {"id"} for item in section):
                _fail(path, section_line, "<decision_rules> must contain one or more <rule id=\"D1\"> elements")
            ids = [item.get("id", "") for item in section]
            if len(set(ids)) != len(ids) or any(not re.fullmatch(r"D[1-9][0-9]*", value) for value in ids):
                _fail(path, section_line, "rule IDs must be unique and use D1, D2, …")
            for rule in section:
                if rule.text and rule.text.strip():
                    _fail(path, line_of(rule), "<rule> must contain only its defined child elements")
                children = [child.tag for child in rule]
                if children not in (["when", "action"], ["when", "action", "otherwise"]):
                    _fail(path, line_of(rule), "each <rule> needs <when>, <action>, and optional <otherwise>, in that order")
                for child in rule:
                    substantive(child)
        elif section.tag == "input_context":
            if len(section) == 0 or any(item.tag != "field" for item in section):
                _fail(path, section_line, "<input_context> must contain one or more <field> elements")
            names: set[str] = set()
            for field in section:
                if set(field.attrib) != {"name", "type", "required", "trust"}:
                    _fail(path, line_of(field), "each <field> needs name, type, required, and trust attributes")
                name = field.get("name", "")
                if not re.fullmatch(r"[a-z][a-z0-9_]*", name) or name in names:
                    _fail(path, line_of(field), "field names must be unique snake_case identifiers")
                names.add(name)
                if field.get("type") not in {"text", "string", "integer", "number", "boolean", "date", "url", "json"}:
                    _fail(path, line_of(field), f"field {name!r} has an unsupported type")
                if field.get("required") not in {"true", "false"} or field.get("trust") not in {"trusted", "untrusted"}:
                    _fail(path, line_of(field), f"field {name!r} requires required=true|false and trust=trusted|untrusted")
                substantive(field, allowed_attributes={"name", "type", "required", "trust"})
        elif section.tag == "examples":
            if len(section) == 0 or any(item.tag != "example" or set(item.attrib) != {"id"} for item in section):
                _fail(path, section_line, "<examples> must contain one or more <example id=\"E1\"> elements")
            ids = [item.get("id", "") for item in section]
            if len(set(ids)) != len(ids) or any(not re.fullmatch(r"E[1-9][0-9]*", value) for value in ids):
                _fail(path, section_line, "example IDs must be unique and use E1, E2, …")
            for example in section:
                if example.text and example.text.strip():
                    _fail(path, line_of(example), "<example> must contain only its defined child elements")
                children = list(example)
                if [child.tag for child in children] != ["input", "expected_behavior", "expected_output"]:
                    _fail(path, line_of(example), "each <example> needs input, expected_behavior, expected_output in order")
                if set(children[0].attrib) != {"trust"} or children[0].get("trust") not in {"trusted", "untrusted"}:
                    _fail(path, line_of(children[0]), "<input> requires trust=trusted or trust=untrusted")
                for child in children:
                    substantive(child, allowed_attributes={"trust"} if child.tag == "input" else set())
        elif section.tag == "references":
            if len(section) == 0 or any(item.tag != "reference" or set(item.attrib) != {"href"} for item in section):
                _fail(path, section_line, "<references> must contain one or more <reference href=\"…\"> elements")
            for item in section:
                if not item.get("href", "").strip():
                    _fail(path, line_of(item), "reference href must not be empty")
                substantive(item, allowed_attributes={"href"})


def validate_skill_file(path: Path) -> None:
    try:
        _, body = split_frontmatter(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise XmlValidationError(f"{path}:1: invalid YAML frontmatter: {exc}") from exc
    validate_xml_body(body, str(path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a skill's XML instruction body")
    parser.add_argument("paths", nargs="*", help="SKILL.md files; defaults to the authoring template")
    args = parser.parse_args()
    root = repo_root_from(__file__)
    paths = [Path(value) for value in args.paths] if args.paths else [root / "templates/skill-template/SKILL.md"]
    errors = 0
    for path in paths:
        try:
            validate_skill_file(path)
            print(f"[PASS] {path}: valid skill XML 1.0")
        except (OSError, XmlValidationError) as exc:
            print(f"[BLOCKER] {exc}")
            errors += 1
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
