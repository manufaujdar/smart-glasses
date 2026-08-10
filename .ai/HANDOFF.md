# Current handoff

## Standalone LiDAR wound-progress reviewer

- Objective: add a separate open-source research tool that compares calibrated
  LiDAR/depth captures over time and reports a geometry-only trajectory signal.
- Result: `tools/lidar_wound_progress/` is self-contained and independently
  structured into a surface-metrics engine and longitudinal manifest/trend
  reviewer. It supports synthetic JSON manifests, quality gates, deterministic
  depth/volume comparisons, and explicit safety/provenance documentation.
- References reviewed: UWM wound segmentation, WoundScope provenance/routing,
  OpenGeoS LiDAR surface-depression geometry, and published 3D/LiDAR wound
  measurement studies. No source code, clinical data, weights, or SDK content
  was copied.
- License proposal: Apache License 2.0 for the standalone tool, with a
  copyright-holder confirmation gate before public release. Datasets, vendor
  SDKs, and future model weights require separate terms.
- Safety/privacy boundary: `geometry_signal` is not a healing, recovery,
  diagnosis, treatment, triage, infection, tissue-viability, or prognosis
  determination. Only synthetic data is included; patient captures and
  identifiers must remain outside Git.
- Validation: focused tests, whole-project tests, Python compilation, and the
  synthetic CLI smoke run are required before release.
- Active role: execution and open-source packaging. Next owner: human clinical
  reviewer for intended use and validation design, then a release owner to
  confirm copyright/license and whether to publish the branch.
