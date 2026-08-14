# Platform validation protocol

This is a research protocol scaffold, not evidence that the platform is
clinically validated. Use synthetic or formally approved, de-identified data.

## Device and protocol validation

1. Freeze device model, firmware, SDK/driver version, phone OS, application
   revision, network profile, and configuration.
2. Measure discovery, connection, command acknowledgement, reconnection,
   duplicate suppression, interrupted transfer, checksum, battery, and thermal
   behavior across repeated trials.
3. Exercise Bluetooth/Wi-Fi loss, app backgrounding, low battery, capture
   indicator loss, permission removal, storage exhaustion, and firmware mismatch.
4. Report failures and confidence intervals; do not report only successful runs.

## Media and voice validation

- Report latency percentiles, frame loss, keyframe recovery, resolution, audio
  intelligibility, word/command error, false activation, confirmation failure,
  and safe-stop latency in representative environments.
- Stratify speech testing by language, accent, mask/PPE, room noise, microphone
  placement, sex/age where appropriate, and device model.
- Validate that narration cannot trigger commands and that every consequential
  voice action requires the documented confirmation policy.

## Workflow and human-factors validation

- Predefine task success, use error, completion time, workload, distraction,
  visual obstruction, discomfort, override, abandonment, and near-miss metrics.
- Use representative clinicians, PPE, loupes, lighting, posture, procedure
  duration, interruptions, and team communication.
- Record whether failures are detectable, recoverable, and attributable.
- Test the clear-view and safe-stop paths without network or AI availability.

## AI or model validation

Before enabling any model beyond synthetic research, complete the repository's
[MODEL_CARD_TEMPLATE.md](MODEL_CARD_TEMPLATE.md) and
[DATASET_CARD_TEMPLATE.md](DATASET_CARD_TEMPLATE.md). Freeze hashes,
preprocessing, prompts, tools, thresholds, fallback behavior, and monitoring.
Report task-specific accuracy, calibration, abstention, subgroup performance,
robustness, provenance, and clinically meaningful failure modes.

## Release gate

A research release requires passing automated tests, syntax/compilation checks,
frontend audit, provenance review, documentation of known failures, and human
review. Physical-device or clinical claims require additional evidence and are
not authorized by this protocol alone.
