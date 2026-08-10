# Depthline paired-photo webapp

Run locally from the `Smart Glasses` project root:

```bash
python3 -m http.server 8766 --directory tools/lidar_wound_progress/webapp
```

Open `http://127.0.0.1:8766/`.

## Workflow

1. Add an earlier and later photograph. On a phone, the file inputs can open the
   camera; on a laptop, they open the image picker.
2. Include the same ruler or scale/color reference in both images and enter its
   known width plus pixel width per image.
3. Keep the same angle, distance, lighting, and anatomical framing. Set the
   normalized wound region around the wound.
4. Run the comparison and review the red segmentation overlays. Adjust
   sensitivity or conditions, then check the review box before treating the
   numbers as a comparable pair.
5. Save only the numeric result locally or download a JSON report. Image pixels
   are not stored in history.

## What is functional

- Local image loading and in-memory previews.
- A deterministic operator-assisted color-difference mask inside a chosen wound
  region, with largest-component cleanup.
- Calibrated 2D planimetry: area, perimeter, longest/widest dimensions,
  equivalent geometry, and circularity.
- Paired percentage area reduction and mean linear edge change.
- ROI image difference, changed-pixel fraction, and SSIM-style structural signal.
- Acquisition/review quality gates for scale, pose, lighting, segmentation review,
  and basic image quality.
- Optional operator-entered context for exudate, visible tissue context, and
  periwound context. These fields are not inferred by the app.

## What is not claimed

The browser mask is an operator-assistive heuristic, not a validated wound
segmentation model. It can fail with glare, dressings, blood, skin-tone or
lighting variation, shadows, blur, and a poorly chosen ROI. The result is a
photo-derived change report, not a healing score, diagnosis, infection result,
treatment recommendation, or clinical outcome.

For the evidence basis and limitations, see
[`WOUND_COMPARISON_METHOD.md`](../WOUND_COMPARISON_METHOD.md) and
[`VALIDATION_PROTOCOL.md`](../VALIDATION_PROTOCOL.md). Native ARCore/ARKit and
the calibrated depth-grid workflow remain separate from this photo route.
