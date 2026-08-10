# Optional ML boundary

The first version does not require ML or an AI API. The deterministic plane-fit
and trend rules are easier to audit, test, and validate than an unvalidated
clinical model.

Future local model work may implement the interfaces in `contracts.py` for:

- operator-assistive wound-region segmentation;
- frame-quality or occlusion assessment;
- pose/registration quality assessment.

The first optional implementations are now available as explicit seams:

- `segmentation.py` contains a prompted [SAM 2](https://github.com/facebookresearch/sam2)
  adapter. SAM 2 is a general segmentation model, not an automatic wound
  segmenter; use it only with an operator prompt until a wound-specific model
  and held-out validation set exist. The same module also contains a
  TorchScript adapter for a locally trained automatic binary segmenter; the
  model weights and training pipeline are intentionally not bundled.
- `registration.py` contains an [Open3D](https://github.com/isl-org/Open3D)
  point-to-point ICP adapter with fitness and RMSE gates. Rejected alignment
  must block longitudinal comparison.

Keep these optional because the baseline browser/CLI tool must remain
dependency-free. Install the research dependencies from
`../requirements-optional.txt` only in an isolated environment, and record
the exact versions, model weights, and notices used for a study.

Any model must run behind an explicit adapter, emit model/version provenance,
return uncertainty or quality information, and fail closed to clinician review.
It must not infer infection, tissue viability, prognosis, treatment, or recovery
without a separately approved intended use and clinical validation plan.

Do not commit model weights, patient images, or cloud credentials here. A model
selection should be documented with dataset license, population coverage,
external validation, calibration, bias/robustness testing, and rollback plan.
