"""tools/metrics.py writes aggregates and nothing else: off means no call
at all, every key is the spec's, no name, title, branch or text from the
repository reaches the output, and the judge keeps counts only, never runs
with an API key and, in a dry run, sends nothing. The workflow's write step
is run here against local git repositories, so the lease that keeps a judge
push is tested as it runs, not read."""

import io
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
from contextlib import redirect_stderr, redirect_stdout
from functools import partial
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import guard_push  # noqa: E402
import metrics  # noqa: E402

WORKFLOW = ROOT / ".github" / "workflows" / "metrics.yml"
REPO = "octo/widgets"
API = f"/repos/{REPO}"
NOW = "2026-10-10T12:00:00Z"
GIT_ENV = {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.invalid", "GIT_COMMITTER_NAME": "Test",
           "GIT_COMMITTER_EMAIL": "test@example.invalid", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}

# Every string below is something of the repository's own that must never
# reach METRICS.json or JUDGE.json.
PRIVATE = ("Secret plan for widgets", "Fix the login page", "mona-secret", "lisa-secret", "octo-reviewer",
           "agent@example.invalid", "claude/4711", "claude/4712", "claude/4713", "claude/4714",
           "feature/login-page", "the body says secret things", "secret text in a comment", REPO,
           "src/secret_module.py", "Sounds good", "secret words of the judge")
NUMBERS = (99, 101, 102, 103, 104, 4711, 4712, 4713, 4714, 4715, 4716)


def user(login, kind="User"):
    return {"login": login, "type": kind}


def commit(sha, authored, committed=None, login=None, email=None):
    return {"sha": sha, "author": user(login, "Bot" if login and login.endswith("[bot]") else "User") if login else None,
            "commit": {"author": {"name": "someone", "email": email or f"{login}@example.invalid", "date": authored},
                       "committer": {"date": committed or authored}}}


def pull(number, ref, author, created, updated, head, state="closed", merged=None, closed=None, kind="User"):
    return {"number": number, "title": "Secret plan for widgets" if number != 104 else "Fix the login page",
            "body": "the body says secret things", "state": state, "created_at": created, "updated_at": updated,
            "merged_at": merged, "closed_at": closed or merged, "user": user(author, kind),
            "head": {"ref": ref, "sha": head}}


def review(login, state, submitted):
    return {"user": user(login), "state": state, "submitted_at": submitted, "body": "secret text in a comment"}


def run(number, conclusion, completed, name="check"):
    return {"id": number, "name": name, "status": "completed", "conclusion": conclusion, "completed_at": completed}


def runs(*items):
    return {"total_count": len(items), "check_runs": list(items)}


def comment(issue, created, body):
    return {"issue_url": f"https://api.github.com{API}/issues/{issue}", "created_at": created, "body": body,
            "user": user("lisa-secret")}


SHA = {name: name * 40 for name in "abcdef9"}
BEHIND = metrics.board.MAIN_MOVED_MARKER.format(sha="abc1234") + "\n" + \
    metrics.board.main_moved_text("behind", "main", "abc1234")
CONFLICTING = metrics.board.MAIN_MOVED_MARKER.format(sha="abc1234") + "\n" + \
    metrics.board.main_moved_text("conflicting", "main", "abc1234")

# A window from 2026-09-10 12:00 to 2026-10-10 12:00. Pull request 101 is
# merged, 102 closed unmerged, 103 open, a draft in conflict, 104 open, old
# and a bot's, 99 changed before the window, where the listing stops.
PULLS = [
    pull(103, "claude/4713", "lisa-secret", "2026-10-05T00:00:00Z", "2026-10-09T00:00:00Z", SHA["f"], state="open"),
    pull(102, "claude/4712", "mona-secret", "2026-10-03T00:00:00Z", "2026-10-04T00:00:00Z", SHA["d"],
         closed="2026-10-04T00:00:00Z"),
    pull(101, "claude/4711", "mona-secret", "2026-10-01T10:00:00Z", "2026-10-02T10:00:00Z", SHA["c"],
         merged="2026-10-02T10:00:00Z"),
    pull(104, "feature/login-page", "dependabot[bot]", "2026-08-01T00:00:00Z", "2026-09-20T00:00:00Z", SHA["9"],
         state="open", kind="Bot"),
    pull(99, "claude/4710", "mona-secret", "2026-08-01T00:00:00Z", "2026-09-01T00:00:00Z", "0" * 40),
]
ROUTES = {
    f"{API}/pulls": PULLS,
    f"{API}/pulls/101/commits": [commit(SHA["a"], "2026-10-01T09:00:00Z", login="mona-secret"),
                                 commit(SHA["b"], "2026-10-01T09:30:00Z", login="mona-secret"),
                                 commit(SHA["c"], "2026-10-01T15:00:00Z", login="mona-secret")],
    f"{API}/pulls/101/reviews": [review("octo-reviewer", "CHANGES_REQUESTED", "2026-10-01T12:00:00Z"),
                                 review("octo-reviewer", "APPROVED", "2026-10-02T09:00:00Z"),
                                 review("octo-reviewer", "PENDING", None)],
    f"{API}/commits/{SHA['c']}/check-runs": runs(run(1, "success", "2026-10-01T15:05:00Z"),
                                                 run(2, "success", "2026-10-01T15:02:00Z", "board")),
    f"{API}/commits/{SHA['b']}/check-runs": runs(run(3, "failure", "2026-10-01T10:05:00Z")),
    f"{API}/pulls/102/commits": [commit(SHA["d"], "2026-10-02T22:00:00Z", email="agent@example.invalid")],
    f"{API}/pulls/102/reviews": [review("mona-secret", "COMMENTED", "2026-10-03T01:00:00Z")],
    f"{API}/commits/{SHA['d']}/check-runs": runs(run(4, "success", "2026-10-03T00:05:00Z")),
    f"{API}/pulls/103": {"number": 103, "mergeable": False, "mergeable_state": "dirty"},
    f"{API}/pulls/103/commits": [commit(SHA["e"], "2026-10-04T21:00:00Z", login="lisa-secret"),
                                 commit(SHA["f"], "2026-10-06T00:00:00Z", login="lisa-secret")],
    f"{API}/pulls/103/reviews": [],
    f"{API}/commits/{SHA['e']}/check-runs": runs(run(5, "success", "2026-10-05T00:05:00Z"),
                                                 run(6, "timed_out", "2026-10-05T00:20:00Z", "lint")),
    f"{API}/commits/{SHA['f']}/check-runs": runs(run(7, "timed_out", "2026-10-06T00:10:00Z"),
                                                 run(9, "cancelled", "2026-10-06T00:11:00Z", "lint")),
    f"{API}/pulls/104": {"number": 104, "mergeable": True, "mergeable_state": "clean"},
    f"{API}/pulls/104/commits": [commit(SHA["9"], "2026-08-01T00:00:00Z", login="dependabot[bot]")],
    f"{API}/pulls/104/reviews": [review("octo-reviewer", "APPROVED", "2026-09-20T00:00:00Z")],
    f"{API}/commits/{SHA['9']}/check-runs": runs(run(8, "success", "2026-08-01T01:00:00Z")),
    f"{API}/branches": [{"name": n, "commit": {"sha": s}} for n, s in (
        ("main", "5" * 40), ("board", "6" * 40), ("metrics", "7" * 40), ("claude/4711", SHA["c"]),
        ("claude/4713", SHA["f"]), ("claude/4714", "1" * 40), ("claude/4715", "2" * 40), ("claude/notes", "3" * 40))],
    f"{API}/commits/{'1' * 40}": commit("1" * 40, "2026-10-08T00:00:00Z", login="lisa-secret"),
    f"{API}/commits/{'2' * 40}": commit("2" * 40, "2026-08-01T00:00:00Z", login="lisa-secret"),
    f"{API}/issues/comments": [
        comment(4716, "2026-10-07T00:00:00Z", metrics.RELEASE_MARKER + "\nReleased: no commit for a day."),
        comment(4716, "2026-09-01T00:00:00Z", metrics.RELEASE_MARKER + "\nAn old release, edited lately."),
        comment(101, "2026-10-01T20:00:00Z", BEHIND),
        comment(104, "2026-09-25T00:00:00Z", CONFLICTING),
        comment(102, "2026-10-03T02:00:00Z", "secret text in a comment"),
    ],
}
EXPECTED = {
    "counts": {"claims": 4, "pull_requests_opened": 3, "merged": 1, "closed_unmerged": 1, "reviews": 3,
               "changes_requested": 1, "check_runs_passed": 3, "check_runs_failed": 1, "conflicts_seen": 2,
               "released_claims": 1, "contributors": 4},
    "durations_seconds": {"claim_to_first_pull_request_median": 7200, "claim_to_first_pull_request_p90": 10800,
                          "open_to_merge_median": 86400, "open_to_merge_p90": 86400,
                          "first_review_median": 7200, "first_review_p90": 7200},
    "rates": {"merge_rate": 0.5, "first_check_pass_rate": 0.3333},
}


class Answer:
    def __init__(self, body):
        self.body, self.status, self.headers = json.dumps(body).encode(), 200, {}

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeGitHub:
    """Stands in for urllib's opener: answers by path, one page each, and
    a 404 for any path it has no answer for, so a call the code should not
    make fails the test that made it."""

    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def open(self, request, timeout=None):
        path = urllib.parse.urlsplit(request.full_url).path
        self.calls.append(path)
        if path not in self.routes:
            raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, io.BytesIO(b"{}"))
        return Answer(self.routes[path])


class NoCalls:
    def open(self, request, timeout=None):
        raise AssertionError(f"an API call was made: {request.full_url}")


def collect(folder, environ, opener, extra=()):
    out = Path(folder) / "METRICS.json"
    args = metrics.parse_args(["collect", "--repo", REPO, "--out", str(out), "--root", str(folder), "--now", NOW,
                               *extra])
    with redirect_stdout(io.StringIO()):
        code = metrics.collect(args, environ, opener=opener, sleep=lambda seconds: None)
    return code, json.loads(out.read_text()), out.read_text()


def switch(folder, text):
    path = Path(folder) / ".github" / "sdlc-metrics"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


class Switch(unittest.TestCase):
    def test_off_in_the_file_writes_off_alone_and_calls_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            switch(folder, "off\n\nwhy it is off\n")
            code, record, text = collect(folder, {"GITHUB_TOKEN": "t"}, NoCalls())
        self.assertEqual(code, 0)
        self.assertEqual(record, {"schema": "sdlc-metrics/1", "sharing": "off"})
        self.assertEqual(list(record), ["schema", "sharing"])

    def test_off_in_the_variable_wins_over_on_in_the_file_and_needs_no_token(self):
        with tempfile.TemporaryDirectory() as folder:
            switch(folder, "on\n")
            code, record, _ = collect(folder, {metrics.SWITCH_VARIABLE: "off"}, NoCalls())
        self.assertEqual((code, record), (0, metrics.OFF_RECORD))

    def test_each_doubt_falls_to_off(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(metrics.sharing(folder, {}), "on")
            self.assertEqual(metrics.sharing(folder, {metrics.SWITCH_VARIABLE: ""}), "on")
            self.assertEqual(metrics.sharing(folder, {metrics.SWITCH_VARIABLE: " On "}), "on")
            for said in ("off", "OFF", "false", "no"):
                self.assertEqual(metrics.sharing(folder, {metrics.SWITCH_VARIABLE: said}), "off", said)
            for text in ("", "maybe\n", "offline\n", "  OFF  \n"):
                switch(folder, text)
                self.assertEqual(metrics.sharing(folder, {}), "off", text)
            switch(folder, "ON\nthe rest is prose\n")
            self.assertEqual(metrics.sharing(folder, {}), "on")
            self.assertEqual(metrics.sharing(folder, {metrics.SWITCH_VARIABLE: "on"}), "on")

    def test_the_template_ships_the_switch_on(self):
        self.assertEqual(metrics.first_word((ROOT / metrics.SWITCH_FILE).read_text(encoding="utf-8")), "on")


class Collect(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.opener = FakeGitHub(ROUTES)
        with tempfile.TemporaryDirectory() as folder:
            cls.code, cls.record, cls.text = collect(folder, {"GITHUB_TOKEN": "t"}, cls.opener)

    def test_the_window_measures_what_it_holds(self):
        self.assertEqual(self.code, 0)
        for section, values in EXPECTED.items():
            self.assertEqual(self.record[section], values, section)
        self.assertEqual(self.record["generated_at"], NOW)
        self.assertEqual(self.record["window_days"], 30)
        self.assertEqual(self.record["sharing"], "on")
        self.assertEqual(self.record["protocol_version"], metrics.protocol_version())
        self.assertRegex(self.record["protocol_version"], r"^\d+\.\d+\.\d+ [0-9a-f]{7}$")

    def test_the_listing_stops_at_the_first_pull_request_older_than_the_window(self):
        self.assertFalse([path for path in self.opener.calls if "/pulls/99" in path])
        self.assertEqual(self.opener.calls.count(f"{API}/pulls"), 1)

    def test_every_key_is_the_specs_and_every_value_its_type(self):
        self.assertEqual(tuple(self.record), metrics.RECORD_KEYS)
        self.assertEqual(tuple(self.record["counts"]), metrics.COUNT_KEYS)
        self.assertEqual(tuple(self.record["durations_seconds"]), metrics.DURATION_KEYS)
        self.assertEqual(tuple(self.record["rates"]), metrics.RATE_KEYS)
        for value in self.record["counts"].values():
            self.assertIs(type(value), int)
        for value in self.record["durations_seconds"].values():
            self.assertIn(type(value), (int, type(None)))
        for value in self.record["rates"].values():
            self.assertIn(type(value), (float, type(None)))

    def test_nothing_of_the_repository_reaches_the_file(self):
        for secret in PRIVATE:
            self.assertNotIn(secret, self.text, secret)
        numbers = [v for section in ("counts", "durations_seconds") for v in self.record[section].values()]
        for number in NUMBERS:
            self.assertNotIn(number, numbers)
        strings = [v for v in self.record.values() if isinstance(v, str)]
        self.assertEqual(len(strings), 4)

    def test_an_empty_window_gives_zeros_and_nulls(self):
        routes = {f"{API}/pulls": [], f"{API}/branches": [], f"{API}/issues/comments": []}
        with tempfile.TemporaryDirectory() as folder:
            _, record, _ = collect(folder, {"GITHUB_TOKEN": "t"}, FakeGitHub(routes))
        self.assertEqual(set(record["counts"].values()), {0})
        self.assertEqual(set(record["durations_seconds"].values()), {None})
        self.assertEqual(record["rates"], {"merge_rate": None, "first_check_pass_rate": None})

    def test_on_without_a_token_fails_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(os.environ, {}, clear=True):
            out = Path(folder) / "METRICS.json"
            with redirect_stderr(io.StringIO()) as said:
                with mock.patch.object(metrics, "collect", partial(metrics.collect, opener=NoCalls())):
                    code = metrics.main(["collect", "--repo", REPO, "--out", str(out), "--root", folder])
            self.assertEqual(code, 1)
            self.assertIn("no token", said.getvalue())
            self.assertFalse(out.exists())


class Durations(unittest.TestCase):
    def test_the_median_rounds_half_up_to_whole_seconds(self):
        self.assertIsNone(metrics.median_seconds([]))
        self.assertEqual(metrics.median_seconds([5]), 5)
        self.assertEqual(metrics.median_seconds([1, 2]), 2)
        self.assertEqual(metrics.median_seconds([4, 1, 3, 2]), 3)
        self.assertEqual(metrics.median_seconds([30, 10, 20]), 20)

    def test_the_p90_is_the_nearest_rank(self):
        self.assertIsNone(metrics.p90_seconds([]))
        self.assertEqual(metrics.p90_seconds([7]), 7)
        self.assertEqual(metrics.p90_seconds([2, 1]), 2)
        self.assertEqual(metrics.p90_seconds(list(range(1, 11))), 9)
        self.assertEqual(metrics.p90_seconds(list(range(20, 0, -1))), 18)

    def test_a_wait_against_the_clock_is_left_out(self):
        early, late = metrics.parse_time("2026-10-01T00:00:00Z"), metrics.parse_time("2026-10-01T01:00:00Z")
        self.assertEqual(metrics.seconds_between(early, late), 3600)
        self.assertIsNone(metrics.seconds_between(late, early))
        self.assertIsNone(metrics.seconds_between(None, late))

    def test_rates_round_to_four_places(self):
        self.assertEqual(metrics.ratio(1, 3), 0.3333)
        self.assertEqual(metrics.ratio(2, 3), 0.6667)
        self.assertIsNone(metrics.ratio(0, 0))


class Unchanged(unittest.TestCase):
    def test_only_generated_at_may_differ(self):
        old = dict(EXPECTED, schema="sdlc-metrics/1", generated_at="2026-10-09T04:43:00Z")
        same = dict(old, generated_at="2026-10-10T04:43:00Z")
        moved = dict(same, rates={"merge_rate": 1.0, "first_check_pass_rate": None})
        self.assertTrue(metrics.same_apart_from_time(json.dumps(old), json.dumps(same)))
        self.assertFalse(metrics.same_apart_from_time(json.dumps(old), json.dumps(moved)))
        self.assertFalse(metrics.same_apart_from_time("not json", json.dumps(same)))
        self.assertTrue(metrics.same_apart_from_time(json.dumps(metrics.OFF_RECORD), json.dumps(metrics.OFF_RECORD)))


# --- the judge ----------------------------------------------------------------

JUDGE_PULLS = [
    {"number": 201, "body": "Plan: I will change the parser. @lisa-secret can you confirm the format?",
     "created_at": "2026-10-01T10:00:00Z", "updated_at": "2026-10-02T00:00:00Z", "user": user("mona-secret"),
     "title": "Secret plan for widgets", "head": {"ref": "claude/4711", "sha": SHA["a"]}},
    {"number": 202, "body": "", "created_at": "2026-10-03T10:00:00Z", "updated_at": "2026-10-01T00:00:00Z",
     "user": user("mona-secret"), "title": "Fix the login page", "head": {"ref": "claude/4712", "sha": SHA["b"]}},
]
GH_ROUTES = {
    f"repos/{REPO}/pulls": JUDGE_PULLS,
    f"repos/{REPO}/issues/201/comments": [
        {"user": user("lisa-secret"), "created_at": "2026-10-01T11:00:00Z", "body": "Sounds good"},
        {"user": user("github-actions[bot]", "Bot"), "created_at": "2026-10-01T12:00:00Z", "body": BEHIND}],
    f"repos/{REPO}/pulls/201/comments": [
        {"user": user("lisa-secret"), "created_at": "2026-10-01T13:00:00Z", "body": "Rename src/secret_module.py",
         "path": "src/secret_module.py"}],
    f"repos/{REPO}/pulls/201/reviews": [
        {"user": user("lisa-secret"), "state": "APPROVED", "submitted_at": "2026-10-01T14:00:00Z", "body": ""}],
    f"repos/{REPO}/issues/202/comments": [],
    f"repos/{REPO}/pulls/202/comments": [],
    f"repos/{REPO}/pulls/202/reviews": [],
}


class FakeGh:
    """Stands in for subprocess.run for gh: answers gh api by path, the
    query aside, and gh repo view with the repository."""

    def __init__(self, routes=GH_ROUTES):
        self.routes, self.calls = routes, []

    def __call__(self, args, **kwargs):
        self.calls.append(args)
        if args[1:3] == ["repo", "view"]:
            return subprocess.CompletedProcess(args, 0, REPO + "\n", "")
        path = args[-1].split("?", 1)[0]
        if path not in self.routes:
            return subprocess.CompletedProcess(args, 1, "", f"no route for {path}")
        return subprocess.CompletedProcess(args, 0, json.dumps(self.routes[path]), "")


class FakeClaude:
    """Stands in for subprocess.run for claude: answers with each reply in
    turn, in claude -p's JSON result, and keeps what it was given."""

    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        body = {"type": "result", "subtype": "success", "is_error": False, "result": reply}
        return subprocess.CompletedProcess(command, 0, json.dumps(body), "")


def refuse_every_call(*args, **kwargs):
    raise AssertionError(f"called: {args}")


def found(name):
    return f"/usr/bin/{name}"


def run_judge(folder, gh, claude_run, extra=(), environ=None, which=found, git=refuse_every_call):
    out = Path(folder) / "JUDGE.json"
    args = metrics.parse_args(["judge", "--now", NOW, "--out", str(out), *extra])
    shown, said = io.StringIO(), io.StringIO()
    with redirect_stderr(said):
        code = metrics.judge(args, environ or {}, metrics.Gh(run=gh), metrics.LocalClaude(args.model, run=claude_run),
                             which=which, git=git, out=shown)
    return code, out, shown.getvalue(), said.getvalue()


class Judge(unittest.TestCase):
    def test_a_dry_run_sends_nothing_writes_nothing_and_shows_both(self):
        with tempfile.TemporaryDirectory() as folder:
            code, out, shown, _ = run_judge(folder, FakeGh(), refuse_every_call, ["--dry-run", "--repo", REPO])
            self.assertEqual(code, 0)
            self.assertFalse(out.exists())
        self.assertIn(metrics.APPF_PROMPT, shown)
        self.assertIn("[1] 2026-10-01T10:00:00Z A -> all: (description) Plan: I will change the parser. "
                      "@B can you confirm the format?", shown)
        self.assertIn("B -> all: Sounds good", shown)
        self.assertIn("bot -> all: <!-- sdlc-board: main-moved", shown)
        self.assertIn("B -> all: (review: approved)", shown)
        for login in ("mona-secret", "lisa-secret", "github-actions"):
            self.assertNotIn(login, shown)
        record = json.loads(shown.split("(its counts are the model's to fill) ---\n", 1)[1])
        self.assertEqual(record["conversations"], 1)
        self.assertEqual(set(record["counts"].values()), {0})

    def test_it_refuses_while_an_api_key_is_set_and_calls_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            code, out, _, said = run_judge(folder, refuse_every_call, refuse_every_call,
                                           environ={"ANTHROPIC_API_KEY": "set"})
            self.assertFalse(out.exists())
        self.assertEqual(code, 1)
        self.assertIn("unset ANTHROPIC_API_KEY", said)

    def test_it_refuses_without_claude_or_gh(self):
        for missing in ("claude", "gh"):
            with tempfile.TemporaryDirectory() as folder:
                which = partial(lambda gone, name: None if name == gone else found(name), missing)
                code, _, _, said = run_judge(folder, refuse_every_call, refuse_every_call, which=which)
            self.assertEqual(code, 1)
            self.assertIn(f"judge: {missing} is not on PATH", said)

    def test_it_keeps_counts_only_whatever_the_reply_carries(self):
        reply = json.dumps({"codes": ["c1A", "C4b"], "evidence": ["Sounds good"],
                            "issue": {"description": "secret words of the judge"}})
        claude = FakeClaude("Here it is:\n" + reply)
        with tempfile.TemporaryDirectory() as folder:
            code, out, _, _ = run_judge(folder, FakeGh(), claude, ["--repo", REPO, "--model", "claude-test"])
            text = out.read_text()
        self.assertEqual(code, 0)
        record = json.loads(text)
        self.assertEqual(list(record), ["schema", "generated_at", "model", "prompt_variant", "conversations",
                                        "counts", "groups"])
        self.assertEqual(record["schema"], "sdlc-judge/1")
        self.assertEqual((record["model"], record["prompt_variant"], record["conversations"]),
                         ("claude-test", "appF-7", 1))
        self.assertEqual(record["counts"], {"C1a": 1, "C1b": 0, "C2": 0, "C3a": 0, "C3b": 0, "C4a": 0, "C4b": 0})
        self.assertEqual(record["groups"], {"unresponsiveness": 1, "hallucination": 0, "repetition": 0})
        for secret in PRIVATE:
            self.assertNotIn(secret, text, secret)

    def test_the_conversation_goes_to_one_local_claude_on_stdin_and_nowhere_else(self):
        claude = FakeClaude('{"codes": []}')
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            run_judge(folder, FakeGh(), claude, ["--repo", REPO])
        self.assertEqual(len(claude.calls), 1)
        command, kwargs = claude.calls[0]
        self.assertEqual(command[:4], ["claude", "-p", "--output-format", "json"])
        self.assertEqual(command[command.index("--system-prompt") + 1], metrics.APPF_PROMPT)
        self.assertEqual(command[command.index("--tools") + 1], "")
        self.assertEqual(command[command.index("--setting-sources") + 1], "")
        self.assertIn("A -> all: (description)", kwargs["input"])
        self.assertNotIn("lisa-secret", kwargs["input"])
        self.assertNotEqual(Path(kwargs["cwd"]).resolve(), ROOT)
        self.assertNotIn("ANTHROPIC_API_KEY", kwargs["env"])

    def test_a_reply_that_is_not_json_is_asked_once_more_then_left_out(self):
        claude = FakeClaude("I think it is C1a.")
        with tempfile.TemporaryDirectory() as folder:
            code, out, _, said = run_judge(folder, FakeGh(), claude, ["--repo", REPO])
            record = json.loads(out.read_text())
        self.assertEqual((code, len(claude.calls), record["conversations"]), (0, 2, 0))
        self.assertEqual(set(record["counts"].values()), {0})
        self.assertIn("left out", said)

    def test_a_reply_names_at_most_one_code_of_the_taxonomy(self):
        read = metrics.reply_object
        self.assertEqual(metrics.reply_code(read('{"codes": ["C9", "C2", "C3a"]}')), "C2")
        self.assertEqual(metrics.reply_code(read('```json\n{"codes": ["C4b"]}\n```')), "C4b")
        self.assertIsNone(metrics.reply_code(read('{"codes": ["C1"]}')))
        self.assertIsNone(metrics.reply_code(read('{"codes": "C1a"}')))
        self.assertIsNone(metrics.reply_code(read('{"issue": {"category": "C1a"}}')))
        self.assertIsNone(read("no braces here"))

    def test_the_prompt_is_app_f_with_the_codes_and_names_of_coordbench(self):
        self.assertEqual(metrics.APPF_CODES, ("C1a", "C1b", "C2", "C3a", "C3b", "C4a", "C4b"))
        for code in metrics.APPF_CODES:
            self.assertIn(f"- {code} {metrics.APPF_NAMES[code]}\n", metrics.APPF_PROMPT)
        self.assertEqual({metrics.APPF_GROUPS[code] for code in metrics.APPF_CODES}, set(metrics.GROUPS))
        self.assertTrue(metrics.APPF_PROMPT.startswith("You are a careful reviewer of two agent collaboration"))
        self.assertIn('{"codes": ["<category id>"]}', metrics.APPF_PROMPT)

    def test_speakers_are_lettered_and_long_conversations_cut(self):
        self.assertEqual([metrics.letters(i) for i in (0, 1, 25, 26, 27)], ["A", "B", "Z", "AA", "AB"])
        long_text = "x" * metrics.CONVERSATION_LIMIT * 2
        cut = metrics.bounded(long_text)
        self.assertLess(len(cut), metrics.CONVERSATION_LIMIT + 1000)
        self.assertTrue(cut.startswith("x" * metrics.CONVERSATION_KEEP))
        self.assertIn("left out here", cut)
        self.assertEqual(metrics.bounded("short"), "short")


def git(cwd, *args):
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV})
    if done.returncode != 0:
        raise AssertionError(f"git {args}: {done.stderr}")
    return done.stdout.strip()


def seeded_origin(folder, files):
    """A bare origin whose branch metrics is one commit holding files."""
    origin, seed = Path(folder) / "origin.git", Path(folder) / "seed"
    git(folder, "init", "--quiet", "--bare", str(origin))
    git(folder, "init", "--quiet", str(seed))
    entries = []
    for name, text in files.items():
        path = Path(folder) / name
        path.write_text(text)
        entries.append(f"100644 blob {git(seed, 'hash-object', '-w', str(path))}\t{name}")
    tree = subprocess.run(["git", "-C", str(seed), "mktree"], input="\n".join(entries) + "\n", capture_output=True,
                          text=True, check=True).stdout.strip()
    sha = git(seed, "commit-tree", tree, "-m", "Metrics")
    git(seed, "push", "--quiet", str(origin), f"{sha}:refs/heads/metrics")
    return origin, sha


def clone_of(folder, origin, name):
    clone = Path(folder) / name
    git(folder, "init", "--quiet", str(clone))
    git(clone, "remote", "add", "origin", str(origin))
    return clone


def tree_of(cwd, ref):
    return {line.split("\t")[1]: line.split()[2] for line in git(cwd, "ls-tree", ref).splitlines()}


class JudgePush(unittest.TestCase):
    def push(self, folder, origin):
        clone = clone_of(folder, origin, "clone")
        path = Path(folder) / "JUDGE.json"
        path.write_text('{"schema": "sdlc-judge/1"}\n')
        with mock.patch.dict(os.environ, GIT_ENV):
            commit = metrics.push_judge(path, partial(run_in, clone))
        return clone, commit, path

    def test_it_lands_as_a_fast_forward_that_keeps_metrics_json(self):
        with tempfile.TemporaryDirectory() as folder:
            origin, seeded = seeded_origin(folder, {"METRICS.json": '{"schema": "sdlc-metrics/1"}\n'})
            before = tree_of(origin, seeded)
            clone, commit, path = self.push(folder, origin)
            self.assertEqual(git(origin, "rev-parse", "metrics"), commit)
            self.assertEqual(git(origin, "rev-parse", "metrics^"), seeded)
            after = tree_of(origin, "metrics")
            self.assertEqual(after["METRICS.json"], before["METRICS.json"])
            self.assertEqual(git(origin, "show", "metrics:JUDGE.json") + "\n", path.read_text())

    def test_it_starts_the_branch_when_there_is_none(self):
        with tempfile.TemporaryDirectory() as folder:
            origin = Path(folder) / "origin.git"
            git(folder, "init", "--quiet", "--bare", str(origin))
            _, commit, _ = self.push(folder, origin)
            self.assertEqual(sorted(tree_of(origin, "metrics")), ["JUDGE.json"])
            self.assertEqual(git(origin, "rev-list", "--count", "metrics"), "1")

    def test_the_push_guard_lets_its_push_through(self):
        command = shlex.join(["git", *metrics.push_arguments("0123456789abcdef0123456789abcdef01234567")])
        pushes = [args for argv in guard_push.simple_commands(command)
                  if (args := guard_push.push_arguments(argv)) is not None]
        self.assertEqual(len(pushes), 1)
        for current in (None, "main", "claude/7", "metrics"):
            self.assertIsNone(guard_push.refusal(pushes[0], current, "main"), current)
        self.assertNotIn("--force", " ".join(pushes[0]))
        payload = json.dumps({"tool_input": {"command": command}})
        with mock.patch.object(guard_push, "branches", return_value=("main", "main")), \
                mock.patch.object(sys, "stdin", io.StringIO(payload)), redirect_stderr(io.StringIO()):
            self.assertEqual(guard_push.main(), 0)


def run_in(cwd, *args, input=None):
    done = subprocess.run(["git", "-C", str(cwd), *args], input=input, capture_output=True, text=True)
    if done.returncode != 0:
        raise metrics.JudgeError(f"git {args[0]}: {done.stderr.strip()}")
    return done.stdout


# --- the workflow ---------------------------------------------------------------

def step_lines(name):
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    start = lines.index(f"      - name: {name}")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("      - ")), len(lines))
    return lines[start:end]


def run_block(lines):
    start = next(i for i, line in enumerate(lines) if line.strip() == "run: |")
    return "\n".join(line[10:] for line in lines[start + 1:]) + "\n"


WRITE_STEP = "Write METRICS.json to the branch metrics when it changed"
OLD = dict(EXPECTED, schema="sdlc-metrics/1", generated_at="2026-10-09T04:43:00Z")
NEW_TIME = dict(OLD, generated_at="2026-10-10T04:43:00Z")
MOVED = dict(NEW_TIME, counts=dict(EXPECTED["counts"], merged=2))
RACE_GIT = """#!/bin/bash
# The first push of the run is preceded by a judge's, as if it landed
# between the run's fetch and its own push.
if [ "$1" = "push" ] && [ ! -e "$RACE_DONE" ]; then
  touch "$RACE_DONE"
  "$REAL_GIT" -C "$RACE_CLONE" push --quiet origin "$RACE_COMMIT:refs/heads/metrics"
fi
exec "$REAL_GIT" "$@"
"""


class WriteStep(unittest.TestCase):
    """The step's own script, run against a bare origin."""

    def run_step(self, folder, origin, record, extra_env=None):
        work = clone_of(folder, origin, "work")
        (work / "tools").symlink_to(ROOT / "tools")
        temp = Path(folder) / "runner"
        temp.mkdir()
        (temp / "METRICS.json").write_text(json.dumps(record, indent=2) + "\n")
        env = {**os.environ, **GIT_ENV, "RUNNER_TEMP": str(temp), **(extra_env or {})}
        done = subprocess.run(["bash", "-e", "-c", run_block(step_lines(WRITE_STEP))], cwd=work, env=env,
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout

    def origin_with_judge(self, folder):
        return seeded_origin(folder, {"METRICS.json": json.dumps(OLD, indent=2) + "\n", "JUDGE.json": '{"n": 1}\n'})

    def test_a_change_replaces_the_branch_with_one_commit_that_keeps_judge_json(self):
        with tempfile.TemporaryDirectory() as folder:
            origin, seeded = self.origin_with_judge(folder)
            judge_blob = tree_of(origin, seeded)["JUDGE.json"]
            said = self.run_step(folder, origin, MOVED)
            self.assertIn("metrics written as", said)
            self.assertEqual(git(origin, "rev-list", "--count", "metrics"), "1")
            self.assertEqual(tree_of(origin, "metrics")["JUDGE.json"], judge_blob)
            self.assertEqual(json.loads(git(origin, "show", "metrics:METRICS.json")), MOVED)

    def test_a_new_time_alone_writes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            origin, seeded = self.origin_with_judge(folder)
            said = self.run_step(folder, origin, NEW_TIME)
            self.assertIn("metrics unchanged", said)
            self.assertEqual(git(origin, "rev-parse", "metrics"), seeded)

    def test_the_first_write_starts_the_branch(self):
        with tempfile.TemporaryDirectory() as folder:
            origin = Path(folder) / "origin.git"
            git(folder, "init", "--quiet", "--bare", str(origin))
            self.run_step(folder, origin, MOVED)
            self.assertEqual(sorted(tree_of(origin, "metrics")), ["METRICS.json"])

    def test_a_judge_push_landing_meanwhile_is_kept(self):
        with tempfile.TemporaryDirectory() as folder:
            origin, seeded = self.origin_with_judge(folder)
            race = clone_of(folder, origin, "race")
            judge = Path(folder) / "JUDGE.json"
            judge.write_text('{"n": 2}\n')
            git(race, "fetch", "--quiet", "origin", "metrics")
            with mock.patch.dict(os.environ, GIT_ENV):
                race_commit = metrics.judge_commit(partial(run_in, race), judge, seeded)
            shim = Path(folder) / "bin"
            shim.mkdir()
            (shim / "git").write_text(RACE_GIT)
            (shim / "git").chmod(0o755)
            env = {"PATH": f"{shim}{os.pathsep}{os.environ['PATH']}", "REAL_GIT": subprocess.run(
                ["bash", "-c", "command -v git"], capture_output=True, text=True).stdout.strip(),
                "RACE_DONE": str(Path(folder) / "race-done"), "RACE_CLONE": str(race), "RACE_COMMIT": race_commit}
            said = self.run_step(folder, origin, MOVED, env)
            self.assertIn("moved during this run", said)
            self.assertEqual(git(origin, "show", "metrics:JUDGE.json"), '{"n": 2}')
            self.assertEqual(json.loads(git(origin, "show", "metrics:METRICS.json")), MOVED)
            self.assertEqual(git(origin, "rev-list", "--count", "metrics"), "1")


class Workflow(unittest.TestCase):
    TEXT = WORKFLOW.read_text(encoding="utf-8")

    def test_daily_at_an_odd_minute_and_by_hand(self):
        self.assertRegex(self.TEXT, r'\n  schedule:\n    - cron: "([1-9]|[1-5][0-9]) \d{1,2} \* \* \*"\n')
        self.assertIn("\n  workflow_dispatch:\n", self.TEXT)

    def test_its_permissions_are_these_four(self):
        block = self.TEXT.split("\npermissions:\n", 1)[1].split("\n\n", 1)[0]
        self.assertEqual(block.splitlines(), ["  contents: write", "  pull-requests: read", "  issues: read",
                                              "  checks: read"])

    def test_it_skips_the_template_and_a_pending_copy(self):
        self.assertIn("    if: github.event.repository.is_template == false\n", self.TEXT)
        self.assertIn("if [ -e .template/PENDING ]; then", "\n".join(step_lines("Stop in the template repository itself")))

    def test_values_reach_the_shell_through_env_alone(self):
        for name in ("Stop in the template repository itself", "Collect the aggregates", WRITE_STEP):
            lines = step_lines(name)
            start = next(i for i, line in enumerate(lines) if line.strip().startswith("run:"))
            self.assertNotIn("${{", "\n".join(lines[start:]), name)
        collect_step = "\n".join(step_lines("Collect the aggregates"))
        self.assertIn("SDLC_METRICS: ${{ vars.SDLC_METRICS }}", collect_step)
        self.assertIn("GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}", collect_step)

    def test_it_names_no_secret_but_its_own_token(self):
        import re
        self.assertEqual(set(re.findall(r"secrets\.([A-Z_]+)", self.TEXT)), {"GITHUB_TOKEN"})
        self.assertNotIn("anthropics/claude-code-action", self.TEXT)
        self.assertIn("In crowd mode", self.TEXT.split("\non:", 1)[0])

    def test_its_one_forced_push_is_leased_to_the_commit_it_read(self):
        script = run_block(step_lines(WRITE_STEP))
        self.assertIn('--force-with-lease="refs/heads/metrics:$previous"', script)
        self.assertNotRegex(script, r"--force(?!-with-lease)|\s-f\s|\+\$commit")


class Coordinator(unittest.TestCase):
    def test_both_coordinator_prompts_mark_a_release_as_metrics_counts_it(self):
        for page in ("docs/agents/routines/coordinator.md", "docs/setup/crowd/coordinator.md"):
            prompt = (ROOT / page).read_text(encoding="utf-8").split("```")[-2]
            self.assertIn(f"`{metrics.RELEASE_MARKER}` as the comment's first line", prompt, page)


class Page(unittest.TestCase):
    TEXT = (ROOT / "docs" / "setup" / "metrics.md").read_text(encoding="utf-8")

    def samples(self):
        return [json.loads(block.split("\n", 1)[1]) for block in self.TEXT.split("```")[1::2]
                if block.startswith("json\n")]

    def test_the_samples_have_exactly_the_keys_the_tool_writes(self):
        found = {}
        for sample in self.samples():
            found.setdefault(sample["schema"], sample)
        sample = found["sdlc-metrics/1"]
        self.assertEqual(tuple(sample), metrics.RECORD_KEYS)
        self.assertEqual(tuple(sample["counts"]), metrics.COUNT_KEYS)
        self.assertEqual(tuple(sample["durations_seconds"]), metrics.DURATION_KEYS)
        self.assertEqual(tuple(sample["rates"]), metrics.RATE_KEYS)
        judge = found["sdlc-judge/1"]
        self.assertEqual(tuple(judge), ("schema", "generated_at", "model", "prompt_variant", "conversations",
                                        "counts", "groups"))
        self.assertEqual(tuple(judge["counts"]), metrics.APPF_CODES)
        self.assertEqual(tuple(judge["groups"]), metrics.GROUPS)

    def test_it_names_the_switch_both_ways_and_never_an_api_key_for_the_judge(self):
        for needed in (metrics.SWITCH_FILE, "SDLC_METRICS", "python3 tools/metrics.py judge --dry-run",
                       "unset ANTHROPIC_API_KEY", metrics.RELEASE_MARKER):
            self.assertIn(needed, self.TEXT)


if __name__ == "__main__":
    unittest.main()
