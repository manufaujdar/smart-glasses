# Contributing

Contributions are welcome as research software improvements, subject to review
by the project owner.

Before opening a pull request:

1. Run `python3 -m unittest discover -s tests -v` from the `Smart Glasses`
   project root.
2. Keep LiDAR/vendor SDK calls behind an adapter; do not add proprietary
   binaries.
3. Use synthetic fixtures or de-identified, explicitly approved research data.
   Never commit patient identifiers, clinical captures, or credentials.
4. Preserve the distinction between geometric trajectory signals and clinical
   healing, diagnosis, prognosis, or treatment decisions.
5. Add provenance and license notes for any third-party code, data, model, or
   documentation introduced.

Contributors should confirm they have the right to submit their work under the
Apache-2.0 license candidate. This project does not currently require a CLA or
DCO, but contributors remain responsible for their own copyright permissions.
