import shutil
import subprocess
import unittest
from pathlib import Path


class WebappUiTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "JavaScript tests require Node.js")
    def test_save_failure_and_reduced_motion(self):
        subprocess.run(["node", str(Path(__file__).with_name("webapp-ui.test.mjs"))], check=True)
