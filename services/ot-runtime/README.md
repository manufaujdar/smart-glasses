# OT runtime

`OTRuntime` is a synthetic, fail-safe orchestrator for smart-glasses
observation and documentation workflows. It requires consent, a visible
capture indicator, a connected device, minimum battery, and declared camera,
audio, and display capabilities before streaming can start.

It accepts voice intents and video packets, records bounded non-sensitive
events, clears media on stop/disconnect, and does not control instruments,
navigate the room, diagnose, or select treatment.

`observe_device()` rechecks battery, connection, and capabilities during an
active session so health loss transitions to safe stop instead of waiting for
the next frame or command.
