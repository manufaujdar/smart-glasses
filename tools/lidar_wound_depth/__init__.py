"""Vendor-neutral LiDAR depth analysis primitives for research prototypes."""

from .lidar_wound_depth import (
    AnalysisResult,
    DepthFrame,
    DepthFrameSource,
    DepthGridError,
    analyze_depth_frame,
    load_depth_input,
)

__all__ = [
    "AnalysisResult",
    "DepthFrame",
    "DepthFrameSource",
    "DepthGridError",
    "analyze_depth_frame",
    "load_depth_input",
]
