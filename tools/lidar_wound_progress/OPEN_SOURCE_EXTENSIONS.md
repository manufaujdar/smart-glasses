# Open-source extension plan

Reviewed 2026-08-10. These projects are references or optional future
dependencies. No source code, model weights, datasets, or proprietary SDKs were
copied into Depthline.

| Project | Proposed use | Current decision | License/provenance boundary |
|---|---|---|---|
| [Open3D](https://github.com/isl-org/Open3D) | Optional point-cloud registration, outlier filtering, and 3D QA for professional scans. | Keep behind `RegistrationAdapter`; do not add to the dependency-free baseline. | Confirm the exact release and third-party notices before distribution. |
| [MONAI](https://github.com/Project-MONAI/MONAI) | Future local segmentation/quality-model training and evaluation. | Use only after a wound dataset, external validation plan, and model-card process exist. | Apache-2.0 project license does not license a future dataset or model weights. |
| [MONAI Label](https://github.com/Project-MONAI/MONAILabel) | Human-in-the-loop annotation and review workflow for research data. | Prefer for an offline research labeling station, not embedded in the small webapp. | Review server, data, and extension security before any real captures. |
| [3D Slicer](https://github.com/Slicer/Slicer) | Independent visual QA of exported point clouds/depth surfaces. | Use as a reviewer tool during validation, not as a runtime dependency. | Follow Slicer and bundled extension notices. |
| [Wound Vision](https://github.com/OneManLabs/wound-vision) | Product/UX and on-device privacy reference for camera/LiDAR workflows. | Reference only; do not reuse source or model assets. | PolyForm Noncommercial is source-available, not an OSI open-source license. |
| [WoundFilling3D](https://github.com/SIMOGroup/WoundFilling3D) | Research reference for 3D wound segmentation and fill extraction. | Reference only until code, dataset, and model terms are independently verified. | Do not copy code or download linked datasets into this repository without review. |

## Recommended order

1. Improve calibration fixtures and repeated-scan registration with synthetic and
   phantom data.
2. Add an optional Open3D adapter for professional point clouds and compare its
   registration error against a known transform.
3. Add operator-reviewed segmentation only after a licensed, representative
   dataset and a held-out validation protocol exist.
4. Keep the browser camera path as a documented 2D/manual estimate until a
   validated depth-capable device API is available.

The core tool remains intentionally small: Python standard library, explicit
quality flags, reproducible synthetic fixtures, and no cloud inference.
