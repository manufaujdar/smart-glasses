---
name: smart-glasses-analyze-protocol
description: Analyze smart-glasses device behavior and translate evidence into vendor-neutral capability, command, event, and state-machine contracts. Use for protocol research, packet or log interpretation, adapter design, capability negotiation, disconnect behavior, media transfer, or adding a hardware target.
---

# Analyze a smart-glasses protocol

Read `AGENTS.md`, the relevant `docs/protocols/` and architecture documents,
`packages/device-contracts/`, the adapter boundary, and related tests.

1. Identify the exact device, firmware, transport, evidence source, capture date,
   license, and confidence. Keep observed behavior separate from vendor claims and
   inference.
2. Inspect only the approved capture or commit-pinned reference needed for the task.
   Never expose patient data, credentials, proprietary binaries, or unrelated
   captured content.
3. Map operations into vendor-neutral capabilities, commands, events, states,
   timeouts, retries, idempotency, errors, and cancellation behavior.
4. Define safe behavior for disconnect, capability mismatch, partial transfer,
   interruption, stale state, unsupported commands, and ambiguous acknowledgements.
5. Keep uncertain behavior behind the adapter and label it; do not promote guessed
   packet semantics into a shared contract.
6. Add synthetic simulator scenarios and focused state-transition tests before
   changing a shared interface.

Handoff the evidence table, proposed contract delta, uncertainty, compatibility
impact, license/provenance status, tests, and any physical-device verification still
required. Stop before invasive capture, bypassing access controls, or importing
unlicensed SDK material.
