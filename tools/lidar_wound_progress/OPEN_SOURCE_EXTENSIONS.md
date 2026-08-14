# Open-source extension plan

Reviewed 2026-08-10. These projects are references or optional future
dependencies. No source code, model weights, datasets, or proprietary SDKs were
copied into Depthline.

| Project | Proposed use | Current decision | License/provenance boundary |
|---|---|---|---|
| [Open3D](https://github.com/isl-org/Open3D) | Optional point-cloud registration, outlier filtering, and 3D QA for professional scans. | Keep behind `RegistrationAdapter`; do not add to the dependency-free baseline. | Confirm the exact release and third-party notices before distribution. |
| [SAM 2](https://github.com/facebookresearch/sam2) | Prompted mask generation as a research assist for operator-reviewed wound-region segmentation. | `ml/segmentation.py` provides a lazy adapter; it is not an automatic wound model. | Upstream code includes BSD-3-Clause and separate component notices; verify the exact release and model-checkpoint terms before redistribution. |
| [OpenCV ArUco/ChArUco](https://docs.opencv.org/4.x/da/d13/tutorial_aruco_calibration.html) | Camera/phantom board calibration and pose markers. | Use for a native capture/calibration utility; keep board geometry and error reports in the study record. | OpenCV is Apache-2.0; review contrib and bundled notices for the selected build. |
| [MONAI](https://github.com/Project-MONAI/MONAI) | Future local segmentation/quality-model training and evaluation. | Use only after a wound dataset, external validation plan, and model-card process exist. | Apache-2.0 project license does not license a future dataset or model weights. |
| [MONAI Label](https://github.com/Project-MONAI/MONAILabel) | Human-in-the-loop annotation and review workflow for research data. | Prefer for an offline research labeling station, not embedded in the small webapp. | Review server, data, and extension security before any real captures. |
| [3D Slicer](https://github.com/Slicer/Slicer) | Independent visual QA of exported point clouds/depth surfaces. | Use as a reviewer tool during validation, not as a runtime dependency. | Follow Slicer and bundled extension notices. |
| [Wound Vision](https://github.com/OneManLabs/wound-vision) | Product/UX and on-device privacy reference for camera/LiDAR workflows. | Reference only; do not reuse source or model assets. | PolyForm Noncommercial is source-available, not an OSI open-source license. |
| [WoundFilling3D](https://github.com/SIMOGroup/WoundFilling3D) | Research reference for 3D wound segmentation and fill extraction. | Reference only until code, dataset, and model terms are independently verified. | Do not copy code or download linked datasets into this repository without review. |
| [ARCore Depth API](https://developers.google.com/ar/develop/depth) | Native Android depth frames when supported by the device and enabled by the app. | `apps/android-controller/src/ArCoreDepthProvider.kt` defines the integration boundary; it is not part of the browser app. | Google platform SDK terms apply; this is a platform integration, not an open-source dependency. |
| [ARKit sceneDepth](https://developer.apple.com/documentation/arkit/arframe/scenedepth) | Native iOS LiDAR scene depth and confidence buffers on supported devices. | `apps/ios-depth-adapter/ARKitDepthProvider.swift` defines the integration boundary. | Apple platform SDK terms apply; this is a platform integration, not an open-source dependency. |
| [WebXR Depth Sensing](https://immersive-web.github.io/depth-sensing/) | Capability-detected browser depth when a browser/device exposes it. | `webapp/depth-adapter.js` detects it without prompting and leaves permission/session start to an explicit native-capable workflow. | W3C specification; browser support and privacy/permission behavior vary. |

## Recommended order

1. Improve calibration fixtures and repeated-scan registration with synthetic and
   phantom data.
2. Add an optional Open3D adapter for professional point clouds and compare its
   registration error against a known transform.
3. Add operator-reviewed segmentation only after a licensed, representative
   dataset and a held-out validation protocol exist.
4. Keep the browser camera path as a documented 2D/manual estimate until a
   validated depth-capable device API is available.

The new research utilities in `calibration.py`, `validation.py`, and
`depth_provider.py` are intentionally metric/contract code. They do not ship a
wound model, infer healing, or establish clinical validity. Clinical validation
requires a preregistered protocol, representative de-identified data, an
independent reference method, blinded review, repeatability/reproducibility
analysis, subgroup analysis, and appropriate ethics/regulatory review.

The core tool remains intentionally small: Python standard library, explicit
quality flags, reproducible synthetic fixtures, and no cloud inference.
