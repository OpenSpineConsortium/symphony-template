"""tools/overlap.py: every open pull request is judged against the default
branch as it now stands and gets the check run named overlap on its head,
with the conclusion the switch and the tool's answer give; off writes
nothing, and a head that moved since the list was read is left to its own
run. GitHub and git are fakes here; the judgement itself is the library's
(symphony-protocol's tests.test_git_locks)."""

import io
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import overlap  # noqa: E402

MEETING = ("locks: origin/main edited m.py#f since this change's base, which this change builds on: "
           "bring origin/main in\n")
NOTHING = "locks: nothing origin/main changed since the base meets this change; it need not bring it in\n"


class FakeGitHub:
    def __init__(self, pulls):
        self.pulls = pulls
        self.posted = []

    def __call__(self, method, path, payload=None):
        if method == "GET":
            page = int(path.rsplit("page=", 1)[1])
            start = (page - 1) * overlap.PAGE
            return [{"number": n, "head": {"sha": sha}} for n, sha in self.pulls[start:start + overlap.PAGE]]
        self.posted.append((path, payload))
        return {"id": len(self.posted)}


class Conclusions(unittest.TestCase):
    def test_the_tool_s_answer_gives_the_conclusion(self):
        self.assertEqual(overlap.conclusion_of(0, NOTHING), "success")
        self.assertEqual(overlap.conclusion_of(0, MEETING), "neutral")
        self.assertEqual(overlap.conclusion_of(1, MEETING), "failure")
        self.assertEqual(overlap.conclusion_of(0, "locks: origin/main and abc share no history here\n"), "neutral")
        self.assertEqual(overlap.conclusion_of(1, "locks: the clone is shallow\n"), "failure")

    def test_the_title_counts_the_meetings(self):
        self.assertEqual(overlap.title_of("neutral", MEETING * 3, "origin/main"),
                         "This change should bring origin/main in: 3 meetings")
        self.assertEqual(overlap.title_of("failure", MEETING, "origin/main"),
                         "This change must bring origin/main in: 1 meeting")
        self.assertEqual(overlap.title_of("success", NOTHING, "origin/main"),
                         "Nothing origin/main changed since this change's base meets it")
        self.assertEqual(overlap.title_of("neutral", "locks: x\n", "origin/main"),
                         "The change could not be judged against origin/main")


class TheRun(unittest.TestCase):
    def run_over(self, pulls, mode="advise", answers=None, moved=()):
        github = FakeGitHub(pulls)
        answers = answers or {}

        def judge_head(repo_dir, base, sha):
            return answers.get(sha, (0, NOTHING))

        def fetch(repo_dir, number, sha):
            return number not in moved

        out = io.StringIO()
        written = overlap.run("o/r", "origin/main", "/nowhere", "https://run", github, mode,
                              judge_head=judge_head, fetch=fetch, out=out)
        return written, github.posted, out.getvalue()

    def test_every_open_pull_request_gets_the_check_run_on_its_head(self):
        written, posted, said = self.run_over([(1, "a" * 40), (2, "b" * 40)],
                                              answers={"b" * 40: (0, MEETING)})
        self.assertEqual(written, {1: "success", 2: "neutral"})
        self.assertEqual([p["head_sha"] for _, p in posted], ["a" * 40, "b" * 40])
        self.assertEqual([p["conclusion"] for _, p in posted], ["success", "neutral"])
        self.assertTrue(all(path == "repos/o/r/check-runs" and p["name"] == "overlap" and p["status"] == "completed"
                            and p["details_url"] == "https://run" for path, p in posted))
        self.assertIn(MEETING.strip(), posted[1][1]["output"]["summary"])
        self.assertIn("#2 at bbbbbbb: neutral", said)

    def test_enforce_fails_the_change_that_must_bring_main_in(self):
        written, posted, _ = self.run_over([(3, "c" * 40)], mode="enforce", answers={"c" * 40: (1, MEETING)})
        self.assertEqual(written, {3: "failure"})
        self.assertEqual(posted[0][1]["output"]["title"], "This change must bring origin/main in: 1 meeting")

    def test_off_asks_nothing_and_writes_nothing(self):
        written, posted, said = self.run_over([(1, "a" * 40)], mode="off")
        self.assertEqual((written, posted), ({}, []))
        self.assertIn("locks are off", said)

    def test_a_head_that_moved_is_left_to_its_own_run(self):
        written, posted, said = self.run_over([(1, "a" * 40), (2, "b" * 40)], moved=(1,))
        self.assertEqual(written, {2: "success"})
        self.assertEqual(len(posted), 1)
        self.assertIn("#1: head aaaaaaa is not the head any more", said)

    def test_the_list_is_read_page_by_page(self):
        pulls = [(n, f"{n:040x}") for n in range(1, overlap.PAGE + 2)]
        written, posted, _ = self.run_over(pulls)
        self.assertEqual(len(written), overlap.PAGE + 1)
        self.assertEqual(len(posted), overlap.PAGE + 1)

    def test_a_long_summary_is_cut_to_what_github_takes(self):
        written, posted, _ = self.run_over([(1, "a" * 40)], answers={"a" * 40: (0, MEETING * 2000)})
        self.assertLessEqual(len(posted[0][1]["output"]["summary"]), overlap.SUMMARY_LIMIT)


class TheSwitch(unittest.TestCase):
    def test_the_environment_then_the_file_then_off(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(overlap.switch_mode({}, root), "off")
            (Path(root) / ".github").mkdir()
            (Path(root) / overlap.SWITCH_FILE).write_text("Advise\n", encoding="utf-8")
            self.assertEqual(overlap.switch_mode({}, root), "advise")
            self.assertEqual(overlap.switch_mode({"SYMPHONY_LOCKS": "enforce"}, root), "enforce")
            self.assertEqual(overlap.switch_mode({"SYMPHONY_LOCKS": "loud"}, root), "advise")
            (Path(root) / overlap.SWITCH_FILE).write_text("yes please\n", encoding="utf-8")
            self.assertEqual(overlap.switch_mode({}, root), "off")

    def test_main_does_nothing_while_the_switch_is_off(self):
        with tempfile.TemporaryDirectory() as root:
            out = io.StringIO()
            with unittest.mock.patch("sys.stdout", out):
                code = overlap.main({"REPO_DIR": root, "GITHUB_REPOSITORY": "o/r", "GH_TOKEN": "t"})
            self.assertEqual(code, 0)
            self.assertIn("locks are off", out.getvalue())

    def test_main_needs_the_token_and_the_repository_once_the_switch_is_on(self):
        with tempfile.TemporaryDirectory() as root:
            err = io.StringIO()
            with unittest.mock.patch("sys.stderr", err):
                code = overlap.main({"REPO_DIR": root, "SYMPHONY_LOCKS": "advise"})
            self.assertEqual(code, 1)
            self.assertIn("GH_TOKEN and GITHUB_REPOSITORY are needed", err.getvalue())


if __name__ == "__main__":
    unittest.main()
