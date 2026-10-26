from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.catalog.generate_site_catalog import build_catalog, collect_workflow_sources  # noqa: E402
from scripts.catalog.sync_cloud_catalog import build_snapshot  # noqa: E402


class SiteCatalogContractTests(unittest.TestCase):
    def workflow_registry(self) -> str:
        return (ROOT / "workflows/runtime-registry.yaml").read_text(encoding="utf-8")

    def capability_contract(self) -> str:
        return (ROOT / "release/capability-contract.yaml").read_text(encoding="utf-8")

    def workflow_sources(self) -> dict[str, str]:
        return collect_workflow_sources(ROOT)

    def test_generated_catalog_carries_package_versions_and_source_identity(self) -> None:
        markdown = (ROOT / "CATALOG.md").read_text(encoding="utf-8")
        package_manifest = (ROOT / "release/package.yaml").read_text(encoding="utf-8")
        catalog = build_catalog(markdown, package_manifest, "abcdef1234567890", self.workflow_registry(), self.capability_contract(), self.workflow_sources())

        self.assertEqual("abcdef123456", catalog["metadata"]["source_revision"])
        self.assertEqual("skills-factory", catalog["metadata"]["packages"]["production"]["name"])
        self.assertEqual("skills-factory-lab", catalog["metadata"]["packages"]["lab"]["name"])
        self.assertTrue(catalog["metadata"]["packages"]["production"]["version"])
        self.assertTrue(catalog["metadata"]["packages"]["lab"]["version"])
        self.assertTrue(catalog["skills"])
        self.assertTrue(catalog["workflows"])
        self.assertEqual(len(self.workflow_sources()), catalog["metadata"]["source_workflow_count"])
        self.assertEqual(19, catalog["metadata"]["registered_workflow_count"])
        skill_development = next(item for item in catalog["workflows"] if item["name"] == "skill-development")
        self.assertEqual("registered", skill_development["runtime_registration"])
        self.assertEqual("draft", skill_development["maturity"])
        self.assertEqual({"lab": "supported", "plugin": "unavailable", "chatgpt-zip": "unavailable"}, skill_development["declared_channels"])
        presentation = next(item for item in catalog["workflows"] if item["name"] == "presentation-production")
        self.assertEqual("registered", presentation["runtime_registration"])
        self.assertEqual("draft", presentation["maturity"])
        self.assertEqual({"lab": "supported", "plugin": "unavailable", "chatgpt-zip": "unavailable"}, presentation["declared_channels"])
        report_production = next(item for item in catalog["workflows"] if item["name"] == "report-production")
        self.assertEqual("registered", report_production["runtime_registration"])
        self.assertEqual("draft", report_production["maturity"])
        self.assertEqual({"lab": "supported", "plugin": "unavailable", "chatgpt-zip": "unavailable"}, report_production["declared_channels"])
        self.assertEqual("PARTIALLY_DECLARED", catalog["metadata"]["capability_assessment"])
        self.assertTrue(any(item["capability_assessment"] != "UNASSESSED" for item in catalog["skills"]))
        self.assertTrue(all(item["declared_channels"] for item in catalog["workflows"] if item["runtime_registration"] == "registered"))
        self.assertEqual("NOT_OBSERVED", catalog["metadata"]["runtime_installation"])

    def test_site_catalog_does_not_promote_partial_capability_declaration(self) -> None:
        markdown = ("| Skill | Domain | Maturity | Version | Description | Source |\n"
                    "|---|---|---|---|---|---|\n"
                    "| example | meta | draft | 0.1.0 | Example | skills/meta/example/SKILL.md |\n")
        manifest = 'package:\n  name: skills-factory\n  version: "1.0"\nlab:\n  name: skills-factory-lab\n  version: "1.0"\n'
        contract = (
            "contract_id: repository-side-v1\n"
            "component_declarations:\n  example:\n    requirements:\n"
            "      network: none\n      filesystem: none\n"
            "      shell_exec: none\n      credentials: unassessed\n"
            "      external_actions: none\n"
        )
        catalog = build_catalog(markdown, manifest, "revision", capability_contract=contract)
        self.assertEqual("UNASSESSED", catalog["skills"][0]["capability_assessment"])
        self.assertEqual("UNASSESSED", catalog["metadata"]["capability_assessment"])

        invalid_contract = contract.replace("external_actions: none", "unexpected_dimension: none")
        invalid = build_catalog(markdown, manifest, "revision", capability_contract=invalid_contract)
        self.assertEqual("UNASSESSED", invalid["skills"][0]["capability_assessment"])

    def test_catalog_rejects_missing_package_or_revision_provenance(self) -> None:
        markdown = """| Skill | Domain | Maturity | Version | Description | Source |
|---|---|---|---|---|---|
| sample | meta | draft | 0.1.0 | Example | skills/meta/sample/SKILL.md |
"""
        valid_manifest = """package:
  name: skills-factory
  version: "1.0.0"
lab:
  name: skills-factory-lab
  version: "0.1.0"
"""

        with self.assertRaisesRegex(ValueError, "Source revision"):
            build_catalog(markdown, valid_manifest, " ")
        with self.assertRaisesRegex(ValueError, "Missing lab"):
            build_catalog(markdown, """package:
  name: skills-factory
  version: "1.0.0"
""", "abc")

    def test_published_catalog_versions_match_package_source(self) -> None:
        markdown = (ROOT / "CATALOG.md").read_text(encoding="utf-8")
        package_manifest = (ROOT / "release/package.yaml").read_text(encoding="utf-8")
        source_catalog = build_catalog(markdown, package_manifest, "revision", self.workflow_registry(), self.capability_contract(), self.workflow_sources())
        published = json.loads((ROOT / "docs/catalog.json").read_text(encoding="utf-8"))

        self.assertEqual(source_catalog["metadata"]["packages"], published["metadata"]["packages"])
        self.assertEqual(source_catalog["skills"], published["skills"])
        self.assertEqual(source_catalog["workflows"], published["workflows"])
        self.assertTrue(published["metadata"]["source_revision"])
        by_name = {skill["name"]: skill for skill in published["skills"]}
        for name, version in (
            ("skill-evaluation", "0.3.5"),
            ("skill-release-review", "0.3.0"),
            ("skill-test-design", "0.3.1"),
        ):
            self.assertEqual(version, by_name[name]["version"])
            self.assertEqual("draft", by_name[name]["maturity"])

    def test_default_page_is_area_first_and_discloses_versions(self) -> None:
        page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        for marker in (
            'data-view="areas" aria-pressed="true"',
            'id="areas-view"',
            'id="source-versions"',
            'id="source-revision"',
            'data-view="catalog"',
            "./processes.json",
            'id="area-cards"',
            "area-status-bar",
            "area-flows",
            "Pokaż ścieżki",
            "Production",
            "Candidate",
            "Draft",
        ):
            self.assertIn(marker, page)

    def test_site_lab_receipt_has_source_bound_identity(self) -> None:
        receipt = json.loads((ROOT / "docs/lab-release.json").read_text(encoding="utf-8"))
        # Pages publishes the last verified immutable Lab build receipt. The
        # checked-in plugin snapshot can intentionally lag that independent build.
        self.assertEqual("lab", receipt["channel"])
        self.assertRegex(receipt["source_revision"], r"^[0-9a-f]{40}$")
        self.assertRegex(receipt["payload_content_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(f"{receipt['version']}+{receipt['source_revision'][:12]}", receipt["release_id"])
        catalog = json.loads((ROOT / "docs/catalog.json").read_text(encoding="utf-8"))
        expected_components = {item["name"] for item in catalog["skills"] + catalog["workflows"]}
        actual_components = {item["name"] for item in receipt["components"]}
        self.assertEqual(expected_components, actual_components)
        manifest = json.loads((ROOT / "plugins/skills-factory-lab/release-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest, receipt)

    def test_private_mcp_receipt_describes_observed_deployment_independently_of_candidate(self) -> None:
        receipt = json.loads((ROOT / "docs/cloud-release.json").read_text(encoding="utf-8"))
        catalog = json.loads((ROOT / "docs/catalog.json").read_text(encoding="utf-8"))
        lab = json.loads((ROOT / "docs/lab-release.json").read_text(encoding="utf-8"))
        source_names = {item["name"] for item in catalog["skills"] + catalog["workflows"]}
        current_lab_names = {item["name"] for item in lab["components"]}
        observed_names = {item["name"] for item in receipt["catalog_entries"]}
        drafts = (receipt.get("draft_extension") or {}).get("components", [])
        # This receipt describes an observed deployment, not an automatic
        # promotion whenever the candidate Lab manifest changes.
        self.assertEqual("verified", receipt["attestation_status"])
        self.assertRegex(receipt["site_source_revision"], r"^[a-f0-9]{40}$")
        self.assertEqual(len(drafts), len(set(drafts)))
        self.assertTrue(set(drafts) <= source_names)
        self.assertEqual(receipt["lab_release"]["skill_count"] + len(drafts), receipt["runtime_release"]["skill_count"])
        self.assertEqual(receipt["runtime_release"]["skill_count"], len(observed_names))
        self.assertTrue(observed_names <= source_names)
        if not drafts:
            self.assertEqual(receipt["lab_release"]["catalog_digest"], receipt["runtime_release"]["catalog_digest"])
            self.assertEqual("complete_lab", receipt["runtime_release"]["artifact_scope"])
        if lab["source_revision"] == receipt["lab_release"]["source_revision"]:
            self.assertEqual(current_lab_names, observed_names - set(drafts))
            self.assertEqual(lab["version"], receipt["lab_release"]["version"])
        self.assertTrue(set(drafts) <= current_lab_names)
        self.assertTrue({"skill-development", "presentation-production", "report-production"} <= current_lab_names)
        self.assertEqual("NOT_RUN", receipt["checks"]["model_campaign"])
        entries = receipt["catalog_entries"]
        self.assertEqual(receipt["runtime_release"]["skill_count"], len(entries))
        self.assertEqual(receipt["runtime_release"]["skill_count"], sum(entry["kind"] in {"skill", "workflow"} for entry in entries))
        self.assertTrue(all(entry["domain"] for entry in entries))

    def test_runtime_snapshot_rejects_unverified_mismatched_or_duplicate_catalogs(self) -> None:
        import copy
        receipt = json.loads((ROOT / "docs/cloud-release.json").read_text())
        source = json.loads((ROOT / "docs/catalog.json").read_text())
        runtime = {"attestation_status": "verified", "source_revision": receipt["site_source_revision"], "runtime_release": receipt["runtime_release"]}
        catalog = {"skills": receipt["catalog_entries"], "skill_count": len(receipt["catalog_entries"]), "catalog_digest": receipt["runtime_release"]["catalog_digest"], "source_revision": receipt["runtime_release"]["source_revision"], "tool_receipt": {"source_revision": runtime["source_revision"], "completed_at": receipt["catalog_observed_at"], "output_sha256": receipt["catalog_receipt_sha256"]}}
        snapshot = build_snapshot(runtime, catalog, source)
        self.assertEqual(catalog["skills"], snapshot["catalog_entries"])
        for mutate in (
            lambda r, c: r.update(attestation_status="unattested"),
            lambda r, c: c["tool_receipt"].update(source_revision="different"),
            lambda r, c: c["skills"].append(c["skills"][0]),
            lambda r, c: c.update(catalog_digest="invalid"),
            lambda r, c: c["skills"][0].update(kind="invented"),
        ):
            r, c = copy.deepcopy(runtime), copy.deepcopy(catalog)
            mutate(r, c)
            with self.assertRaises(ValueError):
                build_snapshot(r, c, source)

    def test_hero_counts_actual_runtime_entries_instead_of_source_files(self) -> None:
        page = (ROOT / "docs/index.html").read_text()
        self.assertIn('pozycji w MCP', page)
        self.assertIn('id="runtime-breakdown"', page)
        self.assertIn('new Set(entries.map(entry=>entry.domain)).size', page)
        self.assertIn('state.runtimeEntries=release.catalog_entries', page)
        self.assertNotIn('document.querySelector("#total-count").textContent=state.skills.length', page)

    def test_new_domains_have_named_areas_and_complete_pathways(self) -> None:
        page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        catalog = json.loads((ROOT / "docs/catalog.json").read_text(encoding="utf-8"))
        processes = json.loads((ROOT / "docs/processes.json").read_text(encoding="utf-8"))
        for name in ("Prezentacje i narracja", "Raporty i dokumenty", 'data-view="workflows"', 'id="workflow-search"'):
            self.assertIn(name, page)
        for domain in ("presentations", "reports"):
            expected = {skill["name"] for skill in catalog["skills"] if skill["domain"] == domain}
            paths = [p for p in processes["processes"] if p["domain"] == domain]
            self.assertTrue(paths)
            actual = {name for p in paths for lane in p["lanes"] for step in lane["steps"] for name in step.get("skills", []) + step.get("optionalSkills", [])}
            self.assertTrue(expected <= actual)
            self.assertTrue(all(p["maturity"] == "draft" for p in paths))

    def test_new_domain_icons_use_local_transparent_assets(self) -> None:
        page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        self.assertIn('./assets/domain-icons.svg', page)
        for domain in ("presentations", "reports"):
            path = ROOT / "docs/assets" / f"{domain}.png"
            data = path.read_bytes()
            self.assertIn(f'./assets/{domain}.png', page)
            self.assertEqual(b"\x89PNG\r\n\x1a\n", data[:8])
            self.assertEqual(6, data[25], "new icons must preserve RGBA transparency")
            self.assertLess(len(data), 2_000_000)

    def test_web_design_candidate_has_a_local_domain_label_and_icon(self) -> None:
        page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        icon = ROOT / "docs/assets/web-design.svg"
        self.assertIn('web-design:"Projektowanie interfejsów"', page)
        self.assertIn('.icon-web-design{background-image:url("./assets/web-design.svg")', page)
        self.assertTrue(icon.is_file())
        self.assertIn("<svg", icon.read_text(encoding="utf-8"))

    def test_lab_packager_uploads_candidate_and_opens_validated_marketplace_pr(self) -> None:
        workflow = (ROOT / ".github/workflows/release-lab-plugin.yml").read_text(encoding="utf-8")
        self.assertIn("cp plugins/skills-factory-lab/release-manifest.json docs/lab-release.json", workflow)
        self.assertIn("actions/upload-artifact@", workflow)
        self.assertIn("include-hidden-files: true", workflow)
        self.assertIn("name: skills-factory-lab-${{ github.sha }}", workflow)
        self.assertNotIn("Bump Lab package patch version", workflow)
        self.assertIn("--lab-artifact plugins/skills-factory-lab --write-generated", workflow)
        self.assertIn("name: skills-factory-site-${{ github.sha }}", workflow)
        self.assertIn("git add plugins/skills-factory-lab docs/lab-release.json", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("pull-requests: write", workflow)
        self.assertIn("actions: write", workflow)
        self.assertIn('branch="automation/lab-marketplace-$SOURCE_REVISION"', workflow)
        self.assertIn('git push origin "HEAD:refs/heads/$branch"', workflow)
        self.assertIn('gh pr create --base main --head "$branch"', workflow)
        self.assertIn('gh workflow run ci-validate.yml --ref "$branch"', workflow)
        self.assertIn('gh workflow run ci-domain-integrity.yml --ref "$branch"', workflow)
        self.assertIn('current_main="$(git ls-remote origin refs/heads/main | cut -f1)"', workflow)
        self.assertNotIn("HEAD:refs/heads/main", workflow)
        self.assertNotIn('      - "release/package.yaml"', workflow)
        self.assertIn('"plugins/skills-factory-lab/**"', workflow)
        self.assertIn('"docs/lab-release.json"', workflow)

    def test_page_distinguishes_catalog_revision_from_lab_build_revision(self) -> None:
        page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        self.assertIn('id="source-revision"', page)
        self.assertIn('id="lab-source-revision"', page)
        self.assertIn('id="lab-release-link"', page)
        self.assertIn('fetch("./lab-release.json")', page)

    def test_process_data_has_domain_scoped_flows(self) -> None:
        catalog = json.loads((ROOT / "docs/catalog.json").read_text(encoding="utf-8"))
        processes = json.loads((ROOT / "docs/processes.json").read_text(encoding="utf-8"))
        domains = {skill["domain"] for skill in catalog["skills"]}
        flow_domains = {flow["domain"] for flow in processes["processes"]}

        self.assertTrue(domains)
        self.assertTrue(flow_domains)
        self.assertTrue(flow_domains <= domains)
        for process in processes["processes"]:
            self.assertTrue(process["title"])
            self.assertTrue(process["lanes"])


if __name__ == "__main__":
    unittest.main()
