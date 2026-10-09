"""Team mode's clerk decides with no Claude usage, so its decisions are
pinned here against an in-memory GitHub: when the lead plans and when it
integrates, what a member carries or takes, and what seed writes."""

import io
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import team  # noqa: E402
from board import API, BoardError  # noqa: E402

REPO = "octo/widgets"


class FakeGitHub:
    """Just enough of the REST API for team.py, kept in dictionaries."""

    def __init__(self):
        self.repo = REPO
        self.issues, self.branches, self.pulls, self.checks = {}, set(), {}, {}
        self.labels, self.sub_issues = {"todo", "epic"}, []
        self.next_number = 100

    def add_issue(self, number, labels=(), body="", state="open", title="t"):
        self.issues[number] = {"number": number, "id": 9000 + number, "title": title, "body": body,
                               "state": state, "labels": [{"name": n} for n in labels]}
        return self.issues[number]

    def add_pull(self, issue, draft=False, state="clean", conclusion="success"):
        sha = f"sha{issue}"
        self.pulls[f"claude/{issue}"] = {"number": 500 + issue, "draft": draft,
                                         "mergeable_state": state, "head": {"sha": sha}}
        self.checks[sha] = [{"conclusion": conclusion}]

    def url(self, path, params=None):
        return API + path

    def tail(self, path):
        prefix = f"/repos/{REPO}/"
        assert path.startswith(prefix), path
        return path[len(prefix):].split("/")

    def get(self, path, params=None, missing_ok=False):
        parts = self.tail(path)
        if parts[0] == "issues":
            return self.issues[int(parts[1])]
        if parts == ["pulls"]:
            head = params["head"].split(":", 1)[1]
            return [self.pulls[head]] if head in self.pulls else []
        if parts[0] == "pulls":
            return next(p for p in self.pulls.values() if p["number"] == int(parts[1]))
        if parts[0] == "commits":
            return {"check_runs": self.checks.get(parts[1], [])}
        raise AssertionError(path)

    def get_all(self, path, params=None):
        parts = self.tail(path)
        if parts == ["issues"]:
            return [i for i in self.issues.values() if i["state"] == params["state"]]
        if parts == ["branches"]:
            return [{"name": name} for name in sorted(self.branches)]
        raise AssertionError(path)

    def post(self, path, body):
        parts = self.tail(path)
        if parts == ["labels"]:
            if body["name"] in self.labels:
                raise BoardError("POST /labels: HTTP 422")
            self.labels.add(body["name"])
            return {}
        if parts == ["issues"]:
            self.next_number += 1
            return self.add_issue(self.next_number, body["labels"], body["body"], title=body["title"])
        if parts[-1] == "sub_issues":
            self.sub_issues.append((int(parts[1]), body["sub_issue_id"]))
            return {}
        raise AssertionError(path)

    def request(self, method, url, body=None, missing_ok=False):
        assert method == "PATCH"
        self.issues[int(self.tail(url[len(API):])[1])].update(body)
        return {}, {}


class RouteTest(unittest.TestCase):
    def test_a_new_epic_is_planned_once(self):
        api = FakeGitHub()
        api.add_issue(1, ["epic"], body="Build the widget.")
        self.assertEqual(team.route(api, "labeled", 1, "epic"), "plan 1")
        api.issues[1]["body"] += "\n" + team.PLAN_MARKER
        self.assertEqual(team.route(api, "labeled", 1, "epic"), "none")

    def test_other_labels_and_closed_epics_plan_nothing(self):
        api = FakeGitHub()
        api.add_issue(1, ["epic"])
        api.add_issue(2, ["epic"], state="closed")
        self.assertEqual(team.route(api, "labeled", 1, "todo"), "none")
        self.assertEqual(team.route(api, "labeled", 2, "epic"), "none")

    def test_the_last_task_closing_calls_for_integration(self):
        api = FakeGitHub()
        api.add_issue(1, ["epic"], body="spec\n<!-- team:tasks 2 3 -->")
        api.add_issue(2, body="Epic: #1\n\nfirst", state="closed")
        api.add_issue(3, body="Epic: #1\n\nsecond")
        self.assertEqual(team.route(api, "closed", 2), "none")
        api.issues[3]["state"] = "closed"
        self.assertEqual(team.route(api, "closed", 3), "integrate 1")

    def test_a_closed_issue_outside_any_epic_routes_nowhere(self):
        api = FakeGitHub()
        api.add_issue(5, body="no epic here", state="closed")
        self.assertEqual(team.route(api, "closed", 5), "none")


class NextTest(unittest.TestCase):
    def setUp(self):
        self.api = FakeGitHub()
        self.api.add_issue(1, ["epic"])

    def test_a_member_takes_its_own_task_before_the_open_queue(self):
        self.api.add_issue(2, ["todo"])
        self.api.add_issue(3, ["todo", "agent:w1"])
        self.assertEqual(team.next_for(self.api, "w1"), "take 3")
        self.assertEqual(team.next_for(self.api, "w2"), "take 2")

    def test_another_members_task_and_the_epic_are_never_taken(self):
        self.api.add_issue(2, ["todo", "agent:w2"])
        self.assertEqual(team.next_for(self.api, "w1"), "none")

    def test_a_claimed_task_is_not_taken_again(self):
        self.api.add_issue(2, ["todo"])
        self.api.branches.add("claude/2")
        self.assertEqual(team.next_for(self.api, "w1"), "none")

    def test_a_claim_without_a_pull_request_or_in_draft_is_carried(self):
        self.api.add_issue(2, ["claimed", "agent:w1"])
        self.api.branches.add("claude/2")
        self.assertEqual(team.next_for(self.api, "w1"), "carry 2")
        self.api.add_pull(2, draft=True)
        self.assertEqual(team.next_for(self.api, "w1"), "carry 2")

    def test_a_claim_that_fell_behind_or_failed_is_carried(self):
        self.api.add_issue(2, ["claimed", "agent:w1"])
        self.api.branches.add("claude/2")
        self.api.add_pull(2, state="behind")
        self.assertEqual(team.next_for(self.api, "w1"), "carry 2")
        self.api.add_pull(2, state="blocked", conclusion="failure")
        self.assertEqual(team.next_for(self.api, "w1"), "carry 2")

    def test_a_claim_waiting_on_its_checks_or_merge_costs_no_run(self):
        self.api.add_issue(2, ["claimed", "agent:w1"])
        self.api.branches.add("claude/2")
        self.api.add_pull(2, state="blocked", conclusion=None)
        self.assertEqual(team.next_for(self.api, "w1"), "none")
        self.api.add_pull(2, state="clean")
        self.assertEqual(team.next_for(self.api, "w1"), "none")

    def test_a_blocked_task_waits_for_help(self):
        self.api.add_issue(2, ["todo", "agent:w1", "blocked"])
        self.assertEqual(team.next_for(self.api, "w1"), "none")


class SeedTest(unittest.TestCase):
    PLAN = {"plan": "w1 owns the parser, w2 the printer.",
            "tasks": [{"title": "Parser", "owner": "w1", "files": ["src/parse.py"], "body": "Parse it."},
                      {"title": "Printer", "owner": "nobody", "files": [], "body": "Print it."}]}

    def test_seed_opens_owned_tasks_and_writes_the_plan_once(self):
        api = FakeGitHub()
        api.add_issue(1, ["epic"], body="Build the widget.")
        self.assertEqual(team.seed(api, 1, self.PLAN, ["w1", "w2"]), "seeded 101 102")
        parser, printer = api.issues[101], api.issues[102]
        self.assertEqual(team.agent_of(parser), "w1")
        self.assertEqual(team.agent_of(printer), "w2")
        self.assertEqual(team.epic_of(parser), 1)
        self.assertIn("- src/parse.py", parser["body"])
        self.assertEqual(team.task_numbers(api.issues[1]), [101, 102])
        self.assertIn("w1 owns the parser", api.issues[1]["body"])
        self.assertEqual(len(api.sub_issues), 2)
        self.assertEqual(team.seed(api, 1, self.PLAN, ["w1", "w2"]), "already planned")
        self.assertEqual(len(api.issues), 3)

    def test_seeded_tasks_route_to_integration_when_all_close(self):
        api = FakeGitHub()
        api.add_issue(1, ["epic"])
        team.seed(api, 1, self.PLAN, ["w1", "w2"])
        for number in (101, 102):
            api.issues[number]["state"] = "closed"
        self.assertEqual(team.route(api, "closed", 102), "integrate 1")

    def test_a_plan_without_tasks_is_refused(self):
        api = FakeGitHub()
        api.add_issue(1, ["epic"])
        with self.assertRaises(team.TeamError):
            team.seed(api, 1, {"plan": "x", "tasks": []}, ["w1"])


class MembersTest(unittest.TestCase):
    def test_team_members_reads_the_variable(self):
        self.assertEqual(team.team_members('["w1", "w2"]'), ["w1", "w2"])
        for bad in ("w1,w2", '{"w1": 1}', '[""]', "[1]"):
            with self.assertRaises(team.TeamError, msg=bad):
                team.team_members(bad)

    def test_main_needs_a_token(self):
        with mock.patch.dict("os.environ", {}, clear=True), \
             mock.patch.object(sys, "stderr", io.StringIO()):
            self.assertEqual(team.main(["--repo", REPO, "next", "--agent", "w1"]), 1)


if __name__ == "__main__":
    unittest.main()
