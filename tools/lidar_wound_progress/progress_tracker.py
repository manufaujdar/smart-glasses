"""Longitudinal LiDAR geometry review for synthetic research manifests."""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from surface_metrics import DepthFrame, DepthGridError, analyze_depth_frame  # type: ignore[no-redef]
else:
    from .surface_metrics import DepthFrame, DepthGridError, analyze_depth_frame


class ProgressManifestError(ValueError):
    """Raised when a longitudinal manifest is not safe to interpret."""


@dataclass(frozen=True)
class Capture:
    capture_id: str
    captured_at: datetime
    frame: DepthFrame
    roi: tuple[int, int, int, int]
    ring_width: int


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ProgressManifestError("captured_at must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProgressManifestError(f"invalid captured_at timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ProgressManifestError("captured_at must include a timezone offset")
    return parsed.astimezone(timezone.utc)


def _roi(value: Any) -> tuple[int, int, int, int]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 4:
        raise ProgressManifestError("roi must contain x0 y0 x1 y1")
    try:
        return tuple(int(item) for item in value)  # type: ignore[return-value]
    except (TypeError, ValueError) as exc:
        raise ProgressManifestError("roi coordinates must be integers") from exc


def _spacing(value: Any) -> tuple[float, float]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 2:
        raise ProgressManifestError("pixel_size_mm must contain x and y spacing")
    try:
        px, py = (float(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise ProgressManifestError("pixel_size_mm must be numeric") from exc
    if not math.isfinite(px) or not math.isfinite(py) or px <= 0 or py <= 0:
        raise ProgressManifestError("pixel_size_mm must be finite and greater than zero")
    return px, py


def load_manifest(path: str | Path) -> tuple[str, list[Capture]]:
    """Load one opaque study wound and its time-ordered depth captures."""

    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProgressManifestError(f"could not read manifest: {source}") from exc
    if not isinstance(payload, dict):
        raise ProgressManifestError("manifest must be a JSON object")
    wound_id = payload.get("wound_id")
    if not isinstance(wound_id, str) or not wound_id.strip():
        raise ProgressManifestError("manifest requires an opaque, non-empty wound_id")
    captures_payload = payload.get("captures")
    if not isinstance(captures_payload, list) or not captures_payload:
        raise ProgressManifestError("manifest requires a non-empty captures list")
    default_roi = _roi(payload["roi"]) if "roi" in payload else None
    default_spacing = _spacing(payload["pixel_size_mm"]) if "pixel_size_mm" in payload else None
    default_ring = int(payload.get("ring_width_px", 2))
    captures: list[Capture] = []
    for item in captures_payload:
        if not isinstance(item, dict):
            raise ProgressManifestError("each capture must be a JSON object")
        capture_id = item.get("capture_id")
        if not isinstance(capture_id, str) or not capture_id.strip():
            raise ProgressManifestError("each capture requires a non-empty capture_id")
        roi_value = item["roi"] if "roi" in item else default_roi
        spacing_value = item["pixel_size_mm"] if "pixel_size_mm" in item else default_spacing
        roi = _roi(roi_value) if roi_value is not None else None
        spacing = _spacing(spacing_value) if spacing_value is not None else None
        if roi is None or spacing is None:
            raise ProgressManifestError("each capture requires roi and pixel_size_mm, directly or by manifest default")
        try:
            ring_width = int(item.get("ring_width_px", default_ring))
        except (TypeError, ValueError) as exc:
            raise ProgressManifestError("ring_width_px must be an integer") from exc
        if ring_width < 1:
            raise ProgressManifestError("ring_width_px must be greater than zero")
        if "depth_mm" not in item:
            raise ProgressManifestError(f"capture {capture_id!r} is missing depth_mm")
        captures.append(
            Capture(
                capture_id=capture_id,
                captured_at=_timestamp(item.get("captured_at")),
                frame=DepthFrame(item["depth_mm"], spacing[0], spacing[1], capture_id),
                roi=roi,
                ring_width=ring_width,
            )
        )
    captures.sort(key=lambda capture: (capture.captured_at, capture.capture_id))
    if len({capture.capture_id for capture in captures}) != len(captures):
        raise ProgressManifestError("capture_id values must be unique")
    return wound_id, captures


def _change(baseline: float, latest: float) -> dict[str, float | None]:
    absolute = latest - baseline
    percentage = None if abs(baseline) < 1e-9 else absolute / abs(baseline) * 100.0
    return {"absolute": absolute, "percent": percentage}


def _direction(percent: float | None, tolerance_pct: float) -> str:
    if percent is None:
        return "not_comparable"
    if percent <= -tolerance_pct:
        return "decreasing"
    if percent >= tolerance_pct:
        return "increasing"
    return "stable"


def analyze_manifest(
    wound_id: str,
    captures: Sequence[Capture],
    tolerance_pct: float = 5.0,
    min_quality_score: float = 0.6,
) -> dict[str, Any]:
    """Analyze serial captures and return a geometry-only trajectory signal."""

    if not captures:
        raise ProgressManifestError("at least one capture is required")
    if not math.isfinite(tolerance_pct) or tolerance_pct <= 0:
        raise ProgressManifestError("tolerance_pct must be finite and greater than zero")
    if not 0 <= min_quality_score <= 1:
        raise ProgressManifestError("min_quality_score must be between zero and one")
    summaries: list[dict[str, Any]] = []
    for capture in captures:
        metrics = analyze_depth_frame(capture.frame, capture.roi, capture.ring_width)
        summaries.append(
            {
                "capture_id": capture.capture_id,
                "captured_at": capture.captured_at.isoformat().replace("+00:00", "Z"),
                "roi": metrics["roi"],
                "measurements": metrics["measurements"],
                "quality": metrics["quality"],
            }
        )
    baseline = summaries[0]
    latest = summaries[-1]
    metric_names = [
        "median_depth_offset_mm",
        "p95_depth_offset_mm",
        "estimated_positive_volume_mm3",
    ]
    baseline_score = baseline["quality"]["engineering_quality_score"]
    latest_score = latest["quality"]["engineering_quality_score"]
    low_quality_ids = [
        summary["capture_id"]
        for summary in summaries
        if summary["quality"]["engineering_quality_score"] < min_quality_score
    ]
    comparisons: dict[str, Any] = {}
    directions: list[str] = []
    for name in metric_names:
        change = _change(baseline["measurements"][name], latest["measurements"][name])
        direction = _direction(change["percent"], tolerance_pct)
        comparisons[name] = {**change, "direction": direction}
        if direction in {"decreasing", "increasing"}:
            directions.append(direction)
    if len(summaries) < 2:
        signal = "insufficient_data"
    elif low_quality_ids or baseline_score < min_quality_score or latest_score < min_quality_score:
        signal = "insufficient_quality"
    elif directions.count("decreasing") >= 2 and "increasing" not in directions:
        signal = "decreasing_geometry"
    elif directions.count("increasing") >= 2 and "decreasing" not in directions:
        signal = "increasing_geometry"
    else:
        signal = "stable_or_mixed_geometry"
    return {
        "tool": {
            "name": "lidar-wound-progress",
            "version": "0.1.0",
            "purpose": "longitudinal geometry review for open research",
        },
        "study": {
            "wound_id": wound_id,
            "capture_count": len(summaries),
            "baseline_capture_id": baseline["capture_id"],
            "latest_capture_id": latest["capture_id"],
        },
        "captures": summaries,
        "comparison": {
            "tolerance_pct": tolerance_pct,
            "min_quality_score": min_quality_score,
            "latest_vs_baseline": comparisons,
            "geometry_signal": signal,
            "signal_definition": "two of three depth/volume metrics must move beyond tolerance in the same direction; this is not a healing or recovery determination",
        },
        "quality": {
            "low_quality_capture_ids": low_quality_ids,
            "review_required": True,
        },
        "safety": {
            "research_prototype_only": True,
            "not_for_diagnosis_or_treatment": True,
            "not_a_recovery_or_healing_determination": True,
            "not_for_triage_or_autonomous_action": True,
            "requires_consistent_sensor_pose_and_calibration": True,
            "requires_clinician_review": True,
            "limitations": [
                "The operator supplies the ROI for each capture; segmentation and registration are not included.",
                "A geometric decrease can reflect pose, lighting/reflectance, occlusion, ROI selection, or calibration changes rather than tissue healing.",
                "The tool does not assess infection, tissue viability, drainage, pain, odor, perfusion, or treatment response.",
                "Synthetic manifests are the only included data; patient captures and identifiers must remain outside Git.",
            ],
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review longitudinal LiDAR wound geometry from a JSON manifest.")
    parser.add_argument("manifest", help="JSON manifest containing one wound_id and one or more captures")
    parser.add_argument("--tolerance-pct", type=float, default=5.0)
    parser.add_argument("--min-quality-score", type=float, default=0.6)
    args = parser.parse_args(argv)
    try:
        wound_id, captures = load_manifest(args.manifest)
        report = analyze_manifest(wound_id, captures, args.tolerance_pct, args.min_quality_score)
    except (ProgressManifestError, DepthGridError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
