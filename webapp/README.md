# Fieldline integration webapp

Fieldline is the same-origin browser frontend for `tools/integration_server.py`.
It selects a vendor-neutral adapter, discovers/connects a device, executes
capability-gated commands, shows WebSocket state updates, and retains a bounded
metadata-only review history in browser storage.

The browser media panel uses the phone or computer camera/microphone directly.
Snapshots and recordings remain in memory until downloaded and are never sent
to the backend. It is deliberately labeled as a separate source from glasses.

Voice is push-to-talk, exact-phrase allowlisted, and confirmation-gated for
capture/start actions. Browser speech recognition availability and data routing
depend on the browser vendor; do not use patient information.

Run from the repository root:

```bash
./scripts/bootstrap.sh
.venv/bin/python tools/integration_server.py
```

Open `http://127.0.0.1:8766`. The simulator works without hardware. Physical
adapters require the authorized bridge contract documented under
`apps/android-controller/BRIDGE_API.md`.
