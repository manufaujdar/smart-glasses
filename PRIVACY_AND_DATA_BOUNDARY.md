# Privacy and data boundary

Status: synthetic research prototype only. This file is a technical privacy
boundary, not a jurisdiction-specific privacy policy for a clinical or hosted
product.

## Current distribution

The repository contains vendor-neutral contracts, simulators, local tooling,
and research adapters. Examples and tests must remain synthetic. Do not add
patient identifiers, clinical captures, private audio/video, credentials,
vendor SDK binaries, model weights, or production logs. Public source
availability does not authorize collection or use of protected health
information.

Future device, media, voice, gateway, cloud, or clinical integrations may
collect or transmit data. Their terms, licenses, permissions, retention, and
security controls are separate from this repository and must be recorded
before redistribution or deployment.

## Deployment responsibility

Before any real-person or clinical use, the responsible organization must
approve intended use, data classification, notice/consent or authorization,
minimum-necessary handling, identity/access, encryption, key management,
retention/deletion, audit, incident response, device permissions, vendor terms,
contracts, regulatory/IRB requirements, and human-factors validation. A hosted
deployment must publish its own privacy notice and terms of service. This
repository does not provide them.

## Legal and safety boundary

The Apache-2.0 `LICENSE` governs the repository's source code. It does not
license third-party device SDKs, hardware, clinical data, images, models,
providers, or vendor marks. See `NOTICE`, `OPEN_SOURCE_EXTENSIONS.md`,
`COMPLIANCE.md`, `SECURITY.md`, and `VALIDATION_PROTOCOL.md`.

Reviewed: 2026-08-14.
