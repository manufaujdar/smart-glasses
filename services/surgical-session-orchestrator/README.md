# Surgical session orchestrator

Future policy and audit service for surgeon-facing sessions. It should expose a
small OpenAPI contract for synthetic data before any hospital integration.

Planned responsibilities:

- issue short-lived synthetic/approved session tokens
- evaluate recording, streaming, participant and retention policy
- correlate device, workflow and gateway events
- revoke authorization and force a safe-stop event
- route only approved, minimized requests to a versioned model gateway
- export a redacted audit trail without media or patient identifiers

This service must not control instruments, generate navigation, or automatically
write to a clinical record.
