"""Calibrated, explainable surface metrics for a single depth frame.

This module is intentionally self-contained so the longitudinal tool can be
released independently from the rest of the Smart Glasses repository.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable, Sequence


class DepthGridError(ValueError):
    """Raised when a depth frame cannot be safely measured."""


DepthGrid = list[list[float | None]]


@dataclass(frozen=True)
class DepthFrame:
    """A calibrated depth grid; ``None`` means an invalid sensor sample."""

    depth_mm: Sequence[Sequence[Any]]
    pixel_size_x_mm: float
    pixel_size_y_mm: float
    capture_id: str


def _positive_finite(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise DepthGridError(f"depth sample is not numeric: {value!r}") from exc
    if not math.isfinite(number) or number <= 0:
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
    grid = [[_positive_finite(value) for value in row] for row in raw_grid]
    if not any(value is not None for row in grid for value in row):
        raise DepthGridError("depth frame contains no valid positive depth samples")
    return grid


def _spacing(frame: DepthFrame) -> tuple[float, float]:
    try:
        px = float(frame.pixel_size_x_mm)
        py = float(frame.pixel_size_y_mm)
    except (TypeError, ValueError) as exc:
        raise DepthGridError("pixel spacing must be numeric") from exc
    if not math.isfinite(px) or not math.isfinite(py) or px <= 0 or py <= 0:
        raise DepthGridError("pixel spacing must be finite and greater than zero")
    return px, py


def _median(values: Iterable[float]) -> float:
    ordered = sorted(values)
    if not ordered:
        raise DepthGridError("cannot calculate a statistic from zero samples")
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def _percentile(values: Sequence[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise DepthGridError("cannot calculate a percentile from zero samples")
    position = (len(ordered) - 1) * percentile / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _mad(values: Sequence[float], centre: float) -> float:
    return _median(abs(value - centre) for value in values)


def _roi_coordinates(roi: Sequence[int], width: int, height: int) -> tuple[int, int, int, int]:
    if len(roi) != 4:
        raise DepthGridError("roi must contain x0 y0 x1 y1")
    try:
        x0, y0, x1, y1 = (int(value) for value in roi)
    except (TypeError, ValueError) as exc:
        raise DepthGridError("roi coordinates must be integers") from exc
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise DepthGridError("roi must fit inside the frame using half-open coordinates")
    return x0, y0, x1, y1


def _samples(
    grid: DepthGrid,
    roi: tuple[int, int, int, int],
    px: float,
    py: float,
    want_roi: bool,
    ring_width: int,
) -> list[tuple[float, float, float]]:
    x0, y0, x1, y1 = roi
    height = len(grid)
    width = len(grid[0])
    min_x = max(0, x0 - ring_width)
    min_y = max(0, y0 - ring_width)
    max_x = min(width, x1 + ring_width)
    max_y = min(height, y1 + ring_width)
    result: list[tuple[float, float, float]] = []
    for row in range(min_y, max_y):
        for column in range(min_x, max_x):
            inside = x0 <= column < x1 and y0 <= row < y1
            if inside == want_roi and grid[row][column] is not None:
                result.append((column * px, row * py, grid[row][column]))
    return result


def _fit_plane(samples: Sequence[tuple[float, float, float]]) -> tuple[float, float, float]:
    if len(samples) < 3:
        raise DepthGridError("at least three valid background samples are required")
    mean_x = sum(x for x, _, _ in samples) / len(samples)
    mean_y = sum(y for _, y, _ in samples) / len(samples)
    mean_z = sum(z for _, _, z in samples) / len(samples)
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
        raise DepthGridError("background samples do not span a 2D surface")
    slope_x = (sxz * syy - syz * sxy) / determinant
    slope_y = (syz * sxx - sxz * sxy) / determinant
    intercept = mean_z - slope_x * mean_x - slope_y * mean_y
    return slope_x, slope_y, intercept


def analyze_depth_frame(
    frame: DepthFrame,
    roi: Sequence[int],
    ring_width: int = 2,
) -> dict[str, Any]:
    """Return plane-relative geometry metrics for a manually selected ROI."""

    grid = _normalise_grid(frame.depth_mm)
    px, py = _spacing(frame)
    if not isinstance(ring_width, int) or ring_width < 1:
        raise DepthGridError("ring_width must be an integer greater than zero")
    height = len(grid)
    width = len(grid[0])
    coordinates = _roi_coordinates(roi, width, height)
    roi_samples = _samples(grid, coordinates, px, py, True, ring_width)
    background_samples = _samples(grid, coordinates, px, py, False, ring_width)
    x0, y0, x1, y1 = coordinates
    expected_roi = (x1 - x0) * (y1 - y0)
    expected_background = ((x1 - x0) + 2 * ring_width) * ((y1 - y0) + 2 * ring_width) - expected_roi
    if len(roi_samples) < 4:
        raise DepthGridError("at least four valid ROI samples are required")
    if len(background_samples) < 3:
        raise DepthGridError("at least three valid background samples are required")
    slope_x, slope_y, intercept = _fit_plane(background_samples)

    offsets = [z - (slope_x * x + slope_y * y + intercept) for x, y, z in roi_samples]
    median_offset = _median(offsets)
    positive_offsets = [max(0.0, value) for value in offsets]
    background_values = [z for _, _, z in background_samples]
    background_median = _median(background_values)
    background_mad = _mad(background_values, background_median)
    residual_mad = _mad(offsets, median_offset)
    flags: list[str] = []
    if len(roi_samples) < expected_roi:
        flags.append("missing_roi_samples")
    if len(background_samples) < expected_background:
        flags.append("missing_background_samples")
    if len(background_samples) < 12:
        flags.append("small_background_sample")
    if background_mad > 2.0:
        flags.append("noisy_background_surface")
    if residual_mad > 2.0:
        flags.append("variable_roi_surface")
    score = 1.0
    score -= min(0.35, 0.35 * (expected_roi - len(roi_samples)) / max(1, expected_roi))
    score -= min(0.25, 0.25 * (expected_background - len(background_samples)) / max(1, expected_background))
    if len(background_samples) < 12:
        score -= 0.2
    if background_mad > 2.0:
        score -= 0.15
    if residual_mad > 2.0:
        score -= 0.15
    score = max(0.0, min(1.0, score))
    return {
        "capture_id": frame.capture_id,
        "frame_width_px": width,
        "frame_height_px": height,
        "valid_roi_samples": len(roi_samples),
        "valid_background_samples": len(background_samples),
        "pixel_size_x_mm": px,
        "pixel_size_y_mm": py,
        "roi": {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "ring_width_px": ring_width},
        "measurements": {
            "median_depth_offset_mm": median_offset,
            "p95_depth_offset_mm": _percentile(offsets, 95),
            "maximum_depth_offset_mm": max(offsets),
            "mean_positive_depth_offset_mm": sum(positive_offsets) / len(positive_offsets),
            "projected_area_mm2": len(roi_samples) * px * py,
            "estimated_positive_volume_mm3": sum(positive_offsets) * px * py,
            "background_median_depth_mm": background_median,
            "background_mad_mm": background_mad,
            "roi_residual_mad_mm": residual_mad,
        },
        "quality": {
            "engineering_quality_score": round(score, 3),
            "flags": flags,
            "score_definition": "heuristic data-quality indicator; not clinical confidence",
        },
    }
