import importlib.util
from pathlib import Path
import unittest
import yaml

SPEC = importlib.util.spec_from_file_location("delivery_control", Path(__file__).resolve().parents[2] / "scripts/governance/delivery_control.py")
control = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(control)


class DeliveryTests(unittest.TestCase):
    def test_serialized_metadata_events_keep_pending_issues_in_queue(self):
        path = Path(__file__).resolve().parents[2] / ".github/workflows/maintenance-project-metadata.yml"
        concurrency = yaml.safe_load(path.read_text())["concurrency"]
        self.assertEqual("max", concurrency["queue"])
        self.assertIs(False, concurrency["cancel-in-progress"])

    def test_two_independent_packages_are_allowed_without_iteration_lock(self):
        items = [{"id": "a", "status": "In progress"}, {"id": "b", "status": "Ready"}]
        self.assertEqual("PASS", control.check_wip(items, starting_item="b")["status"])
        self.assertEqual("BLOCKED", control.check_wip(items + [{"id": "c", "status": "In review"}], starting_item="b")["status"])

    def test_parked_and_verification_do_not_hold_development_slots(self):
        items = [{"id": "a", "status": "In progress", "blocked": True},
                 {"id": "b", "status": "Verification"}, {"id": "c", "status": "In review"}]
        self.assertEqual(1, control.check_wip(items)["development_wip"])
        self.assertEqual(1, control.check_wip(items, starting_item="c")["development_wip"])

    def test_closed_issue_does_not_consume_development_wip_or_get_reopened_by_start(self):
        items = [{"id": "closed", "status": "In progress", "state": "CLOSED"},
                 {"id": "active", "status": "In progress", "state": "OPEN"}]
        report = control.check_wip(items, starting_item="closed")
        self.assertEqual("PASS", report["status"])
        self.assertEqual(1, report["development_wip"])
        self.assertEqual(["active"], report["active_items"])

    def test_unknown_native_stage_is_not_silently_treated_as_done(self):
        with self.assertRaises(ValueError):
            control.check_wip([{"id": "a", "status": "Validation"}])

    def test_pagination_preserves_all_project_items(self):
        cursors = []
        def gql(query, variables):
            cursors.append(variables["cursor"])
            page = len(cursors)
            node = {"id": str(page), "content": {"number": page, "state": "OPEN", "stateReason": None, "repository": {"nameWithOwner": "o/r"},
                    "labels": {"nodes": [], "pageInfo": {"hasNextPage": False}}},
                    "fieldValues": {"nodes": [{"name": "In progress", "field": {"name": "Status"}}]}}
            return {"user": {"projectV2": {"items": {"nodes": [node],
                    "pageInfo": {"hasNextPage": page == 1, "endCursor": "next"}}}}}
        result = control.read_project_items(gql, "o", 1, "o/r")
        self.assertEqual(2, len(result))
        self.assertEqual("OPEN", result[0]["state"])
        self.assertEqual([None, "next"], cursors)
