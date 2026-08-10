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

Numeric records are stored in browser `localStorage` only. Captured images stay
in memory and are not saved with the numeric history. This is not a clinical
system and must not be used for diagnosis, treatment, triage, or recovery
decisions.
