#!/usr/bin/env python3
"""Explainable LiDAR depth measurements for wound-surface research prototypes.

This module intentionally measures geometry only. It does not identify wounds,
classify tissue, or recommend care. A depth frame is expected to use a positive
sensor-to-surface distance in millimetres; an indentation therefore has a
positive offset from the fitted surrounding-surface plane.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Protocol, Sequence


class DepthGridError(ValueError):
    """Raised when a depth frame cannot be safely interpreted."""


DepthGrid = list[list[float | None]]


@dataclass(frozen=True)
class DepthFrame:
    """A calibrated, vendor-neutral depth frame.

    ``depth_mm`` contains ``None`` for a sensor's invalid/missing sample. The
    pixel spacing must come from the sensor calibration or a validated fixture.
    """

    depth_mm: DepthGrid
    pixel_size_x_mm: float
    pixel_size_y_mm: float
    capture_id: str = "synthetic-frame"


class DepthFrameSource(Protocol):
    """Adapter boundary for a real LiDAR or depth-camera integration."""

    def read_frame(self) -> DepthFrame:
        """Return one calibrated frame without exposing vendor SDK details."""


@dataclass(frozen=True)
class AnalysisResult:
    """JSON-serializable geometry and engineering-quality output."""

    tool: dict[str, str]
    input: dict[str, Any]
    roi: dict[str, int]
    measurements: dict[str, float | int]
    quality: dict[str, Any]
    safety: dict[str, Any]


def _finite_positive(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise DepthGridError(f"depth sample is not numeric: {value!r}") from exc
    if not math.isfinite(number):
        return None
    if number <= 0:
        return None
    return number


def _normalise_grid(raw_grid: Sequence[Sequence[Any]]) -> DepthGrid:
    if (
        not isinstance(raw_grid, Sequence)
        or isinstance(raw_grid, (str, bytes))
        or not raw_grid
        or not all(
            isinstance(row, Sequence) and not isinstance(row, (str, bytes))
            for row in raw_grid
        )
    ):
        raise DepthGridError("depth_mm must be a non-empty rectangular 2D array")
    width = len(raw_grid[0])
    if width == 0 or any(len(row) != width for row in raw_grid):
        raise DepthGridError("depth_mm must be rectangular and non-empty")
    grid = [[_finite_positive(value) for value in row] for row in raw_grid]
    if not any(value is not None for row in grid for value in row):
        raise DepthGridError("depth frame contains no valid positive depth samples")
    return grid


def _validate_spacing(pixel_size_x_mm: float, pixel_size_y_mm: float) -> tuple[float, float]:
    try:
        px = float(pixel_size_x_mm)
        py = float(pixel_size_y_mm)
    except (TypeError, ValueError) as exc:
        raise DepthGridError("pixel spacing must be numeric") from exc
    if not math.isfinite(px) or not math.isfinite(py) or px <= 0 or py <= 0:
        raise DepthGridError("pixel spacing must be finite and greater than zero")
    return px, py


def _median(values: Iterable[float]) -> float:
    ordered = sorted(values)
    if not ordered:
        raise DepthGridError("cannot calculate a statistic from zero samples")
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _percentile(values: Iterable[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise DepthGridError("cannot calculate a percentile from zero samples")
    if not 0 <= percentile <= 100:
        raise ValueError("percentile must be between 0 and 100")
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _mad(values: Sequence[float], centre: float | None = None) -> float:
    midpoint = _median(values) if centre is None else centre
    return _median(abs(value - midpoint) for value in values)


def _validate_roi(roi: Sequence[int], width: int, height: int) -> tuple[int, int, int, int]:
    if len(roi) != 4:
        raise DepthGridError("roi must contain x0 y0 x1 y1")
    try:
        x0, y0, x1, y1 = (int(value) for value in roi)
    except (TypeError, ValueError) as exc:
        raise DepthGridError("roi coordinates must be integers") from exc
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise DepthGridError(
            f"roi must fit inside the frame using half-open coordinates; frame is {width}x{height}"
        )
    return x0, y0, x1, y1


def _collect_samples(
    grid: DepthGrid,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    pixel_size_x_mm: float,
    pixel_size_y_mm: float,
    include_roi: bool,
    ring_width: int = 0,
) -> list[tuple[float, float, float]]:
    height = len(grid)
    width = len(grid[0])
    min_x = max(0, x0 - ring_width)
    min_y = max(0, y0 - ring_width)
    max_x = min(width, x1 + ring_width)
    max_y = min(height, y1 + ring_width)
    samples: list[tuple[float, float, float]] = []
    for row in range(min_y, max_y):
        for column in range(min_x, max_x):
            inside = x0 <= column < x1 and y0 <= row < y1
            if inside == include_roi:
                value = grid[row][column]
                if value is not None:
                    samples.append((column * pixel_size_x_mm, row * pixel_size_y_mm, value))
    return samples


def _fit_plane(samples: Sequence[tuple[float, float, float]]) -> tuple[float, float, float]:
    """Fit z = ax + by + c with centred normal equations."""

    if len(samples) < 3:
        raise DepthGridError("at least three valid surrounding samples are required to fit a plane")
    mean_x = sum(sample[0] for sample in samples) / len(samples)
    mean_y = sum(sample[1] for sample in samples) / len(samples)
    mean_z = sum(sample[2] for sample in samples) / len(samples)
    sxx = syy = sxy = sxz = syz = 0.0
    for x, y, z in samples:
        dx = x - mean_x
        dy = y - mean_y
        dz = z - mean_z
        sxx += dx * dx
        syy += dy * dy
        sxy += dx * dy
        sxz += dx * dz
        syz += dy * dz
    determinant = sxx * syy - sxy * sxy
    if abs(determinant) < 1e-12:
        raise DepthGridError("surrounding samples do not span a 2D surface")
    slope_x = (sxz * syy - syz * sxy) / determinant
    slope_y = (syz * sxx - sxz * sxy) / determinant
    intercept = mean_z - slope_x * mean_x - slope_y * mean_y
    return slope_x, slope_y, intercept


def analyze_depth_frame(
    frame: DepthFrame,
    roi: Sequence[int],
    ring_width: int = 2,
) -> AnalysisResult:
    """Measure an ROI's offset from a fitted surrounding surface plane.

    ROI coordinates are half-open ``x0, y0, x1, y1`` pixel coordinates. The
    estimated positive volume is a geometric approximation based on projected
    pixel area; it is not a wound-volume measurement validated for clinical use.
    """

    grid = _normalise_grid(frame.depth_mm)
    px, py = _validate_spacing(frame.pixel_size_x_mm, frame.pixel_size_y_mm)
    if not isinstance(ring_width, int) or ring_width < 1:
        raise DepthGridError("ring_width must be an integer greater than zero")
    height = len(grid)
    width = len(grid[0])
    x0, y0, x1, y1 = _validate_roi(roi, width, height)
    roi_samples = _collect_samples(grid, x0, y0, x1, y1, px, py, include_roi=True)
    ring_samples = _collect_samples(
        grid, x0, y0, x1, y1, px, py, include_roi=False, ring_width=ring_width
    )
    roi_pixel_count = (x1 - x0) * (y1 - y0)
    ring_pixel_count = ((x1 - x0) + 2 * ring_width) * ((y1 - y0) + 2 * ring_width) - roi_pixel_count
    if len(roi_samples) < 4:
        raise DepthGridError("at least four valid ROI samples are required")
    if len(ring_samples) < 3:
        raise DepthGridError("at least three valid surrounding samples are required")

    slope_x, slope_y, intercept = _fit_plane(ring_samples)

    def plane_at(x: float, y: float) -> float:
        return slope_x * x + slope_y * y + intercept

    offsets = [z - plane_at(x, y) for x, y, z in roi_samples]
    positive_offsets = [max(0.0, offset) for offset in offsets]
    median_offset = _median(offsets)
    projected_area = len(roi_samples) * px * py
    positive_volume = sum(positive_offsets) * px * py
    ring_values = [sample[2] for sample in ring_samples]
    ring_median = _median(ring_values)
    ring_mad = _mad(ring_values, ring_median)
    residual_mad = _mad(offsets, median_offset)

    flags: list[str] = []
    missing_roi = roi_pixel_count - len(roi_samples)
    missing_ring = ring_pixel_count - len(ring_samples)
    if missing_roi:
        flags.append("missing_roi_samples")
    if missing_ring:
        flags.append("missing_ring_samples")
    if len(ring_samples) < 12:
        flags.append("small_background_sample")
    if ring_mad > 2.0:
        flags.append("noisy_background_surface")
    if residual_mad > 2.0:
        flags.append("variable_roi_surface")
    quality_score = 1.0
    quality_score -= min(0.35, 0.35 * missing_roi / max(1, roi_pixel_count))
    quality_score -= min(0.25, 0.25 * missing_ring / max(1, ring_pixel_count))
    if len(ring_samples) < 12:
        quality_score -= 0.2
    if ring_mad > 2.0:
        quality_score -= 0.15
    if residual_mad > 2.0:
        quality_score -= 0.15
    quality_score = max(0.0, min(1.0, quality_score))

    return AnalysisResult(
        tool={
            "name": "lidar-wound-depth",
            "version": "0.1.0",
            "purpose": "geometric depth measurement for research review",
        },
        input={
            "capture_id": frame.capture_id,
            "frame_width_px": width,
            "frame_height_px": height,
            "pixel_size_x_mm": px,
            "pixel_size_y_mm": py,
            "valid_roi_samples": len(roi_samples),
            "valid_ring_samples": len(ring_samples),
        },
        roi={"x0": x0, "y0": y0, "x1": x1, "y1": y1, "ring_width_px": ring_width},
        measurements={
            "median_depth_offset_mm": median_offset,
            "p95_depth_offset_mm": _percentile(offsets, 95),
            "maximum_depth_offset_mm": max(offsets),
            "mean_positive_depth_offset_mm": sum(positive_offsets) / len(positive_offsets),
            "projected_area_mm2": projected_area,
            "estimated_positive_volume_mm3": positive_volume,
            "background_median_depth_mm": ring_median,
            "background_mad_mm": ring_mad,
            "roi_residual_mad_mm": residual_mad,
        },
        quality={
            "engineering_quality_score": round(quality_score, 3),
            "score_definition": "heuristic data-quality indicator; not clinical confidence",
            "flags": flags,
        },
        safety={
            "research_prototype_only": True,
            "requires_calibrated_sensor": True,
            "requires_clinician_review": True,
            "not_for_diagnosis_or_treatment": True,
            "not_for_anatomical_registration_or_navigation": True,
            "limitations": [
                "ROI is supplied by the operator; automatic wound segmentation is not included.",
                "Measurements depend on sensor pose, calibration, occlusion handling, and surface reflectance.",
                "Positive volume is a plane-relative geometric approximation, not a clinically validated wound volume.",
            ],
        },
    )


def _parse_text_sample(value: str) -> float | None:
    stripped = value.strip()
    if not stripped or stripped.lower() in {"nan", "null", "none", "invalid"}:
        return None
    return _finite_positive(stripped)


def load_depth_input(path: str | Path, pixel_size: Sequence[float] | None = None) -> DepthFrame:
    """Load a CSV grid or JSON depth frame for a vendor adapter or CLI."""

    source = Path(path)
    if source.suffix.lower() == ".json":
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DepthGridError(f"could not read JSON depth input: {source}") from exc
        if isinstance(payload, list):
            raw_grid = payload
            metadata: dict[str, Any] = {}
        elif isinstance(payload, dict):
            raw_grid = payload.get("depth_mm")
            metadata = payload
        else:
            raise DepthGridError("JSON depth input must be a 2D array or an object with depth_mm")
        if raw_grid is None:
            raise DepthGridError("JSON depth input is missing depth_mm")
        spacing = pixel_size or metadata.get("pixel_size_mm")
        capture_id = str(metadata.get("capture_id", source.stem))
    else:
        try:
            with source.open(newline="", encoding="utf-8") as handle:
                raw_grid = [[_parse_text_sample(value) for value in row] for row in csv.reader(handle)]
        except OSError as exc:
            raise DepthGridError(f"could not read CSV depth input: {source}") from exc
        spacing = pixel_size
        capture_id = source.stem
    if spacing is None or len(spacing) != 2:
        raise DepthGridError("calibration is required: provide pixel_size_mm [x, y]")
    px, py = _validate_spacing(spacing[0], spacing[1])
    return DepthFrame(_normalise_grid(raw_grid), px, py, capture_id)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Measure a manually selected ROI against its surrounding LiDAR depth plane."
    )
    parser.add_argument("input", help="CSV depth grid or JSON object containing depth_mm")
    parser.add_argument(
        "--roi",
        nargs=4,
        type=int,
        required=True,
        metavar=("X0", "Y0", "X1", "Y1"),
        help="half-open pixel ROI coordinates",
    )
    parser.add_argument(
        "--pixel-size-mm",
        nargs=2,
        type=float,
        metavar=("X", "Y"),
        help="calibrated pixel spacing; optional when JSON contains pixel_size_mm",
    )
    parser.add_argument("--ring-width", type=int, default=2, help="background ring width in pixels (default: 2)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        frame = load_depth_input(args.input, args.pixel_size_mm)
        result = analyze_depth_frame(frame, args.roi, args.ring_width)
    except (DepthGridError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
