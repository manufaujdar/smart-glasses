# Reference repository adoption map

These upstream projects are examples, not approved product components.

| Local need | Study | Reuse now | Do not inherit blindly |
|---|---|---|---|
| shared glasses connection and capabilities | MentraOS mobile/runtime and SDK boundaries | event ownership, device adapters and lifecycle concepts | cloud assumptions, consumer data flows, bundled services |
| Android tele-mentoring | LiveKit Android SDK and samples | room state, track lifecycle, reconnect tests | public-cloud defaults, recording/retention policy, generic tokens |
| optional display/spatial interface | OpenXR SDK Source and `hello_xr` | standard types, capability checks, frame lifecycle | spatial guidance or registration claims |
| medical inference packaging | MONAI Deploy App SDK | operator DAGs, model/version metadata, packaging and tests | radiology assumptions, models, clinical performance claims |
| low-latency surgical-video research | Holohub endoscopy applications/operators | pipeline separation, latency measurement and synthetic demos | pretrained weights, datasets, NVIDIA hardware assumptions, clinical use |

## Recommended code flow

1. Keep `packages/device-contracts` as the stable vendor boundary.
2. Implement Android adapters locally; do not import an upstream runtime wholesale.
3. Map LiveKit room events to the surgical-session controller and policy gateway.
4. Add OpenXR only when a supported display device is selected.
5. Run all AI research out of process behind a versioned, fail-closed model gateway.
6. Use Holohub/MONAI structures for experiments; promote nothing without independent tests.

## Link-only research sources

- Android Camera Samples: https://github.com/android/camera-samples
- Brilliant SDK: https://github.com/brilliantlabsAR/brilliant_sdk
- CAMMA CholecT50: https://github.com/CAMMA-public/cholect50
- CAMMA Endoscapes: https://github.com/CAMMA-public/Endoscapes

The Android Camera Samples archive is not stored because no repository-level license
file was detected at the reviewed revision. CAMMA data/code must be evaluated against
its specific access and non-commercial terms before download or use.

