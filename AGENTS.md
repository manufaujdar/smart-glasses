# Smart Glasses agent guide

Read `START_HERE.txt`, `.ai/CONTEXT.md`, `.ai/MEMORY.md`, `README.md`, `docs/00-project-overview.md`, the relevant architecture/protocol document, and related tests before editing.

For surgeon-facing work, begin with `docs/surgery/START_HERE.md`. Use
`docs/research/reference-repositories/ADOPTION_MAP.md` to select an upstream
reference. Do not unpack or scan every archive under
`third_party/reference-repositories/snapshots/`; inspect only the one needed for
the current task.

- This is a research prototype, not a clinical device. Do not claim diagnostic, treatment, navigation, or production readiness.
- Keep vendor-specific behavior behind the device adapter and preserve vendor-neutral contracts.
- Treat recordings, device captures, identifiers, and clinical context as sensitive. Use synthetic fixtures and keep captures out of Git.
- Preserve safe-state behavior for disconnects, capability mismatches, interrupted transfers, and unsupported commands.
- Do not add proprietary SDK binaries or copied third-party code without license and provenance review.
- Protocol claims should cite captured evidence or authoritative vendor documentation and state uncertainty.

Validate simulator changes with `python3 -m unittest discover -s tests -v`; add focused state-transition tests for new behavior.

Use `.ai/HANDOFF.md` only for active-task continuity. Never put device captures, patient context, identifiers, or proprietary material in AI memory.

## Project skills

- Use `$smart-glasses-analyze-protocol` for protocol evidence, adapter contracts,
  capability negotiation, device states, media transfer, or a new hardware target.
- Use `$smart-glasses-safety-review` for an independent, report-only review of
  surgeon-facing, capture, telepresence, cloud/AI, gateway, or release workflows.

Protocol implementation and safety approval must remain separate responsibilities.

## Startup team

Read `.ai/TEAM.md` before multi-role or idea-to-release work. Use its explicit
gears and keep the task contract in `.ai/HANDOFF.md`; clinical, privacy,
protocol, licensing, and validation boundaries remain authoritative.
