# Changelog

## Unreleased

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
