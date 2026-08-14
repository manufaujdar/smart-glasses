"""Paired wound-photo comparison metrics.

This module contains deterministic geometry and comparability calculations for
two operator-reviewed masks. It deliberately does not infer healing, infection,
or treatment response. A mask may come from a validated model, a native
segmentation adapter, or an operator correction workflow.

The formulas are aligned with digital planimetry practice: calibrated area,
perimeter, longest/widest dimensions, percentage area reduction, and mean
linear edge change. Image similarity is included as an image-quality/change
signal only; it must not be interpreted as a clinical outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence


class PairComparisonError(ValueError):
    """Raised when two captures cannot be compared safely."""


Mask = Sequence[Sequence[bool]]


@dataclass(frozen=True)
class PairQuality:
    """Acquisition comparability inputs and a transparent engineering score."""

    scale_marker_present: bool
    pose_alignment_score: float
    lighting_consistency_score: float
    segmentation_reviewed: bool
    image_quality_score: float

    def report(self) -> dict[str, Any]:
        values = {
            "scale_marker": 1.0 if self.scale_marker_present else 0.0,
            "pose_alignment": _bounded(self.pose_alignment_score),
            "lighting_consistency": _bounded(self.lighting_consistency_score),
            "segmentation_reviewed": 1.0 if self.segmentation_reviewed else 0.0,
            "image_quality": _bounded(self.image_quality_score),
        }
        score = sum(values.values()) / len(values)
        flags: list[str] = []
        if not self.scale_marker_present:
            flags.append("missing_scale_marker")
        if values["pose_alignment"] < 0.75:
            flags.append("pose_not_comparable")
        if values["lighting_consistency"] < 0.75:
            flags.append("lighting_not_comparable")
        if not self.segmentation_reviewed:
            flags.append("segmentation_not_reviewed")
        if values["image_quality"] < 0.6:
            flags.append("low_image_quality")
        return {
            "engineering_comparability_score": round(score, 3),
            "usable_for_measurement": not flags and score >= 0.75,
            "components": values,
            "flags": flags,
            "definition": "weighted acquisition and review indicator; not clinical confidence",
        }


def _bounded(value: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise PairComparisonError("quality inputs must be numeric") from exc
    if not math.isfinite(numeric):
        raise PairComparisonError("quality inputs must be finite")
    return max(0.0, min(1.0, numeric))


def _validate_mask(mask: Mask) -> tuple[tuple[bool, ...], ...]:
    if not isinstance(mask, Sequence) or isinstance(mask, (str, bytes)) or not mask:
        raise PairComparisonError("mask must be a non-empty 2D sequence")
    width: int | None = None
    normalized: list[tuple[bool, ...]] = []
    for row in mask:
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes)) or not row:
            raise PairComparisonError("mask rows must be non-empty sequences")
        values = tuple(bool(value) for value in row)
        width = len(values) if width is None else width
        if len(values) != width:
            raise PairComparisonError("mask must be rectangular")
        normalized.append(values)
    return tuple(normalized)


def _spacing(pixel_size_mm: Sequence[float]) -> tuple[float, float]:
    if len(pixel_size_mm) != 2:
        raise PairComparisonError("pixel_size_mm must contain x and y spacing")
    px, py = (float(value) for value in pixel_size_mm)
    if not all(math.isfinite(value) and value > 0 for value in (px, py)):
        raise PairComparisonError("pixel spacing must be finite and positive")
    return px, py


def wound_mask_metrics(mask: Mask, pixel_size_mm: Sequence[float] = (1.0, 1.0)) -> dict[str, float | int | None]:
    """Calculate calibrated 2D planimetry metrics from a reviewed mask."""

    normalized = _validate_mask(mask)
    px, py = _spacing(pixel_size_mm)
    points = [(x, y) for y, row in enumerate(normalized) for x, value in enumerate(row) if value]
    area_px = len(points)
    area_mm2 = area_px * px * py
    perimeter_mm = 0.0
    point_set = set(points)
    for x, y in points:
        if (x - 1, y) not in point_set:
            perimeter_mm += py
        if (x + 1, y) not in point_set:
            perimeter_mm += py
        if (x, y - 1) not in point_set:
            perimeter_mm += px
        if (x, y + 1) not in point_set:
            perimeter_mm += px
    if not points:
        return {
            "area_px": 0,
            "area_mm2": 0.0,
            "perimeter_mm": 0.0,
            "longest_dimension_mm": 0.0,
            "widest_dimension_mm": 0.0,
            "equivalent_diameter_mm": 0.0,
            "circularity": None,
        }
    width_mm = (max(x for x, _ in points) - min(x for x, _ in points) + 1) * px
    height_mm = (max(y for _, y in points) - min(y for _, y in points) + 1) * py
    return {
        "area_px": area_px,
        "area_mm2": area_mm2,
        "perimeter_mm": perimeter_mm,
        "longest_dimension_mm": max(width_mm, height_mm),
        "widest_dimension_mm": min(width_mm, height_mm),
        "equivalent_diameter_mm": math.sqrt(4.0 * area_mm2 / math.pi),
        "circularity": (4.0 * math.pi * area_mm2 / (perimeter_mm * perimeter_mm)) if perimeter_mm else None,
    }


def _change(baseline: float, followup: float) -> dict[str, float | None]:
    absolute = followup - baseline
    percent = None if abs(baseline) < 1e-12 else absolute / abs(baseline) * 100.0
    return {"absolute": absolute, "percent": percent}


def _validate_grayscale(image: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
    if not image or not image[0] or any(len(row) != len(image[0]) for row in image):
        raise PairComparisonError("grayscale images must be non-empty rectangular arrays")
    rows = tuple(tuple(float(value) for value in row) for row in image)
    if any(not math.isfinite(value) for row in rows for value in row):
        raise PairComparisonError("grayscale images must contain finite values")
    return rows


def grayscale_change_metrics(baseline: Sequence[Sequence[float]], followup: Sequence[Sequence[float]]) -> dict[str, float | int]:
    """Calculate full-reference image change and SSIM-like structural similarity."""

    first = _validate_grayscale(baseline)
    second = _validate_grayscale(followup)
    if (len(first), len(first[0])) != (len(second), len(second[0])):
        raise PairComparisonError("grayscale images must have equal dimensions")
    values_a = [value for row in first for value in row]
    values_b = [value for row in second for value in row]
    mean_a = sum(values_a) / len(values_a)
    mean_b = sum(values_b) / len(values_b)
    variance_a = sum((value - mean_a) ** 2 for value in values_a) / max(1, len(values_a) - 1)
    variance_b = sum((value - mean_b) ** 2 for value in values_b) / max(1, len(values_b) - 1)
    covariance = sum((a - mean_a) * (b - mean_b) for a, b in zip(values_a, values_b)) / max(1, len(values_a) - 1)
    dynamic_range = max(1.0, max(values_a + values_b) - min(values_a + values_b))
    c1 = (0.01 * dynamic_range) ** 2
    c2 = (0.03 * dynamic_range) ** 2
    denominator = (mean_a * mean_a + mean_b * mean_b + c1) * (variance_a + variance_b + c2)
    ssim = ((2 * mean_a * mean_b + c1) * (2 * covariance + c2) / denominator) if denominator else 1.0
    absolute_difference = [abs(a - b) for a, b in zip(values_a, values_b)]
    return {
        "width_px": len(first[0]),
        "height_px": len(first),
        "mean_absolute_difference": sum(absolute_difference) / len(absolute_difference),
        "changed_fraction_over_5_percent": sum(value > dynamic_range * 0.05 for value in absolute_difference) / len(absolute_difference),
        "ssim": max(-1.0, min(1.0, ssim)),
    }


def compare_wound_pair(
    baseline_mask: Mask,
    followup_mask: Mask,
    baseline_pixel_size_mm: Sequence[float],
    followup_pixel_size_mm: Sequence[float],
    quality: PairQuality,
    days_between: float | None = None,
    tissue_fractions_baseline: Mapping[str, float] | None = None,
    tissue_fractions_followup: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Return paired planimetry, change, optional tissue, and quality metrics."""

    first = wound_mask_metrics(baseline_mask, baseline_pixel_size_mm)
    second = wound_mask_metrics(followup_mask, followup_pixel_size_mm)
    area_delta = float(first["area_mm2"]) - float(second["area_mm2"])
    mean_perimeter = (float(first["perimeter_mm"]) + float(second["perimeter_mm"])) / 2.0
    linear_change = area_delta / mean_perimeter if mean_perimeter else None
    result: dict[str, Any] = {
        "baseline": first,
        "followup": second,
        "change": {
            "area_reduction_mm2": area_delta,
            "area_reduction_percent": (area_delta / float(first["area_mm2"]) * 100.0) if first["area_mm2"] else None,
            "perimeter": _change(float(first["perimeter_mm"]), float(second["perimeter_mm"])),
            "longest_dimension": _change(float(first["longest_dimension_mm"]), float(second["longest_dimension_mm"])),
            "widest_dimension": _change(float(first["widest_dimension_mm"]), float(second["widest_dimension_mm"])),
            "linear_edge_change_mm": linear_change,
            "area_reduction_per_week_percent": (area_delta / float(first["area_mm2"]) * 100.0 / (days_between / 7.0)) if first["area_mm2"] and days_between and days_between > 0 else None,
        },
        "quality": quality.report(),
        "interpretation": "measurable photo-derived change only; not a healing, recovery, infection, or treatment determination",
    }
    if tissue_fractions_baseline is not None and tissue_fractions_followup is not None:
        labels = sorted(set(tissue_fractions_baseline) | set(tissue_fractions_followup))
        result["tissue_fractions"] = {
            label: {
                "baseline": float(tissue_fractions_baseline.get(label, 0.0)),
                "followup": float(tissue_fractions_followup.get(label, 0.0)),
                "change_percentage_points": float(tissue_fractions_followup.get(label, 0.0)) - float(tissue_fractions_baseline.get(label, 0.0)),
            }
            for label in labels
        }
    return result
