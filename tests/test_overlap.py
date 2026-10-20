"""tools/overlap.py: every open pull request onto the default branch is
judged against it as it now stands and gets the check run named overlap
on its head, with the conclusion the switch and the tool's answer give;
off writes nothing, a head that moved since the list was read is left to
its own run, and a refusal on one head stops no other. GitHub is a fake
here; the fetch and the judgement run against a bare repository of their
own, with the vendored library, and the judgement's own cases are the
library's (symphony-protocol's tests.test_git_locks)."""

import io
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import overlap  # noqa: E402

MEETING = ("locks: origin/main edited m.py#f since this change's base, which this change builds on: "
           "bring origin/main in\n")
NOTHING = "locks: nothing origin/main changed since the base meets this change; it need not bring it in\n"

# git's automatic maintenance runs detached after a fetch or a push and
# races the scratch folder's removal, so every repository here is told
# not to run it, in the environment and in its own config, since git hands
# GIT_CONFIG_COUNT to neither end it starts for a local remote.
QUIET = {"gc.auto": "0", "gc.autoDetach": "false", "maintenance.auto": "false", "maintenance.autoDetach": "false",
         "receive.autogc": "false"}
GIT_ENV = {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.invalid", "GIT_COMMITTER_NAME": "Test",
           "GIT_COMMITTER_EMAIL": "test@example.invalid", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_CONFIG_COUNT": str(len(QUIET)),
           **{f"GIT_CONFIG_KEY_{i}": key for i, key in enumerate(QUIET)},
           **{f"GIT_CONFIG_VALUE_{i}": value for i, value in enumerate(QUIET.values())}}


class FakeGitHub:
    """The two calls the tool makes: a pull request is (number, head sha)
    or (number, head sha, base branch), main by default, and a number in
    `refuse` gets 422 for its check run, as GitHub answers for a sha it
    does not hold."""

    def __init__(self, pulls, refuse=()):
        self.pulls = [(p[0], p[1], p[2] if len(p) > 2 else "main") for p in pulls]
        self.refuse = set(refuse)
        self.posted = []

    def __call__(self, method, path, payload=None):
        if method == "GET":
            if "state=open" not in path or f"per_page={overlap.PAGE}" not in path:
                raise AssertionError(f"the listing must ask for the open pull requests a page at a time: {path}")
            page = int(path.rsplit("page=", 1)[1])
            start = (page - 1) * overlap.PAGE
            return [{"number": n, "head": {"sha": sha}, "base": {"ref": base}}
                    for n, sha, base in self.pulls[start:start + overlap.PAGE]]
        if payload["head_sha"] in {sha for n, sha, _ in self.pulls if n in self.refuse}:
            raise urllib.error.HTTPError(path, 422, "Unprocessable Entity", {},
                                         io.BytesIO(b'{"message":"No commit found for SHA"}'))
        self.posted.append((path, payload))
        return {"id": len(self.posted)}


class Conclusions(unittest.TestCase):
    def test_the_tool_s_answer_gives_the_conclusion(self):
        self.assertEqual(overlap.conclusion_of(0, NOTHING, "origin/main"), "success")
        self.assertEqual(overlap.conclusion_of(0, MEETING, "origin/main"), "neutral")
        self.assertEqual(overlap.conclusion_of(1, MEETING, "origin/main"), "failure")
        self.assertEqual(overlap.conclusion_of(0, "locks: origin/main and abc share no history here\n", "origin/main"),
                         "neutral")
        self.assertEqual(overlap.conclusion_of(1, "locks: the clone is shallow\n", "origin/main"), "failure")
        self.assertEqual(overlap.conclusion_of(0, "", "origin/main"), "neutral")

    def test_success_is_the_library_s_whole_last_line_and_not_words_in_a_key(self):
        in_a_key = ("locks: origin/main edited docs/it need not bring it in.md since this change's base, "
                    "which this change edits: bring origin/main in\n")
        self.assertEqual(overlap.conclusion_of(0, in_a_key, "origin/main"), "neutral")
        self.assertEqual(overlap.conclusion_of(0, NOTHING, "origin/release"), "neutral")

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
    def run_over(self, pulls, mode="advise", answers=None, moved=(), refuse=()):
        github = FakeGitHub(pulls, refuse)
        answers = answers or {}

        def judge_head(repo_dir, base, sha):
            return answers.get(sha, (0, NOTHING))

        def fetch(repo_dir, number, sha):
            return number not in moved

        out = io.StringIO()
        written = overlap.run("o/r", "main", "/nowhere", "https://run", github, mode,
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

    def test_a_pull_request_onto_another_branch_is_left_to_its_own_run(self):
        written, posted, _ = self.run_over([(1, "a" * 40), (2, "b" * 40, "release"), (3, "c" * 40, "main")])
        self.assertEqual(written, {1: "success", 3: "success"})
        self.assertEqual([p["head_sha"] for _, p in posted], ["a" * 40, "c" * 40])

    def test_a_refusal_on_one_head_stops_no_other_and_is_said(self):
        written, posted, said = self.run_over([(1, "a" * 40), (2, "b" * 40), (3, "c" * 40)], refuse=(2,))
        self.assertEqual(written, {1: "success", 2: overlap.UNWRITTEN, 3: "success"})
        self.assertEqual([p["head_sha"] for _, p in posted], ["a" * 40, "c" * 40])
        self.assertIn("#2 at bbbbbbb: no check run written: GitHub refused 422: {\"message\":\"No commit found", said)
        self.assertEqual(overlap.unwritten_of(written), [2])

    def test_a_fault_in_the_judgement_of_one_head_stops_no_other(self):
        def judge_head(repo_dir, base, sha):
            if sha.startswith("b"):
                raise subprocess.TimeoutExpired(["git", "fetch"], 300)
            return 0, NOTHING

        out = io.StringIO()
        written = overlap.run("o/r", "main", "/nowhere", "", FakeGitHub([(1, "a" * 40), (2, "b" * 40)]), "advise",
                              judge_head=judge_head, fetch=lambda *_: True, out=out)
        self.assertEqual(written, {1: "success", 2: overlap.UNWRITTEN})
        self.assertIn("#2 at bbbbbbb: no check run written: git took more than 300 s", out.getvalue())

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

    def test_main_fails_at_the_end_where_a_head_got_no_check_run(self):
        """The run goes on past a refusal and says at its end which heads
        got no word, so the workflow is red where GitHub holds no answer."""
        for refuse, code in (((), 0), ((2,), 1)):
            github = FakeGitHub([(1, "a" * 40), (2, "b" * 40)], refuse)
            err = io.StringIO()
            with unittest.mock.patch.object(overlap, "api", lambda token, *call: github(*call)), \
                    unittest.mock.patch.object(overlap, "fetch_head", lambda *_: True), \
                    unittest.mock.patch.object(overlap, "judge", lambda *_: (0, NOTHING)), \
                    unittest.mock.patch("sys.stdout", io.StringIO()), unittest.mock.patch("sys.stderr", err):
                got = overlap.main({"REPO_DIR": "/nowhere", "SYMPHONY_LOCKS": "advise", "GH_TOKEN": "t",
                                    "GITHUB_REPOSITORY": "o/r", "DEFAULT_BRANCH": "main"})
            self.assertEqual(got, code, refuse)
            self.assertEqual(len(github.posted), 2 - len(refuse))
            self.assertEqual("no check run was written for #2" in err.getvalue(), bool(refuse))


class TheClone(unittest.TestCase):
    """The fetch and the judgement against a bare repository: main at
    Start holds m.py with f and g, where g calls f; pull request 1 edits g
    and pull request 2 adds n.py; then main edits f and moves on. Judged in
    a clone one commit deep, as actions/checkout leaves it, 1 must bring
    main in (f, which it builds on, changed) and 2 need not."""

    def setUp(self):
        self.enterContext(unittest.mock.patch.dict(os.environ, {**GIT_ENV, "SYMPHONY_LOCKS": "advise"}))
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.origin = self.root / "origin.git"
        self.git(self.root, "init", "--quiet", "--bare", "--initial-branch=main", str(self.origin))
        work = self.root / "work"
        self.git(self.root, "clone", "--quiet", str(self.origin), str(work))
        for repo in (self.origin, work):
            for key, value in QUIET.items():
                self.git(repo, "config", key, value)
        self.commit(work, "m.py", "def f():\n    return 1\n\n\ndef g():\n    return f()\n", "Start")
        self.git(work, "push", "--quiet", "origin", "main")
        self.git(work, "checkout", "--quiet", "-b", "one")
        self.commit(work, "m.py", "def f():\n    return 1\n\n\ndef g():\n    return f() + 1\n", "Edit g")
        self.git(work, "push", "--quiet", "origin", "one:refs/pull/1/head")
        self.one = self.git(work, "rev-parse", "HEAD").stdout.strip()
        self.git(work, "checkout", "--quiet", "-b", "two", "main")
        self.commit(work, "n.py", "def h():\n    return 3\n", "Add n")
        self.git(work, "push", "--quiet", "origin", "two:refs/pull/2/head")
        self.two = self.git(work, "rev-parse", "HEAD").stdout.strip()
        self.git(work, "checkout", "--quiet", "main")
        self.commit(work, "m.py", "def f():\n    return 2\n\n\ndef g():\n    return f()\n", "Edit f")
        self.git(work, "push", "--quiet", "origin", "main")

    def git(self, cwd, *args):
        done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=120)
        if done.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {done.stderr}")
        return done

    def commit(self, repo, name, text, message):
        (repo / name).write_text(text, encoding="utf-8")
        self.git(repo, "add", name)
        self.git(repo, "commit", "--quiet", "-m", message)

    def clone(self, name, *options):
        target = self.root / name
        self.git(self.root, "clone", "--quiet", *options, f"file://{self.origin}", str(target))
        for key, value in QUIET.items():
            self.git(target, "config", key, value)
        return str(target)

    def test_the_heads_are_fetched_and_judged_in_a_shallow_clone(self):
        clone = self.clone("shallow", "--depth=1")
        self.assertEqual(self.git(clone, "rev-parse", "--is-shallow-repository").stdout.strip(), "true")
        self.assertTrue(overlap.fetch_head(clone, 1, self.one))
        self.assertTrue(overlap.fetch_head(clone, 2, self.two))
        self.assertFalse(overlap.fetch_head(clone, 1, "0" * 40))
        self.assertFalse(overlap.fetch_head(clone, 3, self.one))
        code, text = overlap.judge(clone, "origin/main", self.one)
        self.assertEqual((code, overlap.conclusion_of(code, text, "origin/main")), (0, "neutral"), text)
        self.assertIn(MEETING.strip(), text)
        code, text = overlap.judge(clone, "origin/main", self.two)
        self.assertEqual((code, overlap.conclusion_of(code, text, "origin/main")), (0, "success"), text)
        with unittest.mock.patch.dict(os.environ, {"SYMPHONY_LOCKS": "enforce"}):
            code, text = overlap.judge(clone, "origin/main", self.one)
        self.assertEqual((code, overlap.conclusion_of(code, text, "origin/main")), (1, "failure"), text)

    def test_a_whole_clone_stays_whole(self):
        clone = self.clone("whole")
        self.assertTrue(overlap.fetch_head(clone, 1, self.one))
        self.assertEqual(self.git(clone, "rev-parse", "--is-shallow-repository").stdout.strip(), "false")
        code, text = overlap.judge(clone, "origin/main", self.one)
        self.assertEqual(overlap.conclusion_of(code, text, "origin/main"), "neutral", text)

    def test_the_run_writes_both_heads_from_one_look(self):
        clone = self.clone("run", "--depth=1")
        github = FakeGitHub([(1, self.one), (2, self.two)])
        out = io.StringIO()
        written = overlap.run("o/r", "main", clone, "https://run", github, "advise", out=out)
        self.assertEqual(written, {1: "neutral", 2: "success"})
        self.assertEqual([p["output"]["title"] for _, p in github.posted],
                         ["This change should bring origin/main in: 1 meeting",
                          "Nothing origin/main changed since this change's base meets it"])


if __name__ == "__main__":
    unittest.main()
