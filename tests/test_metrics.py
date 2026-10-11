"""tools/metrics.py writes aggregates and nothing else: off means no call
at all, every key is the spec's, no name, title, branch or text from the
repository reaches the output, and the judge keeps counts only, never runs
with an API key and, in a dry run, sends nothing. The workflow's write step
is run here against local git repositories, so the lease that keeps a judge
push is tested as it runs, not read."""

import io
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import guard_push  # noqa: E402
import metrics  # noqa: E402

# A repository made from the template turns sharing off by writing off into
# the switch file, and its tests must pass then: what the shipped file says
# is checked in the template alone, where .template/ still is, as
# tests/test_crowd.py does.
IN_TEMPLATE = (ROOT / ".template" / "PENDING").is_file()
template_only = unittest.skipUnless(IN_TEMPLATE, "reads the template's own switch file, which a copy may have turned off")

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
# OpenSpineConsortium's collector (sdlc-app, its collect script's VERSION)
# keeps protocol_version only when the whole value is a release, alone or
# followed by a space and 7 to 40 hex digits of the commit.
COLLECTOR_VERSION = re.compile(r"[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}( [0-9a-f]{7,40})?")
# An epoch second, as GitHub's X-RateLimit-Reset header is.
RESET = 1791637200
# OpenSpineConsortium's collector (sdlc-app, its collect workflow) reads the
# branch metrics at 04:17 UTC, so the day's record must be there by then.
COLLECTOR_READ = 4 * 60 + 17


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
# and a bot's, 99 changed before the window, where the listing stops. 101's
# check failed on a and passed when run again, failed on b, its first head,
# and passed on c, the head it merged with.
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
    f"{API}/commits/{SHA['a']}/check-runs": runs(run(10, "failure", "2026-10-01T09:05:00Z"),
                                                 run(11, "success", "2026-10-01T09:40:00Z")),
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
               "changes_requested": 1, "check_runs_passed": 5, "check_runs_failed": 4, "conflicts_seen": 2,
               "released_claims": 1, "contributors": 4},
    "durations_seconds": {"claim_to_first_pull_request_median": 7200, "claim_to_first_pull_request_p90": 10800,
                          "open_to_merge_median": 86400, "open_to_merge_p90": 86400,
                          "first_review_median": 7200, "first_review_p90": 7200},
    "rates": {"merge_rate": 0.5, "first_check_pass_rate": 0.3333},
}


class Answer:
    def __init__(self, body, headers=None):
        self.body, self.status, self.headers = json.dumps(body).encode(), 200, headers or {}

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeGitHub:
    """Stands in for urllib's opener: answers by path, one page each, and
    a 404 for any path it has no answer for, so a call the code should not
    make fails the test that made it. Given a number of requests left, it
    counts them down in the rate-limit headers as GitHub does."""

    def __init__(self, routes, remaining=None):
        self.routes, self.calls, self.queries, self.remaining = routes, [], [], remaining

    def open(self, request, timeout=None):
        parts = urllib.parse.urlsplit(request.full_url)
        self.calls.append(parts.path)
        self.queries.append(dict(urllib.parse.parse_qsl(parts.query)))
        headers = {}
        if self.remaining is not None:
            self.remaining -= 1
            headers = {"X-RateLimit-Remaining": str(self.remaining), "X-RateLimit-Reset": str(RESET)}
        if parts.path not in self.routes:
            raise urllib.error.HTTPError(request.full_url, 404, "Not Found", headers, io.BytesIO(b"{}"))
        return Answer(self.routes[parts.path], headers)


class SpentHour:
    """An opener whose every answer is GitHub's refusal of a spent hour."""

    def open(self, request, timeout=None):
        body = io.BytesIO(b'{"message": "API rate limit exceeded for installation ID 1."}')
        raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {"X-RateLimit-Remaining": "0"}, body)


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


def switch(folder, text, name="symphony-metrics"):
    path = Path(folder) / ".github" / name
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

    def test_the_switch_under_its_old_name_still_counts_and_the_new_name_wins(self):
        """A repository set up before the rename carries .github/sdlc-metrics;
        it is read when the new file is absent, and the new file decides
        when both are there."""
        with tempfile.TemporaryDirectory() as folder:
            switch(folder, "off\n", name="sdlc-metrics")
            code, record, _ = collect(folder, {"GITHUB_TOKEN": "t"}, NoCalls())
        self.assertEqual((code, record["sharing"]), (0, "off"))
        with tempfile.TemporaryDirectory() as folder:
            switch(folder, "off\n", name="sdlc-metrics")
            switch(folder, "on\n")
            self.assertEqual(metrics.sharing(folder, {}), metrics.ON)

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

    @template_only
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

    def test_check_runs_are_read_on_every_commit_made_in_the_window_every_attempt_of_each(self):
        asked = [(path, query) for path, query in zip(self.opener.calls, self.opener.queries)
                 if path.endswith("/check-runs")]
        # One call per commit made in the window, the first heads b and d
        # among them once; none for 104's head, made before the window.
        self.assertEqual(sorted(path for path, _ in asked),
                         sorted(f"{API}/commits/{SHA[name]}/check-runs" for name in "abcdef"))
        self.assertEqual({query.get("filter") for _, query in asked}, {"all"})
        # a's failure and its re-run both count, and so does b's failure,
        # which the push of c fixed before the merge.
        self.assertEqual((self.record["counts"]["check_runs_passed"], self.record["counts"]["check_runs_failed"]),
                         (5, 4))

    def test_a_commit_in_two_pull_requests_brings_its_runs_once(self):
        window = metrics.Window.ending(metrics.parse_time(NOW), 30)
        shared = run(1, "failure", "2026-10-01T10:05:00Z")
        facts = [metrics.PullFacts(PULLS[2], runs={SHA["b"]: [shared]}),
                 metrics.PullFacts(PULLS[0], runs={SHA["b"]: [dict(shared)]})]
        self.assertEqual(len(metrics.window_runs(facts, window)), 1)

    def test_a_first_head_made_before_the_window_costs_one_more_call(self):
        old, new = "3" * 40, "4" * 40
        routes = {
            f"{API}/pulls": [pull(105, "claude/4716", "lisa-secret", "2026-10-07T00:00:00Z", "2026-10-08T00:00:00Z",
                                  new, merged="2026-10-08T00:00:00Z")],
            f"{API}/pulls/105/commits": [commit(old, "2026-09-01T00:00:00Z", login="lisa-secret"),
                                         commit(new, "2026-10-07T01:00:00Z", login="lisa-secret")],
            f"{API}/pulls/105/reviews": [],
            f"{API}/commits/{old}/check-runs": runs(run(1, "success", "2026-09-01T00:05:00Z")),
            f"{API}/commits/{new}/check-runs": runs(run(2, "failure", "2026-10-07T01:05:00Z")),
            f"{API}/branches": [], f"{API}/issues/comments": [],
        }
        opener = FakeGitHub(routes)
        with tempfile.TemporaryDirectory() as folder:
            _, record, _ = collect(folder, {"GITHUB_TOKEN": "t"}, opener)
        self.assertEqual([path for path in opener.calls if path.endswith("/check-runs")],
                         [f"{API}/commits/{new}/check-runs", f"{API}/commits/{old}/check-runs"])
        self.assertEqual((record["counts"]["check_runs_passed"], record["counts"]["check_runs_failed"]), (0, 1))
        self.assertEqual(record["rates"]["first_check_pass_rate"], 1.0)

    def test_contributors_are_dated_by_their_own_acts_not_the_pull_requests(self):
        # An open pull request from June, bumped into the window by a board
        # comment: its author, its reviewer and its committer did nothing
        # in the window.
        stale = pull(106, "claude/4717", "alice-secret", "2026-06-01T00:00:00Z", "2026-10-09T00:00:00Z", "4" * 40,
                     state="open")
        routes = {
            f"{API}/pulls": [stale],
            f"{API}/pulls/106": {"number": 106, "mergeable": True, "mergeable_state": "clean"},
            f"{API}/pulls/106/commits": [commit("3" * 40, "2026-06-01T00:00:00Z", login="dave-secret")],
            f"{API}/pulls/106/reviews": [review("carol-secret", "APPROVED", "2026-06-02T00:00:00Z")],
            f"{API}/branches": [], f"{API}/issues/comments": [comment(106, "2026-10-09T00:00:00Z", BEHIND)],
        }
        with tempfile.TemporaryDirectory() as folder:
            _, record, _ = collect(folder, {"GITHUB_TOKEN": "t"}, FakeGitHub(routes))
        self.assertEqual((record["counts"]["contributors"], record["counts"]["reviews"]), (0, 0))
        # A review in the window and a June commit rebased in it count
        # their two people; the author of June still does not.
        routes[f"{API}/pulls/106/reviews"].append(review("carol-secret", "COMMENTED", "2026-10-09T00:00:00Z"))
        routes[f"{API}/pulls/106/commits"].append(
            commit("4" * 40, "2026-06-01T00:00:00Z", "2026-10-08T00:00:00Z", login="dave-secret"))
        routes[f"{API}/commits/{'4' * 40}/check-runs"] = runs()
        with tempfile.TemporaryDirectory() as folder:
            _, record, _ = collect(folder, {"GITHUB_TOKEN": "t"}, FakeGitHub(routes))
        self.assertEqual((record["counts"]["contributors"], record["counts"]["reviews"]), (2, 1))

    def test_it_stops_short_of_the_boards_reserve_and_writes_nothing(self):
        opener, environ = FakeGitHub(ROUTES, remaining=metrics.RESERVE + 5), {"GITHUB_TOKEN": "t"}
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(os.environ, environ, clear=True):
            out = Path(folder) / "METRICS.json"
            with redirect_stderr(io.StringIO()) as said, redirect_stdout(io.StringIO()):
                with mock.patch.object(metrics, "collect", partial(metrics.collect, opener=opener)):
                    code = metrics.main(["collect", "--repo", REPO, "--out", str(out), "--root", folder,
                                         "--now", NOW])
            self.assertEqual(code, 1)
            self.assertFalse(out.exists())
        self.assertEqual(len(opener.calls), 5)
        self.assertIn(f"metrics: stopped after 5 calls, with {metrics.RESERVE} of GITHUB_TOKEN's 1,000 requests an "
                      "hour left for the board, whose reserve is 300: nothing is written, and the branch metrics "
                      "keeps its last record.", said.getvalue())
        self.assertIn(f"comes back at {metrics.iso(datetime.fromtimestamp(RESET, timezone.utc))}", said.getvalue())

    def test_githubs_refusal_of_a_spent_hour_is_told_the_same_way(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "METRICS.json"
            args = metrics.parse_args(["collect", "--repo", REPO, "--out", str(out), "--root", folder, "--now", NOW])
            with self.assertRaises(metrics.OutOfBudget) as caught:
                metrics.collect(args, {"GITHUB_TOKEN": "t"}, opener=SpentHour(), sleep=lambda seconds: None)
            self.assertFalse(out.exists())
        self.assertIn("GitHub refused the call (API rate limit exceeded for installation ID 1.); stopped after "
                      "0 calls, with 0 of GITHUB_TOKEN's", str(caught.exception))
        self.assertIn("comes back within the hour", str(caught.exception))

    def test_a_run_that_fits_says_how_many_calls_it_took(self):
        opener = FakeGitHub(ROUTES, remaining=1000)
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "METRICS.json"
            args = metrics.parse_args(["collect", "--repo", REPO, "--out", str(out), "--root", folder, "--now", NOW])
            with redirect_stdout(io.StringIO()) as shown:
                code = metrics.collect(args, {"GITHUB_TOKEN": "t"}, opener=opener, sleep=lambda seconds: None)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out.read_text())["counts"], EXPECTED["counts"])
        self.assertIn(f"written over 30 days, in {len(opener.calls)} calls", shown.getvalue())
        # The listing, then 103 (commits, reviews, two commits' runs, the
        # detail), 102 (three), 101 (five), 104 (commits, reviews, the
        # detail), the branches with two claim commits, and the comments.
        self.assertEqual(len(opener.calls), 1 + 5 + 3 + 5 + 3 + 3 + 1)


class ProtocolVersion(unittest.TestCase):
    def test_it_is_the_release_and_seven_hex_digits_which_the_collector_keeps(self):
        with tempfile.TemporaryDirectory() as folder:
            vendored = Path(folder) / "VENDORED"
            vendored.write_text("sdlc-protocol 0.2.0 f530a6694477466c5826a6626681c8c84c8f1aa9\nhash  __init__.py\n")
            self.assertEqual(metrics.protocol_version(vendored), "0.2.0 f530a66")
            for text in ("", "0.2.0 f530a66\n", "sdlc-protocol 0.2.0\n", "something 0.2.0 f530a66\n"):
                vendored.write_text(text)
                self.assertIsNone(metrics.protocol_version(vendored), text)
            self.assertIsNone(metrics.protocol_version(Path(folder) / "missing"))
        for version in ("0.2.0 f530a66", metrics.protocol_version()):
            self.assertTrue(COLLECTOR_VERSION.fullmatch(version), version)
        self.assertIsNone(COLLECTOR_VERSION.fullmatch("0.2.0 f530a6"))


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
        {"user": user("github-actions[bot]", "Bot"), "created_at": "2026-10-01T12:00:00Z", "body": BEHIND},
        {"user": user("github-actions[bot]", "Bot"), "created_at": "2026-10-01T12:30:00Z",
         "body": metrics.board.IDLE_MARKER + "\n" + metrics.board.IDLE_TEXT},
        {"user": user("lisa-secret"), "created_at": "2026-10-01T12:40:00Z",
         "body": metrics.RELEASE_MARKER + "\nReleased: no commit for a day."}],
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
    turn, in claude -p's JSON result, and keeps what it was given, the
    system prompt file's text and the folder's listing among it, both read
    now because the folder is gone once the call returns."""

    def __init__(self, *replies):
        self.replies, self.calls, self.prompts, self.folders = list(replies), [], [], []

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        self.prompts.append(Path(command[command.index("--system-prompt-file") + 1]).read_text(encoding="utf-8"))
        self.folders.append(sorted(os.listdir(kwargs["cwd"])))
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        body = {"type": "result", "subtype": "success", "is_error": False, "result": reply}
        return subprocess.CompletedProcess(command, 0, json.dumps(body), "")


def refuse_every_call(*args, **kwargs):
    raise AssertionError(f"called: {args}")


def found(name):
    return f"/usr/bin/{name}"


def origin_at(url):
    """A git whose origin has this URL, and which refuses every other
    call: the origin check must cost nothing else."""
    def git(*args, input=None):
        if args[:2] == ("remote", "get-url"):
            return url + "\n"
        raise AssertionError(f"git called: {args}")
    return git


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
        self.assertIn("B -> all: (review: approved)", shown)
        for login in ("mona-secret", "lisa-secret", "github-actions"):
            self.assertNotIn(login, shown)
        record = json.loads(shown.split("(its counts are the model's to fill) ---\n", 1)[1])
        self.assertEqual(record["conversations"], 1)
        self.assertEqual(set(record["counts"].values()), {0})
        self.assertIn(f"--system-prompt-file '<that folder>/{metrics.PROMPT_FILE}'", shown)
        self.assertNotIn("ANTHROPIC_BASE_URL", shown)

    def test_the_protocols_own_comments_stay_out_of_the_conversation(self):
        with tempfile.TemporaryDirectory() as folder:
            _, _, shown, _ = run_judge(folder, FakeGh(), refuse_every_call, ["--dry-run", "--repo", REPO])
        self.assertIn("Conversation of a pull request: 4 messages", shown)
        for left_out in ("sdlc-board: main-moved", "sdlc-board: idle", metrics.board.IDLE_TEXT,
                         metrics.RELEASE_MARKER, "Released: no commit"):
            self.assertNotIn(left_out, shown, left_out)
        self.assertIn("B -> all: Sounds good", shown)

    def test_a_dry_run_names_a_base_url_it_drops(self):
        with tempfile.TemporaryDirectory() as folder:
            _, _, shown, _ = run_judge(folder, FakeGh(), refuse_every_call, ["--dry-run", "--repo", REPO],
                                       environ={"ANTHROPIC_BASE_URL": "https://gateway.example.invalid"})
        self.assertIn("ANTHROPIC_BASE_URL is set here and is dropped", shown)
        self.assertNotIn("gateway.example.invalid", shown)

    def test_it_refuses_while_an_api_key_is_set_and_calls_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            code, out, _, said = run_judge(folder, refuse_every_call, refuse_every_call,
                                           environ={"ANTHROPIC_API_KEY": "set"})
            self.assertFalse(out.exists())
        self.assertEqual(code, 1)
        self.assertIn("unset ANTHROPIC_API_KEY", said)

    def test_it_refuses_while_another_way_of_billing_is_set_and_calls_nothing(self):
        for name in ("ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX",
                     "CLAUDE_CODE_USE_FOUNDRY"):
            with tempfile.TemporaryDirectory() as folder:
                code, out, _, said = run_judge(folder, refuse_every_call, refuse_every_call, environ={name: "1"})
                self.assertFalse(out.exists(), name)
            self.assertEqual(code, 1, name)
            self.assertIn(f"{name} is set", said)
            self.assertIn(f"unset {name}", said)
            self.assertIn("never does", said)

    def test_a_base_url_alone_is_dropped_not_refused(self):
        self.assertIsNone(metrics.judge_refusal({"ANTHROPIC_BASE_URL": "https://gateway.example.invalid"}, found))
        kept = metrics.judge_environment({name: "set" for name in metrics.DROPPED_VARIABLES} | {"HOME": "/h"})
        self.assertEqual(kept, {"HOME": "/h"})

    def test_a_model_is_a_plain_name_of_the_shape_the_collector_keeps(self):
        for name in ("claude-sonnet-5-5", "opus", "claude-opus-4-1-20250805", "claude-sonnet-4-5[1m]", "a.b_c"):
            self.assertEqual(metrics.parse_args(["judge", "--model", name]).model, name, name)
        for name in ("arn:aws:bedrock:us-east-1:123456789012:inference-profile/x", "a/b", "-x", "", "x" * 65,
                     "sonnet [1m]", "sonnet[1M]"):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit, msg=name):
                metrics.parse_args(["judge", "--model", name])

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
        self.assertEqual(command[:4], [found("claude"), "-p", "--output-format", "json"])
        self.assertNotIn("--system-prompt", command)
        self.assertEqual(claude.prompts, [metrics.APPF_PROMPT])
        self.assertEqual(claude.folders, [[metrics.PROMPT_FILE]])
        self.assertEqual(command[command.index("--tools") + 1], "")
        self.assertEqual(command[command.index("--setting-sources") + 1], "")
        self.assertIn("A -> all: (description)", kwargs["input"])
        self.assertNotIn("lisa-secret", kwargs["input"])
        self.assertNotEqual(Path(kwargs["cwd"]).resolve(), ROOT)
        self.assertNotIn("ANTHROPIC_API_KEY", kwargs["env"])

    def test_nothing_that_bills_or_redirects_reaches_claude(self):
        claude = FakeClaude('{"codes": []}')
        shell = {name: "set" for name in metrics.DROPPED_VARIABLES} | {"HOME": "/home/maintainer"}
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(os.environ, shell):
            run_judge(folder, FakeGh(), claude, ["--repo", REPO])
        _, kwargs = claude.calls[0]
        self.assertEqual(kwargs["env"]["HOME"], "/home/maintainer")
        for name in metrics.DROPPED_VARIABLES:
            self.assertNotIn(name, kwargs["env"])

    def test_claudes_own_reason_is_shown_when_it_fails(self):
        body = {"type": "result", "subtype": "success", "is_error": True, "result": "Not logged in. Please run /login"}
        done = subprocess.CompletedProcess(["claude"], 0, json.dumps(body), "")
        with self.assertRaises(metrics.JudgeError) as caught:
            metrics.claude_result(done)
        self.assertIn("claude failed (success; Not logged in. Please run /login); nothing is written",
                      str(caught.exception))
        body = {"type": "result", "subtype": "error_during_execution", "is_error": True, "errors": ["usage limit"]}
        done = subprocess.CompletedProcess(["claude"], 1, json.dumps(body), "a line on stderr\n")
        with self.assertRaises(metrics.JudgeError) as caught:
            metrics.claude_result(done)
        self.assertIn("error_during_execution; usage limit; a line on stderr", str(caught.exception))

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


def seeded_origin(folder, files, name="origin.git"):
    """A bare origin whose branch metrics is one commit holding files."""
    origin, seed = Path(folder) / name, Path(folder) / "seed"
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


# The judged repository's bare origin, at a path whose last two parts
# name it, as a remote URL's do.
ORIGIN_NAME = REPO + ".git"


def run_push(folder, gh, extra=(), git=refuse_every_call):
    args = metrics.parse_args(["push", "--out", str(Path(folder) / "JUDGE.json"), *extra])
    shown, said = io.StringIO(), io.StringIO()
    with redirect_stderr(said), mock.patch.dict(os.environ, GIT_ENV):
        code = metrics.push(args, metrics.Gh(run=gh), git=git, out=shown)
    return code, shown.getvalue(), said.getvalue()


class JudgeOrigin(unittest.TestCase):
    """--push and push go to origin, which must be the repository judged."""

    def test_a_remote_url_names_its_repository_in_every_form(self):
        for url in ("https://github.com/octo/widgets.git", "https://github.com/octo/widgets",
                    "https://mona@github.com/octo/widgets.git/", "git@github.com:octo/widgets.git",
                    "git@github.com:octo/widgets", "ssh://git@github.com/octo/widgets.git",
                    "ssh://git@github.com:22/octo/widgets.git", "/srv/git/octo/widgets.git"):
            self.assertEqual(metrics.repository_of(url), "octo/widgets", url)
        self.assertIsNone(metrics.repository_of(""))
        self.assertIsNone(metrics.repository_of("widgets"))
        self.assertIsNone(metrics.origin_refusal(origin_at("git@github.com:Octo/Widgets.git"), REPO))

    def test_judge_push_refuses_another_repositorys_clone_before_reading_anything(self):
        gh = FakeGh()
        with tempfile.TemporaryDirectory() as folder:
            code, out, _, said = run_judge(folder, gh, refuse_every_call, ["--repo", REPO, "--push"],
                                           git=origin_at("https://github.com/acme/other.git"))
            self.assertFalse(out.exists())
        self.assertEqual(code, 1)
        self.assertEqual(gh.calls, [])
        self.assertIn(f"judge: --push refused: the repository judged is {REPO}, but this clone's origin is "
                      "https://github.com/acme/other.git", said)
        self.assertIn(f"Run this in a clone of {REPO}", said)

    def test_judge_push_refuses_a_clone_without_an_origin(self):
        with tempfile.TemporaryDirectory() as folder:
            clone = Path(folder) / "clone"
            git(folder, "init", "--quiet", str(clone))
            code, _, _, said = run_judge(folder, FakeGh(), refuse_every_call, ["--repo", REPO, "--push"],
                                         git=partial(run_in, clone))
        self.assertEqual(code, 1)
        self.assertIn("this clone's origin has no URL", said)

    def test_judge_push_lands_in_the_judged_repositorys_clone(self):
        claude = FakeClaude('{"codes": ["C2"]}')
        with tempfile.TemporaryDirectory() as folder:
            origin, seeded = seeded_origin(folder, {"METRICS.json": '{"schema": "sdlc-metrics/1"}\n'}, ORIGIN_NAME)
            clone = clone_of(folder, origin, "clone")
            with mock.patch.dict(os.environ, GIT_ENV):
                code, out, shown, _ = run_judge(folder, FakeGh(), claude, ["--repo", REPO, "--push"],
                                                git=partial(run_in, clone))
            self.assertEqual(code, 0)
            self.assertIn("judge: pushed to metrics as", shown)
            self.assertEqual(git(origin, "rev-parse", "metrics^"), seeded)
            self.assertEqual(git(origin, "show", "metrics:JUDGE.json") + "\n", out.read_text())
            self.assertEqual(json.loads(out.read_text())["counts"]["C2"], 1)

    def test_push_sends_the_written_file_without_judging_again(self):
        claude = FakeClaude('{"codes": ["C3a"]}')
        with tempfile.TemporaryDirectory() as folder:
            origin, seeded = seeded_origin(folder, {"METRICS.json": '{"schema": "sdlc-metrics/1"}\n'}, ORIGIN_NAME)
            clone = clone_of(folder, origin, "clone")
            _, out, _, _ = run_judge(folder, FakeGh(), claude, ["--repo", REPO])
            code, shown, _ = run_push(folder, refuse_every_call, ["--repo", REPO], git=partial(run_in, clone))
            self.assertEqual(code, 0)
            self.assertIn(f"push: {out} pushed to metrics as", shown)
            self.assertEqual(len(claude.calls), 1)
            self.assertEqual(git(origin, "rev-parse", "metrics^"), seeded)
            self.assertEqual(git(origin, "show", "metrics:JUDGE.json") + "\n", out.read_text())
            self.assertEqual(sorted(tree_of(origin, "metrics")), ["JUDGE.json", "METRICS.json"])

    def test_push_asks_gh_for_the_repository_only_without_repo(self):
        gh = FakeGh()
        with tempfile.TemporaryDirectory() as folder:
            origin, _ = seeded_origin(folder, {"METRICS.json": "{}\n"}, ORIGIN_NAME)
            clone = clone_of(folder, origin, "clone")
            run_judge(folder, FakeGh(), FakeClaude('{"codes": []}'), ["--repo", REPO])
            code, _, _ = run_push(folder, gh, git=partial(run_in, clone))
        self.assertEqual(code, 0)
        self.assertEqual([call[1:3] for call in gh.calls], [["repo", "view"]])

    def test_push_refuses_another_repositorys_clone_and_a_file_the_judge_did_not_write(self):
        with tempfile.TemporaryDirectory() as folder:
            run_judge(folder, FakeGh(), FakeClaude('{"codes": []}'), ["--repo", REPO])
            code, _, said = run_push(folder, refuse_every_call, ["--repo", REPO],
                                     git=origin_at("git@github.com:acme/other.git"))
            self.assertEqual(code, 1)
            self.assertIn(f"push: refused: the repository judged is {REPO}, but this clone's origin is "
                          "git@github.com:acme/other.git", said)
            path = Path(folder) / "JUDGE.json"
            for text in ('{"schema": "sdlc-judge/1"}\n', "not json", json.dumps(dict(
                    json.loads(path.read_text()), repository=REPO))):
                path.write_text(text)
                with self.assertRaises(metrics.JudgeError, msg=text) as caught:
                    run_push(folder, refuse_every_call, ["--repo", REPO])
                self.assertIn("not a JUDGE.json the judge wrote", str(caught.exception))
            path.unlink()
            with self.assertRaises(metrics.JudgeError):
                run_push(folder, refuse_every_call, ["--repo", REPO])


def refusing_push(clone):
    """A git on the clone whose every push is refused."""
    real = partial(run_in, clone)

    def git(*args, input=None):
        if args[0] == "push":
            raise metrics.JudgeError("push: refused by the test")
        return real(*args, input=input)
    return git


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
            self.assertRegex(git(origin, "log", "-1", "--format=%s", "metrics"),
                             r"^Judge counts as of \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ \[skip ci\]$")

    def test_after_two_refusals_it_names_the_push_that_judges_nothing_again(self):
        with tempfile.TemporaryDirectory() as folder:
            origin, _ = seeded_origin(folder, {"METRICS.json": "{}\n"})
            clone = clone_of(folder, origin, "clone")
            path = Path(folder) / "JUDGE.json"
            path.write_text('{"schema": "sdlc-judge/1"}\n')
            with mock.patch.dict(os.environ, GIT_ENV), self.assertRaises(metrics.JudgeError) as caught:
                metrics.push_judge(path, refusing_push(clone))
            self.assertIn("refused twice, the last time with: push: refused by the test", str(caught.exception))
            self.assertIn(f"push it alone with `python3 tools/metrics.py push --out {path}`", str(caught.exception))

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

    def step(self, folder, origin, record, extra_env=None):
        work = clone_of(folder, origin, "work")
        (work / "tools").symlink_to(ROOT / "tools")
        temp = Path(folder) / "runner"
        temp.mkdir()
        (temp / "METRICS.json").write_text(json.dumps(record, indent=2) + "\n")
        env = {**os.environ, **GIT_ENV, "RUNNER_TEMP": str(temp), **(extra_env or {})}
        return subprocess.run(["bash", "-e", "-c", run_block(step_lines(WRITE_STEP))], cwd=work, env=env,
                              capture_output=True, text=True)

    def run_step(self, folder, origin, record, extra_env=None):
        done = self.step(folder, origin, record, extra_env)
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

    def test_a_branch_metrics_the_project_had_before_is_left_as_it_is(self):
        # A branch metrics of the project's own holds files this workflow
        # never wrote. The lease alone would hold, since the run fetched
        # that very commit, so the run looks at the tree, pushes nothing
        # and fails, without the second attempt a failed lease gets.
        with tempfile.TemporaryDirectory() as folder:
            origin, seeded = seeded_origin(folder, {"METRICS.json": json.dumps(OLD, indent=2) + "\n",
                                                    "JUDGE.json": '{"n": 1}\n', "README.md": "the project's own\n"})
            done = self.step(folder, origin, MOVED)
            self.assertNotEqual(done.returncode, 0)
            self.assertIn("the branch metrics holds files this workflow did not write:\nREADME.md\n", done.stdout)
            self.assertIn("nothing was pushed", done.stdout)
            self.assertIn("Rename it", done.stdout)
            self.assertNotIn("moved during this run", done.stdout)
            self.assertEqual(git(origin, "rev-parse", "metrics"), seeded)

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

    def test_daily_at_an_odd_minute_before_the_collectors_read_and_by_hand(self):
        found = re.search(r'\n  schedule:\n    - cron: "([1-9]|[1-5][0-9]) (\d{1,2}) \* \* \*"\n', self.TEXT)
        self.assertTrue(found, "one daily cron at an odd minute")
        self.assertLess(int(found.group(2)) * 60 + int(found.group(1)), COLLECTOR_READ)
        self.assertIn("\n  workflow_dispatch:\n", self.TEXT)

    def test_a_change_to_the_switch_on_the_default_branch_starts_it_and_a_fork_never_runs_it(self):
        self.assertIn('\non:\n  push:\n    paths: [".github/symphony-metrics", ".github/sdlc-metrics"]\n', self.TEXT)
        folded = self.TEXT.split("    if: >-\n", 1)[1].split("\n    runs-on:", 1)[0]
        self.assertEqual(" ".join(line.strip() for line in folded.splitlines()),
                         "github.event.repository.is_template == false "
                         "&& (github.event_name != 'push' || github.ref_name == github.event.repository.default_branch) "
                         "&& github.event.repository.fork == false")

    def test_its_permissions_are_these_four(self):
        block = self.TEXT.split("\npermissions:\n", 1)[1].split("\n\n", 1)[0]
        self.assertEqual(block.splitlines(), ["  contents: write", "  pull-requests: read", "  issues: read",
                                              "  checks: read"])

    def test_it_skips_the_template_and_a_pending_copy(self):
        self.assertIn("    if: >-\n      github.event.repository.is_template == false\n", self.TEXT)
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
                       "unset ANTHROPIC_API_KEY", metrics.RELEASE_MARKER, metrics.PUSH_COMMAND, "[skip ci]",
                       *metrics.BILLING_VARIABLES, "ANTHROPIC_BASE_URL"):
            self.assertIn(needed, self.TEXT)

    def test_it_says_how_runs_and_people_are_counted_and_what_the_reserve_is(self):
        for needed in ("filter=all", f"fewer than {metrics.RESERVE} for the board", "shows as dismissed",
                       "reply in a review thread by anyone else", "dated by their own act"):
            self.assertIn(needed, self.TEXT)


if __name__ == "__main__":
    unittest.main()
