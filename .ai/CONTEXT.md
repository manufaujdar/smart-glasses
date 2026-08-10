# Smart Glasses project context

## Mission

Develop an Android-first, vendor-neutral research platform for healthcare-focused smart glasses, initially targeting HeyCyan-compatible camera glasses.

## Source map

- Human entry: `START_HERE.txt`
- Product, safety, protocol, architecture, and research: `docs/`
- Android application: `apps/android-controller/`
- Device contracts: `packages/device-contracts/`
- Surgical workflow contracts: `packages/surgical-workflows/`
- Clinical gateway boundary: `services/clinical-gateway/`
- Simulator and tools: `tools/`
- Verification: `tests/`
- Licensed/vendor records: `third_party/`
- Local device captures: `artifacts/device-captures/`

## Invariants

Research prototype only; no diagnostic or treatment claims; vendor behavior stays behind adapters; captures and identifiers are sensitive; safe-state behavior and license provenance are preserved.

## Surgeon-facing work

Start at `docs/surgery/START_HERE.md`. The current surgical code supports only
synthetic workflow and safety-state simulation. It must not provide anatomical
registration, instrument guidance, diagnosis, treatment selection, or autonomous
clinical action.

Commit-pinned upstream archives are intentionally isolated in
`third_party/reference-repositories/snapshots/`. Read the small adoption map and
register first; do not unpack or index all snapshots by default.
