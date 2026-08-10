# Smart AI glasses for surgeons

This folder is the human entry point for the surgeon-facing workstream within the
existing Smart Glasses Clinical Platform. It is intentionally not a separate
top-level project because it reuses the same device drivers, Android controller,
policy gateway, audit contracts and test infrastructure.

## Read in this order

1. `01-scope-and-non-goals.md`
2. `02-system-design.md`
3. `03-human-factors-safety-and-governance.md`
4. `04-functional-roadmap.md`
5. `05-validation-plan.md`
6. `../research/reference-repositories/ADOPTION_MAP.md`

## Runnable baseline

From the project root:

```bash
python3 -m unittest discover -s tests -v
python3 tools/surgical_session_simulator.py
```

The simulator uses synthetic session identifiers and staged events. It proves
workflow state and safety behavior only; it does not simulate clinical judgment.

## Current status

- Existing Smart Glasses folder reviewed; no duplicate folder was needed.
- Vendor-neutral device simulator: working.
- Synthetic surgical-session safety state machine: working.
- Android application shell: interface scaffold only.
- Physical glasses integration: requires the authorized vendor SDK and hardware.
- Clinical use: prohibited at this stage.

