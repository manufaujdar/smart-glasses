# Authorized Android bridge API

The Python gateway never loads a vendor AAR or sends guessed BLE packets. A
separate Android process owns Bluetooth permissions, pairing, SDK lifecycle,
physical media, and reconnect behavior, then exposes bounded JSON metadata to
the loopback/local development gateway.

## Required routes

| Route | Purpose |
|---|---|
| `POST /bridge/v1/discover` | bounded scan; return device ID, display name and optional RSSI |
| `GET /bridge/v1/state` | connected state, battery, negotiated capabilities and capture flags |
| `GET /bridge/v1/events` | bounded metadata-only event journal |
| `POST /bridge/v1/command` | execute one idempotent vendor-neutral command |

The command body is `{name, command_id, payload}`. Return
`{event, state}` using the shared command/event names. Duplicate command IDs
must replay the original result or return `unknown_result`; they must not repeat
capture or transfer side effects.

## Local security requirements

- Bind to loopback when the gateway runs on the same Android device. If a LAN
  test is unavoidable, use TLS, a short-lived bearer token and an isolated test
  network.
- Never return media bytes, patient context, MAC addresses, Wi-Fi credentials,
  SDK exceptions, or access tokens in the event journal.
- Stop recording, preview and streaming on disconnect or loss of the privacy
  indicator. Report ambiguous acknowledgements as unknown, never success.
- Verify SDK license/provenance and physical behavior before setting a
  capability to available.

`BridgeController.kt` supplies transport-neutral command routing. The Android
host must add an HTTP server and JSON layer approved for the target deployment;
none is bundled here because the physical-device app and SDK are not yet
licensed or selected.
