import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "device-contracts"))
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT / "tools"))

from device_runtime import SimulatorAdapter, build_default_hub  # noqa: E402


class DeviceRuntimeTests(unittest.TestCase):
    def setUp(self):
        for name in (
            "SMART_GLASSES_HEYCYAN_BRIDGE_URL",
            "SMART_GLASSES_MENTRA_BRIDGE_URL",
            "SMART_GLASSES_FRAME_BRIDGE_URL",
        ):
            os.environ.pop(name, None)

    def test_default_hub_exposes_truthful_adapter_availability(self):
        hub = build_default_hub()
        profiles = {item["adapter_id"]: item for item in hub.profiles()}
        self.assertTrue(profiles["simulator"]["available"])
        self.assertTrue(profiles["simulator"]["active"])
        self.assertFalse(profiles["heycyan-licensed-sdk"]["available"])
        self.assertIn("proprietary", profiles["heycyan-licensed-sdk"]["evidence"].lower())

    def test_unconfigured_physical_adapter_cannot_be_selected(self):
        hub = build_default_hub()
        with self.assertRaisesRegex(ValueError, "not configured"):
            hub.select("heycyan-licensed-sdk")
        self.assertEqual(hub.active_id, "simulator")

    def test_simulator_runtime_supports_full_safe_lifecycle(self):
        hub = build_default_hub()
        self.assertEqual(len(hub.discover()["devices"]), 1)
        hub.execute("device.connect", "connect-1")
        hub.execute("camera.open_preview", "preview-1")
        hub.execute("stream.start", "stream-1")
        stopped = hub.execute("device.disconnect", "disconnect-1")
        self.assertFalse(stopped["state"]["preview_open"])
        self.assertFalse(stopped["state"]["streaming"])

    def test_adapter_switch_is_blocked_while_connected(self):
        simulator = SimulatorAdapter()
        second = SimulatorAdapter()
        second.profile = second.profile.__class__(
            "simulator-two", "Second simulator", "Project", "in-process", "synthetic", True,
            second.profile.capabilities, second.profile.evidence, second.profile.limitations,
        )
        from device_runtime import DeviceHub
        hub = DeviceHub([simulator, second])
        hub.execute("device.connect", "connect-1")
        with self.assertRaisesRegex(ValueError, "disconnect"):
            hub.select("simulator-two")

    def test_non_loopback_bridge_requires_https(self):
        from device_runtime import AdapterProfile, ExternalBridgeAdapter
        profile = AdapterProfile("test", "Test", "Test", "HTTP", "external", True, (), "test")
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            ExternalBridgeAdapter(profile, "http://192.0.2.10:8781")


if __name__ == "__main__":
    unittest.main()
