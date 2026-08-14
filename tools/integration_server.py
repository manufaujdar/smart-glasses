#!/usr/bin/env python3
"""Fieldline multi-adapter backend and static web application server.

The default adapter is deterministic and synthetic. Physical devices require an
explicitly configured, separately authorized bridge process.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "device-contracts"))
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT / "tools"))

try:
    import uvicorn
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import FileResponse, JSONResponse
    from starlette.middleware.trustedhost import TrustedHostMiddleware
    from pydantic import BaseModel, Field
    from dotenv import load_dotenv
except ImportError as error:  # pragma: no cover - exercised by manual bootstrap
    raise SystemExit(
        "Integration dependencies are missing. Run ./scripts/bootstrap.sh first."
    ) from error

from device_runtime import DeviceHub, build_default_hub  # noqa: E402

WEBAPP = ROOT / "webapp"
load_dotenv(ROOT / ".env")


class AdapterSelection(BaseModel):
    adapter_id: str = Field(min_length=1, max_length=100)


class DiscoveryRequest(BaseModel):
    timeout_seconds: float = Field(default=5.0, ge=0.1, le=30.0)


class CommandRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    command_id: str = Field(min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)


class SocketHub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)

    async def publish(self, message: dict[str, Any]) -> None:
        stale: list[WebSocket] = []
        for client in tuple(self._clients):
            try:
                await client.send_json(message)
            except Exception:
                stale.append(client)
        for client in stale:
            self.disconnect(client)


def create_app(hub: DeviceHub | None = None) -> FastAPI:
    controller = hub or build_default_hub()
    sockets = SocketHub()
    app = FastAPI(
        title="Fieldline Smart Glasses Research Gateway",
        version="0.2.0",
        docs_url="/api/docs",
        redoc_url=None,
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > 65_536:
                    return JSONResponse({"error": "request is too large"}, status_code=413)
            except ValueError:
                return JSONResponse({"error": "invalid content-length"}, status_code=400)
        response = await call_next(request)
        response.headers["cache-control"] = "no-store"
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["referrer-policy"] = "no-referrer"
        response.headers["permissions-policy"] = "camera=(self), microphone=(self), geolocation=()"
        response.headers["content-security-policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self' ws: wss:; "
            "object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        )
        return response

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, error: ValueError):
        del request
        return JSONResponse({"error": str(error)}, status_code=400)

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request: Request, error: RuntimeError):
        del request
        return JSONResponse({"error": str(error)}, status_code=502)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "active_adapter": controller.active_id, "research_only": True}

    @app.get("/api/adapters")
    async def adapters() -> dict[str, Any]:
        return {"active_adapter": controller.active_id, "adapters": controller.profiles()}

    @app.post("/api/adapters/select")
    async def select_adapter(body: AdapterSelection) -> dict[str, Any]:
        result = controller.select(body.adapter_id)
        await sockets.publish({"type": "adapter.selected", **result})
        return result

    @app.post("/api/discover")
    async def discover(body: DiscoveryRequest) -> dict[str, Any]:
        result = controller.discover(body.timeout_seconds)
        await sockets.publish({"type": "device.discovery_completed", **result})
        return result

    @app.get("/api/state")
    async def state() -> dict[str, Any]:
        return controller.state()

    @app.get("/api/events")
    async def events() -> dict[str, Any]:
        return {"events": controller.events()}

    @app.post("/api/command")
    async def command(body: CommandRequest) -> dict[str, Any]:
        result = controller.execute(body.name, body.command_id, body.payload)
        await sockets.publish({"type": "device.event", **result})
        return result

    @app.post("/api/reset")
    async def reset() -> dict[str, Any]:
        result = controller.reset()
        await sockets.publish({"type": "device.reset", **result})
        return result

    @app.websocket("/ws/events")
    async def websocket_events(websocket: WebSocket) -> None:
        origin = websocket.headers.get("origin")
        host = websocket.headers.get("host")
        if origin and urlsplit(origin).netloc != host:
            await websocket.close(code=1008, reason="same-origin websocket required")
            return
        await sockets.connect(websocket)
        try:
            await websocket.send_json({"type": "state.snapshot", "state": controller.state()})
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            sockets.disconnect(websocket)

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(WEBAPP / "index.html")

    @app.get("/method")
    async def method() -> FileResponse:
        return FileResponse(WEBAPP / "method.html")

    @app.get("/{asset_name}")
    async def asset(asset_name: str) -> FileResponse:
        allowed = {"app.js", "styles.css"}
        if asset_name not in allowed:
            return JSONResponse({"error": "not found"}, status_code=404)
        return FileResponse(WEBAPP / asset_name)

    return app


app = create_app()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Fieldline multi-adapter research gateway")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--host", default="127.0.0.1", choices=["127.0.0.1", "localhost"])
    args = parser.parse_args()
    uvicorn.run("integration_server:app", app_dir=str(ROOT / "tools"), host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
