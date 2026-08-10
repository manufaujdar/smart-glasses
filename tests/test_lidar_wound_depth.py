import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from lidar_wound_depth import (  # noqa: E402
    DepthFrame,
    DepthGridError,
    analyze_depth_frame,
    load_depth_input,
)


def synthetic_grid(size=16):
    grid = [[20.0 for _ in range(size)] for _ in range(size)]
    for row in range(5, 9):
        for column in range(6, 10):
            grid[row][column] = 24.0
    return grid


class LidarWoundDepthTests(unittest.TestCase):
    def test_plane_relative_depth_and_volume(self):
        result = analyze_depth_frame(DepthFrame(synthetic_grid(), 0.8, 0.8), (6, 5, 10, 9))
        measurements = result.measurements
        self.assertAlmostEqual(measurements["median_depth_offset_mm"], 4.0, places=6)
        self.assertAlmostEqual(measurements["projected_area_mm2"], 10.24, places=6)
        self.assertAlmostEqual(measurements["estimated_positive_volume_mm3"], 40.96, places=6)
        self.assertEqual(result.quality["flags"], [])
        self.assertTrue(result.safety["research_prototype_only"])

    def test_missing_samples_are_reported_without_crashing(self):
        grid = synthetic_grid()
        grid[6][7] = None
        result = analyze_depth_frame(DepthFrame(grid, 1.0, 1.0), (6, 5, 10, 9))
        self.assertIn("missing_roi_samples", result.quality["flags"])
        self.assertEqual(result.input["valid_roi_samples"], 15)

    def test_invalid_calibration_fails_closed(self):
        with self.assertRaises(DepthGridError):
            analyze_depth_frame(DepthFrame(synthetic_grid(), 0.0, 1.0), (6, 5, 10, 9))

    def test_invalid_roi_fails_closed(self):
        with self.assertRaises(DepthGridError):
            analyze_depth_frame(DepthFrame(synthetic_grid(), 1.0, 1.0), (10, 5, 6, 9))

    def test_json_loader_preserves_calibration_and_capture_id(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frame.json"
            path.write_text(
                json.dumps(
                    {
                        "capture_id": "fixture-123",
                        "pixel_size_mm": [0.8, 0.8],
                        "depth_mm": synthetic_grid(),
                    }
                ),
                encoding="utf-8",
            )
            frame = load_depth_input(path)
        self.assertEqual(frame.capture_id, "fixture-123")
        self.assertEqual(frame.pixel_size_x_mm, 0.8)
        self.assertEqual(len(frame.depth_mm), 16)

    def test_malformed_json_grid_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps({"depth_mm": 3}), encoding="utf-8")
            with self.assertRaises(DepthGridError):
                load_depth_input(path, [1.0, 1.0])


if __name__ == "__main__":
    unittest.main()
