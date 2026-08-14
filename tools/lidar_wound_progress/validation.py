"""Research validation metrics; these metrics do not prove clinical safety."""

from __future__ import annotations

from dataclasses import dataclass
from math import inf, isfinite, sqrt
from statistics import mean, stdev
from typing import Sequence


class ValidationError(ValueError):
    """Raised when a validation fixture is malformed."""


def _mask_points(mask: Sequence[Sequence[bool]]) -> tuple[tuple[int, int], ...]:
    if not mask or not mask[0] or any(len(row) != len(mask[0]) for row in mask):
        raise ValidationError("masks must be non-empty rectangular arrays")
    return tuple((x, y) for y, row in enumerate(mask) for x, value in enumerate(row) if bool(value))


def _percentile(values: Sequence[float], rank: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return inf
    position = (len(ordered) - 1) * rank / 100
    low, high = int(position), min(len(ordered) - 1, int(position) + 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def segmentation_metrics(predicted: Sequence[Sequence[bool]], reference: Sequence[Sequence[bool]]) -> dict[str, float | int]:
    """Return Dice, IoU, precision, recall, and Hausdorff-95 in pixels."""

    predicted_points = _mask_points(predicted)
    reference_points = _mask_points(reference)
    if len(predicted) != len(reference) or len(predicted[0]) != len(reference[0]):
        raise ValidationError("predicted and reference masks must have the same shape")
    predicted_set, reference_set = set(predicted_points), set(reference_points)
    intersection = len(predicted_set & reference_set)
    union = len(predicted_set | reference_set)
    tp = intersection
    fp = len(predicted_set - reference_set)
    fn = len(reference_set - predicted_set)
    dice = 1.0 if not predicted_set and not reference_set else (2 * tp / (len(predicted_set) + len(reference_set)) if predicted_set or reference_set else 0.0)
    iou = 1.0 if union == 0 else intersection / union
    precision = 1.0 if tp + fp == 0 and fn == 0 else (tp / (tp + fp) if tp + fp else 0.0)
    recall = 1.0 if tp + fn == 0 else (tp / (tp + fn) if tp + fn else 0.0)
    if predicted_set and reference_set:
        forward = [min(sqrt((x - rx) ** 2 + (y - ry) ** 2) for rx, ry in reference_set) for x, y in predicted_set]
        backward = [min(sqrt((x - rx) ** 2 + (y - ry) ** 2) for x, y in reference_set) for rx, ry in reference_set]
        hausdorff95 = max(_percentile(forward, 95), _percentile(backward, 95))
    else:
        hausdorff95 = 0.0 if not predicted_set and not reference_set else inf
    return {"dice": dice, "iou": iou, "precision": precision, "recall": recall, "hausdorff95_px": hausdorff95, "predicted_pixels": len(predicted_set), "reference_pixels": len(reference_set)}


def measurement_metrics(predicted: Sequence[float], reference: Sequence[float]) -> dict[str, float | int]:
    """Return bias, MAE, RMSE, and 95% limits of agreement."""

    if len(predicted) != len(reference) or not predicted:
        raise ValidationError("measurement arrays must be non-empty and equal length")
    errors = [float(actual) - float(expected) for actual, expected in zip(predicted, reference)]
    if not all(isfinite(value) for value in errors):
        raise ValidationError("measurement arrays must contain finite values")
    bias = mean(errors)
    sd = stdev(errors) if len(errors) > 1 else 0.0
    return {"count": len(errors), "bias_mm": bias, "mae_mm": mean(abs(value) for value in errors), "rmse_mm": sqrt(mean(value * value for value in errors)), "limits_of_agreement_low_mm": bias - 1.96 * sd, "limits_of_agreement_high_mm": bias + 1.96 * sd}


def repeatability_metrics(measurements: Sequence[float]) -> dict[str, float | int]:
    """Summarize repeated captures of one fixed phantom or test object."""

    if not measurements:
        raise ValidationError("at least one repeated measurement is required")
    values = [float(value) for value in measurements]
    if not all(isfinite(value) for value in values):
        raise ValidationError("repeatability measurements must be finite")
    average = mean(values)
    deviation = stdev(values) if len(values) > 1 else 0.0
    return {"count": len(values), "mean": average, "standard_deviation": deviation, "coefficient_of_variation_pct": (100 * deviation / abs(average)) if average else inf}
