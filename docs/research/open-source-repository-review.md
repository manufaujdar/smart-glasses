# Open-source smart-glasses repository review

Reviewed July 17, 2026. Popularity figures are snapshots and will change. Exact
source revisions selected for offline study are registered under
`third_party/reference-repositories/`.

| Repository | Snapshot | What to learn | Decision |
|---|---:|---|---|
| [MentraOS](https://github.com/Mentra-Community/MentraOS) | MIT; 2,224 stars; active | phone-hosted runtime, one shared glasses connection, concurrent mini-apps, cross-device API | strongest architecture reference for the long-term platform |
| [OpenGlass](https://github.com/BasedHardware/OpenGlass) | MIT; 4,077 stars; maintenance moved to Omi | inexpensive ESP32 camera endpoint, firmware/app split, rapid multimodal experiments | use concepts only; evaluate current [Omi](https://github.com/BasedHardware/omi) for maintained memory/AI patterns |
| [Brilliant SDK](https://github.com/brilliantlabsAR/brilliant_sdk) | BSD-3-Clause; 51 stars; active | clean BLE transport/message split, MTU-aware packetization, device-side Lua, Python/Flutter/Web parity | best protocol/SDK design reference |
| [OpenSourceSmartGlasses](https://github.com/Mentra-Community/OpenSourceSmartGlasses) | 1,138 stars | ergonomic open-hardware experimentation | hardware research reference, not the first production base |
| [HeyCyanSmartGlassesSDK](https://github.com/ebowwa/HeyCyanSmartGlassesSDK) | proprietary/no open-source license; 61 stars | available functions, public API surface, BLE/Wi-Fi workflow | do not copy or redistribute; use manufacturer binary only with permission |
| [Alternative HeyCyan App and SDK](https://github.com/FerSaiyan/Alternative-HeyCyan-App-and-SDK) | no recognized license; 54 stars; active | Android build lessons, modular audio/connectivity/transcription direction | protocol/reference reading only until a license is supplied |
| [LiveKit Android](https://github.com/livekit/client-sdk-android) | Apache-2.0; active | Android real-time audio/video rooms, reconnect and CameraX integration | tele-mentoring transport reference; hospital policy remains local |
| [OpenXR SDK Source](https://github.com/KhronosGroup/OpenXR-SDK-Source) | Apache-2.0; active | standard XR loader, API layers and `hello_xr` samples | future display/spatial abstraction; not needed for camera-only milestone |
| [MONAI Deploy App SDK](https://github.com/Project-MONAI/monai-deploy-app-sdk) | Apache-2.0; active | versioned medical-imaging operators and inference packaging | AI gateway/pipeline structure only; not a validated surgical model |
| [NVIDIA Holohub](https://github.com/nvidia-holoscan/holohub) | Apache-2.0; active | low-latency sensor pipelines and endoscopy tool-tracking examples | surgical AI research reference only; requires separate model/data/evidence review |
| [Android Camera Samples](https://github.com/android/camera-samples) | file headers are commonly Apache-2.0 but no root license detected at review | CameraX and Android camera architecture | link-only reference pending repository-level license clarification |

## Patterns worth adopting

### From MentraOS

- One connection owner multiplexes access for multiple apps.
- Applications subscribe to capabilities/events rather than handling BLE.
- Run substantial logic on the phone/cloud while glasses remain lightweight.
- Separate device support from app distribution and application lifecycle.

### From Brilliant SDK

- Split `transport` from typed `messages` and high-level `device` APIs.
- Make packetization, MTU, retry and DFU transport concerns.
- Keep platform implementations behaviorally equivalent through contract tests.
- Negotiate capabilities after connection; never assume every frame supports every sensor.

### From OpenGlass/Omi

- A low-cost camera/microphone endpoint is enough to validate many AI workflows.
- Build capture-to-understanding loops before investing in custom optics.
- Long-term memory and proactive agents require explicit consent, retention and deletion controls—especially in healthcare.

## Gaps in the open-source ecosystem

- Clinical identity and wrong-patient protections
- healthcare consent and recording governance
- FHIR/DICOM integration
- medical-device safety lifecycle and human-factors evidence
- deterministic offline/degraded behavior
- model provenance, clinical citations and release governance
- infection-control and PPE/loupe compatibility

These gaps are an opportunity: the differentiated product is a clinical control plane above interchangeable glasses hardware.

## What to build next

1. A vendor-neutral device daemon on Android with session arbitration.
2. A capability manifest for camera, audio, display, input, IMU and transfer modes.
3. A local event journal and replay simulator for deterministic testing.
4. A workflow SDK with patient-context, consent, capture and confirmation primitives.
5. A policy/model gateway with source provenance and audit.
6. A hardware certification kit that runs the same latency, battery, audio, camera and reliability tests on every device.

## Local snapshot rule

Local archives preserve exact upstream source for structural comparison; they are
not vendored runtime dependencies. See the adoption map, commit register, checksums
and provenance record before opening or using them. Dataset/model weights are not
included. CAMMA surgical datasets remain link-only because their terms, access
controls and non-commercial restrictions require project-specific review.
