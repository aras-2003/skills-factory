import unittest
"""SVG presentation contract for lifecycle visualizations."""
import importlib.util
import sys
from pathlib import Path

PATH = (Path(__file__).resolve().parents[2] / "skills/investing/security-underwriting"
        / "scripts/business_lifecycle_visual.py")
spec = importlib.util.spec_from_file_location("business_lifecycle_visual", PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class LifecycleTests(unittest.TestCase):
    def test_all_five_phases_and_active_emphasis(self):
        svg = module.render_lifecycle_svg(
            {"status": "CLASSIFIED", "phase": "operating_leverage",
             "phase_affinity_pct": {x: 20.0 for x, _ in module.PHASES},
             "metrics": {"revenue_growth": 0.15, "operating_margin": 0.12},
             "data_gaps": []}, company="Sample")
        assert all(label in svg for _, label in module.PHASES)
        assert svg.count("CURRENT PHASE") == 1
        assert "NOT probability".upper() in svg.upper()


    def test_insufficient_data_no_selected_stage(self):
        svg = module.render_lifecycle_svg({"status": "INSUFFICIENT_DATA"}, company="X")
        assert "NOT CLASSIFIED" in svg
        assert "CURRENT PHASE" not in svg
        assert svg.count("N/A") == 5


    def test_escapes_untrusted_issuer_name(self):
        svg = module.render_lifecycle_svg({"status": "INSUFFICIENT_DATA"}, company="<script>alert(1)</script>")
        assert "<script>" not in svg
        assert "&lt;script&gt;" in svg
