import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "device-contracts"))
sys.path.insert(0, str(ROOT / "tools"))

from device_contracts import DeviceCommand
from device_simulator import SimulatedGlasses, run_happy_path


class SimulatorTests(unittest.TestCase):
    def test_happy_path_has_correlated_events(self):
        events = run_happy_path()
        self.assertEqual(events[0].name, "device.connected")
        self.assertEqual(events[-1].name, "device.disconnected")
        self.assertTrue(all(event.command_id for event in events))

    def test_commands_fail_closed_while_disconnected(self):
        event = SimulatedGlasses().execute(DeviceCommand("camera.take_photo"))
        self.assertEqual(event.name, "command.rejected")
        self.assertEqual(event.payload["reason"], "not_connected")

    def test_audio_and_video_are_mutually_exclusive(self):
        device = SimulatedGlasses()
        device.execute(DeviceCommand("device.connect"))
        device.execute(DeviceCommand("audio.start_recording"))
        event = device.execute(DeviceCommand("camera.start_video"))
        self.assertEqual(event.name, "command.rejected")
        self.assertEqual(event.payload["reason"], "audio_active")

    def test_duplicate_command_id_is_idempotent(self):
        device = SimulatedGlasses()
        device.execute(DeviceCommand("device.connect"))
        command = DeviceCommand("camera.take_photo")
        first = device.execute(command)
        duplicate = device.execute(command)
        self.assertEqual(first, duplicate)
        self.assertEqual(device.photo_count, 1)

    def test_capability_mismatch_rejects_before_device_action(self):
        device = SimulatedGlasses(capabilities={"device.battery"})
        device.execute(DeviceCommand("device.connect"))
        event = device.execute(DeviceCommand("camera.take_photo"))
        self.assertEqual(event.name, "command.rejected")
        self.assertEqual(event.payload["reason"], "unsupported_capability")
        self.assertEqual(event.payload["required_capability"], "camera.photo")
        self.assertEqual(device.photo_count, 0)

    def test_explicit_empty_capability_set_remains_empty(self):
        device = SimulatedGlasses(capabilities=set())
        device.execute(DeviceCommand("device.connect"))
        event = device.execute(DeviceCommand("camera.take_photo"))
        self.assertEqual(event.payload["reason"], "unsupported_capability")

    def test_reused_command_id_with_different_command_is_rejected(self):
        device = SimulatedGlasses()
        command = DeviceCommand("device.connect", command_id="same-id")
        device.execute(command)
        event = device.execute(DeviceCommand("device.disconnect", command_id="same-id"))
        self.assertEqual(event.payload["reason"], "command_id_conflict")
        self.assertEqual(device.state.value, "connected")

    def test_non_json_payload_is_rejected_without_crashing(self):
        device = SimulatedGlasses()
        event = device.execute(DeviceCommand("device.connect", payload={"bad": {1, 2}}))
        self.assertEqual(event.payload["reason"], "invalid_command_payload")
        self.assertEqual(device.state.value, "disconnected")

    def test_stream_preview_and_disconnect_return_to_safe_state(self):
        device = SimulatedGlasses()
        device.execute(DeviceCommand("device.connect"))
        self.assertEqual(device.execute(DeviceCommand("camera.open_preview")).name, "camera.preview_started")
        self.assertEqual(device.execute(DeviceCommand("stream.start")).name, "stream.started")
        device.execute(DeviceCommand("device.disconnect"))
        self.assertFalse(device.preview_open)
        self.assertFalse(device.streaming)
        self.assertFalse(device.recording_audio)
        self.assertFalse(device.recording_video)

    def test_synthetic_media_list_and_transfer_are_correlated(self):
        device = SimulatedGlasses()
        device.execute(DeviceCommand("device.connect"))
        photo = device.execute(DeviceCommand("camera.take_photo"))
        media_id = photo.payload["media_id"]
        listed = device.execute(DeviceCommand("media.list"))
        self.assertEqual(listed.payload["items"][0]["media_id"], media_id)
        transferred = device.execute(DeviceCommand("media.transfer", {"media_id": media_id}))
        self.assertEqual(transferred.name, "media.transfer_completed")
        self.assertEqual(transferred.payload["checksum_status"], "synthetic_verified")


if __name__ == "__main__":
    unittest.main()
