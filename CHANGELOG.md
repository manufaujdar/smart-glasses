# Changelog

## Unreleased

- Added the Fieldline multi-adapter FastAPI gateway and responsive integration
  console with adapter discovery/selection, capability-gated device actions,
  WebSocket events, browser-local camera/microphone capture, push-to-talk voice
  controls, and simulator media/preview/stream state transitions.
- Added external bridge profiles and contracts for an authorized HeyCyan SDK,
  Mentra Bluetooth SDK, and Brilliant Frame SDK, plus an optional LiveKit
  transport recommendation. No vendor binary, firmware or packet code is
  included.

- Added Apache-2.0 licensing, citation, notice, governance, compliance, conduct,
  validation, model-card, dataset-card, issue, pull-request, and dependency
  maintenance scaffolding for public research collaboration.
- Replaced the inline simulator page with the Fieldline local research console,
  including device-state cards, collapsible details, local synthetic history,
  JSON export, a copyable Markdown review brief, responsive styles, and a
  method/limitations page.
- Retargeted the deterministic frontend review agent to the Smart Glasses
  console and expanded CI with compilation, JavaScript syntax, audit, and
  whitespace checks.

- Added a loopback-only, dependency-free browser lab for the synthetic device
  command simulator, including replay and unsupported-command tests.
- Made simulator command execution idempotent for safe client retries using `command_id` replay.
- Added deterministic capability-mismatch rejection and active-session safe stops
  for critical battery and capture-indicator loss.
- Bound idempotency keys to command fingerprints, enforced capture-mode capabilities,
  latched indicator/battery faults, stabilized terminal states, and coupled simulated
  disconnect events to session safe-stop handling.
- Prepared contributor, security, and CI guidance for public review.

## 0.1.0

- Added vendor-neutral device contracts, safe-state surgical session contracts,
  deterministic simulators, and synthetic state-transition tests.
