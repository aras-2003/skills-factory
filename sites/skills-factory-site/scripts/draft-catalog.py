"""Explicit source-bound private MCP extension; does not promote draft maturity."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

import yaml


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def add_drafts(source, rows):
    source = Path(source).resolve()
    config = json.loads(Path(__file__).with_name("draft-components.json").read_text())
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    if revision != config["source_revision"]:
        raise ValueError("Draft source must match the reviewed pinned revision")
    if subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=source, text=True).strip():
        raise ValueError("Draft source tracked files must be clean")
    existing = {row["name"] for row in rows}
    original_hashes = {}

    def read(relative):
        path = (source / relative).resolve()
        if not path.is_relative_to(source) or not path.is_file() or {"tests", "evals"}.intersection(path.relative_to(source).parts):
            raise ValueError(f"Unsupported draft runtime reference: {relative}")
        # Reject untracked inputs even when the working tree is otherwise clean.
        subprocess.check_call(["git", "ls-files", "--error-unmatch", str(path.relative_to(source))], cwd=source, stdout=subprocess.DEVNULL)
        text = path.read_text(encoding="utf-8")
        original_hashes[str(path.relative_to(source))] = sha(text)
        return text

    shared = read(config["shared_reference"])

    def portable(text):
        return re.sub(r"(?:\.\./)+docs/architecture/content-to-artifact-contract\.md", "references/content-to-artifact-contract.md", text).replace(
            "workflows/presentation-production/references/canva-connector-contract.md", "references/canva-connector-contract.md"
        ).rstrip()

    drafts = []
    for domain, spec in config["domains"].items():
        workflow = spec["workflow"]
        refs = {"references/" + name: portable(read(f"workflows/{workflow}/references/{name}")) for name in spec["references"]}
        refs["references/content-to-artifact-contract.md"] = shared.rstrip()
        for name in spec["skills"] + [workflow]:
            if name in existing or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
                raise ValueError(f"Duplicate or unsafe draft name: {name}")
            existing.add(name)
            support = dict(refs)
            kind = "workflow" if name == workflow else "skill"
            if kind == "workflow":
                support["references/WORKFLOW.md"] = portable(read(f"workflows/{name}/WORKFLOW.md"))
                fm = {"name": name, "description": spec["description"], "metadata": {"version": "0.1.0", "maturity": "draft"}}
                instructions = "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip() + "\n---\n\n# " + name + "\n\nPrivate MCP draft test entrypoint. Load `references/WORKFLOW.md` and follow it. This enables testing only; model behavior, provider authoring and export checks remain NOT_RUN. Verify callable provider capabilities before artifact actions.\n"
            else:
                instructions = portable(read(f"skills/{domain}/{name}/SKILL.md"))
                fm = yaml.safe_load(instructions.split("---", 2)[1])
                if fm["name"] != name or fm["metadata"]["maturity"] != "draft":
                    raise ValueError(f"Not an explicitly selected draft: {name}")
            instructions = instructions.rstrip()
            surface = {"SKILL.md": instructions, **support}
            digest = hashlib.sha256()
            for path, content in sorted(surface.items()):
                digest.update(path.encode() + b"\0" + content.encode() + b"\0")
            drafts.append({"name": name, "domain": domain, "kind": kind, "description": fm["description"], "version": str(fm["metadata"]["version"]), "maturity": "draft", "content_sha256": digest.hexdigest(), "instruction_sha256": sha(instructions), "instructions": instructions, "reference_files": support})
    if len(drafts) != 12:
        raise ValueError("Expected exactly 12 explicitly approved private test drafts")
    rows.extend(drafts)
    return {"channel": "private-mcp-draft-test", "source_revision": revision, "component_count": len(drafts), "components": [row["name"] for row in drafts], "model_campaign": "NOT_RUN", "source_files_sha256": original_hashes}
