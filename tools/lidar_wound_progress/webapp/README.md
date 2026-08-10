# Depthline webapp

This is a dependency-free browser interface for the standalone LiDAR wound
progress reviewer. It is designed to run on a phone, tablet, or laptop browser.

## Run locally

From the `Smart Glasses` project root:

```bash
python3 -m http.server 8766 --directory tools/lidar_wound_progress/webapp
```

Open `http://127.0.0.1:8766`. Camera access is available on localhost or a
secure HTTPS deployment.

The interface offers two routes:

- **Phone/laptop camera** — lower accuracy. The camera is a visual reference;
  the operator enters an approximate depth and area. This is a manual estimate,
  not depth inferred from RGB pixels.
- **Professional LiDAR sensor** — higher accuracy. Import a calibrated JSON
  depth grid and use the plane-relative geometry engine.

## What is functional versus simulated

- Functional: camera preview and in-memory still capture, calibrated depth JSON
  import, deterministic plane-relative depth/area/volume calculations, local
  history, longitudinal geometry signals, and optional loopback SQLite storage.
- Manual/simulated: the camera route does not infer depth from pixels. Its depth
  and area values are entered by the operator and converted into a clearly
  labeled manual estimate. Automatic wound segmentation, pose registration,
  and clinical scoring are not included.

## Important sensor limitation

Browser camera APIs expose RGB/video capture, not a universal raw LiDAR-depth
stream. Depthline therefore keeps the camera capture as an optional visual
reference and accepts a calibrated depth-grid JSON exported by a native
LiDAR/depth-sensor workflow. The included synthetic demo is the only bundled
data.

Expected depth JSON:

```json
{
  "wound_id": "local-demo-wound",
  "capture_id": "visit-1",
  "captured_at": "2026-08-01T09:00:00Z",
  "pixel_size_mm": [0.8, 0.8],
  "roi": [6, 5, 10, 9],
  "depth_mm": [[20.0, 20.0], [20.0, 24.0]]
}
```

Numeric records use browser `localStorage` when the optional service is absent,
or local SQLite when it is running. Captured images stay in memory and are not
saved with numeric history. This is not a clinical system and must not be used
for diagnosis, treatment, triage, or recovery decisions.

## Optional local SQLite service

For a laptop-only local workflow, start the loopback service in a second
terminal:

```bash
python3 tools/lidar_wound_progress/local_service.py
```

The webapp auto-detects `http://127.0.0.1:8787/api` and uses the SQLite service
for numeric summaries and minimal audit events. If it is unavailable, the app
falls back to browser-local storage. The service rejects raw depth grids,
images, direct identifiers, oversized payloads, and non-loopback hosts by
default. SQLite is not encrypted at rest; do not use it for PHI without an
approved encryption, identity, retention, backup, and risk-management design.
