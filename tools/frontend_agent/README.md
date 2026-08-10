# Depthline frontend improvement agent

This is a local-first, provider-neutral review agent for the Depthline webapp.
It is intentionally supervised: it audits the frontend, compares agent
capabilities, and prepares a bounded improvement brief. It does not call a
model, upload source code, edit files, or commit changes by default.

## Run

From the repository root:

```bash
python3 tools/frontend_agent/frontend_agent.py audit
python3 tools/frontend_agent/frontend_agent.py compare --json
python3 tools/frontend_agent/frontend_agent.py prompt > /tmp/depthline-frontend-brief.txt
```

The audit checks responsive metadata, accessibility signals, copy density,
dynamic HTML escaping, persistence disclosure, and camera truthfulness. The
agent comparison is a capability matrix, not a performance benchmark. Use the
same prompt, repository state, browser viewport checks, and regression tests for
any external agent candidate.

## Candidate comparison

- [Codex](https://openai.com/index/introducing-codex/) and
  [Claude Code](https://code.claude.com/docs/en/how-claude-code-works) are
  strong candidates for a supervised repository-edit and test loop, but are
  provider-managed.
- [Gemini CLI](https://github.com/google-gemini/gemini-cli) is an open-source
  terminal agent; the harness license does not determine model/API terms.
- [OpenHands SDK](https://docs.openhands.dev/sdk/index) is an open-source,
  composable agent framework with a higher setup and sandbox-policy cost.

No winner is hard-coded. A human should approve the patch plan and compare the
result against: visual simplicity, mobile usability, accessibility, no unsafe
measurement claims, no data exfiltration, passing tests, and clean diffs.

## Safety boundary

Never pass patient images, identifiers, credentials, or raw clinical captures to
an external agent. Keep source upload disabled unless the destination, data
handling, retention, and approval are explicit. The current camera workflow is
manual; this agent must not turn it into an automatic clinical claim.
