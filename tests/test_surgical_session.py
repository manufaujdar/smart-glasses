import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "surgical-workflows"))
sys.path.insert(0, str(ROOT / "tools"))

from surgical_session import (  # noqa: E402
    PreflightGate,
    SurgicalSession,
    SurgicalSessionState,
    complete_all_preflight_gates,
)
from surgical_session_simulator import (  # noqa: E402
    SyntheticObservationController,
    run_synthetic_observation,
)
from device_simulator import SimulatedGlasses  # noqa: E402
from device_contracts import DeviceCommand  # noqa: E402


class SurgicalSessionTests(unittest.TestCase):
    CAPABILITIES = {"camera.video", "telepresence.stream"}
    def test_requires_synthetic_identifier(self):
        with self.assertRaises(ValueError):
            SurgicalSession("PATIENT-123")

    def test_missing_gate_blocks_ready_state(self):
        session = SurgicalSession()
        session.start_preflight()
        session.confirm_gate(PreflightGate.CONSENT_AUTHORIZED)
        event = session.arm(battery_percent=90, capabilities=self.CAPABILITIES)
        self.assertEqual(event.name, "command.rejected")
        self.assertEqual(event.payload["reason"], "preflight.incomplete")
        self.assertEqual(session.state, SurgicalSessionState.PREFLIGHT)

    def test_low_battery_blocks_ready_state(self):
        session = SurgicalSession()
        session.start_preflight()
        complete_all_preflight_gates(session)
        event = session.arm(battery_percent=29, connected=True, capabilities=self.CAPABILITIES)
        self.assertEqual(event.payload["reason"], "device.low_battery")
        self.assertEqual(session.state, SurgicalSessionState.PREFLIGHT)

    def test_disconnect_safe_stops_every_output(self):
        session = SurgicalSession()
        session.start_preflight()
        complete_all_preflight_gates(session)
        session.arm(battery_percent=80, connected=True, capabilities=self.CAPABILITIES)
        session.start_observation(recording=True, streaming=True)
        session.set_advisory_overlay(True)
        event = session.device_disconnected()
        self.assertEqual(event.name, "session.safe_stopped")
        self.assertEqual(session.state, SurgicalSessionState.SAFE_STOP)
        self.assertFalse(session.recording)
        self.assertFalse(session.streaming)
        self.assertFalse(session.overlays_enabled)

    def test_clear_view_does_not_silently_stop_recording(self):
        session = SurgicalSession()
        session.start_preflight()
        complete_all_preflight_gates(session)
        session.arm(battery_percent=80, connected=True, capabilities=self.CAPABILITIES)
        session.start_observation(recording=True)
        session.set_advisory_overlay(True)
        session.clear_view()
        self.assertFalse(session.overlays_enabled)
        self.assertTrue(session.recording)

    def test_end_to_end_synthetic_scenario_safe_stops(self):
        events = run_synthetic_observation()
        self.assertEqual(events[-1]["name"], "session.safe_stopped")
        self.assertTrue(any(event["name"] == "session.ready" for event in events))

    def test_critical_battery_safe_stops_active_outputs(self):
        session = self._observing_session()
        event = session.battery_changed(14)
        self.assertEqual(event.payload["reason"], "critical_battery")
        self.assertEqual(session.state, SurgicalSessionState.SAFE_STOP)
        self.assertFalse(session.recording)
        self.assertFalse(session.streaming)

    def test_capture_indicator_loss_safe_stops_recording(self):
        session = self._observing_session()
        event = session.capture_indicator_changed(False)
        self.assertEqual(event.payload["reason"], "capture_indicator_lost")
        self.assertEqual(session.state, SurgicalSessionState.SAFE_STOP)
        self.assertFalse(session.recording)

    def test_invalid_battery_reading_safe_stops_active_session(self):
        session = self._observing_session()
        event = session.battery_changed(101)
        self.assertEqual(event.payload["reason"], "battery_telemetry_untrusted")
        self.assertEqual(session.state, SurgicalSessionState.SAFE_STOP)

    def _observing_session(self):
        session = SurgicalSession()
        session.start_preflight()
        complete_all_preflight_gates(session)
        session.arm(battery_percent=80, connected=True, capabilities=self.CAPABILITIES)
        session.start_observation(recording=True, streaming=True)
        return session

    def test_indicator_loss_before_capture_prevents_start(self):
        session = SurgicalSession()
        session.start_preflight()
        complete_all_preflight_gates(session)
        session.arm(battery_percent=80, connected=True, capabilities=self.CAPABILITIES)
        session.capture_indicator_changed(False)
        self.assertEqual(session.state, SurgicalSessionState.SAFE_STOP)
        event = session.start_observation(recording=True)
        self.assertEqual(event.payload["reason"], "session.not_ready")

    def test_missing_mode_capability_blocks_capture(self):
        session = SurgicalSession()
        session.start_preflight()
        complete_all_preflight_gates(session)
        session.arm(battery_percent=80, connected=True, capabilities={"device.battery"})
        event = session.start_observation(recording=True)
        self.assertEqual(event.payload["reason"], "device.capability_missing")

    def test_capability_loss_safe_stops_active_capture(self):
        session = self._observing_session()
        event = session.capabilities_changed({"camera.video"})
        self.assertEqual(event.payload["reason"], "device.capability_lost")
        self.assertEqual(session.state, SurgicalSessionState.SAFE_STOP)

    def test_battery_threshold_is_inclusive(self):
        session = self._observing_session()
        event = session.battery_changed(15)
        self.assertEqual(event.payload["reason"], "critical_battery")
        self.assertEqual(session.state, SurgicalSessionState.SAFE_STOP)

    def test_safe_stop_cannot_be_relabelled_completed(self):
        session = self._observing_session()
        session.device_disconnected()
        event = session.end()
        self.assertEqual(event.payload["reason"], "session.cannot_complete_from_state")
        self.assertEqual(session.state, SurgicalSessionState.SAFE_STOP)

    def test_controller_propagates_disconnect_to_session(self):
        device = SimulatedGlasses()
        session = self._observing_session()
        controller = SyntheticObservationController(device, session)
        controller.execute_device(DeviceCommand("device.connect"))
        events = controller.execute_device(DeviceCommand("device.disconnect"))
        self.assertEqual([event["name"] for event in events], ["device.disconnected", "session.safe_stopped"])
        self.assertEqual(session.state, SurgicalSessionState.SAFE_STOP)

    def test_arm_requires_observed_connection_and_valid_battery(self):
        for battery in (None, True, float("nan"), -1, 101):
            with self.subTest(battery=battery):
                session = SurgicalSession()
                session.start_preflight()
                complete_all_preflight_gates(session)
                event = session.arm(
                    battery_percent=battery,  # type: ignore[arg-type]
                    connected=True,
                    capabilities=self.CAPABILITIES,
                )
                self.assertEqual(event.payload["reason"], "device.invalid_battery")
                self.assertEqual(session.state, SurgicalSessionState.PREFLIGHT)

        session = SurgicalSession()
        session.start_preflight()
        complete_all_preflight_gates(session)
        event = session.arm(battery_percent=80, capabilities=self.CAPABILITIES)
        self.assertEqual(event.payload["reason"], "device.not_connected")

    def test_controller_deduplicates_propagated_disconnect(self):
        device = SimulatedGlasses()
        session = self._observing_session()
        controller = SyntheticObservationController(device, session)
        controller.execute_device(DeviceCommand("device.connect"))
        disconnect = DeviceCommand("device.disconnect", command_id="disconnect-once")
        first = controller.execute_device(disconnect)
        replay = controller.execute_device(disconnect)
        self.assertEqual(len(first), 2)
        self.assertEqual(len(replay), 1)

    def test_safe_stop_preserves_primary_reason(self):
        session = self._observing_session()
        session.capture_indicator_changed(False)
        event = session.device_disconnected()
        self.assertEqual(event.name, "session.safe_stop_fault_recorded")
        self.assertEqual(session.safe_stop_reason, "capture_indicator_lost")


if __name__ == "__main__":
    unittest.main()
