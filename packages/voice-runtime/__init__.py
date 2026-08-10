"""Vendor-neutral voice narration and command primitives."""

from .voice_runtime import (
    AudioChunk,
    NarrationBuffer,
    SyntheticTranscriber,
    TranscriptEvent,
    TranscriptKind,
    VoiceAction,
    VoiceCommandGuard,
    VoiceCommandParser,
    VoiceGuardResult,
    VoiceIntent,
)

__all__ = [
    "AudioChunk",
    "NarrationBuffer",
    "SyntheticTranscriber",
    "TranscriptEvent",
    "TranscriptKind",
    "VoiceAction",
    "VoiceCommandGuard",
    "VoiceCommandParser",
    "VoiceGuardResult",
    "VoiceIntent",
]
