## Summary

Describe the scoped change and why it is needed.

## Boundary and evidence

- [ ] Research-only language and prohibited clinical uses remain explicit.
- [ ] No patient data, raw captures, credentials, proprietary binaries, or unverified weights are included.
- [ ] Vendor/protocol claims include provenance or reproducible evidence.
- [ ] New dependencies, models, data, and reference code have license/provenance review.
- [ ] Anything simulated, hardware-gated, or clinically unvalidated is identified.

## Verification

- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `python3 -m compileall -q apps packages services tools tests`
- [ ] JavaScript syntax checks for changed browser code
- [ ] `python3 tools/frontend_agent/frontend_agent.py audit`
- [ ] Relevant simulator, device, failure-state, or UI checks

## Risk and rollback

Describe safety, privacy, security, compatibility, and rollback implications.
