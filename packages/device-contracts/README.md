# Device contracts

The Python contract is executable today for the simulator. Android mirrors the same names in Kotlin. Keep additions backward-compatible and capability-based.

Commands currently used:

- `device.connect`, `device.disconnect`
- `device.get_battery`, `device.get_version`
- `media.get_counts`, `media.transfer`
- `camera.take_photo`
- `camera.start_video`, `camera.stop_video`
- `audio.start_recording`, `audio.stop_recording`

Every result event carries the originating `command_id` when available. Drivers must make retries idempotent or return an explicit `unknown_result` event.

The simulator replays the original event for a duplicate `command_id`, so retry
behavior can be tested without creating duplicate media or state transitions.
