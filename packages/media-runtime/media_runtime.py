"""Deterministic media controls for low-latency smart-glasses streaming.

This module deliberately stops at an adapter boundary.  It does not decode,
encode, persist, or transmit real camera data.  A device adapter can turn a
camera frame into :class:`FramePacket`, and a WebRTC/LiveKit adapter can
implement :class:`FrameSink` without changing the safety and backpressure
logic here.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
from math import sqrt
from threading import RLock
from typing import Deque, Protocol, Sequence


MAX_FRAME_PAYLOAD_BYTES = 8 * 1024 * 1024


class DropPolicy(str, Enum):
    """How a bounded queue behaves when capture is faster than publishing."""

    DROP_OLDEST = "drop_oldest"
    DROP_NON_KEYFRAME = "drop_non_keyframe"


@dataclass(frozen=True, slots=True)
class VideoProfile:
    """A capture/publish target selected by the latency controller."""

    name: str
    width: int
    height: int
    fps: int
    bitrate_kbps: int


LOW_LATENCY_PROFILE = VideoProfile("low-latency", 640, 360, 24, 700)
BALANCED_PROFILE = VideoProfile("balanced", 1280, 720, 30, 1_500)
DETAIL_PROFILE = VideoProfile("detail", 1920, 1080, 30, 2_500)


@dataclass(frozen=True, slots=True)
class FrameQualityReport:
    """Cheap luma-only indicators used before a frame enters the queue."""

    score: float
    mean_luma: float
    clipped_low_ratio: float
    clipped_high_ratio: float
    detail_score: float
    reasons: tuple[str, ...]


class ImageQualityAnalyzer:
    """Analyze bounded luma samples without requiring an image library.

    Device adapters may compute representative luma samples from a real frame.
    The score is a transport-quality gate, not a clinical image assessment.
    """

    def __init__(self, minimum_width: int = 640, minimum_height: int = 360) -> None:
        if minimum_width < 1 or minimum_height < 1:
            raise ValueError("minimum dimensions must be positive")
        self.minimum_width = minimum_width
        self.minimum_height = minimum_height

    def analyze(
        self, width: int, height: int, luma_samples: Sequence[int]
    ) -> FrameQualityReport:
        if width <= 0 or height <= 0:
            raise ValueError("frame dimensions must be positive")
        if not luma_samples:
            raise ValueError("at least one luma sample is required")
        if len(luma_samples) > 100_000:
            raise ValueError("luma sample count exceeds the bounded analysis limit")
        if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255 for value in luma_samples):
            raise ValueError("luma samples must be integers from 0 through 255")

        count = len(luma_samples)
        mean_luma = sum(luma_samples) / count
        clipped_low_ratio = sum(value <= 8 for value in luma_samples) / count
        clipped_high_ratio = sum(value >= 247 for value in luma_samples) / count
        mean_delta = sum(
            abs(left - right) for left, right in zip(luma_samples, luma_samples[1:])
        ) / max(1, count - 1)
        variance = sum((value - mean_luma) ** 2 for value in luma_samples) / count

        resolution_score = min(
            1.0,
            width / self.minimum_width,
            height / self.minimum_height,
        )
        exposure_score = 1.0 - min(1.0, clipped_low_ratio + clipped_high_ratio)
        detail_score = min(1.0, mean_delta / 32.0)
        dynamic_score = min(1.0, sqrt(variance) / 64.0)
        score = round(
            max(
                0.0,
                min(
                    1.0,
                    0.30 * resolution_score
                    + 0.30 * exposure_score
                    + 0.25 * detail_score
                    + 0.15 * dynamic_score,
                ),
            ),
            4,
        )

        reasons: list[str] = []
        if width < self.minimum_width or height < self.minimum_height:
            reasons.append("low_resolution")
        if clipped_low_ratio >= 0.20:
            reasons.append("underexposed")
        if clipped_high_ratio >= 0.20:
            reasons.append("overexposed")
        if detail_score < 0.15:
            reasons.append("low_detail")

        return FrameQualityReport(
            score=score,
            mean_luma=round(mean_luma, 3),
            clipped_low_ratio=round(clipped_low_ratio, 4),
            clipped_high_ratio=round(clipped_high_ratio, 4),
            detail_score=round(detail_score, 4),
            reasons=tuple(reasons),
        )


@dataclass(frozen=True, slots=True)
class FramePacket:
    """A bounded, ephemeral frame envelope exchanged between adapters."""

    frame_id: str
    sequence: int
    captured_at_ms: int
    width: int
    height: int
    codec: str
    payload: bytes
    keyframe: bool = False
    quality: FrameQualityReport | None = None

    def __post_init__(self) -> None:
        if not self.frame_id or len(self.frame_id) > 128:
            raise ValueError("frame_id must be between 1 and 128 characters")
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 0:
            raise ValueError("sequence must be a non-negative integer")
        if isinstance(self.captured_at_ms, bool) or not isinstance(self.captured_at_ms, int) or self.captured_at_ms < 0:
            raise ValueError("captured_at_ms must be non-negative")
        if self.width < 1 or self.height < 1:
            raise ValueError("frame dimensions must be positive")
        if self.width > 8_192 or self.height > 8_192:
            raise ValueError("frame dimensions exceed the bounded adapter limit")
        if not self.codec or len(self.codec) > 32:
            raise ValueError("codec must be between 1 and 32 characters")
        if not isinstance(self.payload, bytes):
            raise ValueError("payload must be encoded bytes")
        if len(self.payload) > MAX_FRAME_PAYLOAD_BYTES:
            raise ValueError("encoded frame exceeds the bounded payload limit")


@dataclass(frozen=True, slots=True)
class FrameEnqueueResult:
    accepted: bool
    reason: str
    dropped_frame_id: str | None = None


class BoundedFrameBuffer:
    """Small queue that favors freshness and protects keyframes when possible."""

    def __init__(self, max_frames: int = 3, drop_policy: DropPolicy = DropPolicy.DROP_OLDEST) -> None:
        if max_frames < 1 or max_frames > 32:
            raise ValueError("max_frames must be between 1 and 32")
        self.max_frames = max_frames
        self.drop_policy = drop_policy
        self._frames: Deque[FramePacket] = deque()
        self._lock = RLock()

    def push(self, frame: FramePacket) -> FrameEnqueueResult:
        with self._lock:
            if len(self._frames) < self.max_frames:
                self._frames.append(frame)
                return FrameEnqueueResult(True, "queued")

            if self.drop_policy is DropPolicy.DROP_OLDEST:
                dropped = self._frames.popleft()
                self._frames.append(frame)
                return FrameEnqueueResult(True, "dropped_oldest", dropped.frame_id)

            non_keyframe_index = next(
                (index for index, item in enumerate(self._frames) if not item.keyframe),
                None,
            )
            if non_keyframe_index is None and not frame.keyframe:
                return FrameEnqueueResult(False, "queue_full_keyframes")
            if non_keyframe_index is None:
                dropped = self._frames.popleft()
            else:
                self._frames.rotate(-non_keyframe_index)
                dropped = self._frames.popleft()
                self._frames.rotate(non_keyframe_index)
            self._frames.append(frame)
            return FrameEnqueueResult(True, "dropped_non_keyframe", dropped.frame_id)

    def pop(self) -> FramePacket | None:
        with self._lock:
            return self._frames.popleft() if self._frames else None

    def clear(self) -> int:
        with self._lock:
            count = len(self._frames)
            self._frames.clear()
            return count

    @property
    def depth(self) -> int:
        with self._lock:
            return len(self._frames)


class FrameSink(Protocol):
    """Transport boundary for WebRTC, LiveKit, or another publisher."""

    def publish(self, frame: FramePacket) -> bool:
        """Publish one frame and return whether the transport accepted it."""


class InMemoryFrameSink:
    """Synthetic sink used by tests and the OT demo; it never persists media."""

    def __init__(self) -> None:
        self.frames: list[FramePacket] = []

    def publish(self, frame: FramePacket) -> bool:
        self.frames.append(frame)
        return True


@dataclass(slots=True)
class StreamStats:
    enqueued_frames: int = 0
    published_frames: int = 0
    dropped_frames: int = 0
    rejected_quality: int = 0
    rejected_stale: int = 0
    rejected_queue: int = 0
    sink_failures: int = 0
    queue_depth: int = 0


@dataclass(frozen=True, slots=True)
class AdaptiveProfileDecision:
    profile: VideoProfile
    reason: str


class LatencyController:
    """Choose a transport profile from observable pressure signals."""

    def choose(
        self,
        *,
        queue_depth: int,
        rtt_ms: float,
        dropped_frames: int,
        source_quality: float,
    ) -> AdaptiveProfileDecision:
        if isinstance(queue_depth, bool) or queue_depth < 0:
            raise ValueError("queue_depth must be non-negative")
        if rtt_ms < 0:
            raise ValueError("rtt_ms must be non-negative")
        if dropped_frames < 0:
            raise ValueError("dropped_frames must be non-negative")
        if not 0.0 <= source_quality <= 1.0:
            raise ValueError("source_quality must be between 0 and 1")
        if queue_depth >= 3 or rtt_ms > 250 or dropped_frames > 0:
            return AdaptiveProfileDecision(LOW_LATENCY_PROFILE, "transport_pressure")
        if source_quality < 0.55:
            return AdaptiveProfileDecision(BALANCED_PROFILE, "source_quality_limit")
        if source_quality >= 0.85 and queue_depth == 0 and rtt_ms <= 100:
            return AdaptiveProfileDecision(DETAIL_PROFILE, "stable_high_quality")
        return AdaptiveProfileDecision(BALANCED_PROFILE, "balanced_default")


class LiveVideoSession:
    """Quality-gated, bounded live-video pipeline with an injectable sink."""

    def __init__(
        self,
        sink: FrameSink,
        *,
        frame_buffer: BoundedFrameBuffer | None = None,
        minimum_quality: float = 0.45,
    ) -> None:
        if not 0.0 <= minimum_quality <= 1.0:
            raise ValueError("minimum_quality must be between 0 and 1")
        self.sink = sink
        self.frame_buffer = frame_buffer or BoundedFrameBuffer()
        self.minimum_quality = minimum_quality
        self._stats = StreamStats()
        self._last_sequence: int | None = None

    def ingest(self, frame: FramePacket) -> FrameEnqueueResult:
        if self._last_sequence is not None and frame.sequence <= self._last_sequence:
            self._stats.rejected_stale += 1
            self._stats.queue_depth = self.frame_buffer.depth
            return FrameEnqueueResult(False, "stale_frame")
        self._last_sequence = frame.sequence
        if frame.quality is not None and frame.quality.score < self.minimum_quality:
            self._stats.rejected_quality += 1
            self._stats.queue_depth = self.frame_buffer.depth
            return FrameEnqueueResult(False, "quality_gate")

        result = self.frame_buffer.push(frame)
        if result.accepted:
            self._stats.enqueued_frames += 1
        else:
            self._stats.rejected_queue += 1
        if result.dropped_frame_id is not None:
            self._stats.dropped_frames += 1
        self._stats.queue_depth = self.frame_buffer.depth
        return result

    def publish_next(self) -> FramePacket | None:
        frame = self.frame_buffer.pop()
        if frame is None:
            self._stats.queue_depth = 0
            return None
        if self.sink.publish(frame):
            self._stats.published_frames += 1
            self._stats.queue_depth = self.frame_buffer.depth
            return frame
        self._stats.sink_failures += 1
        self._stats.queue_depth = self.frame_buffer.depth
        return None

    def clear(self) -> int:
        cleared = self.frame_buffer.clear()
        self._stats.queue_depth = 0
        self._last_sequence = None
        return cleared

    @property
    def stats(self) -> StreamStats:
        current = StreamStats(
            enqueued_frames=self._stats.enqueued_frames,
            published_frames=self._stats.published_frames,
            dropped_frames=self._stats.dropped_frames,
            rejected_quality=self._stats.rejected_quality,
            rejected_stale=self._stats.rejected_stale,
            rejected_queue=self._stats.rejected_queue,
            sink_failures=self._stats.sink_failures,
            queue_depth=self._stats.queue_depth,
        )
        current.queue_depth = self.frame_buffer.depth
        return current
