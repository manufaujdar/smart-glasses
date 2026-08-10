import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from web_console import CONSOLE_HTML, execute_command, reset_simulator  # noqa: E402


class WebConsoleTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_simulator()

    def test_console_executes_and_replays_a_synthetic_command(self) -> None:
        first = execute_command("device.connect", "same-command")
        replay = execute_command("device.connect", "same-command")
        self.assertEqual(first, replay)
        self.assertEqual(first["name"], "device.connected")

    def test_console_rejects_unknown_commands(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported"):
            execute_command("clinical.navigate", "unsafe")

    def test_console_states_research_boundary(self) -> None:
        self.assertIn("not a medical device", CONSOLE_HTML)


if __name__ == "__main__": unittest.main()
