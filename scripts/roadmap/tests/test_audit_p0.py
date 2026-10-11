import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "audit_p0.py"
spec = importlib.util.spec_from_file_location("audit_p0", MODULE)
audit_p0 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_p0)

class AuditP0Tests(unittest.TestCase):
    def test_valid_preserves_unverified(self):
        errors, rows = audit_p0.audit({"items": [
            {"id": "A", "priority": "P0", "depends_on": ["B"]},
            {"id": "B", "priority": "P1", "depends_on": []}]})
        self.assertEqual(errors, [])
        self.assertEqual(rows[0]["evidence_state"], "UNVERIFIED")

    def test_unknown_dependency(self):
        errors, _ = audit_p0.audit({"items": [
            {"id": "A", "priority": "P0", "depends_on": ["MISSING"]}]})
        self.assertTrue(any("unknown dependency" in x for x in errors))

    def test_cycle_through_p1(self):
        errors, _ = audit_p0.audit({"items": [
            {"id": "A", "priority": "P0", "depends_on": ["B"]},
            {"id": "B", "priority": "P1", "depends_on": ["A"]}]})
        self.assertTrue(any("dependency cycle" in x for x in errors))

    def test_duplicate_and_self_dependency(self):
        errors, _ = audit_p0.audit({"items": [
            {"id": "A", "priority": "P0", "depends_on": ["A"]},
            {"id": "A", "priority": "P0", "depends_on": []}]})
        self.assertTrue(any("duplicate id" in x for x in errors))
        self.assertTrue(any("self dependency" in x for x in errors))

    def test_malformed_transitive_dependency_is_reported(self):
        errors, rows = audit_p0.audit({"items": [
            {"id": "A", "priority": "P0", "depends_on": ["B"]},
            {"id": "B", "priority": "P1", "depends_on": "not-a-list"}]})
        self.assertEqual(len(rows), 1)
        self.assertTrue(any("depends_on is not a list" in x for x in errors))
