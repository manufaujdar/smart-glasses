import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "media-runtime"))

from media_runtime import (  # noqa: E402
    BoundedFrameBuffer,
    DropPolicy,
    FramePacket,
    ImageQualityAnalyzer,
    InMemoryFrameSink,
    LatencyController,
    LiveVideoSession,
)


def make_frame(frame_id, *, keyframe=False, quality=None):
    return FramePacket(
        frame_id=frame_id,
        sequence=int(frame_id.split("-")[-1]),
        captured_at_ms=1,
        width=640,
        height=360,
        codec="synthetic",
        payload=b"synthetic-frame",
        keyframe=keyframe,
        quality=quality,
    )


class MediaRuntimeTests(unittest.TestCase):
    def test_quality_analyzer_flags_clipping_and_empty_samples(self):
        analyzer = ImageQualityAnalyzer()
        report = analyzer.analyze(320, 240, [0, 0, 0, 255, 255])
        self.assertIn("low_resolution", report.reasons)
        self.assertIn("underexposed", report.reasons)
        self.assertIn("overexposed", report.reasons)
        with self.assertRaises(ValueError):
            analyzer.analyze(640, 360, [])

    def test_bounded_queue_drops_oldest_to_keep_latency_bounded(self):
        queue = BoundedFrameBuffer(max_frames=2)
        queue.push(make_frame("frame-1"))
        queue.push(make_frame("frame-2"))
        result = queue.push(make_frame("frame-3"))
        self.assertEqual(result.dropped_frame_id, "frame-1")
        self.assertEqual(queue.pop().frame_id, "frame-2")
        self.assertEqual(queue.pop().frame_id, "frame-3")

    def test_keyframe_policy_rejects_non_keyframe_when_all_slots_are_keyframes(self):
        queue = BoundedFrameBuffer(max_frames=2, drop_policy=DropPolicy.DROP_NON_KEYFRAME)
        queue.push(make_frame("frame-1", keyframe=True))
        queue.push(make_frame("frame-2", keyframe=True))
        result = queue.push(make_frame("frame-3"))
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "queue_full_keyframes")

    def test_video_session_rejects_bad_quality_and_publishes_good_frames(self):
        analyzer = ImageQualityAnalyzer()
        good = analyzer.analyze(640, 360, [20, 80, 140, 220, 60, 180])
        bad = analyzer.analyze(640, 360, [0, 0, 0, 0, 0])
        sink = InMemoryFrameSink()
        session = LiveVideoSession(sink)
        self.assertFalse(session.ingest(make_frame("frame-1", quality=bad)).accepted)
        self.assertTrue(session.ingest(make_frame("frame-2", quality=good)).accepted)
        self.assertEqual(session.publish_next().frame_id, "frame-2")
        self.assertEqual(session.stats.rejected_quality, 1)
        self.assertEqual(session.stats.published_frames, 1)

    def test_video_session_rejects_stale_sequences_and_oversized_payloads(self):
        session = LiveVideoSession(InMemoryFrameSink())
        session.ingest(make_frame("frame-2"))
        stale = make_frame("frame-1")
        self.assertFalse(session.ingest(stale).accepted)
        self.assertEqual(session.stats.rejected_stale, 1)
        with self.assertRaises(ValueError):
            FramePacket("huge", 3, 1, 640, 360, "synthetic", b"x" * (8 * 1024 * 1024 + 1))

    def test_latency_controller_reduces_profile_under_transport_pressure(self):
        controller = LatencyController()
        decision = controller.choose(
            queue_depth=3, rtt_ms=300, dropped_frames=2, source_quality=0.9
        )
        self.assertEqual(decision.profile.name, "low-latency")
        self.assertEqual(decision.reason, "transport_pressure")


if __name__ == "__main__":
    unittest.main()
