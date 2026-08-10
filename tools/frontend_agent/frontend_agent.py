#!/usr/bin/env python3
"""Local-first agent for auditing the Smart Glasses simulator frontend.

The default workflow is deterministic and does not call an external model.
The ``prompt`` command prepares a bounded review brief for a human-selected
agent. It deliberately never uploads repository files or edits source code.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
WEBAPP_RELATIVE = Path("webapp")


@dataclass(frozen=True)
class Finding:
    severity: str
    area: str
    title: str
    detail: str
    next_action: str


@dataclass(frozen=True)
class AgentProfile:
    name: str
    kind: str
    strengths: tuple[str, ...]
    tradeoffs: tuple[str, ...]
    source: str


class _HtmlAuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.ids: set[str] = set()
        self.buttons = 0
        self.inputs = 0
        self.labels = 0
        self.images_without_alt = 0
        self.visible_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.add(str(attributes["id"]))
        if tag == "button":
            self.buttons += 1
        elif tag == "input":
            self.inputs += 1
        elif tag == "label":
            self.labels += 1
        elif tag == "img" and not attributes.get("alt"):
            self.images_without_alt += 1

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            self.visible_text.append(text)


AGENTS: tuple[AgentProfile, ...] = (
    AgentProfile(
        "Codex",
        "managed repo-aware coding agent",
        ("multi-file edits", "test and command loop", "repository instructions"),
        ("provider-managed", "not an open-source runtime"),
        "https://openai.com/index/introducing-codex/",
    ),
    AgentProfile(
        "Claude Code",
        "terminal coding agent",
        ("multi-file edits", "terminal workflow", "tests and repo context"),
        ("provider-managed", "requires its own account/installation"),
        "https://code.claude.com/docs/en/how-claude-code-works",
    ),
    AgentProfile(
        "Gemini CLI",
        "open-source terminal coding agent",
        ("terminal workflow", "open-source harness", "large-repo exploration"),
        ("model/API terms remain separate", "visual/browser loop needs setup"),
        "https://github.com/google-gemini/gemini-cli",
    ),
    AgentProfile(
        "OpenHands SDK",
        "open-source agent framework",
        ("composable agents", "provider flexibility", "local or hosted execution"),
        ("higher setup cost", "requires a deliberate sandbox/tool policy"),
        "https://docs.openhands.dev/sdk/index",
    ),
)


def _read_frontend(root: Path) -> dict[str, str]:
    directory = root / WEBAPP_RELATIVE
    files: dict[str, str] = {}
    for name in ("index.html", "method.html", "styles.css", "app.js", "README.md"):
        path = directory / name
        if path.exists():
            files[name] = path.read_text(encoding="utf-8")
    return files


def audit_frontend(root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    files = _read_frontend(root)
    html = files.get("index.html", "")
    css = files.get("styles.css", "")
    javascript = files.get("app.js", "")
    readme = files.get("README.md", "")
    parser = _HtmlAuditParser()
    parser.feed(html)
    findings: list[Finding] = []

    if '<meta name="viewport"' not in html:
        findings.append(Finding("high", "responsive", "Missing viewport metadata", "Mobile browsers may render the page at a desktop layout width.", "Add a responsive viewport meta tag."))
    if parser.images_without_alt:
        findings.append(Finding("medium", "accessibility", "Image alternative text is incomplete", f"{parser.images_without_alt} image element(s) lack alt text.", "Add meaningful alt text or mark decorative images explicitly."))
    if "@media" not in css:
        findings.append(Finding("medium", "responsive", "No responsive breakpoint found", "The layout has no CSS breakpoint for small screens.", "Add a mobile layout and test at 320px and 768px widths."))
    if "innerHTML" in javascript and "escapeHtml" not in javascript:
        findings.append(Finding("high", "security", "Dynamic HTML needs an escaping boundary", "The app renders dynamic values through innerHTML without an obvious escaping helper.", "Use textContent or escape every untrusted value before interpolation."))
    boundary_text = (html + readme).lower()
    if "does not control physical glasses" not in boundary_text and "physical device" not in boundary_text:
        findings.append(Finding("high", "truthfulness", "Physical-device boundary is under-documented", "Synthetic state-machine behavior could be mistaken for hardware validation.", "State that the console does not control or validate physical glasses."))
    if "localStorage" not in javascript:
        findings.append(Finding("medium", "workflow", "Persistence behavior is unclear", "The user may not know where numeric history is stored.", "Expose the active local persistence mode in the UI."))
    if len(parser.visible_text) > 90:
        findings.append(Finding("low", "clarity", "Visible copy may be too dense", f"The page contains {len(parser.visible_text)} visible text fragments.", "Move secondary explanation into a compact help/disclosure surface."))
    if parser.buttons > 12:
        findings.append(Finding("low", "interaction", "Action surface is crowded", f"The page contains {parser.buttons} buttons.", "Group primary, secondary, and destructive actions by workflow stage."))

    scores = {"clarity": 8, "interaction": 8, "accessibility": 8, "responsive": 8, "security": 8, "maintainability": 7}
    deductions = {"high": 3, "medium": 2, "low": 1}
    for finding in findings:
        if finding.area in scores:
            scores[finding.area] = max(0, scores[finding.area] - deductions[finding.severity])
    return {
        "tool": "smart-glasses-frontend-review-agent",
        "mode": "local_deterministic_audit",
        "root": str(root),
        "files_reviewed": sorted(files),
        "signals": {
            "buttons": parser.buttons,
            "inputs": parser.inputs,
            "labels": parser.labels,
            "visible_text_fragments": len(parser.visible_text),
            "ids": sorted(parser.ids),
        },
        "scores": scores,
        "findings": [asdict(finding) for finding in findings],
        "pending_for_real_measurement": [
            "authorized physical-device SDK and BLE/Wi-Fi validation",
            "camera, microphone, battery, thermal, and cleaning characterization",
            "representative speech, media, network, and human-factors validation",
            "privacy, security, clinical-safety, regulatory, and deployment approval",
        ],
        "external_model_calls": False,
    }


def compare_agents() -> dict[str, Any]:
    profiles = []
    for profile in AGENTS:
        executable = {
            "Codex": "codex",
            "Claude Code": "claude",
            "Gemini CLI": "gemini",
            "OpenHands SDK": "openhands",
        }[profile.name]
        profiles.append({**asdict(profile), "available_on_path": shutil.which(executable) is not None})
    return {
        "method": "capability matrix, not a model benchmark",
        "evaluation_rubric": [
            {"criterion": "product clarity", "weight": 15, "check": "A first-time user can run one synthetic command and understand the resulting state without reading the full page."},
            {"criterion": "visual craft", "weight": 20, "check": "Hierarchy, spacing, typography, and states feel intentional at mobile and desktop widths."},
            {"criterion": "human tone and brand", "weight": 10, "check": "Labels sound like a thoughtful product team wrote them; the brand mark, palette, and content hierarchy have a clear reason to exist."},
            {"criterion": "responsive accessibility", "weight": 15, "check": "Keyboard focus, labels, contrast, reduced copy, and 320/768/desktop layouts are usable."},
            {"criterion": "functional regression", "weight": 20, "check": "Command execution, state refresh, replay, local history, export, and method navigation remain functional."},
            {"criterion": "measurement truthfulness", "weight": 10, "check": "No physical-device, clinical benefit, diagnosis, treatment, or navigation claim is introduced."},
            {"criterion": "privacy and maintainability", "weight": 10, "check": "No patient data upload, secrets, unexplained dependencies, or unreviewed generated bulk rewrite."},
        ],
        "release_gates": [
            "no unsafe clinical claims",
            "no patient data or credentials leave the local workspace",
            "all regression tests pass",
            "human approves the final diff and screenshots",
        ],
        "selection_criteria": [
            "repo-aware multi-file editing",
            "browser/screenshot validation loop",
            "test execution and diff review",
            "local-first data boundary",
            "reproducible prompts and human approval before writes",
        ],
        "recommendation": {
            "first_candidate": "Codex or Claude Code for the supervised repo-edit loop",
            "open_source_candidate": "OpenHands SDK or Gemini CLI when a self-managed harness is required",
            "rule": "Run the same brief and score outputs against the rubric; do not select from marketing claims alone.",
        },
        "agents": profiles,
    }


def improvement_prompt(audit: dict[str, Any], comparison: dict[str, Any]) -> str:
    return f"""You are reviewing Fieldline, the local Smart Glasses synthetic device-state console.

Constraints:
- Do not claim physical-device validation, clinical benefit, diagnosis, treatment, navigation, or production readiness.
- Preserve the dependency-free browser app and loopback-only Python server unless a change is justified.
- Make the UI calm, accessible, responsive, and explicit about synthetic-versus-physical-device limitations.
- Make the content sound human and product-specific: avoid generic AI marketing language, inflated promises, decorative gradients, excessive pills, and equal-weight cards.
- Preserve the restrained field-of-view contour motif and use emphasis only for state, safety, and the primary action.
- Use healthcare-oriented open-source design references such as the CMS Design System, DHIS2 UI, Radix Colors, and Primer as principles, not copied code or assets.
- Prefer small composable modules over a framework migration.
- Do not add cloud uploads, patient identifiers, device captures, model weights, or secrets.
- Return a proposed patch plan first. Do not edit files until a human approves it.

Local audit:
{json.dumps(audit, indent=2, sort_keys=True)}

Agent comparison:
{json.dumps(comparison, indent=2, sort_keys=True)}

Deliver:
1. Three highest-impact frontend changes, including one voice or brand decision.
2. One accessibility improvement and one hardware/clinical-truthfulness check.
3. A browser validation checklist at 320px, 768px, and desktop widths.
4. A small patch plan naming exact files and tests.
5. Explicitly identify anything that remains simulated or clinically unvalidated.
"""


def _print(payload: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, dict) and "findings" in payload:
        print(f"{payload['tool']} · {payload['mode']}")
        print("Scores: " + ", ".join(f"{key}={value}/10" for key, value in payload["scores"].items()))
        for finding in payload["findings"]:
            print(f"- [{finding['severity']}] {finding['area']}: {finding['title']} — {finding['next_action']}")
        print("Pending: " + "; ".join(payload["pending_for_real_measurement"]))
        return
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit and prepare supervised frontend-agent work.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("audit", "compare", "prompt"):
        subparsers.add_parser(command).add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "audit":
        _print(audit_frontend(args.root), args.json)
    elif args.command == "compare":
        _print(compare_agents(), args.json)
    else:
        _print(improvement_prompt(audit_frontend(args.root), compare_agents()), False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
