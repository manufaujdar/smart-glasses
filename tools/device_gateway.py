#!/usr/bin/env python3
"""Loopback-only JSON gateway for the synthetic Smart Glasses simulator.

This is a local research tool, not a physical-device controller. It exposes the
same vendor-neutral command/event contract as ``device_simulator.py`` so a
browser, mobile prototype, or integration test can exercise connection,
capability, replay, and safe-state behavior without hardware or patient data.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "device-contracts"))
sys.path.insert(0, str(ROOT / "tools"))

from device_contracts import DeviceCommand  # noqa: E402
from device_simulator import SimulatedGlasses  # noqa: E402

ALLOWED_COMMANDS = frozenset({"device.connect", "device.disconnect"}) | frozenset(
    SimulatedGlasses.COMMAND_CAPABILITIES
)
MAX_COMMAND_ID_LENGTH = 100
MAX_REQUEST_BYTES = 4096
DEFAULT_PORT = 8767


class DeviceGateway:
    """Thread-safe controller and bounded event log for one synthetic device."""

    def __init__(self, max_events: int = 200) -> None:
        if max_events < 1:
            raise ValueError("max_events must be positive")
        self.max_events = max_events
        self._lock = threading.Lock()
        self._device = SimulatedGlasses()
        self._events: list[dict[str, Any]] = []

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._device = SimulatedGlasses()
            self._events.clear()
            return {"status": "reset", "state": self._state_unlocked()}

    def health(self) -> dict[str, Any]:
        with self._lock:
            return {
                "status": "ok",
                "synthetic": True,
                "device_id": self._device.device_id,
                "connection_state": self._device.state.value,
            }

    def state(self) -> dict[str, Any]:
        with self._lock:
            return self._state_unlocked()

    def events(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {**event, "payload": dict(event["payload"])}
                for event in self._events
            ]

    def execute_command(
        self,
        name: str,
        command_id: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._validate_command(name, command_id, payload)
        command = DeviceCommand(
            name=name,
            command_id=command_id,
            payload=dict(payload or {}),
        )
        with self._lock:
            event = self._device.execute(command)
            event_dict = asdict(event)
            if not any(item["command_id"] == event.command_id for item in self._events):
                self._events.append(event_dict)
                del self._events[:-self.max_events]
            return {"event": event_dict, "state": self._state_unlocked()}

    @staticmethod
    def _validate_command(
        name: str,
        command_id: str,
        payload: dict[str, Any] | None,
    ) -> None:
        if not isinstance(name, str) or name not in ALLOWED_COMMANDS:
            raise ValueError("unsupported command")
        if not isinstance(command_id, str) or not 1 <= len(command_id) <= MAX_COMMAND_ID_LENGTH:
            raise ValueError("command_id must contain 1 to 100 characters")
        if payload is not None and not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")

    def _state_unlocked(self) -> dict[str, Any]:
        return {
            "synthetic": True,
            "device_id": self._device.device_id,
            "connection_state": self._device.state.value,
            "battery": self._device.battery,
            "photo_count": self._device.photo_count,
            "recording_audio": self._device.recording_audio,
            "recording_video": self._device.recording_video,
            "capabilities": sorted(self._device.capabilities),
        }


def create_server(port: int = DEFAULT_PORT, gateway: DeviceGateway | None = None) -> ThreadingHTTPServer:
    """Create a loopback-only server; callers own its lifecycle in tests."""

    controller = gateway or DeviceGateway()

    class GatewayHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/health":
                self._send_json(200, controller.health())
            elif path == "/api/state":
                self._send_json(200, controller.state())
            elif path == "/api/events":
                self._send_json(200, {"events": controller.events()})
            else:
                self._send_json(404, {"error": "not found"})

        def do_POST(self) -> None:
            try:
                body = self._read_json()
                path = urlsplit(self.path).path
                if path == "/api/reset":
                    result = controller.reset()
                elif path == "/api/command":
                    result = controller.execute_command(
                        body.get("name"),
                        body.get("command_id"),
                        body.get("payload", {}),
                    )
                else:
                    self._send_json(404, {"error": "not found"})
                    return
                self._send_json(200, result)
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                self._send_json(400, {"error": str(error)})

        def log_message(self, format: str, *args: object) -> None:
            return

        def _read_json(self) -> dict[str, Any]:
            length_header = self.headers.get("content-length", "0")
            length = int(length_header)
            if length < 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("request is too large")
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise ValueError("request body must be a JSON object")
            return body

        def _send_json(self, status: int, body: dict[str, Any]) -> None:
            payload = json.dumps(body, sort_keys=True).encode()
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(payload)))
            self.send_header("cache-control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

    return ThreadingHTTPServer(("127.0.0.1", port), GatewayHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the synthetic Smart Glasses JSON gateway")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    server = create_server(args.port)
    print(f"Smart Glasses synthetic gateway: http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
