import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("quality", Path(__file__).resolve().parents[1] / "quality.py")
quality = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quality)
HEAD = "a" * 40
BASE = "b" * 40


class RangeTests(unittest.TestCase):
    def test_missing_base_fails_instead_of_scanning_only_last_commit(self):
        with patch.object(quality, "git", return_value=HEAD), self.assertRaisesRegex(ValueError, "Missing base"):
            quality.history_range(None, HEAD)

    def test_explicit_initial_push_scans_all_reachable_history(self):
        with patch.object(quality, "git", return_value=HEAD):
            self.assertEqual(quality.history_range("0" * 40, HEAD), HEAD)

    def test_outgoing_range_keeps_all_merge_ancestors(self):
        with patch.object(quality, "git", side_effect=[HEAD, BASE]), patch.object(quality.subprocess, "run") as run:
            self.assertEqual(quality.history_range(BASE, HEAD), BASE + ".." + HEAD)
            self.assertEqual(run.call_args.args[0], ["git", "merge-base", "--is-ancestor", BASE, HEAD])

    def test_non_fast_forward_fails(self):
        with patch.object(quality, "git", side_effect=[HEAD, BASE]), patch.object(
            quality.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "git")
        ), self.assertRaises(subprocess.CalledProcessError):
            quality.history_range(BASE, HEAD)

    def test_untrusted_ref_is_rejected_before_git(self):
        with self.assertRaises(ValueError):
            quality.revision("--all")

    def test_mismatched_checkout_fails_before_tools_run(self):
        with patch.object(quality, "revision", return_value=HEAD), patch.object(
            quality, "git", return_value=BASE
        ), patch.object(quality, "run") as run:
            with self.assertRaisesRegex(ValueError, "Checkout HEAD"):
                quality.check("push", BASE, HEAD, False)
            run.assert_not_called()


    def test_dirty_worktree_fails_before_scanners(self):
        with patch.object(quality, "revision", return_value=HEAD), patch.object(
            quality, "git", return_value=HEAD
        ), patch.object(quality, "run", side_effect=subprocess.CalledProcessError(1, "git")) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                quality.check("push", BASE, HEAD, False)
            self.assertEqual(run.call_args.args[0], ["git", "diff", "--quiet", "HEAD", "--"])

    def test_dirty_index_fails_before_scanners(self):
        with patch.object(quality, "revision", return_value=HEAD), patch.object(
            quality, "git", return_value=HEAD
        ), patch.object(quality, "run", side_effect=[None, subprocess.CalledProcessError(1, "git")]) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                quality.check("push", BASE, HEAD, False)
            self.assertEqual(run.call_args.args[0], ["git", "diff", "--cached", "--quiet"])

    def test_non_main_outgoing_ref_fails_before_scanners(self):
        with patch.object(quality, "revision", return_value=HEAD), patch.object(
            quality, "git", return_value=HEAD
        ), patch.object(quality, "run") as run, patch.dict(
            quality.os.environ, {"PRE_COMMIT_REMOTE_BRANCH": "refs/heads/topic"}
        ):
            with self.assertRaisesRegex(ValueError, "main only"):
                quality.check("push", BASE, HEAD, False)
            self.assertEqual(run.call_count, 2)

if __name__ == "__main__":
    unittest.main()
