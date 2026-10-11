from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/eval"))
from routing_collision_report import build_report, similarity  # noqa: E402


class RoutingCollisionReportTests(unittest.TestCase):
    def test_similarity_is_symmetric_and_bounded(self) -> None:
        score = similarity("Review organizational decision rights", "Organizational decision rights review")
        self.assertGreater(score, 0.0)
        self.assertEqual(score, similarity("Organizational decision rights review", "Review organizational decision rights"))
        self.assertLessEqual(score, 1.0)

    def test_polish_diacritics_are_normalized_for_static_comparison(self) -> None:
        self.assertEqual(1.0, similarity("zarządzanie organizacją", "zarzadzanie organizacja"))

    def test_report_covers_all_registered_cases_and_never_claims_runtime_pass(self) -> None:
        report = build_report(ROOT)
        self.assertEqual("STATIC_SIGNAL_ONLY", report["classification"])
        self.assertEqual("NOT_PROVIDED", report["runtime_evidence"])
        self.assertGreater(report["catalog_component_count"], 50)
        self.assertEqual(report["case_count"], len(report["cases"]))
        self.assertTrue(all(case["runtime_outcome"] is None for case in report["cases"]))
        self.assertTrue(all(case["runtime_semantic_evidence_required"] for case in report["cases"]))
        self.assertTrue(all(case["semantic_review_signal"] in {"REVIEW", "NO_STATIC_COLLISION_SIGNAL", "INSUFFICIENT_LEXICAL_SIGNAL"} for case in report["cases"]))

    def test_no_skill_near_misses_cover_pl_en_without_runtime_claims(self) -> None:
        report = build_report(ROOT)
        negative = {case["id"]: case for case in report["cases"] if case["route_kind"] == "no_skill_negative"}
        self.assertEqual(3, report["no_skill_negative_case_count"])
        self.assertEqual(24, report["positive_case_count"])
        self.assertEqual({"pl", "en"}, set(report["languages"]))
        for case_id in (
            "commerce-consumer-purchase-no-skill-pl",
            "copyedit-no-skill-en",
            "software-adr-no-skill-en",
        ):
            with self.subTest(case=case_id):
                case = negative[case_id]
                self.assertEqual("no-skill", case["expected_target"])
                self.assertIsNone(case["lexical_target_rank"])
                self.assertIsNone(case["lexical_margin_to_competitor"])
                self.assertIsNone(case["runtime_outcome"])
                self.assertTrue(case["runtime_semantic_evidence_required"])
                self.assertIn(case["semantic_review_signal"], {"REVIEW", "INSUFFICIENT_LEXICAL_SIGNAL"})

    def test_routing_registry_remains_isolated_and_well_formed(self) -> None:
        from validate_routing import validate
        self.assertEqual([], validate(ROOT))



if __name__ == "__main__":
    unittest.main()
