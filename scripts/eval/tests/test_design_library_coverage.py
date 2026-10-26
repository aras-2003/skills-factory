"""Keep optional design selection executable without upgrading runtime evidence."""
import importlib.util
import unittest
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/eval"))
import campaign

class DesignLibraryCoverageTests(unittest.TestCase):
    def test_new_reference_has_a_case_backed_not_run_campaign(self):
        self.assertIn("workflows/presentation-production/references/design-library-selection.md",
                      campaign.separately_validated_presentation_paths(ROOT))

    def test_advisory_selector_regressions_execute_in_required_ci(self):
        path = ROOT / "tests/test_presentation_design_library.py"
        spec = importlib.util.spec_from_file_location("design_library_regressions", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        result = unittest.TestResult()
        suite.run(result)
        self.assertGreaterEqual(result.testsRun, 7)
        self.assertEqual([], result.errors)
        self.assertEqual([], result.failures)
