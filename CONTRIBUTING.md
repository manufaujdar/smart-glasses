# Contributing

Smart Glasses is a healthcare research prototype. Contributions must preserve
vendor-neutral contracts, safe-state behavior, synthetic fixtures, and the
boundary against diagnosis, treatment, navigation, or patient-data handling.

Before opening a pull request:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q apps packages services tools tests
node --check webapp/app.js
python3 tools/frontend_agent/frontend_agent.py audit
```

Do not add proprietary SDK binaries, device captures, patient context,
credentials, unverified model weights, or unlicensed third-party code. Protocol
changes need evidence and a focused state-transition test. Add provenance and
license notes for every new code, data, model, SDK, or reference source.

Contributors confirm they have the right to submit their work under Apache-2.0.
This project does not currently require a CLA or DCO, but contributors remain
responsible for their own copyright permissions.
