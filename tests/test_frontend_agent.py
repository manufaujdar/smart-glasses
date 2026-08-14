import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "frontend_agent"))

from frontend_agent import audit_frontend, compare_agents, improvement_prompt  # noqa: E402


class FrontendAgentTests(unittest.TestCase):
    def test_local_audit_is_deterministic_and_sees_fieldline(self):
        report = audit_frontend(ROOT)
        self.assertEqual(report["mode"], "local_deterministic_audit")
        self.assertIn("index.html", report["files_reviewed"])
        self.assertIn("app.js", report["files_reviewed"])
        self.assertFalse(report["external_model_calls"])
        self.assertEqual(report["tool"], "smart-glasses-frontend-review-agent")
        self.assertIn("physical-device SDK", " ".join(report["pending_for_real_measurement"]))

    def test_agent_matrix_has_supervised_selection_criteria(self):
        comparison = compare_agents()
        self.assertIn("Codex", {agent["name"] for agent in comparison["agents"]})
        self.assertIn("local-first data boundary", comparison["selection_criteria"])
        self.assertIn("capability matrix", comparison["method"])
        self.assertEqual(sum(item["weight"] for item in comparison["evaluation_rubric"]), 100)

    def test_prompt_contains_audit_and_safety_constraints(self):
        prompt = improvement_prompt(audit_frontend(ROOT), compare_agents())
        self.assertIn("Do not claim physical-device validation", prompt)
        self.assertIn("proposed patch plan", prompt)
        self.assertIn("Fieldline", prompt)
        json.dumps(prompt)


if __name__ == "__main__":
    unittest.main()
