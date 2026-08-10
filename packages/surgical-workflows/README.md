# Surgical workflow contracts

`surgical_session.py` is a deterministic, dependency-free research state machine.
It models preflight gates and safe session behavior using synthetic identifiers.

It intentionally contains no patient model, diagnosis, anatomy, navigation or AI
recommendation logic. Android and gateway implementations should reproduce this
behavior through contract tests rather than importing Python into production.

