# Local healthcare-safeguard baseline

This project is research software. It is not HIPAA-certified, GDPR-certified,
FDA-cleared, CDSCO-approved, CE-marked, or approved for production clinical
use. Compliance depends on the organization, jurisdiction, intended use,
claims, data, contracts, hardware, and operating environment.

## Implemented prototype safeguards

- Synthetic-first operation: simulators use synthetic identifiers and staged
  events; production patient context is prohibited.
- Local-first tools: the device gateway, browser console, and analysis tools
  bind to loopback and do not require an external model or cloud service.
- Fail-closed commands: unsupported commands, missing capabilities, stale or
  duplicated intents, malformed inputs, and invalid safety state are rejected.
- Safe-stop behavior: disconnect, critical battery, capture-indicator loss,
  and required-capability loss stop active outputs in the synthetic runtime.
- Data minimization: raw captures are ignored by Git; local history contains
  synthetic command summaries only.
- Vendor isolation: proprietary SDKs remain local, gitignored, and behind a
  vendor-neutral adapter with a provenance record.
- Bounded interfaces: request size, command identifiers, event history, media
  buffers, transcript actions, and quality thresholds are constrained.

## Required before real patient data or clinical deployment

1. Freeze intended use, prohibited use, users, environment, claims, and the
   software/hardware functions subject to medical-device review.
2. Assign a responsible clinical safety owner, privacy owner, security owner,
   regulatory owner, and device/fleet owner.
3. Complete data-flow, threat, privacy, human-factors, and clinical-risk
   assessments with institutional approval.
4. Implement managed identity, least privilege, encryption, key rotation,
   secure logging, device attestation, signed updates, backup/recovery,
   retention, deletion, incident response, and vendor agreements.
5. Validate every supported hardware/firmware combination under representative
   noise, lighting, PPE, network, battery, thermal, cleaning, and failure states.
6. Validate speech, media, model, and workflow performance using a frozen
   protocol, independent references, subgroup reporting, and rollback plans.
7. Obtain any required BAA, DPA, IRB/ethics approval, clinical investigation,
   regulatory clearance, site authorization, and informed-consent process.

Open-source availability and passing automated tests do not constitute clinical
validation, regulatory clearance, cybersecurity certification, or a warranty.
