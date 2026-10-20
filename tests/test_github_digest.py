"""tools/github_digest.py: the digest posts only when something is new,
names titles so nobody is pinged, and a reply from the recipient, and from
nobody else, does what its lines ask."""

import datetime
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import github_digest as gd  # noqa: E402

BOT = {"login": "github-actions[bot]"}
DECISION = {"number": 12, "title": "Next step: @someone #3 train", "state": "open", "labels": [{"name": "decision"}],
            "body": "## Options\n- **Accept**: do it\n- **Decline**: skip it\nRecommended: Accept\n"}
DIGEST = {"number": 40, "state": "open", "user": BOT, "labels": [{"name": "digest"}],
          "body": gd.ISSUE_MARKER + "\nThe digest."}
DONE = {"number": 7, "title": "Fix the board", "state": "closed", "state_reason": "completed",
        "closed_at": "2026-10-20T10:00:00Z"}


class FakeGitHub:
    def __init__(self, lists):
        self.lists, self.calls = lists, []

    def list(self, path):
        for prefix, items in self.lists.items():
            if path.startswith(prefix):
                return items
        return []

    def api(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        return {"number": 99} if (method, path) == ("POST", "issues") else {}


def world(comments=(), closed=(DONE,)):
    return FakeGitHub({"issues?state=open&labels=digest": [DIGEST], "issues/40/comments": list(comments),
                       "issues?state=open&labels=decision": [DECISION], "issues?state=open&labels=proposed": [],
                       "issues?state=closed": list(closed), "labels": [{"name": "digest"}]})


NOW = datetime.datetime(2026, 10, 20, 13, 17, tzinfo=datetime.timezone.utc)


class Post(unittest.TestCase):
    def test_posts_done_and_decisions_with_the_mention(self):
        github = world()
        self.assertIn("posted to #40", gd.post(github, "greg", NOW))
        method, path, payload = github.calls[-1]
        self.assertEqual((method, path), ("POST", "issues/40/comments"))
        self.assertIn("@greg, here is your Symphony digest.", payload["body"])
        self.assertIn("decisions=12 -->", payload["body"])
        self.assertIn("- #12 `Next step: @someone #3 train`", payload["body"])

    def test_nothing_new_posts_nothing(self):
        earlier = {"user": BOT, "created_at": "2026-10-20T11:00:00Z",
                   "body": "<!-- symphony-digest: symphony-digest-202610191317 decisions=12 -->"}
        github = world([earlier])
        self.assertIn("nothing posted", gd.post(github, "greg", NOW))
        self.assertEqual(github.calls, [])

    def test_a_marker_someone_else_wrote_is_not_the_last_digest(self):
        forged = {"user": {"login": "mallory"}, "created_at": "2026-10-20T11:00:00Z",
                  "body": "<!-- symphony-digest: symphony-digest-202610191317 decisions=12 -->"}
        self.assertEqual(gd.last_digest([forged]), (None, set()))

    def test_opens_the_digest_issue_when_there_is_none(self):
        github = world()
        github.lists["issues?state=open&labels=digest"] = []
        gd.post(github, "greg", NOW)
        self.assertEqual(github.calls[0][:2], ("POST", "issues"))
        self.assertEqual(github.calls[-1][1], "issues/99/comments")


class Answer(unittest.TestCase):
    def comment(self, body, login="greg", association="OWNER", issue=40):
        return {"body": body, "user": {"login": login}, "author_association": association,
                "issue_url": f"https://api.github.com/repos/o/r/issues/{issue}"}

    def test_a_reply_line_chooses_and_the_rest_becomes_a_task(self):
        github = world()
        reply = "12 accept\nAlso add the spine dataset as a goal.\n\nOn Mon, Oct 20, 2026 GitHub wrote:\n> old"
        gd.answer(github, "greg", self.comment(reply), "main")
        posted = [(m, p) for m, p, _ in github.calls]
        self.assertIn(("POST", "issues/12/comments"), posted)
        self.assertIn(("DELETE", "issues/12/labels/decision"), posted)
        made = [payload for m, p, payload in github.calls if (m, p) == ("POST", "issues")][0]
        self.assertEqual(made["labels"], ["from-email"])
        self.assertEqual(made["title"], "From the digest email: Also add the spine dataset as a goal.")
        self.assertEqual(github.calls[-1][1], "issues/40/comments")

    def test_nobody_else_can_answer(self):
        for comment in (self.comment("12 accept", login="mallory"), self.comment("12 accept", association="NONE"),
                        self.comment("12 accept", issue=41)):
            github = world()
            self.assertIn("nothing done", gd.answer(github, "greg", comment, "main"))
            self.assertEqual(github.calls, [])

    def test_accepting_a_project_starts_the_organizers_accept(self):
        github = world()
        github.lists["issues?state=open&labels=proposed"] = [
            {"number": 5, "title": "Spine papers", "state": "open", "labels": [{"name": "epic"}, {"name": "proposed"}]}]
        gd.answer(github, "greg", self.comment("5 Accept"), "main")
        self.assertIn(("POST", "actions/workflows/drive-organize.yml/dispatches",
                       {"ref": "main", "inputs": {"step": "accept", "epic": "5"}}), github.calls)


class Mistakes(unittest.TestCase):
    def comment(self, body):
        return {"body": body, "user": {"login": "greg"}, "author_association": "OWNER",
                "issue_url": "https://api.github.com/repos/o/r/issues/40"}

    def test_a_stale_or_misspelled_answer_is_refused_not_a_task(self):
        for line in ("13 Accept", "12 Maybe"):
            github = world()
            gd.answer(github, "greg", self.comment(line), "main")
            self.assertNotIn("issues", [p for m, p, _ in github.calls if m == "POST"])
            self.assertIn("not done:", github.calls[-1][2]["body"])

    def test_one_failure_stops_none_of_the_others_and_is_said(self):
        github = world()
        real = github.api

        def failing(method, path, payload=None):
            if path == "issues/12/comments":
                raise gd.DigestError("HTTP 500")
            return real(method, path, payload)
        github.api = failing
        with self.assertRaises(gd.DigestError):
            gd.answer(github, "greg", self.comment("12 Accept\nA new goal."), "main")
        self.assertIn(("POST", "issues"), [(m, p) for m, p, _ in github.calls])
        self.assertIn("failed: comment", github.calls[-1][2]["body"])

    def test_option_text_pings_nobody(self):
        github = world()
        github.lists["issues?state=open&labels=decision"] = [dict(DECISION, body=DECISION["body"].replace("do it", "tell @team"))]
        gd.post(github, "greg", NOW)
        self.assertIn("`tell @team`", github.calls[-1][2]["body"])


class Recipient(unittest.TestCase):
    def test_codeowners_first_user_then_a_users_owner(self):
        self.assertEqual(gd.recipient("# comment\n* @greg @other\n", "org", "Organization"), "greg")
        self.assertEqual(gd.recipient("* @{{" + "CODE_OWNER}}\n", "greg", "User"), "greg")
        self.assertIsNone(gd.recipient("* @org/team\n", "org", "Organization"))

    def test_an_organizations_repository_falls_back_to_the_runs_actor_never_a_bot(self):
        self.assertEqual(gd.recipient("* @org/team\n", "org", "Organization", "greg"), "greg")
        self.assertIsNone(gd.recipient("", "org", "Organization", "github-actions[bot]"))

    def test_an_answer_is_checked_against_the_login_the_digest_named(self):
        digest = {"user": BOT, "body": "<!-- symphony-digest: symphony-digest-202610201317 decisions=12 -->\n"
                                       "@greg, here is your Symphony digest.\n"}
        github = world([digest])
        comment = {"body": "12 Accept", "user": {"login": "greg"}, "author_association": "MEMBER",
                   "issue_url": "https://api.github.com/repos/o/r/issues/40"}
        gd.answer(github, None, comment, "main")
        self.assertIn(("DELETE", "issues/12/labels/decision"), [(m, p) for m, p, _ in github.calls])
        other = dict(comment, user={"login": "mallory"})
        github = world([digest])
        self.assertIn("nothing done", gd.answer(github, None, other, "main"))


if __name__ == "__main__":
    unittest.main()
