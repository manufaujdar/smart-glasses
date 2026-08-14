"""Streaming voice contracts with strict, side-effect-free command parsing.

The runtime accepts transcript events rather than bundling a speech model.
Android SpeechRecognizer, Vosk, whisper.cpp, or a vendor microphone adapter
can be connected at this boundary.  This keeps model downloads, licenses,
network behavior, and microphone permissions explicit to the host application.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from time import monotonic_ns


class TranscriptKind(str, Enum):
    PARTIAL = "partial"
    FINAL = "final"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class AudioChunk:
    sequence: int
    captured_at_ms: int
    pcm: bytes
    sample_rate_hz: int = 16_000
    channels: int = 1


@dataclass(frozen=True, slots=True)
class TranscriptEvent:
    kind: TranscriptKind
    text: str
    confidence: float
    sequence: int


class SyntheticTranscriber:
    """Text-in test double; no audio or transcript is persisted."""

    def __init__(self) -> None:
        self._sequence = 0

    def submit_text(
        self, text: str, *, final: bool = True, confidence: float = 1.0
    ) -> TranscriptEvent:
        if not text or not text.strip():
            raise ValueError("text must not be empty")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        self._sequence += 1
        return TranscriptEvent(
            kind=TranscriptKind.FINAL if final else TranscriptKind.PARTIAL,
            text=text.strip(),
            confidence=confidence,
            sequence=self._sequence,
        )


class NarrationBuffer:
    """Bounded in-memory final transcript buffer for live narration."""

    def __init__(self, max_chars: int = 4_000) -> None:
        if max_chars < 100 or max_chars > 100_000:
            raise ValueError("max_chars must be between 100 and 100000")
        self.max_chars = max_chars
        self.active = False
        self._parts: list[str] = []
        self._length = 0

    def append(self, event: TranscriptEvent) -> bool:
        if event.kind is not TranscriptKind.FINAL or not event.text.strip():
            return False
        text = re.sub(r"\s+", " ", event.text.strip())
        available = self.max_chars - self._length
        if available <= 0:
            return False
        text = text[:available]
        self._parts.append(text)
        self._length += len(text)
        return True

    def read(self) -> str:
        return " ".join(self._parts)

    def consume(self) -> str:
        text = self.read()
        self._parts.clear()
        self._length = 0
        return text

    def clear(self) -> None:
        self._parts.clear()
        self._length = 0


class VoiceAction(str, Enum):
    START_STREAMING = "start_streaming"
    STOP_STREAMING = "stop_streaming"
    START_NARRATION = "start_narration"
    STOP_NARRATION = "stop_narration"
    CLEAR_VIEW = "clear_view"
    CAPTURE_PHOTO = "capture_photo"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class VoiceIntent:
    action: VoiceAction
    raw_text: str
    normalized_text: str
    confidence: float
    requires_confirmation: bool = False
    reason: str = "matched"


@dataclass(frozen=True, slots=True)
class VoiceGuardResult:
    accepted: bool
    reason: str


class VoiceCommandGuard:
    """Reject duplicate voice activations inside a bounded cooldown window."""

    def __init__(self, cooldown_ms: int = 1_000) -> None:
        if cooldown_ms < 0 or cooldown_ms > 60_000:
            raise ValueError("cooldown_ms must be between 0 and 60000")
        self.cooldown_ms = cooldown_ms
        self._last: tuple[str, int] | None = None

    def evaluate(self, intent: VoiceIntent, captured_at_ms: int) -> VoiceGuardResult:
        if captured_at_ms < 0:
            raise ValueError("captured_at_ms must be non-negative")
        if intent.action is VoiceAction.UNKNOWN:
            return VoiceGuardResult(False, "unknown_intent")
        if self._last is not None:
            last_text, last_timestamp = self._last
            if captured_at_ms < last_timestamp:
                return VoiceGuardResult(False, "stale_transcript")
            if (
                intent.normalized_text == last_text
                and captured_at_ms - last_timestamp <= self.cooldown_ms
            ):
                return VoiceGuardResult(False, "duplicate_within_cooldown")
        self._last = (intent.normalized_text, captured_at_ms)
        return VoiceGuardResult(True, "accepted")


class VoiceCommandParser:
    """Allowlist exact phrases before they can reach an OT controller."""

    MAX_COMMAND_TEXT_CHARS = 256

    _COMMANDS = {
        "start streaming": VoiceAction.START_STREAMING,
        "begin streaming": VoiceAction.START_STREAMING,
        "start live video": VoiceAction.START_STREAMING,
        "stop streaming": VoiceAction.STOP_STREAMING,
        "stop live video": VoiceAction.STOP_STREAMING,
        "start narration": VoiceAction.START_NARRATION,
        "start voice narration": VoiceAction.START_NARRATION,
        "stop narration": VoiceAction.STOP_NARRATION,
        "stop voice narration": VoiceAction.STOP_NARRATION,
        "clear view": VoiceAction.CLEAR_VIEW,
        "clear display": VoiceAction.CLEAR_VIEW,
        "capture photo": VoiceAction.CAPTURE_PHOTO,
        "take photo": VoiceAction.CAPTURE_PHOTO,
    }

    @staticmethod
    def normalize(text: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", text.lower())).strip()

    def parse(self, text: str, *, confidence: float = 1.0) -> VoiceIntent:
        if not isinstance(text, str):
            raise ValueError("text must be a string")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if len(text) > self.MAX_COMMAND_TEXT_CHARS:
            return VoiceIntent(
                VoiceAction.UNKNOWN,
                text[: self.MAX_COMMAND_TEXT_CHARS],
                "",
                confidence,
                reason="text_too_long",
            )
        normalized = self.normalize(text)
        if confidence < 0.75:
            return VoiceIntent(
                VoiceAction.UNKNOWN,
                text,
                normalized,
                confidence,
                reason="low_confidence",
            )
        action = self._COMMANDS.get(normalized, VoiceAction.UNKNOWN)
        if action is VoiceAction.UNKNOWN:
            return VoiceIntent(
                action, text, normalized, confidence, reason="not_allowlisted"
            )
        return VoiceIntent(
            action,
            text,
            normalized,
            confidence,
            requires_confirmation=action is VoiceAction.CAPTURE_PHOTO,
        )
