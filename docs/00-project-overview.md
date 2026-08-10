# Project overview

## Objective

Build an advanced smart-glasses software system for doctors and surgeons while validating the current HeyCyan-class hardware as a camera/audio endpoint.

## Product boundary

The initial product is a clinician-controlled workflow assistant. It can capture, communicate, retrieve and draft. It does not autonomously diagnose, prescribe, triage, register graphics to anatomy, or guide instruments.

## Workstreams

| Workstream | Near-term output | Exit criterion |
|---|---|---|
| Device compatibility | HeyCyan Android bridge and simulator | repeatable scan/connect/query/capture/transfer sequence |
| Clinical experience | capture, checklist and documentation prototypes | clinicians complete tasks without added errors or distraction |
| Platform | event bus, policy gateway and audit schema | every device/AI action attributable and replayable |
| Safety/security | hazard log, threat model and prohibited-use gates | pilot review by clinical safety, privacy and security owners |
| Evidence/business | paid pilot protocol and measurement plan | baseline, target, stop rule and conversion terms agreed |

## Engineering principles

1. Capabilities, not brands: workflows request `camera.capture`, not a vendor class.
2. Phone as edge gateway: keep glasses light and use Android for policy, network and compute.
3. Local-first controls: connection, capture state and clear-stop actions cannot depend on cloud latency.
4. Explicit clinical state: patient, encounter, recording and data destination are always visible.
5. Safe degradation: loss of BLE, Wi-Fi, battery, model or backend returns to a known non-guiding state.
6. Evidence before claims: higher-risk functions require separate intended use, risk file and validation.

## First milestone

A clinician can connect the glasses, see battery/firmware status, capture a photo or audio note, transfer media to an isolated test directory, review it, and explicitly approve or delete it. All transitions are timestamped in a local audit log. No patient data is used.

## Surgeon-facing track

The surgeon-facing track starts with non-guiding observation, documentation,
checklist prompts and named tele-mentoring sessions. Its entry point is
`docs/surgery/START_HERE.md`; the executable baseline is
`tools/surgical_session_simulator.py`. Spatial registration, anatomical overlays,
instrument guidance and diagnostic or treatment recommendations are excluded
until they have a separately approved intended use, risk file, regulatory strategy
and clinical validation plan.
