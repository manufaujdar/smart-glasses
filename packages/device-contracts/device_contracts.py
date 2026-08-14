"""Vendor-neutral command and event contracts for prototyping."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class Capability(str, Enum):
    BATTERY = "device.battery"
    VERSION = "device.version"
    PHOTO = "camera.photo"
    VIDEO = "camera.video"
    AUDIO = "audio.recording"
    MEDIA_LIST = "media.list"
    MEDIA_TRANSFER = "media.transfer"
    DISPLAY = "display.text"
    CAMERA_PREVIEW = "camera.preview"
    LIVE_STREAM = "stream.live"
    VOICE_COMMAND = "voice.command"


class ConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    DISCOVERING = "discovering"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DEGRADED = "degraded"


@dataclass(frozen=True)
class DeviceCommand:
    name: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    command_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass(frozen=True)
class DeviceEvent:
    name: str
    device_id: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    command_id: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
