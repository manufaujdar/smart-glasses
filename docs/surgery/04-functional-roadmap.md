# Functional roadmap

Each stage has an exit gate. Later stages must not begin merely because code exists.

## Stage 0 — foundation (now)

Deliver: device abstraction, deterministic simulator, surgical-session state model,
prohibited-use boundaries, repository provenance and initial hazards.

Exit: all local tests pass; disconnect always safe-stops; no patient data or secrets;
architecture and intended-use review completed.

## Stage 1 — Android bench prototype

Deliver: Android Studio project, real device connection through licensed SDK,
capability negotiation, battery/thermal status, visible recording indicator, local
encrypted audit journal and synthetic capture review/delete.

Exit: connection/capture targets in the device validation plan are met over repeated
cycles; privacy and stop controls pass fault injection.

## Stage 2 — simulation-lab workflow

Deliver: mannequin/staged-scene trial, PPE and loupe fit, voice/noise testing,
glanceable checklist prototype, session handoff and clear-view usability.

Exit: representative surgeons and OR staff complete critical tasks without added
critical errors or unacceptable workload/distraction.

## Stage 3 — secure tele-mentoring prototype

Deliver: hospital-authenticated named rooms, end-to-end transport protection,
participant/recording state, network-quality degradation and retention controls.

Exit: security/privacy owners approve the architecture; loss/rejoin tests never
resume media or guidance silently; an institution-approved protocol exists.

## Stage 4 — observational clinical feasibility

Deliver: ethics/governance-approved protocol for non-guiding documentation or remote
observation, trained operators, incident monitoring and predefined stop rules.

Exit: feasibility evidence supports a bounded intended use; no expansion by default.

## Stage 5 — bounded AI research

Deliver: frozen research question, curated dataset, subgroup/error analysis,
versioned inference pipeline, latency/expiry/abstention, shadow-mode evaluation and
model cards. Start with retrospective or staged data.

Exit: technical and clinical performance, failure modes and human reliance are
measured against an appropriate comparator. Outputs remain non-controlling.

## Stage 6 — regulated higher-risk product, if justified

Navigation, anatomical overlays or treatment-related recommendations require a new
product boundary, quality management system, formal risk/usability/software lifecycle,
regulatory engagement, clinical evidence and controlled model-change process.

## Immediate engineering backlog

1. Create the Android Gradle modules described in `apps/android-controller/README.md`.
2. Implement capability negotiation and connect the Kotlin and Python contracts.
3. Add encrypted local event-journal schema and replay tests.
4. Prototype capture review/delete with synthetic images.
5. Add policy expiry and consent-revocation events to the session controller.
6. Run 50 connect/reconnect cycles and 100 explicit capture/stop cycles.
7. Add a self-hosted tele-mentoring proof of concept only after threat-model review.
8. Define one bounded AI research question; do not begin with real-time guidance.

