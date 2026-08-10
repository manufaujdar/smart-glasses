# HeyCyan compatibility plan

## Legal and technical boundary

The available GitHub repository describes its SDK as proprietary and asks users to contact HeyCyan for licensing. The Android AAR and iOS framework must not be copied into this repository or redistributed without written permission. The adapter in this project is a clean boundary around the documented public capabilities; it does not reproduce proprietary binary code or undocumented packet bytes.

## Observed capability surface

- BLE scan/connect/disconnect
- hardware, firmware, Wi-Fi version and MAC queries
- battery and charging state
- photo/video/audio media counts
- device time synchronization
- photo capture
- video start/stop
- audio start/stop
- AI-photo trigger and image callback
- Wi-Fi-based media transfer in sample applications

Published service UUID references include `7905FFF0-B5CE-4E99-A40F-4B1E122D00D0` and `6e40fff0-b5a3-f393-e0a9-e50e24dcca9e`. Treat these as discovery clues, not a stable or licensed protocol contract.

## Integration options

### Option A — licensed manufacturer SDK (preferred for current testing)

Place the authorized Android AAR at `third_party/heycyan/heycyan-sdk.aar`, accept the SDK terms, and implement the small binder described by the Android app. This is fastest and preserves manufacturer behavior.

### Option B — clean-room protocol implementation

Use only if legally approved. One team records external behavior and writes a protocol specification; a separate implementation team codes from that specification. Capture firmware versions, timing, acknowledgements, error states, packet boundaries and checksums. Do not decompile or copy proprietary implementation code without authorization.

### Option C — replace hardware

If licensing, security or reliability cannot meet healthcare requirements, retain the device contract and substitute a licensed/open driver.

## Test sequence

1. Record device model, firmware and app/SDK version.
2. Scan for 30 seconds and save advertisements without personal identifiers.
3. Connect/disconnect 50 cycles; record time and failures.
4. Query battery/version/media counts 100 times.
5. Capture 25 photos, five 60-second videos and ten 60-second audio files.
6. Interrupt each operation with Bluetooth loss, Wi-Fi loss, low battery and app backgrounding.
7. Verify media checksum, timestamp, orientation and duplicate handling.
8. Run a two-hour mixed-use thermal/battery test.
9. Confirm privacy indicator and stop behavior.
10. Export the event journal to `artifacts/device-captures/` with synthetic labels only.

## Known questions for the manufacturer

- Authoritative SDK license and redistribution terms
- supported models/firmware and update policy
- full GATT/command specification or supported wrapper API
- encryption, pairing, authentication and key lifecycle
- CVE/security contact and signed firmware/DFU process
- media-at-rest encryption and secure erase
- privacy LED electrical coupling
- Wi-Fi access-point credentials and transfer protection
- lifecycle, supply continuity and enterprise device management

