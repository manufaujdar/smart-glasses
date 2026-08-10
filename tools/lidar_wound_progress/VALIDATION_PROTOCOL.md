# Measurement and model validation plan

This is a research protocol scaffold, not evidence that Depthline is clinically
validated. Run it only with synthetic or ethics-approved, de-identified data.

## Segmentation

1. Freeze the model version, checkpoint hash, preprocessing, prompt policy, and
   device configuration.
2. Split data by subject, not by image. Keep a held-out test set and blind the
   reviewer to the reference mask.
3. Report Dice, IoU, precision, recall, and Hausdorff-95, with confidence
   intervals and subgroup breakdowns for wound type, skin tone, illumination,
   device, and wound size.
4. Require operator review of every automatic mask. An accepted mask must carry
   model/version provenance and an uncertainty or quality flag.

`validation.py` provides deterministic metric calculations. It does not choose
a clinical threshold.

## Depth and calibration

1. Use a traceable phantom with multiple known depths spanning the intended
   measurement range and repeat captures across distance, angle, lighting,
   device orientation, and operators.
2. Fit calibration only on a calibration set. Keep an independent test set for
   bias, MAE, RMSE, maximum error, and limits of agreement.
3. Reject a frame when native confidence, coverage, registration fitness, or
   registration RMSE is outside the predeclared error budget.
4. Never compare a manual RGB estimate against a native depth record as if they
   were the same measurement modality.

`calibration.py` provides an affine phantom fit. `ml/registration.py` provides
an optional Open3D ICP seam with fail-closed quality gates.

## Clinical study handoff

Before any patient-facing or clinical claim, obtain the appropriate ethics,
privacy, security, regulatory, and institutional approvals. Define the intended
use, reference standard, inclusion/exclusion criteria, sample-size rationale,
adjudication process, missing-data rules, adverse-event process, and release
rollback criteria. A lower depth error on a phantom does not establish better
clinical outcomes or recovery prediction.
