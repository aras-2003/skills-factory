"""ARC-05 OAF source extraction, evidence, semantics and impact tests."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.architecture.oaf_architecture_explorer import (
    SOURCE, coverage, extract_model, traverse,
)
from scripts.architecture.visualization_ir import verify_sources

FIXTURE = """# Fixture

## Scenario

Extract:
- Customer Management
  - Customer Onboarding
  - CRM Team
  - Customer Service Process
  - Customer Data Platform
- Payments
  - Payment Processing
  - Fraud Management
  - Payment Operations
- Data & Analytics
  - Reporting
  - Data Governance
  - Power BI
  - Advanced Analytics

Leadership wants to review the map.
Known evidence:
- ownership is incomplete;
"""


class OAFArchitectureExplorerTests(unittest.TestCase):
    def make_repo(self, directory):
        root = Path(directory)
        (root / SOURCE).parent.mkdir(parents=True)
        (root / SOURCE).write_text(FIXTURE, encoding="utf-8")
        def git(*args):
            return subprocess.check_output(
                ["git", "-C", directory, *args], stderr=subprocess.DEVNULL
            ).decode().strip()
        git("init", "-q")
        git("config", "user.name", "Fixture")
        git("config", "user.email", "fixture@example.invalid")
        git("add", ".")
        git("commit", "-qm", "fixture")
        return root, git("rev-parse", "HEAD")

    def test_extracts_typed_map_entries_and_exact_git_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root, revision = self.make_repo(directory)
            model = extract_model(root, revision)
            by_label = {node["label"]: node for node in model["nodes"]}
            self.assertEqual(by_label["CRM Team"]["type"], "owner")
            self.assertEqual(by_label["Customer Service Process"]["type"], "process")
            self.assertEqual(by_label["Customer Data Platform"]["type"], "application")
            self.assertEqual(by_label["Power BI"]["type"], "application")
            self.assertEqual(by_label["Payments"]["type"], "capability")
            self.assertTrue(all(ref["revision"] == revision
                                for node in model["nodes"] for ref in node["evidence"]))
            self.assertEqual(verify_sources(model, root)["source_revision"], revision)

    def test_hierarchy_is_explicit_and_unknown_links_do_not_claim_impact(self):
        with tempfile.TemporaryDirectory() as directory:
            root, revision = self.make_repo(directory)
            model = extract_model(root, revision)
            by_label = {node["label"]: node["id"] for node in model["nodes"]}
            reached = traverse(model, by_label["Customer Management"])
            self.assertIn(by_label["Customer Onboarding"], reached)
            self.assertIn(by_label["Customer Data Platform"], reached)
            self.assertNotIn("unknown:application-owners", reached)
            self.assertTrue(any(edge["type"] == "unknown" and edge["state"] == "unknown"
                                for edge in model["edges"]))

    def test_missing_layers_and_target_state_are_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            root, revision = self.make_repo(directory)
            summary = coverage(extract_model(root, revision))
            self.assertEqual(summary["source_kind"],
                             "synthetic evaluation fixture, not an organization's verified EA repository")
            self.assertEqual(summary["as_is"], "capability-map fixture contents only")
            self.assertEqual(summary["to_be"], "NOT_SUPPLIED")
            self.assertEqual(summary["entity_counts"]["data"], 0)
            self.assertIn("unknown:data-lineage", summary["unresolved"])
            self.assertIn("unknown:to-be", summary["unresolved"])

    def test_bad_revision_and_unsupported_nesting_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root, revision = self.make_repo(directory)
            with self.assertRaises(ValueError):
                extract_model(root, "main")
            path = root / SOURCE
            path.write_text(FIXTURE.replace("  - CRM Team", "    - CRM Team"), encoding="utf-8")
            with self.assertRaises(ValueError):
                extract_model(root, revision)


if __name__ == "__main__":
    unittest.main()
