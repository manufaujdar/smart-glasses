"""Device-neutral contract for native depth streams."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Protocol, Sequence


class DepthProviderError(ValueError):
    """Raised when a native depth frame is incomplete or unsafe to consume."""


@dataclass(frozen=True)
class NativeDepthFrame:
    timestamp_ns: int
    width: int
    height: int
    depth: tuple[tuple[float, ...], ...]
    depth_unit: str
    sensor_name: str
    intrinsics: tuple[tuple[float, ...], ...] | None = None
    confidence: tuple[tuple[int, ...], ...] | None = None

    def __post_init__(self) -> None:
        if self.timestamp_ns < 0 or self.width <= 0 or self.height <= 0:
            raise DepthProviderError("frame dimensions and timestamp must be valid")
        if self.depth_unit not in {"m", "mm"}:
            raise DepthProviderError("depth_unit must be 'm' or 'mm'")
        if len(self.depth) != self.height or any(len(row) != self.width for row in self.depth):
            raise DepthProviderError("depth values do not match frame dimensions")
        if any(not isfinite(value) or value < 0 for row in self.depth for value in row):
            raise DepthProviderError("depth values must be finite and non-negative")
        if self.confidence is not None and (len(self.confidence) != self.height or any(len(row) != self.width for row in self.confidence)):
            raise DepthProviderError("confidence values do not match frame dimensions")

    def depth_mm(self) -> tuple[tuple[float, ...], ...]:
        factor = 1000.0 if self.depth_unit == "m" else 1.0
        return tuple(tuple(value * factor for value in row) for row in self.depth)


class DepthProvider(Protocol):
    """Native platform adapter that yields true sensor depth when available."""

    def latest_frame(self) -> NativeDepthFrame | None:
        """Return the latest frame or None until the sensor has produced one."""
