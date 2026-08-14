# Open-source runtime review: media, voice, and OT structure

Reviewed August 10, 2026. This review records architectural patterns and
license boundaries; no upstream source code, model weights, device firmware,
or clinical data is copied into this repository.

## References and adopted patterns

| Reference | Useful structure | Adopted here | Boundary |
|---|---|---|---|
| [MentraOS](https://github.com/Mentra-Community/MentraOS) | Phone-hosted runtime owns pairing, connection, data streaming, hardware access, and app lifecycle | Keep one host/runtime connection owner and expose vendor-neutral capabilities | This project does not bundle MentraOS code or claim compatibility |
| [Mentra Bluetooth SDK Starter Kit](https://github.com/Mentra-Community/Mentra-Bluetooth-SDK-Starter-Kit) | Platform-specific examples and explicit BLE lifecycle, capability, and media-streaming surfaces | Keep device adapters separate from media and voice contracts | Published SDK dependency and license review are required before Android integration |
| [LiveKit](https://github.com/livekit/livekit) | WebRTC/SFU transport, reconnects, simulcast/SVC, UDP/TCP/TURN, ingress/egress | Use an injectable `FrameSink`; add WebRTC/LiveKit only as a transport adapter | The checked-in sink is synthetic and in-memory; no network stream is created |
| [Vosk API](https://github.com/alphacep/vosk-api) | Offline, streaming speech recognition with per-platform examples | Keep transcription behind a `TranscriptEvent` adapter | Models and language licenses must be selected separately |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Portable C/C++ inference and a real-time audio-stream example | Treat local inference as an optional host adapter | Inference does not by itself provide consent, command safety, or clinical validation |
| [Android SpeechRecognizer](https://developer.android.com/reference/android/speech/SpeechRecognizer) | Android speech API and optional on-device recognizer | Host Android microphone permissions and online/offline policy outside the core | Android warns that recognition may stream audio to remote servers and is not intended for continuous recognition |

## Project structure

```text
packages/media-runtime/
  media_runtime.py       # quality report, bounded queue, sink contract, profiles
packages/voice-runtime/
  voice_runtime.py       # transcript contract, narration buffer, command allowlist
services/ot-runtime/
  ot_runtime.py          # consent/indicator preflight, streaming, voice, safe stop
tools/ot_runtime_simulator.py
  synthetic end-to-end demonstration; no real media or audio
tests/
  test_media_runtime.py
  test_voice_runtime.py
  test_ot_runtime.py
docs/architecture/ot-media-voice-runtime.md
  latency, quality, adapter, and OT safety contract
```

## Why these boundaries matter

1. `packages/media-runtime` owns bounded buffering and quality gates. It can
   reject stale or unusable frames before a transport queue becomes a latency
   bottleneck.
2. `packages/voice-runtime` converts transcript text into a small allowlist of
   intents. It has no device side effects, and photo capture requires explicit
   confirmation.
3. `services/ot-runtime` owns session state and fail-safe behavior. A missing
   capability, low battery, missing consent, hidden capture indicator, or
   disconnect prevents or stops output.
4. Hardware, Android permissions, codecs, WebRTC, LiveKit, and speech models
   remain adapters. They can be tested independently and reviewed for their
   own licenses, data flows, and failure modes.

## Implementation status

The current code is a functional synthetic runtime: it accepts synthetic frame
packets and transcript events, applies bounded backpressure and quality gates,
and produces deterministic events. It is not yet a physical-glasses streamer,
continuous speech recognizer, or clinical system. Real-device work requires an
Android adapter, a permission/consent UX, a selected speech engine, a reviewed
WebRTC transport, hardware measurements, and human-factors/security review.
