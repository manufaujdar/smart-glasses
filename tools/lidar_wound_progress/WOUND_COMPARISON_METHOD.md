# Paired-photo comparison method

Depthline now treats the primary task as comparing an earlier capture with a
later capture. It reports measurable differences only. It must not convert a
photo difference into a healing, recovery, infection, or treatment claim.

## What the algorithm measures

For each operator-reviewed wound mask, the tool calculates:

- calibrated area in mm² using a scale marker or known pixel spacing;
- grid perimeter, longest dimension, widest dimension, equivalent diameter, and
  circularity;
- percentage area reduction from baseline to follow-up;
- mean linear edge change, `Δarea / mean(perimeter)`, which is less dependent on
  wound size than percentage area alone;
- optional tissue-class proportions when a validated segmentation model supplies
  them. The browser's current red/yellow/dark color mix is only a heuristic
  image descriptor and must not be read as granulation, slough, or eschar
  classification;
- an image-difference/SSIM-style signal as an image-change and quality aid, not
  a wound outcome.

The paired result also carries a comparability gate based on scale-marker
presence, pose alignment, lighting consistency, segmentation review, and image
quality. Missing or poor inputs are reported as flags rather than silently
producing a clinical-looking score.

## Why these factors are included

Digital planimetry is preferable to multiplying longest length by widest width:
the latter can overestimate wound area substantially. Wound assessment tools
such as PUSH and BWAT use dimensions and additional clinical observations, so
the app separates image-derived geometry from optional clinician-entered
context. Tissue proportions are kept optional because color is highly sensitive
to acquisition and calibration.

Percentage area reduction is useful for longitudinal research but is not a
complete healing endpoint and can behave differently across wound sizes. The
linear edge-change measure is included as a complementary value, not a
replacement for a validated clinical endpoint.

## Acquisition requirements

Use the same wound orientation, camera distance, field of view, lighting,
scale/color reference, and anatomical framing at both time points. A scale
marker is required for calibrated area. The user must review the segmentation
before accepting a comparison. A change in pose, focus, glare, dressing,
exudate, or lighting can create a large image difference without tissue change.

## Research references

- [NSW Agency for Clinical Innovation wound assessment toolkit](https://aci.health.nsw.gov.au/networks/spinal-cord-injury/pi-toolkit/assessment/wound-assessment/validated-tool)
- [Digital planimetry compared with ruler measurement](https://pmc.ncbi.nlm.nih.gov/articles/PMC2909508/)
- [Non-contact digital planimetry with a scale marker](https://pubmed.ncbi.nlm.nih.gov/36001845/)
- [Automatic colorimetric calibration of human wounds](https://pmc.ncbi.nlm.nih.gov/articles/PMC2850874/)
- [Standardized injury photography protocol](https://pubmed.ncbi.nlm.nih.gov/26932497/)
- [Wound healing rate and wound geometry](https://doi.org/10.1016/S0741-5214(96)80021-8)
- [Structural Similarity Index (SSIM)](https://pubmed.ncbi.nlm.nih.gov/15376593/)

These references support the measurement design, not the clinical validity of
this implementation. Any clinical study still needs a prespecified protocol,
independent reference method, ethics/privacy review, representative data,
inter-rater analysis, and external validation.
