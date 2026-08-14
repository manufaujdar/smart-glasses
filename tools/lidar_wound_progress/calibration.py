"""Research phantom/depth calibration utilities with no runtime dependencies."""

from __future__ import annotations

from dataclasses import dataclass
import json
from math import isfinite, sqrt
from pathlib import Path
from typing import Any, Sequence


class CalibrationError(ValueError):
    """Raised when a phantom calibration cannot be trusted."""


@dataclass(frozen=True)
class CalibrationObservation:
    capture_id: str
    known_mm: float
    measured_mm: float


@dataclass(frozen=True)
class CalibrationReport:
    scale: float
    bias_mm: float
    observation_count: int
    mae_mm: float
    rmse_mm: float
    max_abs_error_mm: float
    passed: bool
    residuals_mm: tuple[float, ...]
    limitations: tuple[str, ...]


def fit_depth_calibration(observations: Sequence[CalibrationObservation], max_abs_error_mm: float = 1.0, min_observations: int = 3) -> CalibrationReport:
    """Fit known_mm = scale * measured_mm + bias_mm and apply a pass gate."""

    if len(observations) < min_observations:
        raise CalibrationError(f"at least {min_observations} phantom observations are required")
    if max_abs_error_mm <= 0:
        raise CalibrationError("max_abs_error_mm must be positive")
    known = [float(item.known_mm) for item in observations]
    measured = [float(item.measured_mm) for item in observations]
    if not all(isfinite(value) and value > 0 for value in known + measured):
        raise CalibrationError("phantom distances must be finite and positive")
    mean_measured = sum(measured) / len(measured)
    mean_known = sum(known) / len(known)
    denominator = sum((value - mean_measured) ** 2 for value in measured)
    if denominator <= 1e-12:
        raise CalibrationError("phantom observations must span more than one measured distance")
    scale = sum((m - mean_measured) * (k - mean_known) for m, k in zip(measured, known)) / denominator
    bias = mean_known - scale * mean_measured
    residuals = tuple(scale * m + bias - k for m, k in zip(measured, known))
    absolute = [abs(value) for value in residuals]
    mae = sum(absolute) / len(absolute)
    rmse = sqrt(sum(value * value for value in residuals) / len(residuals))
    maximum = max(absolute)
    return CalibrationReport(
        scale=scale,
        bias_mm=bias,
        observation_count=len(observations),
        mae_mm=mae,
        rmse_mm=rmse,
        max_abs_error_mm=maximum,
        passed=maximum <= max_abs_error_mm,
        residuals_mm=residuals,
        limitations=(
            "phantom calibration does not establish clinical accuracy",
            "repeat across distance, angle, material, lighting, and device units",
            "store the phantom identity and traceable reference measurements outside this numeric report",
        ),
    )


def load_calibration_observations(path: str | Path) -> list[CalibrationObservation]:
    """Load a synthetic or de-identified JSON calibration manifest."""

    payload: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = payload.get("observations") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise CalibrationError("calibration manifest must contain an observations list")
    return [CalibrationObservation(str(row["capture_id"]), float(row["known_mm"]), float(row["measured_mm"])) for row in rows]
