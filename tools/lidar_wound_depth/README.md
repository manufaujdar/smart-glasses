# LiDAR wound-surface depth tool

This folder contains a small vendor-neutral research prototype for geometric
analysis of a calibrated LiDAR/depth-camera frame. It is intended to support
clinician-reviewed experiments such as wound-surface depth tracking, surface
change review, and measurement of other recessed or raised regions (for example,
swelling or post-procedure surface changes).

It does not detect wounds, classify tissue, estimate healing, diagnose infection,
recommend treatment, register data to anatomy, or guide instruments. It is not a
medical device and must not be used for diagnosis, treatment, triage, or care
decisions.

## What it measures

The operator supplies a rectangular ROI using half-open pixel coordinates
`x0 y0 x1 y1`. The tool fits a plane to a surrounding background ring and
reports the ROI residuals:

- median, 95th-percentile, and maximum depth offset in millimetres;
- projected ROI area in mm²;
- an estimated positive volume in mm³, calculated from positive residuals and
  pixel area;
- background and ROI residual variability;
- explicit data-quality flags and an engineering quality score.

For a sensor whose positive depth axis points away from the surface, a recessed
region has a positive offset. The sign must be verified for each sensor adapter.

## Run the synthetic example

From the `Smart Glasses` project root:

```bash
python3 tools/lidar_wound_depth/lidar_wound_depth.py \
  tools/lidar_wound_depth/examples/synthetic_wound.csv \
  --roi 6 5 10 9 \
  --pixel-size-mm 0.8 0.8 \
  --ring-width 2
```

The fixture is synthetic and contains a flat 20 mm background with a 24 mm
recessed ROI. It is not a patient or device capture.

## Sensor adapter boundary

Real hardware should be integrated through `DepthFrameSource.read_frame()` and
return a `DepthFrame` with calibrated pixel spacing. Keep vendor SDK calls in a
separate adapter; do not add proprietary binaries or patient/device captures to
this folder. JSON input is also supported:

```json
{
  "capture_id": "synthetic-001",
  "pixel_size_mm": [0.8, 0.8],
  "depth_mm": [[20.0, 20.0], [20.0, 24.0]]
}
```

Missing samples (`null`, blank, `NaN`, or non-positive values) are excluded and
reported through quality flags. The tool fails closed when calibration,
geometry, or the minimum valid samples are unavailable.

## Validation and limitations

Run the project test suite from the project root:

```bash
python3 -m unittest discover -s tests -v
```

The output is a geometric measurement aid only. Sensor pose, calibration,
reflectance, occlusion, motion, ROI selection, and background-plane choice can
materially change results. Any clinical research use requires a separate
intended-use statement, privacy review, risk analysis, calibration protocol,
and validation against an appropriate reference method.
