"""Optional OpenCV ChArUco calibration helper."""

from __future__ import annotations

from typing import Any, Sequence


class OpenCVCalibrationError(ValueError):
    """Raised when OpenCV calibration cannot be run."""


def calibrate_charuco(
    corners: Sequence[Any],
    ids: Sequence[Any],
    board: Any,
    image_size: tuple[int, int],
) -> dict[str, Any]:
    """Calibrate camera intrinsics from caller-detected ChArUco corners.

    Detection and board construction stay in the host capture app so the
    physical board dimensions and image preprocessing remain explicit. The
    return value contains plain Python values suitable for a review manifest.
    """

    if image_size[0] <= 0 or image_size[1] <= 0 or not corners or not ids:
        raise OpenCVCalibrationError("corners, ids, and image_size are required")
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ImportError as exc:
        raise OpenCVCalibrationError("ChArUco calibration requires optional opencv-contrib-python and numpy") from exc
    try:
        rms, camera_matrix, distortion, _, _ = cv2.aruco.calibrateCameraCharuco(
            list(corners), list(ids), board, image_size, None, None
        )
    except (AttributeError, cv2.error, TypeError, ValueError) as exc:
        raise OpenCVCalibrationError(f"OpenCV ChArUco calibration failed: {exc}") from exc
    return {
        "backend": "opencv-aruco-charuco",
        "rms_reprojection_error_px": float(rms),
        "image_size_px": [int(image_size[0]), int(image_size[1])],
        "camera_matrix": np.asarray(camera_matrix, dtype=float).tolist(),
        "distortion_coefficients": np.asarray(distortion, dtype=float).reshape(-1).tolist(),
        "limitations": [
            "reprojection error is an image-space calibration metric",
            "validate depth scale separately with a traceable phantom",
            "do not use calibration as evidence of clinical performance",
        ],
    }
