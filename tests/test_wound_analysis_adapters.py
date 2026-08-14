import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from lidar_wound_progress.calibration import CalibrationError, CalibrationObservation, fit_depth_calibration  # noqa: E402
from lidar_wound_progress.calibration_opencv import OpenCVCalibrationError, calibrate_charuco  # noqa: E402
from lidar_wound_progress.depth_provider import DepthProviderError, NativeDepthFrame  # noqa: E402
from lidar_wound_progress.ml.registration import Open3DRegistrationAdapter, RegistrationError  # noqa: E402
from lidar_wound_progress.ml.segmentation import SegmentationError, validate_mask, validate_prompt  # noqa: E402
from lidar_wound_progress.validation import measurement_metrics, repeatability_metrics, segmentation_metrics  # noqa: E402


class WoundAnalysisAdapterTests(unittest.TestCase):
    def test_segmentation_contract_normalizes_mask_and_prompt(self):
        self.assertEqual(validate_mask([[0, 1], [True, False]]), ((False, True), (True, False)))
        self.assertEqual(validate_prompt([1, 2, 8, 9]), (1.0, 2.0, 8.0, 9.0))
        with self.assertRaises(SegmentationError):
            validate_mask([[True], [False, True]])
        with self.assertRaises(SegmentationError):
            validate_prompt([1, 1, 1, 2])

    def test_registration_is_explicitly_optional(self):
        adapter = Open3DRegistrationAdapter()
        try:
            result = adapter.register([[0, 0, 0], [1, 0, 0], [0, 1, 0]], [[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        except RegistrationError as error:
            self.assertIn("optional", str(error))
        else:
            self.assertTrue(result.accepted)
            self.assertEqual(len(result.transform), 4)

    def test_phantom_calibration_fits_scale_and_bias_and_applies_gate(self):
        observations = [
            CalibrationObservation("a", 11.0, 10.0),
            CalibrationObservation("b", 22.0, 20.0),
            CalibrationObservation("c", 33.0, 30.0),
        ]
        report = fit_depth_calibration(observations, max_abs_error_mm=0.01)
        self.assertAlmostEqual(report.scale, 1.1)
        self.assertAlmostEqual(report.bias_mm, 0.0)
        self.assertTrue(report.passed)
        with self.assertRaises(CalibrationError):
            fit_depth_calibration([CalibrationObservation("only", 1.0, 1.0)])

    def test_validation_metrics_cover_segmentation_measurement_and_repeatability(self):
        metrics = segmentation_metrics([[False, True], [False, True]], [[False, True], [True, False]])
        self.assertAlmostEqual(metrics["dice"], 0.5)
        self.assertAlmostEqual(metrics["iou"], 1 / 3)
        measurement = measurement_metrics([4.1, 3.9, 4.0], [4.0, 4.0, 4.0])
        self.assertAlmostEqual(measurement["mae_mm"], 0.0666666667, places=6)
        repeatability = repeatability_metrics([4.0, 4.1, 3.9])
        self.assertEqual(repeatability["count"], 3)
        self.assertGreater(repeatability["standard_deviation"], 0)

    def test_native_depth_contract_converts_meters_to_mm(self):
        frame = NativeDepthFrame(1, 2, 1, ((0.5, 0.75),), "m", "synthetic")
        self.assertEqual(frame.depth_mm(), ((500.0, 750.0),))
        with self.assertRaises(DepthProviderError):
            NativeDepthFrame(1, 2, 1, ((1.0,),), "mm", "bad")

    def test_opencv_calibration_is_optional_and_input_validated(self):
        with self.assertRaises(OpenCVCalibrationError):
            calibrate_charuco([], [], object(), (640, 480))


if __name__ == "__main__":
    unittest.main()
