# Smart Glasses documentation

Recommended reading order:

1. [`00-project-overview.md`](00-project-overview.md) — mission, scope, and non-goals.
2. [`architecture/system-architecture.md`](architecture/system-architecture.md) and
   [`architecture/device-integration-runtime.md`](architecture/device-integration-runtime.md) —
   boundaries and runtime contracts.
3. [`surgery/START_HERE.md`](surgery/START_HERE.md) — surgeon-facing research scope,
   safety, and validation.
4. [`research/open-source-repository-review.md`](research/open-source-repository-review.md),
   [`research/open-source-runtime-review.md`](research/open-source-runtime-review.md),
   and [`../third_party/README.md`](../third_party/README.md) — provenance and reuse.
5. [`../PRIVACY_AND_DATA_BOUNDARY.md`](../PRIVACY_AND_DATA_BOUNDARY.md),
   [`security/threat-model.md`](security/threat-model.md), and the test plans —
   privacy, security, and validation.

## Release boundary

The repository is Apache-2.0 research code with synthetic simulators. It is not
a clinical device, diagnostic or treatment system, medical-navigation service,
or evidence of regulatory clearance. Physical hardware, vendor SDKs, patient
media, PHI, clinical gateways, and hospital deployment require separate
provenance, privacy, safety, security, and human approval gates.
