import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "voice-runtime"))

from voice_runtime import (  # noqa: E402
    NarrationBuffer,
    SyntheticTranscriber,
    TranscriptKind,
    VoiceAction,
    VoiceCommandGuard,
    VoiceCommandParser,
)


class VoiceRuntimeTests(unittest.TestCase):
    def test_synthetic_transcriber_emits_partial_and_final_events(self):
        transcriber = SyntheticTranscriber()
        partial = transcriber.submit_text("start stream", final=False)
        final = transcriber.submit_text("start streaming", final=True)
        self.assertEqual(partial.kind, TranscriptKind.PARTIAL)
        self.assertEqual(final.kind, TranscriptKind.FINAL)
        self.assertGreater(final.sequence, partial.sequence)

    def test_parser_only_accepts_allowlisted_commands(self):
        parser = VoiceCommandParser()
        self.assertEqual(parser.parse(" Start Live Video! ").action, VoiceAction.START_STREAMING)
        self.assertEqual(parser.parse("do something unsafe").action, VoiceAction.UNKNOWN)

    def test_low_confidence_command_is_rejected(self):
        intent = VoiceCommandParser().parse("stop streaming", confidence=0.4)
        self.assertEqual(intent.action, VoiceAction.UNKNOWN)
        self.assertEqual(intent.reason, "low_confidence")

    def test_capture_requires_confirmation_and_narration_is_bounded(self):
        parser = VoiceCommandParser()
        self.assertTrue(parser.parse("capture photo").requires_confirmation)
        buffer = NarrationBuffer(max_chars=100)
        buffer.active = True
        transcriber = SyntheticTranscriber()
        self.assertTrue(buffer.append(transcriber.submit_text("hello team")))
        self.assertEqual(buffer.consume(), "hello team")
        self.assertEqual(buffer.consume(), "")

    def test_voice_guard_rejects_duplicate_and_stale_intents(self):
        parser = VoiceCommandParser()
        guard = VoiceCommandGuard(cooldown_ms=1000)
        intent = parser.parse("start streaming")
        self.assertTrue(guard.evaluate(intent, 100).accepted)
        self.assertEqual(guard.evaluate(intent, 500).reason, "duplicate_within_cooldown")
        self.assertEqual(guard.evaluate(parser.parse("stop streaming"), 50).reason, "stale_transcript")


if __name__ == "__main__":
    unittest.main()
