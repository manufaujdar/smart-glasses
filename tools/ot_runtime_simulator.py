#!/usr/bin/env python3
"""Run a deterministic end-to-end synthetic OT runtime sequence."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "media-runtime"))
sys.path.insert(0, str(ROOT / "packages" / "voice-runtime"))
sys.path.insert(0, str(ROOT / "services" / "ot-runtime"))

from media_runtime import FramePacket, ImageQualityAnalyzer, InMemoryFrameSink, LiveVideoSession  # noqa: E402
from ot_runtime import DeviceSnapshot, OTRuntime  # noqa: E402


def main() -> int:
    sink = InMemoryFrameSink()
    runtime = OTRuntime(LiveVideoSession(sink))
    runtime.begin_preflight("SYNTHETIC-OT-DEMO")
    runtime.confirm_consent(True)
    runtime.confirm_capture_indicator(True)
    runtime.arm(
        DeviceSnapshot(
            connected=True,
            battery_percent=90,
            capabilities={"camera.video", "audio.recording", "display.text"},
        )
    )
    runtime.accept_voice_text("start streaming")

    quality = ImageQualityAnalyzer().analyze(640, 360, [20, 80, 140, 220, 60, 180])
    runtime.ingest_frame(
        FramePacket(
            frame_id="synthetic-frame-1",
            sequence=1,
            captured_at_ms=1,
            width=640,
            height=360,
            codec="synthetic",
            payload=b"synthetic-frame",
            keyframe=True,
            quality=quality,
        )
    )
    runtime.publish_next()
    runtime.accept_voice_text("stop streaming")

    print(
        json.dumps(
            {
                "synthetic": True,
                "state": runtime.state.value,
                "published_frame_ids": [frame.frame_id for frame in sink.frames],
                "events": [asdict(event) for event in runtime.events],
            },
            indent=2,
            default=lambda value: value.value if hasattr(value, "value") else value,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
