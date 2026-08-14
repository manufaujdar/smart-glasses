# Technical overview

Status: synthetic research code is runnable; hardware/publication remains
gated.

## Repository map

- apps/android-controller: Android companion and vendor adapter boundary; not yet a complete Android application.
- packages/device-contracts: vendor-neutral device events, commands, and retry contracts.
- packages/surgical-workflows: synthetic operating-room session state machine.
- services/clinical-gateway: future PHI-aware policy/integration boundary.
- services/surgical-session-orchestrator: future synthetic session-token/policy/audit contract.
- tools/: device, session, and browser simulators.
- tests/: simulator, session, web-console, disconnect, replay, capability, and safe-stop checks.
- docs/: architecture, product, protocol, security, surgery, research, testing, and provenance.

## Runtime and technology

The current executable path is Python and dependency-free simulator tooling.
Android source establishes a licensed-SDK boundary but is not physical-device
validation. The planned topology includes Android edge state, clinical gateway
policy, hospital adapters, and an approved model gateway; those layers are not
implied to be deployed.

## Safety contracts

The device lifecycle is discover -> connect -> negotiate capabilities ->
observe -> execute -> emit result -> disconnect. Commands are capability
checked and duplicate command IDs replay the original result. Active sessions
safe-stop on disconnect, critical battery, and capture-indicator loss.

## Validation and maintenance

Run unittest discovery, both simulators, and the browser console commands in
README.md. Physical permissions, thermal limits, media checksums, BLE/Wi-Fi
behavior, vendor SDK rights, PHI handling, and clinical/human-factors evidence
remain hardware or governance gates. New commands, events, capabilities,
states, adapters, or patient-data paths require protocol, threat-model, test,
and provenance updates.

