# ARKit depth boundary

This adapter exposes ARKit `sceneDepth` and its confidence map for supported
LiDAR devices. Add it to a native iOS target with the appropriate camera usage
description and an explicit user-consent flow. Convert the depth map to the
project's `NativeDepthFrame` contract only after recording units, intrinsics,
device model, frame timestamp, and capture quality.

The browser cannot assume this API exists. A native host can export a calibrated
depth grid to the local Depthline workflow, or keep the full analysis on-device.
