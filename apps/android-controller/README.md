# Android controller

This folder defines the production boundary for the current HeyCyan test device. It intentionally does not include the proprietary AAR.

## Physical-device setup

1. Obtain the SDK and written license directly from HeyCyan/manufacturer.
2. Verify and record its SHA-256 in `third_party/heycyan/PROVENANCE.md`.
3. Place it at `third_party/heycyan/heycyan-sdk.aar` (gitignored).
4. Create an Android Studio project in this folder or integrate the Kotlin interfaces below into the licensed sample.
5. Implement `HeyCyanVendorApi` using only the authorized SDK API.
6. Wrap `BridgeController` with the local authenticated routes in
   [`BRIDGE_API.md`](BRIDGE_API.md).
7. Run the validation plan with synthetic scenes and no patient data.

## Modules to create in the Android project

- `device-api`: contracts and state machine
- `driver-heycyan`: isolated proprietary SDK binder
- `workflow-shell`: capture/review/consent UI
- `audit`: encrypted event journal and export
- `app`: dependency injection, permissions and test screens

## Required Android permissions

Use the narrow Android-version-specific Bluetooth permissions, camera/microphone only when the phone itself uses them, and location only where Android BLE scanning requires it. Request at the moment of use and explain why. Do not request broad media access when app-scoped storage is sufficient.
