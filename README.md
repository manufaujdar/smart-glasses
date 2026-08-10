# Smart Glasses Clinical Platform

Android-first research and prototyping workspace for a healthcare-focused smart-glasses platform.

The first hardware target is HeyCyan-compatible camera glasses. The architecture deliberately keeps the device driver behind a small capability API so the same clinical workflows can later run on MentraOS-compatible devices, Brilliant Frame/Halo, Vuzix, or proprietary hardware.

## Start here

1. Read [`docs/00-project-overview.md`](docs/00-project-overview.md).
2. Review the [`docs/research/open-source-repository-review.md`](docs/research/open-source-repository-review.md) and the HeyCyan [`docs/protocols/heycyan-compatibility.md`](docs/protocols/heycyan-compatibility.md).
3. For surgeon-facing work, read [`docs/surgery/START_HERE.md`](docs/surgery/START_HERE.md).
4. Run the device and surgical-session simulators:

   ```bash
   python3 -m unittest discover -s tests -v
   python3 tools/device_simulator.py --scenario happy-path
   python3 tools/surgical_session_simulator.py
   ```

   For a dependency-free browser view of the synthetic device state machine, run
   `python3 tools/web_console.py` and open `http://127.0.0.1:8766`.

5. For a physical Android/HeyCyan test, follow [`apps/android-controller/README.md`](apps/android-controller/README.md).

## Repository map

```text
apps/android-controller/       Android companion and HeyCyan adapter boundary
packages/device-contracts/     Vendor-neutral device events and commands
packages/surgical-workflows/   Non-clinical OR session and safety-state contracts
services/clinical-gateway/     Future PHI-aware policy and integration service
tools/                         Deterministic local device simulator
tools/lidar_wound_depth/       Calibrated LiDAR surface-depth research tool
tools/lidar_wound_progress/    Standalone longitudinal LiDAR geometry reviewer
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

This repository is a research prototype. It must not be used for diagnosis, treatment selection, surgical navigation, or production handling of patient data.

The Android adapter sources define a licensed-SDK boundary but are not yet a
buildable Android application. Physical-device behavior, permissions, thermal
limits, media checksums, and the validation targets in
`docs/testing/device-validation-plan.md` remain hardware-gated.
