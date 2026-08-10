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

## Depthline webapp

- Objective: provide a phone/tablet/laptop browser interface for visual camera
  reference, calibrated depth JSON import, current geometry review, and local
  baseline comparison.
- Result: `tools/lidar_wound_progress/webapp/` is a dependency-free responsive
  static webapp. RGB camera frames stay in memory; only numeric summaries are
  stored in browser-local history. A browser camera is not treated as a raw
  LiDAR depth source.
- Validation: JavaScript syntax check, JSON validation, static HTTP-server
  smoke test, full project test suite, Python compilation, and diff checks.
- Publication: `manufaujdar/smart-glasses-research` is now public. The current
  branch still excludes the pre-existing untracked reference snapshots.
- Active role: release packaging. Next owner: human reviewer to approve the
  public webapp wording, copyright/license candidate, and future real-sensor
  validation before any clinical use.
