# LiDAR wound-progress reviewer

Standalone open-source research software for comparing calibrated LiDAR/depth
captures of the same wound-shaped surface over time. It reports a deterministic
`geometry_signal` from depth and plane-relative volume changes:

- `decreasing_geometry`
- `stable_or_mixed_geometry`
- `increasing_geometry`
- `insufficient_data`
- `insufficient_quality`

These labels describe measured surface geometry only. They are not statements
about healing, recovery, infection, tissue viability, treatment response, or
clinical outcome. The tool does not diagnose, triage, recommend treatment, or
take autonomous action.

## Why this structure

The package is intentionally self-contained and vendor-neutral:

```text
lidar_wound_progress/
  surface_metrics.py       calibrated single-frame plane-relative metrics
  progress_tracker.py      manifest loading and longitudinal comparison
  examples/                 synthetic-only input
  REFERENCES.md             reviewed references and provenance boundary
  LICENSE                   Apache-2.0 candidate for this tool
  NOTICE                    attribution and no-copy statement
  CONTRIBUTING.md           contribution and data rules
  SECURITY.md               privacy and vulnerability reporting boundary
```

There are no runtime dependencies beyond Python 3.10+ standard library modules.
The code does not contain a vendor SDK, segmentation model, patient capture, or
automatic anatomical registration.

## Run the synthetic example

From the `Smart Glasses` project root:

```bash
python3 tools/lidar_wound_progress/progress_tracker.py \
  tools/lidar_wound_progress/examples/synthetic_progress_manifest.json
```

The example contains three synthetic captures of a flat background and a
recessed region whose depth decreases from 4.0 mm to 0.5 mm. It is expected to
produce `decreasing_geometry`; that output demonstrates the rule engine only,
not wound recovery.

## Input contract

The manifest is JSON and contains one opaque study key, shared calibration, and
one or more captures:

```json
{
  "wound_id": "synthetic-study-wound-001",
  "roi": [3, 3, 7, 7],
  "pixel_size_mm": [1.0, 1.0],
  "ring_width_px": 2,
  "captures": [
    {
      "capture_id": "visit-1",
      "captured_at": "2026-08-01T09:00:00Z",
      "depth_mm": [[20.0, 20.0], [20.0, 24.0]]
    }
  ]
}
```

`captured_at` must include a timezone. `depth_mm` uses positive sensor-to-surface
distance in millimetres; a recessed region therefore has a positive residual
from the fitted surrounding plane. Each capture may override `roi`,
`pixel_size_mm`, or `ring_width_px`. Missing or non-positive depth samples are
excluded and surfaced as quality flags.

## Trend rule

The latest capture is compared with the chronological baseline using three
metrics: median depth offset, 95th-percentile depth offset, and estimated
positive volume. A direction is counted only when the change exceeds the
configured tolerance (default 5%). At least two of the three metrics must move
in the same direction and the baseline/latest quality scores must meet the
minimum threshold (default 0.6).

The current implementation intentionally uses operator-supplied ROIs. For a
future clinical research version, add validated segmentation, pose
standardization, anatomical registration, repeatability statistics, and a
reference-method comparison before interpreting trajectory signals.

## Open-source licensing choice

The code in this standalone folder is prepared for Apache License 2.0
(`Apache-2.0`), a permissive OSI-approved license with an express patent grant
that is practical for academic, community, and commercial collaboration. The
license candidate still requires the copyright holder to confirm authorship and
approve release. See [LICENSE](LICENSE), [NOTICE](NOTICE), and
[REFERENCES.md](REFERENCES.md).

This license applies to the source in this standalone folder only. Any datasets,
device SDKs, model weights, clinical images, or future third-party assets must
carry their own documented terms and must not be added by default.

## Validation

Run the whole project test suite from the project root:

```bash
python3 -m unittest discover -s tests -v
```

The included tests use synthetic grids only. Any real sensor adapter or clinical
research deployment requires separate calibration, privacy, intended-use, risk,
regulatory, and validation review.

The optional [`webapp/`](webapp/) folder provides a responsive phone/tablet/laptop
interface. It captures an in-memory visual reference, imports calibrated depth
JSON, and stores numeric history locally in the browser; it does not claim that
an ordinary RGB camera can measure LiDAR depth.
