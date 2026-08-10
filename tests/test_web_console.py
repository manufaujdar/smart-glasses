import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from web_console import (
    APP_JS,
    CONSOLE_HTML,
    METHOD_HTML,
    STYLES_CSS,
    current_state,
    execute_command,
    reset_simulator,
)  # noqa: E402


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

    def test_console_has_accessible_responsive_local_workflow(self) -> None:
        self.assertIn('name="viewport"', CONSOLE_HTML)
        self.assertIn('class="skip-link"', CONSOLE_HTML)
        self.assertIn('aria-live="polite"', CONSOLE_HTML)
        self.assertIn("@media(max-width:760px)", STYLES_CSS)
        self.assertIn("localStorage", APP_JS)
        self.assertIn("Copy Markdown brief", CONSOLE_HTML)

    def test_method_page_and_state_are_available(self) -> None:
        self.assertIn("What the simulator proves", METHOD_HTML)
        self.assertTrue(current_state()["synthetic"])


if __name__ == "__main__": unittest.main()
