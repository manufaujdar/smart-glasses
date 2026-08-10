"""Optional ML seams; the baseline project intentionally uses no model."""

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
