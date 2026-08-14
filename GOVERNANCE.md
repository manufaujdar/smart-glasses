# Governance

Smart Glasses Clinical Platform is an early-stage open-source research project.

## Maintainer

The repository maintainer is Manu Faujdar. The maintainer reviews pull
requests, releases, dependency and provenance changes, safety language, and
changes to vendor or clinical boundaries. A change may be rejected when it
increases safety, privacy, security, licensing, or overclaiming risk.

## Contributions

Contributions should include focused tests, documentation, provenance, and a
clear statement of what remains simulated or unvalidated. Changes involving
patient data, clinical claims, medical-device intended use, proprietary SDK
redistribution, device capture, model weights, or external AI services require
explicit review before merge.

## Decision ownership

- Device/protocol changes require reproducible evidence and adapter-contract review.
- Surgeon-facing changes require independent clinical-safety and human-factors review.
- Data or recording changes require privacy and security review.
- AI/model changes require model, dataset, evaluation, monitoring, and rollback records.
- A maintainer approval is an open-source decision, not clinical sign-off.

## Releases

Releases should update [CHANGELOG.md](CHANGELOG.md), pass CI, run the local
frontend audit, confirm license/provenance boundaries, and state unresolved
limitations. A version tag never implies clinical validation or regulatory
clearance.
