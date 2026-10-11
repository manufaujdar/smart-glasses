# Repository quality gates

Publish this project's authorized changes to main only. Use a clean integration
checkout; preserve unrelated work. A passing local gate identifies the exact
outgoing SHA, then main-push CI verifies the received commit. Neither gate
deploys, creates a PR, calls a model or approves a device/clinical/store release.

## Local setup

Use Python 3.10+ and Node 24. Install the pinned system tools and the existing
project dependencies, then install the small development-only QA package:

```sh
npm ci --prefix .quality
pre-commit install --hook-type pre-commit --hook-type pre-push
git config --local rerere.enabled true
git config --local rerere.autoupdate false
```

pre-commit must be 4.6.2 or later. Its normal install preserves existing hooks;
do not use overwrite, alter a configured hooksPath or disable a failing hook.
The original checkout can reuse this configuration after it has been integrated
without discarding that checkout's local changes.

Required local versions: Betterleaks 1.8.1, Ruff 0.16.9, actionlint 1.7.12,
zizmor 1.30.1, lychee 0.24.2 and markdownlint-cli 0.49.1. The runner finds native
binaries on PATH and the locked Markdown binary in .quality/node_modules/.bin.
The shared workstation Markdown install is also supported. Node audit checks the
QA lockfile, including the explicit patched transitive overrides.

The QA folder pins Playwright 1.64.0 and axe 4.13.0. Install its Chromium browser:

```sh
./.quality/node_modules/.bin/playwright install chromium
```

## What runs

Staged checks scan the Git index for secrets with complete redaction and no
credential validation, check changed Python, workflow configuration and selected
engineering Markdown. No formatter edits files.

Pre-push requires the checked-out committed SHA to match the outgoing ref and
the tracked tree to be clean. It accepts main only, rejects non-fast-forward
integration, scans all outgoing commit ancestry, runs native tests and synthetic
browser QA, and audits the declared dependency scope. Missing tools or missing
base commits fail the gate. An explicit zero base means an initial push and
scans all reachable history, rather than only the last commit.

Main CI uses the push event's previous SHA with full Git history. Workflow actions
are pinned; [the binary installer](tools/install_ci_tools.py) checks SHA-256 before
extracting only the expected executables. Native tests remain in the existing CI.
The quality job adds outgoing-history secrets, workflow audits, QA-tool dependency
checks, changed engineering docs, guard regressions and browser checks.

Engineering Markdown scope is explicit in [.quality/config.json](.quality/config.json).
It includes this guide, contribution guidance, webapp instructions, architecture,
testing and release docs changed by a push. Historical research/AI logs and
generated outputs are not automatically rewritten or presented as audited.
Markdown style and offline local links/anchors must pass for the selected files.
External links are not contacted by this gate.

Install the existing pinned integration requirements in the project environment before a full
integration test. pip-audit checks those direct pinned requirements without installing
SDKs/models or resolving an ML stack. The test output exposes any optional local skips. Physical
glasses, vendor SDK and clinical gates remain separate.

Public-repository CodeQL analyzes Python and JavaScript on main pushes. Its findings
still need triage and do not certify research, clinical or physical-device use.

## Conflict and review handling

rerere may reuse an earlier resolution, but autoupdate remains false: inspect the
diff and stage only a verified resolution. Git merge-tree can preview integration
without touching the working tree/index. Resolve against callers and tests;
never apply a generic accept-ours/accept-theirs policy. If remote main advances,
reintegrate and retest affected behavior; never force or bypass branch rules.

CodeRabbit is an optional manual advisory step. This command only prepares a
scope, without uploading source or calling a reviewer:

```sh
python3 tools/coderabbit_review.py --base FULL_PREVIOUS_MAIN_SHA
```

The manual CodeRabbit scope workflow does the same. External review requires a
separate explicit --execute invocation, authenticated CLI, agreed source scope
and usable capacity. It is never part of push CI. The adapter distinguishes
completed, skipped and incomplete results; success/skipped bot statuses do not
prove an actual review. Findings still need owner judgment and relevant tests.
Keep captures, identifiers, user data, credentials and proprietary material out
of any external review. No billing or Autofix option is enabled here.

## Tool provenance and limits

- Git: GPL-2.0 core; existing native conflict tools.
- pre-commit, Ruff, Betterleaks, actionlint, zizmor, markdownlint: MIT.
- lychee: Apache-2.0 OR MIT; checks are offline.
- Playwright: Apache-2.0; axe: MPL-2.0. Both are QA-only dependencies.
- pip-audit: Apache-2.0; only declared package metadata goes to advisory services.

Tool versions are explicit in the installer, CI and npm lockfiles. No upstream
application code was copied into the product. Automated accessibility checks
cover synthetic rendered states and do not replace screen-reader, representative
touch/device, privacy, clinical or native release evidence.
