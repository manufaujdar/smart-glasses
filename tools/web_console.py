#!/usr/bin/env python3
"""Loopback-only browser console for the synthetic glasses simulator."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "device-contracts"))
sys.path.insert(0, str(ROOT / "tools"))

from device_gateway import DeviceGateway  # noqa: E402

WEBAPP_ROOT = ROOT / "webapp"


def _read_webapp(name: str) -> str:
    return (WEBAPP_ROOT / name).read_text(encoding="utf-8")


CONSOLE_HTML = _read_webapp("index.html")
METHOD_HTML = _read_webapp("method.html")
STYLES_CSS = _read_webapp("styles.css")
APP_JS = _read_webapp("app.js")

_gateway = DeviceGateway()


def reset_simulator() -> dict[str, Any]:
    return _gateway.reset()


def execute_command(name: str, command_id: str) -> dict[str, Any]:
    return _gateway.execute_command(name, command_id)["event"]


def current_state() -> dict[str, Any]:
    return _gateway.state()


def current_events() -> list[dict[str, Any]]:
    return _gateway.events()


class ConsoleHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        resources = {
            "/": (CONSOLE_HTML, "text/html; charset=utf-8"),
            "/method": (METHOD_HTML, "text/html; charset=utf-8"),
            "/styles.css": (STYLES_CSS, "text/css; charset=utf-8"),
            "/app.js": (APP_JS, "text/javascript; charset=utf-8"),
        }
        if path in resources:
            body, content_type = resources[path]
            self._send(200, body, content_type)
        elif path == "/api/state":
            self._send(200, json.dumps(current_state()))
        elif path == "/api/events":
            self._send(200, json.dumps({"events": current_events()}))
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("content-length", "0"))
            if length > 4096:
                raise ValueError("request is too large")
            body = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/reset":
                result = reset_simulator()
            elif self.path == "/api/command":
                event = execute_command(body.get("name"), body.get("command_id"))
                result = {"event": event, "state": current_state()}
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
        self.send_header("x-content-type-options", "nosniff")
        self.send_header("referrer-policy", "no-referrer")
        self.send_header(
            "content-security-policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the synthetic Smart Glasses browser lab")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), ConsoleHandler)
    print(f"Smart Glasses simulator lab: http://127.0.0.1:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
