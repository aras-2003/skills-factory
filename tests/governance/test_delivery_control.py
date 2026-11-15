import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("delivery_control", Path(__file__).resolve().parents[2] / "scripts/governance/delivery_control.py")
control = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(control)


class DeliveryTests(unittest.TestCase):
    def test_two_independent_packages_are_allowed_without_iteration_lock(self):
        items = [{"id": "a", "status": "In progress"}, {"id": "b", "status": "Ready"}]
        self.assertEqual("PASS", control.check_wip(items, starting_item="b")["status"])
        self.assertEqual("BLOCKED", control.check_wip(items + [{"id": "c", "status": "In review"}], starting_item="b")["status"])

    def test_parked_and_verification_do_not_hold_development_slots(self):
        items = [{"id": "a", "status": "In progress", "blocked": True},
                 {"id": "b", "status": "Verification"}, {"id": "c", "status": "In review"}]
        self.assertEqual(1, control.check_wip(items)["development_wip"])
        self.assertEqual(1, control.check_wip(items, starting_item="c")["development_wip"])

    def test_unknown_native_stage_is_not_silently_treated_as_done(self):
        with self.assertRaises(ValueError):
            control.check_wip([{"id": "a", "status": "Validation"}])

    def test_pagination_preserves_all_project_items(self):
        cursors = []
        def gql(query, variables):
            cursors.append(variables["cursor"])
            page = len(cursors)
            node = {"id": str(page), "content": {"number": page, "repository": {"nameWithOwner": "o/r"},
                    "labels": {"nodes": [], "pageInfo": {"hasNextPage": False}}},
                    "fieldValues": {"nodes": [{"name": "In progress", "field": {"name": "Status"}}]}}
            return {"user": {"projectV2": {"items": {"nodes": [node],
                    "pageInfo": {"hasNextPage": page == 1, "endCursor": "next"}}}}}
        self.assertEqual(2, len(control.read_project_items(gql, "o", 1, "o/r")))
        self.assertEqual([None, "next"], cursors)
