"""The board renders the same bytes for the same snapshot and speaks only to
the pull requests the rules name. No network: the fixture stands in for the
API, and a fake opener stands in for urllib where the client is tested."""

import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import board  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "board.json"

# A claim file in the shape docs/agents/claims/README.md gives.
CLAIM_TEXT = "\n".join([
    "# Claim: #16",
    "",
    "- Issue: https://github.com/octo/widgets/issues/16",
    "- Account: main",
    "- Branch: claude/16",
    "",
    "## Plan",
    "",
    "Two sentences on what changes.",
    "",
    "## Files to touch",
    "",
    "- docs/b.md",
    "- `docs/a.md`",
    "",
])


def snapshot():
    return board.load_fixture(FIXTURE)


class Rendering(unittest.TestCase):
    def setUp(self):
        self.text = board.render(snapshot())

    def test_same_input_renders_the_same_bytes(self):
        self.assertEqual(board.render(snapshot()).encode(), self.text.encode())

    def test_the_layout(self):
        lines = self.text.splitlines()
        self.assertEqual(lines[0], "# Board")
        self.assertEqual(lines[2], "As of commit 0123abc on main. Rewritten by .github/workflows/board.yml; do not edit by hand.")
        for heading in (board.CLAIM_HEADING, board.PULL_HEADING, board.QUEUE_HEADING, board.BLOCKER_HEADING, board.MERGED_HEADING):
            self.assertIn(heading, lines)
        self.assertIn("| Issue | Branch | Account | PR | Files it touches |", lines)
        self.assertIn("| PR | Title | Branch | State (clean, behind, conflicting, blocked, unknown) | Last update |", lines)
        self.assertIn("| Issue | Title | Labels |", lines)
        self.assertTrue(self.text.endswith("|\n"))
        self.assertNotIn("\n\n\n", self.text)

    def test_claims_name_the_account_or_the_missing_file(self):
        self.assertIn("| #12 | claude/12 | main | #40 | docs/agents/README.md, docs/agents/STATE.md |", self.text)
        self.assertIn("| #13 | claude/13 | no claim file yet | #41 | .claude/skills/remember/SKILL.md |", self.text)
        self.assertNotIn("| main |", self.text.split(board.PULL_HEADING)[0].split("| #12")[0])

    def test_a_claim_whose_issue_is_closed_says_so_and_asks_for_the_branch_to_go(self):
        snap = snapshot()
        snap["branches"].append("claude/3")
        snap["claim_issues"] = {"3": {"state": "closed", "labels": ["account:main", "claimed", "todo"]}}
        self.assertIn("| #3 | claude/3 | main | issue closed | delete the branch |", board.render(snap))

    def test_a_released_claim_file_takes_the_account_from_the_issue_label(self):
        snap = snapshot()
        snap["claim_issues"] = {"13": {"state": "open", "labels": ["account:second", "claimed"]}}
        self.assertIn("| #13 | claude/13 | second | #41 | .claude/skills/remember/SKILL.md |", board.render(snap))

    def test_merged_rows_come_newest_first(self):
        snap = snapshot()
        snap["merged"] = [
            {"number": 30, "title": "Older", "head": {"ref": "claude/30"}, "merged_at": "2026-09-20T10:00:00Z"},
            {"number": 29, "title": "Newer", "head": {"ref": "claude/29"}, "merged_at": "2026-09-21T10:00:00Z"},
        ]
        text = board.render(snap)
        self.assertLess(text.index("| #29 |"), text.index("| #30 |"))

    def test_a_claim_without_a_pull_request_shows_the_files_it_names(self):
        snap = snapshot()
        snap["branches"].append("claude/16")
        snap["claims"]["16"] = CLAIM_TEXT
        snap["branches"].append("claude/17")
        snap["claims"]["17"] = CLAIM_TEXT.replace("## Files to touch\n\n- docs/b.md\n- `docs/a.md`\n", "")
        text = board.render(snap)
        self.assertIn("| #16 | claude/16 | main | (no pull request yet) | docs/a.md, docs/b.md |", text)
        self.assertIn("| #17 | claude/17 | main | (no pull request yet) | - |", text)

    def test_pull_rows_carry_the_state_word_and_the_escaped_title(self):
        self.assertIn("| #40 | Describe the board \\| its tables | claude/12 | behind | 2026-09-18T12:00:00Z |", self.text)
        self.assertIn("| #41 | Add the remember skill | claude/13 | clean | 2026-09-22T08:00:00Z |", self.text)

    def test_queue_and_blockers(self):
        queue = self.text.split(board.QUEUE_HEADING)[1].split(board.BLOCKER_HEADING)[0]
        self.assertIn("| #14 | Write the release notes | todo |", queue)
        self.assertNotIn("#15", queue)
        blockers = self.text.split(board.BLOCKER_HEADING)[1].split(board.MERGED_HEADING)[0]
        self.assertIn("| #15 | CI is red on every branch | blocker |", blockers)

    def test_merged_section(self):
        self.assertIn("| #39 | Seed the memory index | claude/11 | 2026-09-17T16:45:00Z |", self.text)

    def test_no_wall_clock_value(self):
        now = datetime.now(timezone.utc)
        for stamp in (now.strftime("%Y-%m-%dT%H"), now.strftime("%d %B %Y"), now.strftime("%Y-%m-%d ")):
            self.assertNotIn(stamp, self.text)

    def test_the_file_is_ascii_with_lf(self):
        self.text.encode("ascii")
        self.assertNotIn("\r", self.text)

    def test_an_empty_snapshot_keeps_every_table(self):
        text = board.render({"sha": "", "default_branch": "main", "issues": [], "pulls": [], "branches": [], "claims": {}, "merged": []})
        self.assertIn("As of commit unknown on main.", text)
        self.assertEqual(text.count("| (none) |"), 5)

    def test_the_intro_line_is_folded_to_ascii_too(self):
        snap = snapshot()
        snap["default_branch"] = "tr\u00fcnk"
        snap["sha"] = "\u00e9123abcdef"
        text = board.render(snap)
        self.assertIn("As of commit e123abc on trunk.", text)
        text.encode("ascii")

    def test_rows_sort_by_number_not_by_string(self):
        snap = snapshot()
        snap["pulls"].append({"number": 9, "title": "Nine", "head": {"ref": "claude/9"}, "mergeable_state": "clean", "updated_at": "2026-09-01T00:00:00Z", "files": []})
        snap["pulls"].append({"number": 100, "title": "Hundred", "head": {"ref": "claude/100"}, "mergeable_state": "clean", "updated_at": "2026-09-01T00:00:00Z", "files": []})
        pulls = board.render(snap).split(board.PULL_HEADING)[1].split(board.QUEUE_HEADING)[0]
        self.assertLess(pulls.index("| #9 |"), pulls.index("| #40 |"))
        self.assertLess(pulls.index("| #41 |"), pulls.index("| #100 |"))

    def test_a_non_ascii_title_is_folded(self):
        self.assertEqual(board.cell("caf\u00e9 \u2014 \u201cquoted\u201d"), "cafe  quoted")

    def test_a_claimed_todo_leaves_the_queue(self):
        snap = snapshot()
        snap["issues"].append({"number": 12, "title": "Claimed by branch", "labels": [{"name": "todo"}]})
        snap["issues"].append({"number": 16, "title": "Claimed by label", "labels": [{"name": "todo"}, {"name": "claimed"}]})
        queue = board.render(snap).split(board.QUEUE_HEADING)[1].split(board.BLOCKER_HEADING)[0]
        self.assertNotIn("#12", queue)
        self.assertNotIn("#16", queue)
        self.assertIn("#14", queue)


class Rules(unittest.TestCase):
    def test_state_words(self):
        cases = (
            ("clean", "clean"), ("behind", "behind"), ("has_hooks", "clean"), ("unstable", "clean"),
            ("dirty", "conflicting"), ("blocked", "blocked"), ("unknown", "unknown"), ("draft", "unknown"), (None, "unknown"),
        )
        for given, word in cases:
            self.assertEqual(board.pr_state({"mergeable_state": given}), word, given)

    def test_main_moved_picks_behind_and_dirty_only(self):
        pulls = [
            {"number": 1, "mergeable_state": "behind"},
            {"number": 2, "mergeable_state": "dirty"},
            {"number": 3, "mergeable_state": "clean"},
            {"number": 4, "mergeable_state": "unknown"},
            {"number": 5, "mergeable_state": "blocked"},
            {"number": 6, "mergeable_state": "unstable"},
        ]
        picked = [p["number"] for p in board.pulls_behind_main(pulls)]
        self.assertEqual(picked, [1, 2])

    def test_main_moved_text_and_marker(self):
        self.assertEqual(
            board.main_moved_text("behind", "main", "0123abc"),
            "main moved: this branch is behind main at 0123abc; rebase or merge main before the next push.",
        )
        self.assertEqual(
            board.main_moved_text("conflicting", "main", "0123abc"),
            "main moved: this branch is conflicting with main at 0123abc; rebase or merge main before the next push.",
        )
        self.assertEqual(board.MAIN_MOVED_MARKER.format(sha="0123abc"), "<!-- sdlc-board: main-moved 0123abc -->")

    def test_idle_picks_pulls_older_than_a_day(self):
        now = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)
        pulls = [
            {"number": 1, "updated_at": "2026-09-22T11:00:00Z"},
            {"number": 2, "updated_at": "2026-09-22T13:00:00Z"},
            {"number": 3, "updated_at": (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")},
        ]
        self.assertEqual([p["number"] for p in board.idle_pulls(pulls, now)], [1])

    def test_claim_account_spellings(self):
        spellings = (
            "Account: main",
            "- Account: main",
            "**Account**: main",
            "- **Account:** `main`",
            "- Account: main (label account:main)",
            "- **Account:** `main` (the label account:main)",
        )
        for text in spellings:
            self.assertEqual(board.claim_account(text + "\nPlan: x\n"), "main", text)
        self.assertEqual(board.claim_account("Plan: nothing named\n"), "unnamed")
        self.assertEqual(board.claim_account(CLAIM_TEXT), "main")

    def test_claim_files_reads_the_list_under_its_heading_only(self):
        self.assertEqual(board.claim_files(CLAIM_TEXT), ["docs/a.md", "docs/b.md"])
        self.assertEqual(board.claim_files("- Account: main\n- Branch: claude/1\n"), [])
        two_lists = "## Files to touch\n\n- x.md\n\n## Notes\n\n- not a file\n"
        self.assertEqual(board.claim_files(two_lists), ["x.md"])

    def test_parse_time(self):
        self.assertEqual(board.parse_time("2026-09-22T08:00:00Z"), datetime(2026, 9, 22, 8, tzinfo=timezone.utc))
        self.assertEqual(board.parse_time("2026-09-22T10:00:00+02:00"), datetime(2026, 9, 22, 8, tzinfo=timezone.utc))

    def test_next_link(self):
        headers = {"Link": '<https://api.github.com/repos/o/r/issues?page=2>; rel="next", <https://api.github.com/repos/o/r/issues?page=3>; rel="last"'}
        self.assertEqual(board.next_link(headers), "https://api.github.com/repos/o/r/issues?page=2")
        self.assertIsNone(board.next_link({"Link": '<https://x/>; rel="last"'}))
        self.assertIsNone(board.next_link({}))
        self.assertIsNone(board.next_link(None))


class FakeAnswer:
    def __init__(self, body, headers=None):
        self.body = json.dumps(body).encode()
        self.headers = headers or {}

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakeOpener:
    """Answers by path and query, and remembers every request."""

    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def open(self, call, timeout=None):
        self.calls.append(call)
        key = call.full_url.replace(board.API, "")
        if key not in self.answers:
            import urllib.error
            raise urllib.error.HTTPError(call.full_url, 404, "Not Found", {}, io.BytesIO(b""))
        return self.answers[key]


def closed_pull(number, updated_at, merged_at):
    return {"number": number, "title": f"PR {number}", "head": {"ref": f"claude/{number}"}, "updated_at": updated_at, "merged_at": merged_at}


CLOSED_FIRST = "/repos/o/r/pulls?state=closed&sort=updated&direction=desc&per_page=100"
CLOSED_SECOND = CLOSED_FIRST + "&page=2"


class Client(unittest.TestCase):
    def test_pages_by_the_link_header_and_sends_the_headers(self):
        first = "/repos/o/r/issues?state=open&per_page=100"
        second = "/repos/o/r/issues?state=open&per_page=100&page=2"
        opener = FakeOpener({
            first: FakeAnswer([{"number": 1}], {"Link": f'<{board.API}{second}>; rel="next"'}),
            second: FakeAnswer([{"number": 2}]),
        })
        api = board.GitHub("secret-token", "o/r", opener=opener, sleep=lambda s: None)
        items = api.get_all("/repos/o/r/issues", {"state": "open"})
        self.assertEqual([i["number"] for i in items], [1, 2])
        self.assertEqual(len(opener.calls), 2)
        sent = opener.calls[0]
        self.assertEqual(sent.get_header("Authorization"), "Bearer secret-token")
        self.assertEqual(sent.get_header("Accept"), "application/vnd.github+json")
        self.assertEqual(sent.get_header("X-github-api-version"), "2022-11-28")
        self.assertEqual(sent.get_header("User-agent"), "sdlc-board")

    def test_a_missing_claim_file_is_none_and_an_error_never_names_the_token(self):
        api = board.GitHub("secret-token", "o/r", opener=FakeOpener({}), sleep=lambda s: None)
        self.assertIsNone(board.claim_text(api, "claude/12"))
        with self.assertRaises(board.BoardError) as caught:
            api.get("/repos/o/r/pulls/1")
        self.assertEqual(str(caught.exception), "GET /repos/o/r/pulls/1: HTTP 404")
        self.assertNotIn("secret-token", str(caught.exception))

    def test_mergeable_is_asked_once_more_then_unknown(self):
        detail = "/repos/o/r/pulls/7"
        opener = FakeOpener({
            detail: FakeAnswer({"number": 7, "mergeable": None, "mergeable_state": "unknown", "head": {"ref": "claude/7"}}),
            detail + "/files?per_page=100": FakeAnswer([{"filename": "a.md"}]),
        })
        waits = []
        api = board.GitHub("t", "o/r", opener=opener, sleep=waits.append)
        pull = board.pull_with_detail(api, 7)
        self.assertEqual(waits, [board.MERGEABLE_RETRY_SECONDS])
        self.assertEqual(pull["mergeable_state"], "unknown")
        self.assertEqual(pull["files"], ["a.md"])

    def test_comment_once_posts_only_without_the_marker(self):
        comments = "/repos/o/r/issues/40/comments?per_page=100"
        opener = FakeOpener({comments: FakeAnswer([{"body": board.IDLE_MARKER + "\nidle"}])})
        api = board.GitHub("t", "o/r", opener=opener)
        self.assertFalse(board.comment_once(api, 40, board.IDLE_MARKER, board.IDLE_TEXT))
        self.assertEqual(len(opener.calls), 1)

    def test_recent_merged_takes_the_five_merged_last_from_the_first_page(self):
        page = [closed_pull(n, "2026-09-22T10:00:00Z", f"2026-09-{n:02d}T10:00:00Z") for n in range(1, 9)]
        page.append(closed_pull(9, "2026-09-23T10:00:00Z", None))
        opener = FakeOpener({
            CLOSED_FIRST: FakeAnswer(page, {"Link": f'<{board.API}{CLOSED_SECOND}>; rel="next"'}),
        })
        api = board.GitHub("t", "o/r", opener=opener)
        merged = board.recent_merged(api)
        self.assertEqual([p["number"] for p in merged], [8, 7, 6, 5, 4])
        self.assertEqual(len(opener.calls), 1)

    def test_recent_merged_is_the_same_list_each_time_it_is_asked(self):
        # A merge fires two runs; the list depends on the repository alone, so
        # the second run reports the same merge the first did.
        page = [closed_pull(50, "2026-09-22T10:00:00Z", "2026-09-22T10:00:00Z")]
        opener = FakeOpener({CLOSED_FIRST: FakeAnswer(page)})
        api = board.GitHub("t", "o/r", opener=opener)
        self.assertEqual(board.recent_merged(api), board.recent_merged(api))
        self.assertEqual([p["number"] for p in board.recent_merged(api)], [50])

    def test_recent_merged_with_no_closed_pull_requests_is_empty(self):
        opener = FakeOpener({CLOSED_FIRST: FakeAnswer([])})
        api = board.GitHub("t", "o/r", opener=opener)
        self.assertEqual(board.recent_merged(api), [])

    def test_claim_issues_reads_only_the_issues_the_open_list_lacks(self):
        opener = FakeOpener({
            "/repos/o/r/issues/3": FakeAnswer({"number": 3, "state": "closed", "labels": [{"name": "account:main"}, {"name": "todo"}]}),
        })
        api = board.GitHub("t", "o/r", opener=opener)
        open_issues = [{"number": 14, "state": "open", "labels": [{"name": "todo"}]}]
        found = board.claim_issues(api, ["main", "claude/3", "claude/14", "claude/x"], open_issues)
        self.assertEqual(found, {
            "3": {"state": "closed", "labels": ["account:main", "todo"]},
            "14": {"state": "open", "labels": ["todo"]},
        })
        self.assertEqual(len(opener.calls), 1)


class DryRun(unittest.TestCase):
    def test_writes_the_board_to_out_and_exits_0(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "STATE.md"
            self.assertEqual(board.main(["--dry-run", str(FIXTURE), "--out", str(out)]), 0)
            self.assertEqual(out.read_text(encoding="utf-8"), board.render(snapshot()))
            self.assertEqual(board.main(["--dry-run", str(FIXTURE), "--out", str(out)]), 0)
            self.assertEqual(out.read_text(encoding="utf-8"), board.render(snapshot()))

    def test_prints_to_stdout_without_out(self):
        from contextlib import redirect_stdout
        held = io.StringIO()
        with redirect_stdout(held):
            self.assertEqual(board.main(["--dry-run", str(FIXTURE)]), 0)
        self.assertEqual(held.getvalue(), board.render(snapshot()))

    def test_the_default_out_is_state_md_in_the_current_directory(self):
        self.assertEqual(board.STATE_PATH, Path("STATE.md"))

    def test_live_run_without_a_token_exits_1(self):
        import os
        from contextlib import redirect_stderr
        saved = {k: os.environ.pop(k) for k in ("GITHUB_TOKEN", "GITHUB_REPOSITORY") if k in os.environ}
        held = io.StringIO()
        try:
            with redirect_stderr(held):
                self.assertEqual(board.main(["--render-only", "--out", "/nonexistent/STATE.md"]), 1)
        finally:
            os.environ.update(saved)
        self.assertIn("GITHUB_TOKEN", held.getvalue())


if __name__ == "__main__":
    unittest.main()
