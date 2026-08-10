# Contributing

Smart Glasses is a healthcare research prototype. Contributions must preserve
vendor-neutral contracts, safe-state behavior, synthetic fixtures, and the
boundary against diagnosis, treatment, navigation, or patient-data handling.

Before opening a pull request:

```bash
python3 -m unittest discover -s tests -v
```

Do not add proprietary SDK binaries, device captures, patient context, or
unlicensed third-party code. Protocol changes need evidence and a focused state
transition test.
