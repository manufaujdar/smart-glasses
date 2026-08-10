"""Optional, provenance-first segmentation adapters.

The dependency-free project does not ship a wound model.  This module defines
the seam for a locally hosted model and includes a prompted SAM 2 adapter for
research use.  SAM 2 is a general segmentation model; its output is not a
wound classifier and must be validated with wound-specific data before use.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Protocol, Sequence


class SegmentationError(ValueError):
    """Raised when an adapter cannot produce a reviewable mask."""


@dataclass(frozen=True)
class SegmentationResult:
    """A mask plus enough provenance for an operator to review it."""

    mask: tuple[tuple[bool, ...], ...]
    model_name: str
    model_version: str
    confidence: float
    uncertainty: str
    limitations: tuple[str, ...]


class WoundSegmentationAdapter(Protocol):
    """Local segmentation boundary; implementations must not recommend care."""

    def segment(self, image: Any, prompt: Sequence[float]) -> SegmentationResult:
        """Return a reviewable mask for an image and a user-supplied prompt."""


def validate_mask(mask: Sequence[Sequence[Any]]) -> tuple[tuple[bool, ...], ...]:
    """Validate and normalize a rectangular binary mask without NumPy."""

    if not isinstance(mask, Sequence) or isinstance(mask, (str, bytes)) or not mask:
        raise SegmentationError("mask must be a non-empty 2D sequence")
    rows: list[tuple[bool, ...]] = []
    width: int | None = None
    for row in mask:
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes)) or not row:
            raise SegmentationError("mask rows must be non-empty sequences")
        normalized = tuple(bool(value) for value in row)
        width = width or len(normalized)
        if len(normalized) != width:
            raise SegmentationError("mask must be rectangular")
        rows.append(normalized)
    return tuple(rows)


def validate_prompt(prompt: Sequence[float]) -> tuple[float, float, float, float]:
    """Validate an XYXY pixel box used to keep a general model supervised."""

    if len(prompt) != 4:
        raise SegmentationError("prompt must be [x0, y0, x1, y1]")
    values = tuple(float(value) for value in prompt)
    if not all(isfinite(value) for value in values) or values[2] <= values[0] or values[3] <= values[1]:
        raise SegmentationError("prompt must contain a finite, positive XYXY box")
    return values  # type: ignore[return-value]


class PromptedSam2Adapter:
    """Lazy SAM 2 integration; weights and model selection remain caller-owned.

    The adapter intentionally requires a box prompt.  Automatic wound
    segmentation still needs a wound-specific detector/segmenter, a licensed
    dataset, and a held-out validation protocol.
    """

    def __init__(self, checkpoint: str, model_config: str, model_version: str, device: str = "cpu") -> None:
        self.checkpoint = checkpoint
        self.model_config = model_config
        self.model_version = model_version
        self.device = device
        self._predictor: Any | None = None

    def _load(self) -> Any:
        if self._predictor is not None:
            return self._predictor
        try:
            import torch  # type: ignore
            from sam2.build_sam import build_sam2  # type: ignore
            from sam2.sam2_image_predictor import SAM2ImagePredictor  # type: ignore
        except ImportError as exc:
            raise SegmentationError(
                "SAM 2 adapter requires the optional sam2, torch, and image dependencies"
            ) from exc
        model = build_sam2(self.model_config, self.checkpoint, device=self.device)
        self._predictor = (SAM2ImagePredictor(model), torch)
        return self._predictor

    def segment(self, image: Any, prompt: Sequence[float]) -> SegmentationResult:
        box = validate_prompt(prompt)
        predictor, torch = self._load()
        try:
            import numpy as np  # type: ignore

            predictor.set_image(np.asarray(image))
            with torch.inference_mode():
                masks, scores, _ = predictor.predict(box=np.asarray(box, dtype=float), multimask_output=True)
            best = max(range(len(scores)), key=lambda index: float(scores[index]))
            mask = validate_mask(np.asarray(masks[best], dtype=bool).tolist())
            confidence = float(scores[best])
        except (ImportError, TypeError, ValueError, IndexError) as exc:
            raise SegmentationError(f"SAM 2 could not produce a valid mask: {exc}") from exc
        return SegmentationResult(
            mask=mask,
            model_name="SAM 2 prompted segmentation",
            model_version=self.model_version,
            confidence=confidence,
            uncertainty="model confidence is not clinical uncertainty",
            limitations=(
                "generic prompted segmentation; not wound-specific",
                "operator must review the mask",
                "requires local model weights and external validation",
            ),
        )
