"""Repository-local gates; no model calls, auto-fixes, deployment or credential validation."""
import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / ".quality/config.json").read_text())


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def run(args, cwd=ROOT):
    print("+ " + " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, check=True)


def executable(name):
    local = ROOT / ".quality/bin" / name
    package = ROOT / ".quality/node_modules/.bin" / name
    shared = Path.home() / ".local/share/manu-quality-tools/node_modules/.bin" / name
    for path in (local, package, shared):
        if path.is_file():
            return str(path)
    found = shutil.which(name)
    if not found:
        raise ValueError(f"Missing {name}; see QUALITY.md. Checks cannot be skipped.")
    return found


def revision(value):
    if not re.fullmatch(r"[0-9a-f]{40}", value or ""):
        raise ValueError("Revision must be a full Git commit SHA.")
    return git("rev-parse", "--verify", value + "^{commit}")


def history_range(base, head):
    head = revision(head)
    if base == "0" * 40:
        return head  # Explicit first push: scan every reachable ancestor.
    if not base:
        raise ValueError("Missing base; pass --base or an explicit zero SHA for initial history.")
    base = revision(base)
    subprocess.run(["git", "merge-base", "--is-ancestor", base, head], cwd=ROOT, check=True)
    return base + ".." + head


def paths(base, head, staged):
    if staged:
        args = ["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"]
    elif base == "0" * 40:
        args = ["ls-tree", "-r", "--name-only", "-z", head]
    else:
        args = ["diff", "--name-only", "--diff-filter=ACMR", "-z", base, head]
    raw = subprocess.check_output(["git", *args], cwd=ROOT)
    return [os.fsdecode(p) for p in raw.split(b"\0") if p and (ROOT / os.fsdecode(p)).is_file()]


def check(mode, base, head, native):
    staged = mode == "staged"
    if not staged:
        head = revision(head)
        if head != git("rev-parse", "HEAD"):
            raise ValueError("Checkout HEAD must equal the outgoing/tested commit.")
        run(["git", "diff", "--quiet", "HEAD", "--"])
        run(["git", "diff", "--cached", "--quiet"])
        if mode == "push":
            target = os.environ.get("PRE_COMMIT_REMOTE_BRANCH", "refs/heads/main")
            if target != "refs/heads/main":
                raise ValueError("This project publishes main only.")
        log_range = history_range(base, head)
        print(f"Testing committed SHA {head}; history {log_range}", flush=True)
    changed = paths(base, head, staged)
    run(["git", "diff", "--cached", "--check"] if staged else
        ["git", "diff", "--check", base, head] if base != "0" * 40 else
        ["git", "show", "--format=", "--check", head])
    scanner = [executable("betterleaks"), "git", "--redact", "--no-banner",
               "--no-color", "--timeout", "120", "--ignore-gitleaks-allow"]
    run(scanner + (["--pre-commit", "--staged"] if staged else ["--log-opts", log_range]))
    py = [p for p in changed if p.endswith(".py")]
    if py:
        run([executable("ruff"), "check", "--no-cache", *py])
    if any(p.startswith(".github/") and p.endswith((".yml", ".yaml")) for p in changed):
        workflows = sorted(str(p.relative_to(ROOT)) for p in (ROOT / ".github/workflows").glob("*.y*ml"))
        run([executable("actionlint"), *workflows])
        run([executable("zizmor"), "--offline", "--no-ignores", "--format", "plain", *workflows])
    docs = [p for p in changed if any(fnmatch.fnmatch(p, g) for g in CONFIG["engineering_docs"])]
    if docs:
        run([executable("markdownlint"), "--config", ".quality/markdownlint.jsonc", *docs])
        run([executable("lychee"), "--offline", "--no-progress", "--include-fragments",
             "--root-dir", str(ROOT), *docs])
    if not staged:
        run([sys.executable, "-m", "unittest", "discover", "-s", "tools", "-p", "test_tooling_templates.py", "-v"])
        for task in CONFIG["dependencies"]:
            args = [executable(task["tool"]), *task["args"]]
            run(args, ROOT / task.get("cwd", "."))
        run([sys.executable, "-m", "unittest", "discover", "-s", "tools/quality_tests", "-v"])
        for task in CONFIG["browser"]:
            run(task["args"], ROOT / task.get("cwd", "."))
    if native:
        for task in CONFIG["native"]:
            run(task["args"], ROOT / task.get("cwd", "."))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["staged", "push", "ci"], required=True)
    parser.add_argument("--base", default=os.environ.get("PRE_COMMIT_FROM_REF") or os.environ.get("QUALITY_BASE"))
    parser.add_argument("--head", default=os.environ.get("PRE_COMMIT_TO_REF") or git("rev-parse", "HEAD"))
    parser.add_argument("--native", action="store_true")
    args = parser.parse_args()
    try:
        check(args.mode, args.base, args.head, args.native or args.mode == "push")
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f"Quality gate failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
