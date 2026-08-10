# Optional ML boundary

The first version does not require ML or an AI API. The deterministic plane-fit
and trend rules are easier to audit, test, and validate than an unvalidated
clinical model.

Future local model work may implement the interfaces in `contracts.py` for:

- operator-assistive wound-region segmentation;
- frame-quality or occlusion assessment;
- pose/registration quality assessment.

For professional multi-frame scans, a future adapter may wrap an open-source
point-cloud library such as [Open3D](https://github.com/isl-org/Open3D) for
registration. Keep this optional because the baseline browser/CLI tool must
remain dependency-free and registration needs a validated fixture and error
budget before it can support longitudinal comparison.

Any model must run behind an explicit adapter, emit model/version provenance,
return uncertainty or quality information, and fail closed to clinician review.
It must not infer infection, tissue viability, prognosis, treatment, or recovery
without a separately approved intended use and clinical validation plan.

Do not commit model weights, patient images, or cloud credentials here. A model
selection should be documented with dataset license, population coverage,
external validation, calibration, bias/robustness testing, and rollback plan.
