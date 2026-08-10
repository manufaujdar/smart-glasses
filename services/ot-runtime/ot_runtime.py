"""Safe-state orchestration for synthetic OT smart-glasses sessions.

This is an observation and documentation runtime.  It does not control a
surgical instrument, navigate a room, make a diagnosis, or issue a treatment
instruction.  Device, media transport, and speech engines are injected so a
real deployment can add explicit adapter and approval layers later.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import monotonic_ns
from media_runtime import FramePacket, FrameEnqueueResult, LiveVideoSession
from voice_runtime import (
    NarrationBuffer,
    TranscriptEvent,
    TranscriptKind,
    VoiceAction,
    VoiceCommandGuard,
    VoiceCommandParser,
    VoiceGuardResult,
    VoiceIntent,
)


class OTRuntimeState(str, Enum):
    IDLE = "idle"
    PREFLIGHT = "preflight"
    READY = "ready"
    STREAMING = "streaming"
    PAUSED = "paused"
    SAFE_STOP = "safe_stop"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class DeviceSnapshot:
    connected: bool
    battery_percent: int
    capabilities: frozenset[str]

    def __post_init__(self) -> None:
        if isinstance(self.battery_percent, bool) or not 0 <= self.battery_percent <= 100:
            raise ValueError("battery_percent must be between 0 and 100")
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))


@dataclass(frozen=True, slots=True)
class OTEvent:
    name: str
    state: OTRuntimeState
    payload: tuple[tuple[str, str], ...] = ()
    timestamp_ns: int = 0


class OTRuntime:
    """Explicit preflight, voice, media, and disconnect-safe state machine."""

    REQUIRED_CAPABILITIES = frozenset({"camera.video", "audio.recording", "display.text"})
    MINIMUM_BATTERY_PERCENT = 30

    def __init__(
        self,
        video_session: LiveVideoSession,
        *,
        command_parser: VoiceCommandParser | None = None,
        voice_guard: VoiceCommandGuard | None = None,
        narration_buffer: NarrationBuffer | None = None,
        max_events: int = 200,
    ) -> None:
        if max_events < 10 or max_events > 10_000:
            raise ValueError("max_events must be between 10 and 10000")
        self.video_session = video_session
        self.command_parser = command_parser or VoiceCommandParser()
        self.voice_guard = voice_guard or VoiceCommandGuard()
        self.narration = narration_buffer or NarrationBuffer()
        self.state = OTRuntimeState.IDLE
        self.session_id: str | None = None
        self.device: DeviceSnapshot | None = None
        self.consent_confirmed = False
        self.capture_indicator_visible = False
        self._events: list[OTEvent] = []
        self.max_events = max_events

    def _emit(self, name: str, **payload: object) -> OTEvent:
        event = OTEvent(
            name=name,
            state=self.state,
            payload=tuple(sorted((key, str(value)) for key, value in payload.items())),
            timestamp_ns=monotonic_ns(),
        )
        self._events.append(event)
        del self._events[:-self.max_events]
        return event

    @property
    def events(self) -> tuple[OTEvent, ...]:
        return tuple(self._events)

    def begin_preflight(self, session_id: str) -> OTEvent:
        if not session_id.startswith("SYNTHETIC-"):
            raise ValueError("only synthetic session IDs are accepted by this prototype")
        if self.state not in {OTRuntimeState.IDLE, OTRuntimeState.COMPLETED, OTRuntimeState.SAFE_STOP}:
            raise RuntimeError("a session is already active")
        self.state = OTRuntimeState.PREFLIGHT
        self.session_id = session_id
        self.device = None
        self.consent_confirmed = False
        self.capture_indicator_visible = False
        self.narration.clear()
        return self._emit("ot.preflight_started", session_id=session_id)

    def confirm_consent(self, confirmed: bool) -> OTEvent:
        if self.state is not OTRuntimeState.PREFLIGHT:
            raise RuntimeError("consent can only be confirmed during preflight")
        self.consent_confirmed = bool(confirmed)
        return self._emit("ot.consent_confirmed", confirmed=self.consent_confirmed)

    def confirm_capture_indicator(self, visible: bool) -> OTEvent:
        if self.state is not OTRuntimeState.PREFLIGHT:
            raise RuntimeError("capture indicator can only be checked during preflight")
        self.capture_indicator_visible = bool(visible)
        return self._emit("ot.capture_indicator_checked", visible=self.capture_indicator_visible)

    def arm(self, device: DeviceSnapshot) -> OTEvent:
        if self.state is not OTRuntimeState.PREFLIGHT:
            raise RuntimeError("device can only be armed during preflight")
        missing = self.REQUIRED_CAPABILITIES - device.capabilities
        if not self.consent_confirmed:
            return self._fail_safe("consent_required")
        if not self.capture_indicator_visible:
            return self._fail_safe("capture_indicator_required")
        if not device.connected:
            return self._fail_safe("device_disconnected")
        if device.battery_percent < self.MINIMUM_BATTERY_PERCENT:
            return self._fail_safe("battery_below_threshold")
        if missing:
            return self._fail_safe("missing_capabilities:" + ",".join(sorted(missing)))
        self.device = device
        self.state = OTRuntimeState.READY
        return self._emit("ot.ready", battery_percent=device.battery_percent)

    def _fail_safe(self, reason: str) -> OTEvent:
        self.video_session.clear()
        self.narration.active = False
        self.device = None
        self.state = OTRuntimeState.SAFE_STOP
        return self._emit("ot.safe_stop", reason=reason)

    def observe_device(self, device: DeviceSnapshot) -> OTEvent:
        """Re-check live device health while READY or STREAMING."""

        self.device = device
        if self.state not in {OTRuntimeState.READY, OTRuntimeState.STREAMING}:
            return self._emit("device.observed", connected=device.connected)
        missing = self.REQUIRED_CAPABILITIES - device.capabilities
        if not device.connected:
            return self._fail_safe("device_disconnected")
        if device.battery_percent < self.MINIMUM_BATTERY_PERCENT:
            return self._fail_safe("battery_below_threshold")
        if missing:
            return self._fail_safe("missing_capabilities:" + ",".join(sorted(missing)))
        return self._emit("device.health_ok", battery_percent=device.battery_percent)

    def start_streaming(self) -> OTEvent:
        if self.state is not OTRuntimeState.READY:
            return self._fail_safe("stream_start_not_ready")
        if self.device is None or not self.device.connected:
            return self._fail_safe("device_disconnected")
        self.state = OTRuntimeState.STREAMING
        return self._emit("video.streaming_started")

    def stop_streaming(self) -> OTEvent:
        if self.state not in {OTRuntimeState.STREAMING, OTRuntimeState.PAUSED}:
            return self._emit("video.stop_ignored", reason="not_streaming")
        self.video_session.clear()
        self.state = OTRuntimeState.READY
        return self._emit("video.streaming_stopped")

    def ingest_frame(self, frame: FramePacket) -> FrameEnqueueResult:
        if self.state is not OTRuntimeState.STREAMING:
            return FrameEnqueueResult(False, "runtime_not_streaming")
        result = self.video_session.ingest(frame)
        if not result.accepted:
            self._emit("video.frame_rejected", reason=result.reason)
        elif result.dropped_frame_id is not None:
            self._emit("video.frame_dropped", frame_id=result.dropped_frame_id)
        return result

    def publish_next(self) -> FramePacket | None:
        if self.state is not OTRuntimeState.STREAMING:
            return None
        frame = self.video_session.publish_next()
        if frame is not None:
            self._emit("video.frame_published", frame_id=frame.frame_id)
        return frame

    def accept_transcript(self, event: TranscriptEvent) -> VoiceIntent | None:
        if event.kind is not TranscriptKind.FINAL:
            return None
        intent = self.command_parser.parse(event.text, confidence=event.confidence)
        if self.narration.active and intent.action is VoiceAction.UNKNOWN:
            self.narration.append(event)
        return self._accept_intent(intent, captured_at_ms=event.sequence)

    def accept_voice_text(
        self,
        text: str,
        *,
        confidence: float = 1.0,
        confirmed: bool = False,
        captured_at_ms: int | None = None,
    ) -> VoiceIntent:
        intent = self.command_parser.parse(text, confidence=confidence)
        return self._accept_intent(
            intent,
            confirmed=confirmed,
            captured_at_ms=(monotonic_ns() // 1_000_000 if captured_at_ms is None else captured_at_ms),
        )

    def _accept_intent(
        self,
        intent: VoiceIntent,
        *,
        confirmed: bool = False,
        captured_at_ms: int,
    ) -> VoiceIntent:
        self._emit("voice.intent", action=intent.action.value, reason=intent.reason)
        if intent.action is VoiceAction.UNKNOWN:
            self._emit("voice.command_rejected", reason=intent.reason)
            return intent
        if intent.requires_confirmation and not confirmed:
            self._emit("voice.confirmation_required", action=intent.action.value)
            return intent
        guard_result: VoiceGuardResult = self.voice_guard.evaluate(intent, captured_at_ms)
        if not guard_result.accepted:
            self._emit("voice.command_rejected", reason=guard_result.reason)
            return intent
        if intent.action is VoiceAction.START_STREAMING:
            self.start_streaming()
        elif intent.action is VoiceAction.STOP_STREAMING:
            self.stop_streaming()
        elif intent.action is VoiceAction.START_NARRATION:
            self.narration.active = True
            self._emit("voice.narration_started")
        elif intent.action is VoiceAction.STOP_NARRATION:
            self.narration.active = False
            self._emit("voice.narration_stopped")
        elif intent.action is VoiceAction.CLEAR_VIEW:
            self._emit("display.clear_view")
        elif intent.action is VoiceAction.CAPTURE_PHOTO:
            self._emit("capture.requested")
        return intent

    def disconnect(self, reason: str = "device_disconnected") -> OTEvent:
        self.device = None
        return self._fail_safe(reason)

    def complete(self) -> OTEvent:
        self.video_session.clear()
        self.narration.active = False
        self.state = OTRuntimeState.COMPLETED
        return self._emit("ot.completed")
