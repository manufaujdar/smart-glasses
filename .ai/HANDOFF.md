# Current handoff

## LiDAR wound-surface depth prototype

- Objective: add a vendor-neutral research tool for geometric depth analysis of
  manually selected surface regions from calibrated LiDAR/depth-camera frames.
- Result: `tools/lidar_wound_depth/` provides CSV/JSON loading, a
  `DepthFrameSource` adapter boundary, local background-plane fitting, ROI
  depth-offset/area/plane-relative volume measurements, quality flags, and
  explicit research-only safety metadata.
- Synthetic fixture: `tools/lidar_wound_depth/examples/synthetic_wound.csv`.
- Validation: 35 project tests, Python compilation, `git diff --check`, and the
  synthetic CLI smoke run passed.
- Safety/privacy boundary: no patient data, device captures, proprietary SDKs,
  wound classification, diagnosis, treatment, anatomical registration,
  navigation, or production-clinical claim. Any real sensor adapter needs its
  own calibration, privacy, risk, intended-use, and validation review.
- Publication blockers: no human-approved `LICENSE`; the existing untracked
  third-party reference snapshots are intentionally excluded from this change.
- Active role: release handoff. Next owner: human clinical/product reviewer for
  intended use and validation design, followed by a hardware adapter owner.
