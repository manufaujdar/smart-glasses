"""Optional point-cloud registration for repeated professional scans."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Sequence


class RegistrationError(ValueError):
    """Raised when registration is unavailable or fails quality gates."""


@dataclass(frozen=True)
class RegistrationResult:
    transform: tuple[tuple[float, ...], ...]
    fitness: float
    inlier_rmse_mm: float
    backend: str
    accepted: bool
    limitations: tuple[str, ...]


def _validate_points(points: Sequence[Sequence[float]]) -> list[list[float]]:
    if len(points) < 3:
        raise RegistrationError("at least three 3D points are required")
    output: list[list[float]] = []
    for point in points:
        if len(point) != 3:
            raise RegistrationError("registration points must be XYZ triples")
        values = [float(value) for value in point]
        if not all(isfinite(value) for value in values):
            raise RegistrationError("registration points must be finite")
        output.append(values)
    return output


class Open3DRegistrationAdapter:
    """Open3D ICP adapter with explicit fitness/RMSE gates.

    This is a geometric alignment helper, not a substitute for a clinical
    landmark protocol.  Callers should record the rejected result and ask for
    a recapture when quality gates fail.
    """

    def __init__(self, max_correspondence_distance_mm: float = 5.0, min_fitness: float = 0.7, max_rmse_mm: float = 2.0) -> None:
        if max_correspondence_distance_mm <= 0 or not 0 <= min_fitness <= 1 or max_rmse_mm <= 0:
            raise RegistrationError("registration thresholds must be positive and fitness must be 0..1")
        self.max_correspondence_distance_mm = float(max_correspondence_distance_mm)
        self.min_fitness = float(min_fitness)
        self.max_rmse_mm = float(max_rmse_mm)

    def register(self, reference_points: Sequence[Sequence[float]], current_points: Sequence[Sequence[float]]) -> RegistrationResult:
        reference = _validate_points(reference_points)
        current = _validate_points(current_points)
        try:
            import numpy as np  # type: ignore
            import open3d as o3d  # type: ignore
        except ImportError as exc:
            raise RegistrationError("Open3D registration requires optional open3d and numpy dependencies") from exc
        reference_cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(np.asarray(reference, dtype=float)))
        current_cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(np.asarray(current, dtype=float)))
        result = o3d.pipelines.registration.registration_icp(
            current_cloud,
            reference_cloud,
            self.max_correspondence_distance_mm,
            np.eye(4),
            o3d.pipelines.registration.TransformationEstimationPointToPoint(),
        )
        transform = tuple(tuple(float(value) for value in row) for row in result.transformation.tolist())
        fitness = float(result.fitness)
        rmse = float(result.inlier_rmse)
        accepted = fitness >= self.min_fitness and rmse <= self.max_rmse_mm
        return RegistrationResult(
            transform=transform,
            fitness=fitness,
            inlier_rmse_mm=rmse,
            backend="open3d-icp-point-to-point",
            accepted=accepted,
            limitations=(
                "requires stable surface/landmark capture and consistent units",
                "rejected registrations must not be used for longitudinal comparison",
                "geometric alignment is not clinical validation",
            ),
        )
