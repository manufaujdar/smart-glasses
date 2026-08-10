#!/usr/bin/env python3
"""Loopback-only local API for Depthline numeric record storage."""

from __future__ import annotations

import argparse
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from local_storage import LocalRecordStore, StorageValidationError, token_is_valid


MAX_BODY_BYTES = 1_000_000
ALLOWED_ORIGINS = {"http://127.0.0.1:8766", "http://localhost:8766"}


def make_handler(store: LocalRecordStore, local_token: str | None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "DepthlineLocal/0.1"

        def _origin(self) -> str | None:
            origin = self.headers.get("Origin")
            return origin if origin in ALLOWED_ORIGINS else None

        def _send(self, status: int, payload: dict | list, content_type: str = "application/json") -> None:
            encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            origin = self._origin()
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.end_headers()
            self.wfile.write(encoded)

        def _unauthorized(self) -> None:
            self._send(401, {"error": "local token required"})

        def _authorized(self) -> bool:
            if token_is_valid(local_token, self.headers.get("X-Depthline-Local-Token")):
                return True
            self._unauthorized()
            return False

        def _read_json(self) -> dict:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise StorageValidationError("invalid Content-Length") from exc
            if length <= 0 or length > MAX_BODY_BYTES:
                raise StorageValidationError("request body is empty or too large")
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise StorageValidationError("request body must be UTF-8 JSON") from exc
            if not isinstance(payload, dict):
                raise StorageValidationError("request body must be a JSON object")
            return payload

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            origin = self._origin()
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Depthline-Local-Token")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
                self.send_header("Vary", "Origin")
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            if not self._authorized():
                return
            parsed = urlparse(self.path)
            if parsed.path == "/api/health":
                self._send(200, {"status": "ok", "storage": "local-sqlite", "images_stored": False})
                return
            if parsed.path == "/api/records":
                query = parse_qs(parsed.query)
                try:
                    records = store.list(
                        query.get("wound_id", [None])[0],
                        query.get("sensor_mode", [None])[0],
                    )
                except StorageValidationError as exc:
                    self._send(400, {"error": str(exc)})
                    return
                self._send(200, {"records": records})
                return
            if parsed.path == "/api/audit":
                self._send(200, {"events": store.audit()})
                return
            self._send(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            if not self._authorized():
                return
            if urlparse(self.path).path != "/api/records":
                self._send(404, {"error": "not found"})
                return
            try:
                saved = store.save(self._read_json())
            except (StorageValidationError, ValueError, TypeError) as exc:
                self._send(400, {"error": str(exc)})
                return
            self._send(201, saved)

        def do_DELETE(self) -> None:  # noqa: N802
            if not self._authorized():
                return
            match = re.fullmatch(r"/api/records/([a-f0-9]{32})", urlparse(self.path).path)
            if not match:
                self._send(404, {"error": "not found"})
                return
            try:
                deleted = store.delete(match.group(1))
            except StorageValidationError as exc:
                self._send(400, {"error": str(exc)})
                return
            self._send(200, {"deleted": deleted})

        def log_message(self, format: str, *args: object) -> None:
            print(f"[depthline-local] {self.address_string()} - {format % args}")

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the loopback-only Depthline numeric storage service.")
    parser.add_argument("--host", default="127.0.0.1", help="loopback host only by default")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument(
        "--db",
        default=str(Path(__file__).resolve().parent / "local_data" / "depthline.sqlite3"),
        help="SQLite path; ignored by Git when inside local_data",
    )
    parser.add_argument("--token", default=os.environ.get("DEPTHLINE_LOCAL_TOKEN"))
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("refusing non-loopback host; use a reviewed deployment for network access")
    store = LocalRecordStore(args.db)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(store, args.token))
    print(f"Depthline local service listening on http://{args.host}:{args.port}")
    print("Storage is numeric-summary-only; images and raw depth grids are rejected.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
