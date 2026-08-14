# Voice runtime

Dependency-free transcript and voice-command contracts.

- `SyntheticTranscriber` supports deterministic tests without a speech model.
- `NarrationBuffer` keeps final transcript text bounded and in memory.
- `VoiceCommandParser` uses an exact allowlist and confidence gate.
- `VoiceCommandGuard` rejects stale or duplicate activations inside a cooldown.
- Capture commands require explicit confirmation.

Connect Android SpeechRecognizer, Vosk, whisper.cpp, or another reviewed
adapter at the transcript boundary. The parser itself never touches a device.
