# Current handoff

## Multi-device integration console and gateway

- Objective: create a runnable frontend/backend research system for connecting
  smart-glasses adapters and exercising connection, camera, photo, video, audio,
  voice-command, media, and live-stream lifecycle actions.
- Architecture: preserve `packages/device-contracts` as the vendor-neutral
  boundary; keep HeyCyan behavior in an authorized-SDK Android bridge; expose
  simulator and external bridge adapters through one loopback backend; keep
  browser camera/microphone previews distinct from glasses hardware evidence.
- Evidence boundary: public HeyCyan material describes capabilities but labels
  the SDK/protocol proprietary. No AAR, firmware, packet bytes, credentials,
  device captures, or copied upstream code may enter the repository.
- Safety gates: synthetic data by default; explicit adapter/capability labels;
  visible recording/streaming state; exact voice allowlist and confirmation;
  disconnect-safe stop; bounded event/media metadata; no clinical navigation,
  diagnosis, treatment, patient identifiers, or production-readiness claim.
- Validation: focused adapter/API/state-transition tests, full unit suite,
  Python/JavaScript checks, loopback smoke test, and separate report-only safety
  review before release.
- Active role: device/platform execution. Next owner: independent safety and
  release review, followed by licensed physical-device verification.

## Standalone LiDAR wound-progress reviewer

- Objective: add a separate open-source research tool that compares calibrated
  LiDAR/depth captures over time and reports a geometry-only trajectory signal.
- Result: `tools/lidar_wound_progress/` is self-contained and independently
  structured into a surface-metrics engine and longitudinal manifest/trend
  reviewer. It supports synthetic JSON manifests, quality gates, deterministic
  depth/volume comparisons, and explicit safety/provenance documentation.
- References reviewed: UWM wound segmentation, WoundScope provenance/routing,
  OpenGeoS LiDAR surface-depression geometry, and published 3D/LiDAR wound
  measurement studies. No source code, clinical data, weights, or SDK content
  was copied.
- License proposal: Apache License 2.0 for the standalone tool, with a
  copyright-holder confirmation gate before public release. Datasets, vendor
  SDKs, and future model weights require separate terms.
- Safety/privacy boundary: `geometry_signal` is not a healing, recovery,
  diagnosis, treatment, triage, infection, tissue-viability, or prognosis
  determination. Only synthetic data is included; patient captures and
  identifiers must remain outside Git.
- Validation: focused tests, whole-project tests, Python compilation, and the
  synthetic CLI smoke run are required before release.
- Active role: execution and open-source packaging. Next owner: human clinical
  reviewer for intended use and validation design, then a release owner to
  confirm copyright/license and whether to publish the branch.

## Depthline webapp

- Objective: provide a phone/tablet/laptop browser interface for visual camera
  reference, calibrated depth JSON import, current geometry review, and local
  baseline comparison.
- Result: `tools/lidar_wound_progress/webapp/` is a dependency-free responsive
  static webapp. RGB camera frames stay in memory; only numeric summaries are
  stored in browser-local history. A browser camera is not treated as a raw
  LiDAR depth source.
- Validation: JavaScript syntax check, JSON validation, static HTTP-server
  smoke test, full project test suite, Python compilation, and diff checks.
- Publication: `manufaujdar/smart-glasses` is now public. The current
  branch still excludes the pre-existing untracked reference snapshots.
- Active role: release packaging. Next owner: human reviewer to approve the
  public webapp wording, copyright/license candidate, and future real-sensor
  validation before any clinical use.

## Local persistence, security, and ML boundary

- Result: `tools/lidar_wound_progress/local_storage.py` provides a local-only
  SQLite store for validated numeric summaries and minimal save/delete audit
  events. It rejects images, raw depth grids, direct identifiers, oversized
  payloads, non-finite values, and unsupported fields.
- Result: `tools/lidar_wound_progress/local_service.py` provides an optional
  loopback HTTP API with bounded requests, no-store/security headers, optional
  local token authentication, and browser fallback to `localStorage` when the
  service is unavailable.
- Result: `COMPLIANCE.md` states the research-only boundary and lists the
  privacy, encryption, identity, retention, validation, and regulatory gates
  required before PHI or clinical deployment.
- Result: `ml/contracts.py` and `ml/README.md` define an optional provenance-
  first seam for segmentation or quality models. The baseline requires no AI
  API and does not commit model weights, images, or credentials.
- Validation: storage unit tests, API smoke tests, full project tests, Python
  compilation, JavaScript syntax check, static webapp smoke test, and diff
  checks remain required before release.
- Next owner: clinical/privacy/security reviewer to approve intended use,
  data handling, and validation design; release owner to confirm copyright and
  license authorization.

## Repository rename and synthetic device gateway

TASK: Rename the public repository from `smart-glasses-research` to
`smart-glasses` and add a runnable, vendor-neutral functional tool.

OUTCOME: A loopback-only JSON gateway lets developers inspect synthetic device
state, execute allowlisted commands, replay commands safely, inspect bounded
event history, and reset the simulator without hardware, credentials, or patient
data.

SCOPE: `tools/device_gateway.py`, shared web-console controller reuse, focused
HTTP/state/replay/fail-closed tests, README quickstart, and GitHub repository
rename. Physical-device control, clinical workflows, cloud services, and patient
data remain out of scope.

ACTIVE ROLE: execution and release packaging.

SAFETY GATES: loopback bind only; synthetic payloads only; allowlisted commands;
bounded request size and command IDs; existing simulator capability and
disconnect-safe behavior preserved; no clinical navigation or treatment command.

VALIDATION: `python3 -m unittest discover -s tests -v`, Python compilation,
loopback HTTP smoke tests, and independent safety review before release.

STATUS: READY FOR RELEASE — repository renamed; implementation and validation
passed; functional branch push remains.

## Low-latency media, voice, and OT runtime

TASK: Add reusable open-source runtime structure for low-latency glasses video,
image-quality bottleneck controls, transcript narration, voice commands, and
operating-room-safe orchestration.

SCOPE: `packages/media-runtime/`, `packages/voice-runtime/`,
`services/ot-runtime/`, `tools/ot_runtime_simulator.py`, focused tests, and
architecture/research documentation. Hardware, codec, WebRTC, speech-model,
and Android permission integrations remain adapter work.

SAFETY GATES: synthetic fixtures only; bounded queues and transcript buffers;
exact voice allowlist; explicit confirmation for capture; preflight consent and
visible capture-indicator checks; minimum battery/capability checks; disconnect
safe stop; no patient identifiers, clinical navigation, diagnosis, treatment,
or instrument control.

VALIDATION: focused media/voice/OT tests, whole-project unit suite, Python
compilation, and synthetic simulator smoke run. Open-source references are
documented without copying upstream code, firmware, models, or data.

RELEASE HARDENING: bounded frame payloads and metadata, stale sequence
rejection, duplicate/stale voice-command guard, command text limits, narration
command separation, and active device-health rechecks were added before
publication.

ACTIVE ROLE: execution and red-team packaging. NEXT OWNER: safety/privacy and
human-factors reviewer, then release owner for license confirmation and any
real-device adapter approval.
