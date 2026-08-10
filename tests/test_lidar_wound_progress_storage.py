import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "tools" / "lidar_wound_progress"))

from local_storage import LocalRecordStore, StorageValidationError  # noqa: E402


def record(sensor_mode="professional_lidar"):
    return {
        "wound_id": "synthetic-wound-001",
        "capture_id": "visit-1",
        "captured_at": "2026-08-10T09:00:00Z",
        "sensor_mode": sensor_mode,
        "accuracy_tier": "high" if sensor_mode == "professional_lidar" else "low",
        "measurements": {
            "median_depth_offset_mm": 2.0,
            "estimated_positive_volume_mm3": 32.0,
        },
        "quality": {"engineering_quality_score": 1.0, "flags": []},
    }


class LocalStorageTests(unittest.TestCase):
    def test_round_trip_and_audit_event(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LocalRecordStore(Path(directory) / "depthline.sqlite3")
            saved = store.save(record())
            rows = store.list("synthetic-wound-001", "professional_lidar")
            audit = store.audit()
            store.close()
        self.assertEqual(rows[0]["record_id"], saved["record_id"])
        self.assertEqual(rows[0]["measurements"]["estimated_positive_volume_mm3"], 32.0)
        self.assertEqual(audit[0]["event_type"], "record_saved")

    def test_raw_depth_and_image_data_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LocalRecordStore(Path(directory) / "depthline.sqlite3")
            bad = record()
            bad["depth_mm"] = [[20.0]]
            with self.assertRaises(StorageValidationError):
                store.save(bad)
            store.close()

    def test_non_finite_measurement_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LocalRecordStore(Path(directory) / "depthline.sqlite3")
            bad = record()
            bad["measurements"]["median_depth_offset_mm"] = float("inf")
            with self.assertRaises(StorageValidationError):
                store.save(bad)
            store.close()

    def test_sensor_route_and_accuracy_tier_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LocalRecordStore(Path(directory) / "depthline.sqlite3")
            bad = record(sensor_mode="camera")
            bad["accuracy_tier"] = "high"
            with self.assertRaises(StorageValidationError):
                store.save(bad)
            store.close()

    def test_delete_is_audited(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LocalRecordStore(Path(directory) / "depthline.sqlite3")
            saved = store.save(record())
            self.assertTrue(store.delete(saved["record_id"]))
            self.assertEqual(store.list(), [])
            audit_types = [event["event_type"] for event in store.audit()]
            store.close()
        self.assertIn("record_deleted", audit_types)


if __name__ == "__main__":
    unittest.main()
