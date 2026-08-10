# Prototype threat model

| Threat | Required control |
|---|---|
| unauthorized BLE control | authenticated pairing, allowlist, connection ownership |
| replayed capture command | session nonce/sequence where supported; deduplicate at adapter |
| open Wi-Fi media endpoint | isolated test network, temporary credentials, verify vendor security |
| lost phone or glasses | encrypted storage, short retention, remote wipe where supported |
| covert recording | hard-visible indicator, explicit session state, immediate stop |
| PHI in logs | structured redaction; synthetic data in development |
| malicious scene/prompt injection | camera content is untrusted; tool allowlists and confirmation |
| compromised SDK/AAR | hash pinning, provenance record, isolated wrapper, SBOM |
| unsafe model output | draft-only, citations, abstention, human approval |
| wrong patient | explicit context, persistent identifier, expiry and switch confirmation |

## Prototype rule

Do not use real patient data. Use synthetic encounters and staged scenes until privacy, security and clinical governance approve a controlled pilot.

