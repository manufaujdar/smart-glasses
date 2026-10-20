# Documentation index

Smart Glasses is an Android-first, vendor-neutral healthcare smart-glasses
research and prototyping workspace. Its executable baseline is synthetic/local;
the Android/HeyCyan boundary and physical-device validation remain gated.

## Choose a task

| Task | Read first | Continue with |
| --- | --- | --- |
| Run the synthetic platform | [Quick start](../README.md#start-here) | [Technical overview](technical-overview.md) |
| Change device adapters | [System architecture](architecture/system-architecture.md) | [Runtime boundary](architecture/device-integration-runtime.md), [device contracts](../packages/device-contracts/README.md) |
| Work on media or voice | [OT media and voice architecture](architecture/ot-media-voice-runtime.md) | [Media contract](../packages/media-runtime/README.md), [voice contract](../packages/voice-runtime/README.md) |
| Work on surgical observation | [Surgery start page](surgery/START_HERE.md) | [Safety and human factors](surgery/03-human-factors-safety-and-governance.md) |
| Plan hardware verification | [Device validation plan](testing/device-validation-plan.md) | [HeyCyan compatibility evidence](protocols/heycyan-compatibility.md), [Android controller](../apps/android-controller/README.md) |
| Select an upstream reference | [Adoption map](research/reference-repositories/ADOPTION_MAP.md) | [Repository review](research/open-source-repository-review.md) |
| Contribute or publish | [Contribution guide](../CONTRIBUTING.md) | [Quality gates](../QUALITY.md), [security model](security/threat-model.md), [governance](../GOVERNANCE.md) |

## File and folder ownership

| Location | Purpose |
| --- | --- |
| `docs/product/`, `docs/surgery/` | Product scope, clinical research limits, safety and validation plans |
| `docs/architecture/`, `docs/protocols/`, `docs/decisions/` | System boundaries, device evidence and architecture decisions |
| `docs/research/` | Source reviews and the reference adoption register |
| `apps/`, `packages/`, `services/` | Controller code, shared contracts and service boundaries |
| `tools/`, `tests/`, `webapp/` | Runnable simulators, synthetic verification and local consoles |
| `third_party/` | Licensed reference records; snapshots are selected through the adoption map |
| `artifacts/device-captures/` | Local sensitive captures; never a place for committed patient data |
| `.ai/`, `AGENTS.md` | Task continuity and agent instructions |

Keep research notes with their owning workstream and contracts beside their
implementation. Preserve existing paths when linking evidence; do not unpack all
reference snapshots to find one source. Root legal and governance files remain
the common entry points for the whole repository.

## Evidence and release limits

[Project scope](00-project-overview.md), [compliance](../COMPLIANCE.md) and the
owning validation plans distinguish synthetic behavior from physical hardware
evidence. A successful simulator run does not establish SDK rights, real-device
reliability, clinical validation or release approval. License and third-party
provenance are recorded in [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
