import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from lidar_wound_progress import (  # noqa: E402
    DepthFrame,
    DepthGridError,
    ProgressManifestError,
    analyze_depth_frame,
    analyze_manifest,
    load_manifest,
)


def depth_grid(roi_depth: float) -> list[list[float]]:
    grid = [[20.0 for _ in range(10)] for _ in range(10)]
    for row in range(3, 7):
        for column in range(3, 7):
            grid[row][column] = roi_depth
    return grid


def write_manifest(directory: str, values: list[float]) -> Path:
    path = Path(directory) / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "wound_id": "synthetic-study-wound-001",
                "roi": [3, 3, 7, 7],
                "pixel_size_mm": [1.0, 1.0],
                "captures": [
                    {
                        "capture_id": f"visit-{index + 1}",
                        "captured_at": f"2026-08-{index + 1:02d}T09:00:00Z",
                        "depth_mm": depth_grid(value),
                    }
                    for index, value in enumerate(values)
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


class LidarWoundProgressTests(unittest.TestCase):
    def test_decreasing_geometry_signal_from_serial_captures(self):
        with tempfile.TemporaryDirectory() as directory:
            wound_id, captures = load_manifest(write_manifest(directory, [24.0, 22.0, 20.5]))
        report = analyze_manifest(wound_id, captures)
        self.assertEqual(report["comparison"]["geometry_signal"], "decreasing_geometry")
        volume_change = report["comparison"]["latest_vs_baseline"]["estimated_positive_volume_mm3"]
        self.assertLess(volume_change["percent"], -80.0)
        self.assertTrue(report["safety"]["not_a_recovery_or_healing_determination"])

    def test_increasing_geometry_signal_is_not_called_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            wound_id, captures = load_manifest(write_manifest(directory, [20.5, 22.0, 24.0]))
        report = analyze_manifest(wound_id, captures)
        self.assertEqual(report["comparison"]["geometry_signal"], "increasing_geometry")
        self.assertNotIn("recovery", report["comparison"]["geometry_signal"])

    def test_single_capture_requires_more_data(self):
        with tempfile.TemporaryDirectory() as directory:
            wound_id, captures = load_manifest(write_manifest(directory, [24.0]))
        report = analyze_manifest(wound_id, captures)
        self.assertEqual(report["comparison"]["geometry_signal"], "insufficient_data")

    def test_naive_timestamp_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_manifest(directory, [24.0])
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["captures"][0]["captured_at"] = "2026-08-01T09:00:00"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ProgressManifestError):
                load_manifest(path)

    def test_malformed_depth_grid_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_manifest(directory, [24.0])
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["captures"][0]["depth_mm"] = 3
            path.write_text(json.dumps(payload), encoding="utf-8")
            wound_id, captures = load_manifest(path)
            with self.assertRaises(DepthGridError):
                analyze_manifest(wound_id, captures)

    def test_robust_plane_fit_trims_isolated_background_spike(self):
        grid = depth_grid(24.0)
        grid[1][1] = 100.0
        summary = analyze_depth_frame(
            DepthFrame(grid, 1.0, 1.0, "synthetic-outlier"),
            [3, 3, 7, 7],
            ring_width=2,
        )
        self.assertGreater(summary["measurements"]["background_outliers_trimmed"], 0)
        self.assertAlmostEqual(summary["measurements"]["median_depth_offset_mm"], 4.0)
        self.assertIn("background_outliers_trimmed", summary["quality"]["flags"])


if __name__ == "__main__":
    unittest.main()
