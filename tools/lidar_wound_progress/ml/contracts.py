"""Compatibility contracts for optional model and registration adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence


@dataclass(frozen=True)
class SegmentationResult:
    """A future segmentation adapter's reviewable output contract."""

    mask: Sequence[Sequence[bool]]
    model_name: str
    model_version: str
    quality_score: float
    limitations: tuple[str, ...]


class WoundSegmentationAdapter(Protocol):
    """Implement behind this boundary if a locally validated model is added."""

    def segment(self, image_bytes: bytes, metadata: dict[str, Any]) -> SegmentationResult:
        """Return a mask and provenance; never return a treatment recommendation."""


class ReviewQualityAdapter(Protocol):
    """Optional model-assisted quality review, not a diagnostic classifier."""

    def assess(self, measurements: dict[str, float], metadata: dict[str, Any]) -> dict[str, Any]:
        """Return data-quality information with model/version provenance."""


class RegistrationAdapter(Protocol):
    """Optional frame-registration boundary for repeated professional scans."""

    def register(
        self,
        reference_points: Sequence[Sequence[float]],
        current_points: Sequence[Sequence[float]],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Return a transform, fitness, and uncertainty; never a clinical label."""


# Concrete optional adapters live in separate modules so importing the package
# never imports torch, Open3D, NumPy, or a vendor SDK.
