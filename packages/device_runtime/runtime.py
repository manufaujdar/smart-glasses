"""Vendor-neutral runtime with a simulator and explicit external bridge seams.

External bridges are separate, authorized mobile/device processes. This module
does not contain proprietary SDK code, firmware, BLE packets, or credentials.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from device_contracts import DeviceCommand
from device_simulator import SimulatedGlasses


MAX_EVENTS = 300
MAX_BRIDGE_RESPONSE_BYTES = 1_000_000
ALLOWED_COMMANDS = {"device.connect", "device.disconnect"} | set(SimulatedGlasses.COMMAND_CAPABILITIES)


@dataclass(frozen=True)
class AdapterProfile:
    adapter_id: str
    name: str
    vendor: str
    transport: str
    mode: str
    available: bool
    capabilities: tuple[str, ...]
    evidence: str
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuntimeAdapter(Protocol):
    profile: AdapterProfile

    def discover(self, timeout_seconds: float = 5.0) -> list[dict[str, Any]]: ...
    def state(self) -> dict[str, Any]: ...
    def events(self) -> list[dict[str, Any]]: ...
    def execute(self, name: str, command_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...
    def reset(self) -> dict[str, Any]: ...


class SimulatorAdapter:
    """Deterministic adapter used for development and automated tests."""

    def __init__(self) -> None:
        self.profile = AdapterProfile(
            adapter_id="simulator",
            name="HeyCyan-class simulator",
            vendor="Project simulator",
            transport="in-process",
            mode="synthetic",
            available=True,
            capabilities=tuple(sorted(SimulatedGlasses.DEFAULT_CAPABILITIES)),
            evidence="Deterministic project state machine; no physical hardware.",
            limitations=("Synthetic events only", "No Bluetooth or physical media"),
        )
        self._lock = threading.RLock()
        self._device = SimulatedGlasses()
        self._events: list[dict[str, Any]] = []

    def discover(self, timeout_seconds: float = 5.0) -> list[dict[str, Any]]:
        del timeout_seconds
        return [{
            "device_id": self._device.device_id,
            "name": "Synthetic HeyCyan-class glasses",
            "signal": None,
            "synthetic": True,
        }]

    def state(self) -> dict[str, Any]:
        with self._lock:
            return self._state_unlocked()

    def events(self) -> list[dict[str, Any]]:
        with self._lock:
            return [{**event, "payload": dict(event["payload"])} for event in self._events]

    def execute(self, name: str, command_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if name not in ({"device.connect", "device.disconnect"} | set(SimulatedGlasses.COMMAND_CAPABILITIES)):
            raise ValueError("unsupported command")
        if not isinstance(command_id, str) or not 1 <= len(command_id) <= 100:
            raise ValueError("command_id must contain 1 to 100 characters")
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")
        command = DeviceCommand(name=name, command_id=command_id, payload=payload)
        with self._lock:
            event = self._device.execute(command)
            event_dict = asdict(event)
            if not any(item["command_id"] == event.command_id for item in self._events):
                self._events.append(event_dict)
                del self._events[:-MAX_EVENTS]
            return {"event": event_dict, "state": self._state_unlocked()}

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._device = SimulatedGlasses()
            self._events.clear()
            return {"status": "reset", "state": self._state_unlocked()}

    def _state_unlocked(self) -> dict[str, Any]:
        return {
            "adapter_id": self.profile.adapter_id,
            "adapter_mode": self.profile.mode,
            "synthetic": True,
            "device_id": self._device.device_id,
            "connection_state": self._device.state.value,
            "battery": self._device.battery,
            "photo_count": self._device.photo_count,
            "video_count": self._device.video_count,
            "audio_count": self._device.audio_count,
            "recording_audio": self._device.recording_audio,
            "recording_video": self._device.recording_video,
            "preview_open": self._device.preview_open,
            "streaming": self._device.streaming,
            "capabilities": sorted(self._device.capabilities),
        }


class ExternalBridgeAdapter:
    """HTTP client for an authorized Android/vendor bridge.

    The bridge owns Bluetooth permissions, SDK calls, pairing, and media bytes.
    This process receives only bounded JSON state and event metadata.
    """

    def __init__(self, profile: AdapterProfile, base_url: str | None, token: str | None = None) -> None:
        self.profile = profile
        self.base_url = base_url.rstrip("/") if base_url else None
        self.token = token
        if self.base_url:
            parsed = urlsplit(self.base_url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError(f"invalid bridge URL for {profile.adapter_id}")
            if parsed.scheme == "http" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
                raise ValueError(f"non-loopback bridge for {profile.adapter_id} must use HTTPS")

    def discover(self, timeout_seconds: float = 5.0) -> list[dict[str, Any]]:
        result = self._request("/bridge/v1/discover", {"timeout_seconds": timeout_seconds})
        devices = result.get("devices", [])
        if not isinstance(devices, list):
            raise RuntimeError("bridge returned an invalid device list")
        return devices

    def state(self) -> dict[str, Any]:
        state = self._request("/bridge/v1/state")
        return {"adapter_id": self.profile.adapter_id, "adapter_mode": self.profile.mode, **state}

    def events(self) -> list[dict[str, Any]]:
        result = self._request("/bridge/v1/events")
        events = result.get("events", [])
        if not isinstance(events, list):
            raise RuntimeError("bridge returned an invalid event list")
        return events[-MAX_EVENTS:]

    def execute(self, name: str, command_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("/bridge/v1/command", {
            "name": name,
            "command_id": command_id,
            "payload": payload,
        })

    def reset(self) -> dict[str, Any]:
        raise ValueError("physical bridges cannot be reset from the research console")

    def _request(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.base_url or not self.profile.available:
            raise ValueError(f"{self.profile.adapter_id} bridge is not configured")
        encoded = None if body is None else json.dumps(body).encode()
        headers = {"accept": "application/json"}
        if encoded is not None:
            headers["content-type"] = "application/json"
        if self.token:
            headers["authorization"] = f"Bearer {self.token}"
        request = Request(f"{self.base_url}{path}", data=encoded, headers=headers, method="GET" if body is None else "POST")
        try:
            with urlopen(request, timeout=8) as response:
                raw = response.read(MAX_BRIDGE_RESPONSE_BYTES + 1)
        except HTTPError as error:
            raise RuntimeError(f"bridge HTTP error {error.code}") from error
        except URLError as error:
            raise RuntimeError("bridge unavailable") from error
        if len(raw) > MAX_BRIDGE_RESPONSE_BYTES:
            raise RuntimeError("bridge response is too large")
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise RuntimeError("bridge response must be a JSON object")
        return result


class DeviceHub:
    def __init__(self, adapters: list[RuntimeAdapter]) -> None:
        if not adapters:
            raise ValueError("at least one adapter is required")
        self._adapters = {adapter.profile.adapter_id: adapter for adapter in adapters}
        self._active_id = next(adapter.profile.adapter_id for adapter in adapters if adapter.profile.available)
        self._lock = threading.RLock()

    @property
    def active_id(self) -> str:
        return self._active_id

    def profiles(self) -> list[dict[str, Any]]:
        return [
            {**adapter.profile.to_dict(), "active": adapter.profile.adapter_id == self._active_id}
            for adapter in self._adapters.values()
        ]

    def select(self, adapter_id: str) -> dict[str, Any]:
        with self._lock:
            adapter = self._adapters.get(adapter_id)
            if adapter is None:
                raise ValueError("unknown adapter")
            if not adapter.profile.available:
                raise ValueError("adapter bridge is not configured")
            current = self._adapters[self._active_id]
            current_state = current.state()
            if current_state.get("connection_state") == "connected":
                raise ValueError("disconnect the active adapter before switching")
            self._active_id = adapter_id
            return {"active_adapter": adapter_id, "state": adapter.state()}

    def discover(self, timeout_seconds: float = 5.0) -> dict[str, Any]:
        adapter = self._active()
        return {"adapter_id": self._active_id, "devices": adapter.discover(timeout_seconds)}

    def state(self) -> dict[str, Any]:
        return self._active().state()

    def events(self) -> list[dict[str, Any]]:
        return self._active().events()

    def execute(self, name: str, command_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if name not in ALLOWED_COMMANDS:
            raise ValueError("unsupported command")
        return self._active().execute(name, command_id, dict(payload or {}))

    def reset(self) -> dict[str, Any]:
        return self._active().reset()

    def _active(self) -> RuntimeAdapter:
        return self._adapters[self._active_id]


def _external_profile(
    adapter_id: str,
    name: str,
    vendor: str,
    transport: str,
    mode: str,
    env_name: str,
    capabilities: tuple[str, ...],
    evidence: str,
    limitations: tuple[str, ...],
) -> ExternalBridgeAdapter:
    url = os.getenv(env_name)
    token = os.getenv(f"{env_name}_TOKEN")
    return ExternalBridgeAdapter(
        AdapterProfile(adapter_id, name, vendor, transport, mode, bool(url), capabilities, evidence, limitations),
        url,
        token,
    )


def build_default_hub() -> DeviceHub:
    return DeviceHub([
        SimulatorAdapter(),
        _external_profile(
            "heycyan-licensed-sdk",
            "HeyCyan licensed SDK bridge",
            "HeyCyan-compatible",
            "Android BLE + vendor Wi-Fi transfer",
            "licensed_external_bridge",
            "SMART_GLASSES_HEYCYAN_BRIDGE_URL",
            ("device.battery", "device.version", "camera.photo", "camera.video", "audio.recording", "media.list", "media.transfer"),
            "Public SDK capability surface; proprietary SDK requires written authorization.",
            ("No SDK binary included", "Live preview/streaming not established by current evidence"),
        ),
        _external_profile(
            "mentra-bluetooth-sdk",
            "MentraOS Bluetooth SDK bridge",
            "Mentra",
            "Android/iOS Bluetooth SDK",
            "open_external_bridge",
            "SMART_GLASSES_MENTRA_BRIDGE_URL",
            ("camera.photo", "camera.video", "audio.recording", "display.text", "stream.live"),
            "MentraOS and Bluetooth SDK public repositories; capability negotiation required.",
            ("Supported capabilities vary by glasses", "Cloud routing and retention require local review"),
        ),
        _external_profile(
            "brilliant-frame-sdk",
            "Brilliant Frame SDK bridge",
            "Brilliant Labs",
            "BLE + Lua runtime",
            "open_external_bridge",
            "SMART_GLASSES_FRAME_BRIDGE_URL",
            ("camera.photo", "display.text", "audio.recording"),
            "Official Frame SDK/documentation and open firmware; negotiate actual device capabilities.",
            ("Different interaction model from camera-only HeyCyan devices",),
        ),
    ])
