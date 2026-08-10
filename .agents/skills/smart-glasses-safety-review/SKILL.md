---
name: smart-glasses-safety-review
description: Perform an independent safety, privacy, human-factors, and clinical-claim review of Smart Glasses prototype workflows. Use for surgeon-facing features, capture or telepresence flows, new device states, cloud or AI dependencies, clinical gateway changes, demonstrations, or release decisions.
---

# Review Smart Glasses prototype safety

Remain report-only. Read `AGENTS.md`, `docs/surgery/START_HERE.md` when applicable,
the workflow and architecture, safety/security documents, data flow, tests, and
user-visible claims.

1. Define user, environment, intended use, excluded use, and the harm caused by
   delay, distraction, stale information, false confidence, data exposure, or loss
   of control.
2. Trace capture, identifiers, media, metadata, display, storage, transfer, access,
   retention, deletion, and any cloud or model processing.
3. Test preflight, consent indicators, recording state, disconnects, low power,
   unsupported capability, interrupted transfer, network loss, AI failure, and the
   clear-view or safe-stop path.
4. Check that the prototype cannot be mistaken for navigation, diagnosis, treatment
   selection, autonomous action, or production clinical readiness.
5. Verify synthetic fixtures, least privilege, auditability, vendor isolation,
   license provenance, and human override.

Return severity-ranked findings, affected workflow/state, evidence, missing tests,
required mitigation, human approval gates, and release recommendation. Do not grant
clinical, privacy, security, legal, or regulatory approval.
