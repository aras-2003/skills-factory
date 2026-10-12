from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
RENDERER = ROOT / "runtime" / "mcp" / "chart_renderer.py"


def load_renderer():
    spec = importlib.util.spec_from_file_location("skills_factory_chart_renderer", RENDERER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load chart renderer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ChartRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.renderer = load_renderer()

    def _assert_png_result(self, result) -> None:
        self.assertEqual(2, len(result))
        receipt, image = result
        self.assertIn("CHART_PAYLOAD_OK", receipt)
        self.assertIn("mime=image/png", receipt)
        self.assertIn("bytes=", receipt)
        self.assertIn("sha256=", receipt)
        self.assertIn("canvas_px=", receipt)
        self.assertIsNotNone(image.data)
        self.assertTrue(image.data.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_bar_chart_returns_png_image(self) -> None:
        result = self.renderer.render_bar_chart(
            labels=["ACN", "IUIT", "SMH"],
            values=[25.26, 22.16, 5.68],
            title="Portfolio concentration",
            unit="%",
        )
        self._assert_png_result(result)

    def test_line_chart_returns_png_image(self) -> None:
        result = self.renderer.render_line_chart(
            x_labels=["2026-01", "2026-02", "2026-03"],
            series_names=["Portfolio"],
            series_values=[[100.0, 103.5, 101.2]],
            title="Portfolio performance",
            unit="index",
        )
        self._assert_png_result(result)

    def test_zero_and_negative_values_are_preserved_in_chart_payload(self) -> None:
        image = self.renderer.render_bar_chart(
            labels=["zero", "negative", "positive"], values=[0, -5, 3],
            title="Signed bar chart",
        )
        self._assert_png_result(image)
        line = self.renderer.render_line_chart(
            x_labels=["first", "second"], series_names=["series"],
            series_values=[[-2.0, 0.0]], title="Signed line chart",
        )
        self._assert_png_result(line)

    def test_malformed_labels_and_bad_titles_fail_before_render(self) -> None:
        for bad in (["A", 42], [""], "not-a-list"):
            with self.subTest(bad=bad):
                with self.assertRaises(Exception):
                    self.renderer.render_bar_chart(labels=bad, values=[1] * len(bad))
        with self.assertRaises(Exception):
            self.renderer.render_bar_chart(labels=["A"], values=[1], title=chr(0) + "bad")
        with self.assertRaises(Exception):
            self.renderer.render_line_chart(x_labels=["first"], series_names=["s"], series_values=[[1]])
        with self.assertRaises(Exception):
            self.renderer.render_line_chart(x_labels=["x", "y"], series_names=[None], series_values=[[1, 2]])
        with self.assertRaises(Exception):
            self.renderer.render_line_chart(x_labels=["x", "y"], series_names=["s"], series_values=[123])

    def test_invalid_parallel_data_fails_closed(self) -> None:
        with self.assertRaises(Exception):
            self.renderer.render_bar_chart(
                labels=["A", "B"],
                values=[1.0],
            )

    def test_site_compatible_chart_boundaries(self) -> None:
        # Smallest and upper-limit numeric values must be representable.
        self._assert_png_result(self.renderer.render_bar_chart(
            labels=["lower", "upper"], values=[-1_000_000_000_000, 1_000_000_000_000],
            unit="PLN",
        ))
        self._assert_png_result(self.renderer.render_line_chart(
            x_labels=["before", "after"], series_names=["synthetic"],
            series_values=[[-1_000_000_000_000, 1_000_000_000_000]],
        ))

    def test_rejects_values_outside_site_schema_limits(self) -> None:
        for value in (-1_000_000_000_000.01, 1_000_000_000_000.01):
            with self.subTest(value=value):
                with self.assertRaises(Exception):
                    self.renderer.render_bar_chart(labels=["a"], values=[value])
                with self.assertRaises(Exception):
                    self.renderer.render_line_chart(
                        x_labels=["a", "b"], series_names=["s"],
                        series_values=[[0, value]],
                    )

    def test_rejects_site_incompatible_dimensions(self) -> None:
        with self.assertRaises(Exception):
            self.renderer.render_bar_chart(
                labels=["item"] * 61, values=[1] * 61,
            )
        with self.assertRaises(Exception):
            self.renderer.render_bar_chart(labels=["a"], values=[1], unit="x" * 31)
        with self.assertRaises(Exception):
            self.renderer.render_line_chart(
                x_labels=[str(x) for x in range(101)], series_names=["s"],
                series_values=[[1] * 101],
            )
        with self.assertRaises(Exception):
            self.renderer.render_line_chart(
                x_labels=["before", "after"],
                series_names=[f"s{i}" for i in range(9)],
                series_values=[[1, 2]] * 9,
            )
        with self.assertRaises(Exception):
            self.renderer.render_line_chart(
                x_labels=["before", "after"], series_names=["s"],
                series_values=[[1, 2]], unit="x" * 31,
            )

    def test_non_finite_and_boolean_chart_values_fail_closed(self) -> None:
        for value in (math.nan, math.inf, -math.inf, True):
            with self.subTest(value=value):
                with self.assertRaises(Exception):
                    self.renderer.render_bar_chart(labels=["A"], values=[value])
        with self.assertRaises(Exception):
            self.renderer.render_line_chart(
                x_labels=["2026-01"],
                series_names=["Portfolio"],
                series_values=[[math.nan]],
            )


if __name__ == "__main__":
    unittest.main()
