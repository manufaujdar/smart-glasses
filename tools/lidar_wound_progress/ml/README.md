# Optional ML boundary

The first version does not require ML or an AI API. The deterministic plane-fit
and trend rules are easier to audit, test, and validate than an unvalidated
clinical model.

Future local model work may implement the interfaces in `contracts.py` for:

- operator-assistive wound-region segmentation;
- frame-quality or occlusion assessment;
- pose/registration quality assessment.

Any model must run behind an explicit adapter, emit model/version provenance,
return uncertainty or quality information, and fail closed to clinician review.
It must not infer infection, tissue viability, prognosis, treatment, or recovery
without a separately approved intended use and clinical validation plan.

Do not commit model weights, patient images, or cloud credentials here. A model
selection should be documented with dataset license, population coverage,
external validation, calibration, bias/robustness testing, and rollback plan.
