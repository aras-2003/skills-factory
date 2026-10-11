from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.catalog.generate_site_catalog import build_catalog, collect_workflow_sources  # noqa: E402


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
        self.assertEqual(16, catalog["metadata"]["registered_workflow_count"])
        skill_development = next(item for item in catalog["workflows"] if item["name"] == "skill-development")
        self.assertEqual("not_registered", skill_development["runtime_registration"])
        self.assertEqual("unknown", skill_development["maturity"])
        presentation = next(item for item in catalog["workflows"] if item["name"] == "presentation-production")
        self.assertEqual("not_registered", presentation["runtime_registration"])
        self.assertEqual({}, presentation["declared_channels"])
        report_production = next(item for item in catalog["workflows"] if item["name"] == "report-production")
        self.assertEqual("not_registered", report_production["runtime_registration"])
        self.assertEqual({}, report_production["declared_channels"])
        self.assertEqual("UNASSESSED", catalog["metadata"]["capability_assessment"])
        self.assertTrue(all(item["capability_assessment"] == "UNASSESSED" for item in catalog["skills"]))
        self.assertTrue(all(item["declared_channels"] for item in catalog["workflows"] if item["runtime_registration"] == "registered"))
        self.assertEqual({}, skill_development["declared_channels"])
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
            ("skill-evaluation", "0.3.4"),
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

    def test_site_lab_receipt_matches_the_exact_packaged_lab_identity(self) -> None:
        receipt = json.loads((ROOT / "docs/lab-release.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "plugins/skills-factory-lab/release-manifest.json").read_text(encoding="utf-8"))
        for field in ("channel", "version", "release_id", "source_revision", "payload_content_sha256"):
            self.assertEqual(manifest[field], receipt[field], field)
        self.assertEqual("lab", receipt["channel"])

    def test_lab_packager_uploads_an_immutable_candidate_without_branch_writes(self) -> None:
        workflow = (ROOT / ".github/workflows/package-main-lab-plugin.yml").read_text(encoding="utf-8")
        self.assertIn("cp plugins/skills-factory-lab/release-manifest.json docs/lab-release.json", workflow)
        self.assertIn("actions/upload-artifact@", workflow)
        self.assertIn("include-hidden-files: true", workflow)
        self.assertIn("name: skills-factory-lab-${{ github.sha }}", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn('"plugins/skills-factory-lab/**"', workflow)
        self.assertIn('"docs/lab-release.json"', workflow)
        self.assertNotIn("git push", workflow)
        self.assertNotIn("contents: write", workflow)

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
