#!/usr/bin/env python3
"""Loopback-only browser console for the synthetic glasses simulator."""

from __future__ import annotations

import argparse
import json
import sys
import threading
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "device-contracts"))
sys.path.insert(0, str(ROOT / "tools"))

from device_contracts import DeviceCommand  # noqa: E402
from device_simulator import SimulatedGlasses  # noqa: E402

ALLOWED_COMMANDS = {
    "device.connect", "device.disconnect", "device.get_battery", "device.get_version",
    "camera.take_photo", "camera.start_video", "camera.stop_video",
    "audio.start_recording", "audio.stop_recording", "media.get_counts",
}
CONSOLE_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Smart Glasses simulator lab</title><style>body{font:16px system-ui;max-width:900px;margin:2rem auto;padding:0 1rem}select,input,button{font:inherit;padding:.6rem}label{display:block;margin:.8rem 0}pre{background:#111827;color:#e5e7eb;padding:1rem;min-height:12rem;overflow:auto}.warn{background:#fff1ec;border-left:4px solid #a23b24;padding:.8rem}</style></head><body><h1>Smart Glasses simulator lab</h1><p class="warn">Synthetic research simulator only—not a medical device, physical-device controller, diagnostic system, or surgical navigation tool.</p><label>Command <select id="command"><option>device.connect</option><option>device.get_version</option><option>device.get_battery</option><option>camera.take_photo</option><option>camera.start_video</option><option>camera.stop_video</option><option>audio.start_recording</option><option>audio.stop_recording</option><option>media.get_counts</option><option>device.disconnect</option></select></label><label>Command ID (reuse it to test replay) <input id="id" value="browser-command-1"></label><button id="send">Send synthetic command</button><button id="reset">Reset simulator</button><pre id="result" aria-live="polite">Disconnected.</pre><script>let count=1;const out=document.querySelector('#result');async function request(path,body){const response=await fetch(path,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});out.textContent=JSON.stringify(await response.json(),null,2)}document.querySelector('#send').onclick=async()=>{try{await request('/api/command',{name:document.querySelector('#command').value,command_id:document.querySelector('#id').value})}catch(error){out.textContent=String(error)}};document.querySelector('#reset').onclick=async()=>{try{await request('/api/reset',{});count+=1;document.querySelector('#id').value='browser-command-'+count}catch(error){out.textContent=String(error)}};</script></body></html>"""

_device = SimulatedGlasses()
_lock = threading.Lock()


def reset_simulator() -> dict[str, Any]:
    global _device
    with _lock:
        _device = SimulatedGlasses()
        return {"status": "reset", "state": _device.state.value, "device_id": _device.device_id}


def execute_command(name: str, command_id: str) -> dict[str, Any]:
    if name not in ALLOWED_COMMANDS:
        raise ValueError("unsupported command")
    if not isinstance(command_id, str) or not 1 <= len(command_id) <= 100:
        raise ValueError("command_id must contain 1 to 100 characters")
    with _lock:
        return asdict(_device.execute(DeviceCommand(name=name, command_id=command_id)))


class ConsoleHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return
        self._send(200, CONSOLE_HTML, "text/html; charset=utf-8")

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            if length > 4096:
                raise ValueError("request is too large")
            body = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/reset":
                result = reset_simulator()
            elif self.path == "/api/command":
                result = execute_command(body.get("name"), body.get("command_id"))
            else:
                self.send_error(404)
                return
            self._send(200, json.dumps(result))
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            self._send(400, json.dumps({"error": str(error)}))

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: int, body: str, content_type: str = "application/json") -> None:
        payload = body.encode()
        self.send_response(status)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(payload)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the synthetic Smart Glasses browser lab")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), ConsoleHandler)
    print(f"Smart Glasses simulator lab: http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
