import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "media-runtime"))
sys.path.insert(0, str(ROOT / "packages" / "voice-runtime"))
sys.path.insert(0, str(ROOT / "services" / "ot-runtime"))

from media_runtime import FramePacket, ImageQualityAnalyzer, InMemoryFrameSink, LiveVideoSession  # noqa: E402
from ot_runtime import DeviceSnapshot, OTRuntime, OTRuntimeState  # noqa: E402
from voice_runtime import SyntheticTranscriber  # noqa: E402


class OTRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.sink = InMemoryFrameSink()
        self.runtime = OTRuntime(LiveVideoSession(self.sink))
        self.runtime.begin_preflight("SYNTHETIC-OT-001")
        self.runtime.confirm_consent(True)
        self.runtime.confirm_capture_indicator(True)

    def arm_runtime(self):
        return self.runtime.arm(
            DeviceSnapshot(
                connected=True,
                battery_percent=90,
                capabilities={"camera.video", "audio.recording", "display.text"},
            )
        )

    def test_preflight_and_voice_start_streaming(self):
        self.assertEqual(self.arm_runtime().name, "ot.ready")
        self.runtime.accept_voice_text("start streaming")
        self.assertEqual(self.runtime.state, OTRuntimeState.STREAMING)
        self.assertEqual(self.runtime.events[-1].name, "video.streaming_started")

    def test_missing_capability_enters_safe_stop(self):
        event = self.runtime.arm(
            DeviceSnapshot(connected=True, battery_percent=90, capabilities={"camera.video"})
        )
        self.assertEqual(event.name, "ot.safe_stop")
        self.assertEqual(self.runtime.state, OTRuntimeState.SAFE_STOP)

    def test_low_quality_frame_is_rejected_without_publishing(self):
        self.arm_runtime()
        self.runtime.start_streaming()
        bad_quality = ImageQualityAnalyzer().analyze(640, 360, [0, 0, 0, 0])
        result = self.runtime.ingest_frame(
            FramePacket("frame-1", 1, 1, 640, 360, "synthetic", b"frame", quality=bad_quality)
        )
        self.assertFalse(result.accepted)
        self.assertIsNone(self.runtime.publish_next())
        self.assertEqual(self.sink.frames, [])

    def test_disconnect_clears_media_and_enters_safe_stop(self):
        self.arm_runtime()
        self.runtime.accept_voice_text("start streaming")
        self.runtime.disconnect()
        self.assertEqual(self.runtime.state, OTRuntimeState.SAFE_STOP)
        self.assertEqual(self.runtime.video_session.stats.queue_depth, 0)
        self.assertEqual(self.runtime.events[-1].name, "ot.safe_stop")

    def test_live_device_health_loss_safe_stops_active_stream(self):
        self.arm_runtime()
        self.runtime.start_streaming()
        event = self.runtime.observe_device(
            DeviceSnapshot(
                connected=True,
                battery_percent=20,
                capabilities={"camera.video", "audio.recording", "display.text"},
            )
        )
        self.assertEqual(event.name, "ot.safe_stop")
        self.assertEqual(self.runtime.state, OTRuntimeState.SAFE_STOP)

    def test_narration_does_not_repeat_allowlisted_commands(self):
        self.arm_runtime()
        self.runtime.narration.active = True
        transcriber = SyntheticTranscriber()
        self.runtime.accept_transcript(transcriber.submit_text("start streaming"))
        self.assertEqual(self.runtime.narration.read(), "")
        self.assertEqual(self.runtime.state, OTRuntimeState.STREAMING)

    def test_capture_voice_command_requires_confirmation(self):
        self.arm_runtime()
        intent = self.runtime.accept_voice_text("capture photo")
        self.assertTrue(intent.requires_confirmation)
        self.assertNotIn("capture.requested", [event.name for event in self.runtime.events])
        self.runtime.accept_voice_text("capture photo", confirmed=True)
        self.assertEqual(self.runtime.events[-1].name, "capture.requested")


if __name__ == "__main__":
    unittest.main()
