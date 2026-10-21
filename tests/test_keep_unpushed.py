"""scripts/keep-unpushed.sh keeps what a worker's cut-off run left unpushed on its own claim branch,
and nowhere else: never another worker's claim, never a branch that is no claim, never a file that
looks like a secret, and never by force."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "keep-unpushed.sh"
# git's background maintenance races a test's cleanup (symphony-template#63)
QUIET = ["-c", "gc.auto=0", "-c", "gc.autoDetach=false", "-c", "maintenance.auto=false",
         "-c", "maintenance.autoDetach=false", "-c", "receive.autogc=false"]
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.org", GIT_COMMITTER_NAME="t",
           GIT_COMMITTER_EMAIL="t@example.org", GIT_CONFIG_NOSYSTEM="1", HOME=tempfile.gettempdir())


def git(cwd, *args):
    return subprocess.run(["git", *QUIET, *args], cwd=cwd, env=ENV, capture_output=True, text=True, check=True).stdout


class KeepUnpushed(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.origin = base / "origin.git"
        git(base, "init", "-q", "--bare", "-b", "main", str(self.origin))
        for key in ("gc.auto=0", "receive.autogc=false", "maintenance.auto=false"):
            git(self.origin, "config", *key.split("="))
        self.work = base / "work"
        git(base, "clone", "-q", str(self.origin), str(self.work))
        git(self.work, "config", "gc.auto", "0")
        (self.work / "README.md").write_text("hello\n")
        git(self.work, "add", "-A")
        git(self.work, "commit", "-q", "-m", "start")
        git(self.work, "push", "-q", "origin", "HEAD:refs/heads/main")

    def tearDown(self):
        self.tmp.cleanup()

    def claim(self, issue, holder):
        git(self.work, "switch", "-q", "-c", f"claude/{issue}", "--no-track", "main")
        claims = self.work / "docs" / "agents" / "claims"
        claims.mkdir(parents=True, exist_ok=True)
        (claims / f"{issue}.md").write_text(f"# Claim\n\n- Worker: {holder}\n")
        git(self.work, "add", "-A")
        git(self.work, "commit", "-q", "-m", "claim")
        git(self.work, "push", "-q", "origin", f"claude/{issue}")

    def keep(self, worker="alpha"):
        env = dict(ENV, WORKER=worker, KEEP_TOOLS=str(ROOT / "tools"))
        proc = subprocess.run(["bash", str(SCRIPT)], cwd=self.work, env=env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    def on_origin(self, branch):
        return git(self.origin, "log", "--format=%s", branch).splitlines()

    def test_unpushed_work_is_kept_on_the_workers_own_claim(self):
        self.claim(7, "alpha")
        (self.work / "new.txt").write_text("half done\n")
        (self.work / "README.md").write_text("changed\n")
        out = self.keep()
        self.assertIn("kept 1 commit(s) on claude/7", out)
        self.assertEqual(self.on_origin("claude/7")[0], "Work in progress kept when the run ended before pushing it")
        self.assertEqual(git(self.origin, "show", "claude/7:new.txt"), "half done\n")

    def test_commits_made_but_not_pushed_are_pushed(self):
        self.claim(7, "alpha")
        (self.work / "a.txt").write_text("a\n")
        git(self.work, "add", "-A")
        git(self.work, "commit", "-q", "-m", "step one")
        self.assertIn("kept 1 commit(s)", self.keep())
        self.assertEqual(self.on_origin("claude/7")[0], "step one")

    def test_another_workers_claim_is_left_alone(self):
        self.claim(8, "beta")
        (self.work / "x.txt").write_text("x\n")
        self.assertIn("names beta, not alpha", self.keep())
        self.assertEqual(self.on_origin("claude/8"), ["claim", "start"])

    def test_a_branch_that_is_no_claim_is_left_alone(self):
        (self.work / "x.txt").write_text("x\n")
        self.assertIn("which is no claim", self.keep())
        for name in ("claude/07", "feature"):
            git(self.work, "switch", "-q", "-c", name)
            self.assertIn("which is no claim", self.keep())
        self.assertEqual(self.on_origin("main"), ["start"])

    def test_a_secret_shaped_file_keeps_nothing(self):
        self.claim(9, "alpha")
        (self.work / "notes.txt").write_text("token " + "gh" + "p_" + "A" * 36 + "\n")
        self.assertIn("looks like a secret", self.keep())
        self.assertEqual(self.on_origin("claude/9"), ["claim", "start"])
        self.assertTrue((self.work / "notes.txt").exists())

    def test_a_branch_that_moved_on_is_never_forced(self):
        self.claim(10, "alpha")
        other = Path(self.tmp.name) / "other"
        git(Path(self.tmp.name), "clone", "-q", "-b", "claude/10", str(self.origin), str(other))
        (other / "b.txt").write_text("b\n")
        git(other, "add", "-A")
        git(other, "commit", "-q", "-m", "pushed elsewhere")
        git(other, "push", "-q", "origin", "claude/10")
        (self.work / "c.txt").write_text("c\n")
        self.assertIn("nothing forced", self.keep())
        self.assertEqual(self.on_origin("claude/10")[0], "pushed elsewhere")


if __name__ == "__main__":
    unittest.main()
