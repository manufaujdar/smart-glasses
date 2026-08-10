import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from lidar_wound_progress.paired_comparison import (  # noqa: E402
    PairComparisonError,
    PairQuality,
    compare_wound_pair,
    grayscale_change_metrics,
    wound_mask_metrics,
)


def rectangle(width=4, height=3, canvas=8):
    return [[x < width and y < height for x in range(canvas)] for y in range(canvas)]


class PairedComparisonTests(unittest.TestCase):
    def test_calibrated_planimetry_reports_area_perimeter_and_dimensions(self):
        metrics = wound_mask_metrics(rectangle(), (2.0, 1.0))
        self.assertEqual(metrics["area_px"], 12)
        self.assertAlmostEqual(metrics["area_mm2"], 24.0)
        self.assertAlmostEqual(metrics["longest_dimension_mm"], 8.0)
        self.assertAlmostEqual(metrics["widest_dimension_mm"], 3.0)

    def test_pair_reports_area_reduction_and_linear_edge_change(self):
        quality = PairQuality(True, 1.0, 1.0, True, 1.0)
        result = compare_wound_pair(rectangle(4, 3), rectangle(2, 3), (1.0, 1.0), (1.0, 1.0), quality, days_between=14)
        self.assertAlmostEqual(result["change"]["area_reduction_percent"], 50.0)
        self.assertAlmostEqual(result["change"]["area_reduction_per_week_percent"], 25.0)
        self.assertTrue(result["quality"]["usable_for_measurement"])

    def test_quality_gate_blocks_unreviewed_unscaled_pair(self):
        quality = PairQuality(False, 0.5, 0.4, False, 0.5)
        result = compare_wound_pair(rectangle(), rectangle(), (1.0, 1.0), (1.0, 1.0), quality)
        self.assertFalse(result["quality"]["usable_for_measurement"])
        self.assertIn("missing_scale_marker", result["quality"]["flags"])

    def test_grayscale_change_returns_ssim_and_changed_fraction(self):
        first = [[0.0, 0.0], [0.0, 1.0]]
        second = [[0.0, 0.0], [1.0, 1.0]]
        result = grayscale_change_metrics(first, second)
        self.assertIn("ssim", result)
        self.assertGreater(result["changed_fraction_over_5_percent"], 0)

    def test_malformed_masks_fail_closed(self):
        with self.assertRaises(PairComparisonError):
            wound_mask_metrics([[True], [True, False]])


if __name__ == "__main__":
    unittest.main()
