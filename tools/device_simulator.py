#!/usr/bin/env python3
"""Deterministic simulator for the vendor-neutral glasses contract."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "device-contracts"))

from device_contracts import ConnectionState, DeviceCommand, DeviceEvent  # noqa: E402


class SimulatedGlasses:
    DEFAULT_CAPABILITIES = {
        "device.battery",
        "device.version",
        "camera.photo",
        "camera.video",
        "audio.recording",
        "media.list",
    }
    COMMAND_CAPABILITIES = {
        "device.get_battery": "device.battery",
        "device.get_version": "device.version",
        "camera.take_photo": "camera.photo",
        "camera.start_video": "camera.video",
        "camera.stop_video": "camera.video",
        "audio.start_recording": "audio.recording",
        "audio.stop_recording": "audio.recording",
        "media.get_counts": "media.list",
    }

    def __init__(
        self,
        device_id: str = "SIM-HEYCYAN-001",
        capabilities: set[str] | None = None,
    ) -> None:
        self.device_id = device_id
        self.state = ConnectionState.DISCONNECTED
        self.battery = 86
        self.photo_count = 0
        self.recording_audio = False
        self.recording_video = False
        self.capabilities = set(self.DEFAULT_CAPABILITIES if capabilities is None else capabilities)
        self._completed_commands: dict[str, tuple[str, DeviceEvent]] = {}

    def execute(self, command: DeviceCommand) -> DeviceEvent:
        """Execute a command once and replay the event for duplicate command IDs."""

        try:
            fingerprint = json.dumps(
                {"name": command.name, "payload": command.payload},
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError):
            return self._event(
                "command.rejected", command, {"reason": "invalid_command_payload"}
            )
        if command.command_id in self._completed_commands:
            previous_fingerprint, previous_event = self._completed_commands[command.command_id]
            if previous_fingerprint != fingerprint:
                return self._event(
                    "command.rejected",
                    command,
                    {"reason": "command_id_conflict"},
                )
            return previous_event
        event = self._execute(command)
        self._completed_commands[command.command_id] = (fingerprint, event)
        return event

    def _execute(self, command: DeviceCommand) -> DeviceEvent:
        if command.name == "device.connect":
            self.state = ConnectionState.CONNECTED
            return self._event("device.connected", command, {"battery": self.battery})
        if command.name == "device.disconnect":
            self.state = ConnectionState.DISCONNECTED
            self.recording_audio = self.recording_video = False
            return self._event("device.disconnected", command)
        if self.state != ConnectionState.CONNECTED:
            return self._event("command.rejected", command, {"reason": "not_connected"})
        required_capability = self.COMMAND_CAPABILITIES.get(command.name)
        if required_capability and required_capability not in self.capabilities:
            return self._event(
                "command.rejected",
                command,
                {
                    "reason": "unsupported_capability",
                    "required_capability": required_capability,
                },
            )
        if command.name == "device.get_battery":
            return self._event("device.battery", command, {"level": self.battery, "charging": False})
        if command.name == "device.get_version":
            return self._event("device.version", command, {"hardware": "sim-1", "firmware": "0.1.0"})
        if command.name == "camera.take_photo":
            self.photo_count += 1
            self.battery = max(0, self.battery - 1)
            return self._event("camera.photo_captured", command, {"media_id": f"photo-{self.photo_count:04d}"})
        if command.name == "audio.start_recording":
            if self.recording_video:
                return self._event("command.rejected", command, {"reason": "video_active"})
            self.recording_audio = True
            return self._event("audio.recording_started", command)
        if command.name == "audio.stop_recording":
            if not self.recording_audio:
                return self._event("command.rejected", command, {"reason": "audio_not_active"})
            self.recording_audio = False
            return self._event("audio.recording_stopped", command, {"media_id": "audio-0001"})
        if command.name == "camera.start_video":
            if self.recording_audio:
                return self._event("command.rejected", command, {"reason": "audio_active"})
            self.recording_video = True
            return self._event("camera.video_started", command)
        if command.name == "camera.stop_video":
            if not self.recording_video:
                return self._event("command.rejected", command, {"reason": "video_not_active"})
            self.recording_video = False
            return self._event("camera.video_stopped", command, {"media_id": "video-0001"})
        if command.name == "media.get_counts":
            return self._event("media.counts", command, {"photos": self.photo_count, "videos": 0, "audio": 0})
        return self._event("command.rejected", command, {"reason": "unsupported_command"})

    def _event(self, name: str, command: DeviceCommand, payload=None) -> DeviceEvent:
        return DeviceEvent(name=name, device_id=self.device_id, command_id=command.command_id, payload=payload or {})


def run_happy_path() -> list[DeviceEvent]:
    device = SimulatedGlasses()
    commands = [
        DeviceCommand("device.connect"),
        DeviceCommand("device.get_version"),
        DeviceCommand("device.get_battery"),
        DeviceCommand("camera.take_photo"),
        DeviceCommand("audio.start_recording"),
        DeviceCommand("audio.stop_recording"),
        DeviceCommand("media.get_counts"),
        DeviceCommand("device.disconnect"),
    ]
    return [device.execute(command) for command in commands]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["happy-path"], default="happy-path")
    args = parser.parse_args()
    events = run_happy_path()
    print("\n".join(json.dumps(asdict(event), sort_keys=True) for event in events))
