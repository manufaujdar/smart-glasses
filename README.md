# Smart Glasses Clinical Platform

Clinical smart-glasses workflows are difficult to test when device behavior, capture, voice, and safe-stop states are not modeled together. Smart Glasses Clinical Platform is an Android-first research and prototyping workspace that simulates those contracts before hardware deployment.

The first hardware target is HeyCyan-compatible camera glasses. The architecture deliberately keeps the device driver behind a small capability API so the same clinical workflows can later run on MentraOS-compatible devices, Brilliant Frame/Halo, Vuzix, or proprietary hardware.

## Start here

1. Read [`docs/00-project-overview.md`](docs/00-project-overview.md).
2. Review the [`docs/research/open-source-repository-review.md`](docs/research/open-source-repository-review.md) and the HeyCyan [`docs/protocols/heycyan-compatibility.md`](docs/protocols/heycyan-compatibility.md).
3. For surgeon-facing work, read [`docs/surgery/START_HERE.md`](docs/surgery/START_HERE.md).
4. Run the device and surgical-session simulators:

   ```bash
   python3 -m unittest discover -s tests -v
   python3 tools/device_simulator.py --scenario happy-path
   python3 tools/device_gateway.py --port 8767
   python3 tools/surgical_session_simulator.py
   python3 tools/ot_runtime_simulator.py
   ```

   For the dependency-free synthetic JSON gateway, run
   `python3 tools/device_gateway.py --port 8767`. It provides `GET /health`,
   `GET /api/state`, `GET /api/events`, `POST /api/command`, and
   `POST /api/reset` on loopback only.

   Example command:

   ```bash
   curl -s http://127.0.0.1:8767/api/command \
     -H 'content-type: application/json' \
     -d '{"name":"device.connect","command_id":"connect-1"}'
   ```

   The gateway is synthetic and fail-closed: it does not connect to physical
   glasses, accept clinical navigation commands, or store patient data.

   For the multi-adapter frontend/backend integration lab:

   ```bash
   ./scripts/bootstrap.sh
   .venv/bin/python tools/integration_server.py
   ```

   Open `http://127.0.0.1:8766`. The simulator supports discovery, connection,
   camera/photo/video/audio/stream lifecycle, media metadata, browser-local
   camera/microphone capture, WebSocket events and push-to-talk commands.
   HeyCyan, Mentra and Brilliant profiles remain unavailable until their
   authorized external bridge URL is configured; see
   [`docs/architecture/device-integration-runtime.md`](docs/architecture/device-integration-runtime.md).

5. For a physical Android/HeyCyan test, follow [`apps/android-controller/README.md`](apps/android-controller/README.md).

## Open-source and research boundary

The original project code is available under Apache-2.0. See [LICENSE](LICENSE),
[NOTICE](NOTICE), [CONTRIBUTING.md](CONTRIBUTING.md),
[GOVERNANCE.md](GOVERNANCE.md), and [COMPLIANCE.md](COMPLIANCE.md). Third-party
SDKs, source archives, datasets, and models retain their own terms and require
separate provenance review. A version or passing test suite does not imply
clinical validation, regulatory clearance, or production readiness.

## Repository map

```text
apps/android-controller/       Android companion and HeyCyan adapter boundary
packages/device-contracts/     Vendor-neutral device events and commands
packages/device_runtime/       Multi-adapter runtime and external bridge clients
packages/surgical-workflows/   Non-clinical OR session and safety-state contracts
packages/media-runtime/         Bounded low-latency video and image-quality controls
packages/voice-runtime/         Narration and allowlisted voice-command contracts
services/clinical-gateway/     Future PHI-aware policy and integration service
services/ot-runtime/            Synthetic OT-safe media/voice session orchestrator
tools/                         Deterministic local device simulator
tools/integration_server.py    FastAPI multi-adapter backend and webapp server
tools/ot_runtime_simulator.py  End-to-end synthetic media/voice/OT smoke tool
webapp/                        Calm local simulator console and method page
tools/lidar_wound_depth/       Calibrated LiDAR surface-depth research tool
tools/lidar_wound_progress/    Standalone longitudinal LiDAR geometry reviewer
tools/lidar_wound_progress/webapp/  Local-first camera/depth review webapp
tools/lidar_wound_progress/local_service.py  Loopback SQLite summary service
tests/                         Protocol/state-machine tests
docs/                          Architecture, research, safety, product and test plans
third_party/                   License records and placeholders; no unlicensed SDK code
```

## Current scope

- simulated connection lifecycle (physical BLE discovery remains hardware-gated)
- battery, version and media-count queries
- photo, video and audio controls
- media-count queries; transfer interruption and checksum handling remain planned
- device simulator and event log
- declared capability enforcement and safe-state rules in the simulator
- idempotent command replay behavior in the simulator
- capability-mismatch rejection before device actions
- active-session safe stops for disconnect, critical battery, and capture-indicator loss
- groundwork for clinical capture, telepresence and documentation workflows
- vendor-neutral LiDAR surface-depth measurements with synthetic wound-surface fixtures
- standalone longitudinal geometry signals with synthetic serial LiDAR captures
- a runnable, synthetic surgical-observation session state machine
- bounded low-latency frame buffering with keyframe-aware dropping
- luma-based transport quality gates and adaptive media profiles
- transcript/narration contracts and confirmation-gated voice commands
- synthetic OT runtime with preflight, voice start/stop, live frame publishing,
  and disconnect-safe stopping

This repository is a research prototype. It must not be used for diagnosis, treatment selection, surgical navigation, or production handling of patient data.

The Android adapter sources define a licensed-SDK boundary but are not yet a
buildable Android application. Physical-device behavior, permissions, thermal
limits, media checksums, and the validation targets in
`docs/testing/device-validation-plan.md` remain hardware-gated.

The media and voice runtimes are intentionally adapter-first. They are
functional with synthetic frames and transcripts; real glasses streaming,
continuous speech recognition, codec tuning, and operating-room deployment
still require hardware, network, permission, safety, privacy, security, and
human-factors validation.
