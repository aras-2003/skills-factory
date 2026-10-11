"""Publish public-safe catalog metadata from observed MCP tool outputs."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def build_snapshot(runtime, catalog, source):
    if runtime.get("attestation_status") != "verified":
        raise ValueError("MCP identity must be verified")
    if catalog.get("tool_receipt", {}).get("source_revision") != runtime["source_revision"]:
        raise ValueError("Catalog receipt and deployed Site revision differ")
    if catalog.get("source_revision") != runtime["runtime_release"]["source_revision"]:
        raise ValueError("Embedded source revisions differ")
    entries = catalog.get("skills") or []
    if not entries or len(entries) != catalog["skill_count"]:
        raise ValueError("Runtime entry count mismatch")
    names = [entry["name"] for entry in entries]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate MCP entry names")
    digest = hashlib.sha256("\n".join(f"{item['name']}:{item['content_sha256']}" for item in sorted(entries, key=lambda item: item["name"])).encode()).hexdigest()
    if digest != catalog["catalog_digest"] or digest != runtime["runtime_release"]["catalog_digest"]:
        raise ValueError("Catalog content digest mismatch")
    domains = {item["name"]: item["domain"] for item in source["skills"]}
    workflows = {item["name"] for item in source["workflows"]}
    prefixes = {"presentation-": "presentations", "report-": "reports", "investment-": "investing", "commerce-": "commerce", "oaf-": "oaf", "skill-": "meta"}
    public = []
    for entry in entries:
        name, kind = entry["name"], entry["kind"]
        if kind == "skill" and name in domains:
            domain = domains[name]
        elif kind == "workflow" and name in workflows:
            domain = next((domain for prefix, domain in prefixes.items() if name.startswith(prefix)), None)
            if domain is None:
                raise ValueError(f"Missing source domain for {name}")
        else:
            raise ValueError(f"Unmapped runtime component: {name}")
        public.append({key: entry[key] for key in ("name", "kind", "version", "maturity", "content_sha256")} | {"domain": domain})
    return {"catalog_observed_at": catalog["tool_receipt"]["completed_at"], "catalog_receipt_sha256": catalog["tool_receipt"]["output_sha256"], "catalog_entries": public}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads((ROOT / "docs/catalog.json").read_text())
    runtime = json.loads(args.runtime.read_text())
    catalog = json.loads(args.catalog.read_text())
    snapshot = build_snapshot(runtime, catalog, source)
    path = ROOT / "docs/cloud-release.json"
    receipt = json.loads(path.read_text())
    if receipt["site_source_revision"] != runtime["source_revision"]:
        raise ValueError("Refresh the verified deployment receipt before syncing its catalog")
    receipt.update(snapshot)
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(f"Published {len(snapshot['catalog_entries'])} observed MCP entries")


if __name__ == "__main__":
    main()
