# Clinical gateway

Planned server-side control plane. Keep it out of the first BLE bring-up loop.

Responsibilities:

- hospital identity and tenant policy
- encounter-context tokens and expiry
- consent/recording policy
- FHIR and DICOM adapters
- AI model routing, citations, abstention and release versions
- immutable clinical audit events
- encrypted media upload and retention

The first implementation should expose a small OpenAPI contract and accept synthetic data only. Do not send PHI to generic development services.

