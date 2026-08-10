# Device contracts

The Python contract is executable today for the simulator. Android mirrors the same names in Kotlin. Keep additions backward-compatible and capability-based.

Commands currently used:

- `device.connect`, `device.disconnect`
- `device.get_battery`, `device.get_version`
- `media.get_counts`, `media.transfer`
- `media.list`
- `camera.take_photo`
- `camera.open_preview`, `camera.close_preview`
- `camera.start_video`, `camera.stop_video`
- `audio.start_recording`, `audio.stop_recording`
- `stream.start`, `stream.stop`

Every result event carries the originating `command_id` when available. Drivers must make retries idempotent or return an explicit `unknown_result` event.

The simulator replays the original event for a duplicate `command_id`, so retry
behavior can be tested without creating duplicate media or state transitions.

`camera.preview` and `stream.live` are negotiated capabilities. HeyCyan public
SDK material does not establish a continuous live-preview/streaming contract, so
those commands must remain unavailable in that adapter until licensed SDK and
physical-device evidence confirms them. A browser/phone preview is a separate
source and must never be labeled as a glasses camera feed.
