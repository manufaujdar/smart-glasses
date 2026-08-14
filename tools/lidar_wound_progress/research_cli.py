"""Small local CLI for synthetic calibration/validation manifests."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .calibration import fit_depth_calibration, load_calibration_observations
from .validation import measurement_metrics, repeatability_metrics, segmentation_metrics


def validate_manifest(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    result: dict[str, Any] = {}
    result["segmentation"] = [segmentation_metrics(case["predicted"], case["reference"]) for case in payload.get("segmentation_cases", [])]
    pairs = payload.get("measurement_pairs", [])
    if pairs:
        result["measurement"] = measurement_metrics(
            [case["predicted_mm"] for case in pairs],
            [case["reference_mm"] for case in pairs],
        )
    if payload.get("repeatability_mm"):
        result["repeatability"] = repeatability_metrics(payload["repeatability_mm"])
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Depthline research calibration and validation utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    calibration = subparsers.add_parser("calibrate", help="fit a phantom depth calibration")
    calibration.add_argument("manifest", type=Path)
    calibration.add_argument("--max-error-mm", type=float, default=1.0)
    validate = subparsers.add_parser("validate", help="calculate research metrics")
    validate.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    if args.command == "calibrate":
        report = fit_depth_calibration(load_calibration_observations(args.manifest), max_abs_error_mm=args.max_error_mm)
        print(json.dumps(asdict(report), indent=2))
    else:
        print(json.dumps(validate_manifest(args.manifest), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
