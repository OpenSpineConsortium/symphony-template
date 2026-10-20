"""tools/staleness.py: what it cost each pull request that the default
branch moved under it, read from timelines and the check's runs."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import staleness  # noqa: E402


def pull(number, branch, created, merged=None, closed=None, merge_sha="", state="closed"):
    return {"number": number, "state": state, "draft": False, "head": {"ref": branch}, "base": {"ref": "main"},
            "created_at": created, "merged_at": merged, "closed_at": closed or merged, "merge_commit_sha": merge_sha}


def commit(sha, when, parents, message="Work", committer="Claude"):
    return {"event": "committed", "sha": sha, "message": message,
            "committer": {"name": committer, "date": when}, "parents": [{"sha": p} for p in parents]}


def run(sha, created, done, conclusion="success", attempt=1):
    return {"head_sha": sha, "created_at": created, "run_started_at": created, "updated_at": done,
            "conclusion": conclusion, "run_attempt": attempt, "pull_requests": []}


# Two threads at once: #1 lands first, so #2, finished and green, has to
# take main in and run its check again before it lands.
FIRST = pull(1, "claude/thread-a", "2026-10-20T10:00:00Z", "2026-10-20T10:30:00Z", merge_sha="m1")
SECOND = pull(2, "claude/thread-b", "2026-10-20T10:05:00Z", "2026-10-20T11:00:00Z", merge_sha="m2")
SECOND_TIMELINE = [
    commit("b1", "2026-10-20T10:04:00Z", ["m0"]),
    {"event": "ready_for_review", "created_at": "2026-10-20T10:10:00Z"},
    commit("b2", "2026-10-20T10:40:00Z", ["b1", "m1"], "Merge remote-tracking branch 'origin/main' into claude/thread-b"),
    {"event": "merged", "created_at": "2026-10-20T11:00:00Z"},
]
SECOND_RUNS = [
    run("b1", "2026-10-20T10:05:30Z", "2026-10-20T10:20:00Z"),
    run("b2", "2026-10-20T10:40:30Z", "2026-10-20T10:55:00Z", attempt=2),
    # A later pull request on the same branch: not this one's.
    run("b9", "2026-10-21T09:00:00Z", "2026-10-21T09:10:00Z"),
]


class CatchUps(unittest.TestCase):
    def test_merges_of_the_default_branch_read_as_catch_ups(self):
        for message in ("Merge branch 'main' into claude/x", "Merge remote-tracking branch 'origin/main' into claude/x",
                        "Merge main into claude/x"):
            self.assertTrue(staleness.catch_up_message(message, "main"), message)

    def test_a_merge_of_another_branch_is_not_one(self):
        self.assertFalse(staleness.catch_up_message("Merge branch 'claude/other' into claude/x", "main"))
        merge = commit("x", "2026-10-20T10:00:00Z", ["a", "b"], "Merge branch 'claude/other' into claude/x")
        self.assertFalse(staleness.is_catch_up(merge, "main", {"m1"}))

    def test_a_merge_whose_parent_is_a_landing_is_one_whatever_it_says(self):
        merge = commit("x", "2026-10-20T10:00:00Z", ["a", "m1"], "Sync")
        self.assertTrue(staleness.is_catch_up(merge, "main", {"m1"}))


class Record(unittest.TestCase):
    def setUp(self):
        self.moves = staleness.landings([FIRST, SECOND], "main")
        self.record = staleness.pull_record(SECOND, SECOND_TIMELINE, SECOND_RUNS, self.moves, "main")

    def test_counts_the_catch_up_and_the_run_it_cost(self):
        r = self.record
        self.assertEqual((r["catch_ups"], r["check_runs"], r["check_runs_redone"], r["reruns"]), (1, 2, 1, 1))
        self.assertEqual(r["check_seconds_redone"], 870)

    def test_finished_and_green_then_stale_until_it_landed(self):
        r = self.record
        self.assertEqual(r["first_green"], "2026-10-20T10:20:00Z")
        self.assertEqual(r["catch_ups_after_green"], 1)
        self.assertEqual(r["stale_seconds"], 40 * 60)
        self.assertEqual(r["landings_after_green"], 1)

    def test_names_the_landing_that_made_it_stale(self):
        self.assertEqual(self.record["caused_by"], [["b2", [1]]])

    def test_a_head_counts_once_however_many_events_ran_its_check(self):
        runs = SECOND_RUNS + [run("b2", "2026-10-20T10:41:00Z", "2026-10-20T10:56:00Z"),
                              run("b2", "2026-10-20T10:40:10Z", "2026-10-20T10:40:20Z", conclusion="cancelled")]
        r = staleness.pull_record(SECOND, SECOND_TIMELINE, runs, self.moves, "main")
        self.assertEqual((r["check_runs"], r["check_runs_redone"], r["runs_cancelled"]), (2, 1, 1))

    def test_a_green_run_on_an_older_head_is_not_the_finished_work_green(self):
        timeline = SECOND_TIMELINE[:1] + [commit("b3", "2026-10-20T10:15:00Z", ["b1"])] + SECOND_TIMELINE[1:]
        r = staleness.pull_record(SECOND, timeline, SECOND_RUNS, self.moves, "main")
        self.assertEqual(r["first_green"], "2026-10-20T10:55:00Z")
        self.assertEqual(r["catch_ups_after_green"], 0)

    def test_a_branch_that_is_no_claim_is_marked_so(self):
        self.assertFalse(self.record["claim"])
        self.assertTrue(staleness.is_claim("claude/12"))
        self.assertFalse(staleness.is_claim("claude/012"))


class Causes(unittest.TestCase):
    def test_a_catch_up_after_one_matched_by_place_takes_only_what_is_new(self):
        moves = [{"number": n, "sha": f"m{n}", "at": staleness.parse_time(f"2026-10-20T1{n}:00:00Z")} for n in (1, 2, 4)]
        commits = [commit("c0", "2026-10-20T10:30:00Z", ["m1"]),
                   commit("c1", "2026-10-20T12:30:00Z", ["c0", "m2"], "Merge branch 'main' into x"),
                   commit("c2", "2026-10-20T14:30:00Z", ["c1", "z9"], "Merge branch 'main' into x")]
        found = staleness.causes(commits, commits[1:], moves, staleness.parse_time("2026-10-20T10:30:00Z"), 9)
        self.assertEqual(found, [[2], [4]])

    def test_a_catch_up_before_the_pull_request_opened_is_counted(self):
        moves = [{"number": 1, "sha": "m1", "at": staleness.parse_time("2026-10-20T10:00:00Z")}]
        commits = [commit("c0", "2026-10-20T09:00:00Z", ["zz"]),
                   commit("c1", "2026-10-20T10:10:00Z", ["c0", "m1x"], "Merge branch 'main' into x")]
        found = staleness.causes(commits, commits[1:], moves, staleness.parse_time("2026-10-20T09:00:00Z"), 9)
        self.assertEqual(found, [[1]])


class Summary(unittest.TestCase):
    def test_sums_the_records_and_sorts_them_by_parallel_work(self):
        moves = staleness.landings([FIRST, SECOND], "main")
        first = staleness.pull_record(FIRST, [commit("a1", "2026-10-20T09:59:00Z", ["m0"])],
                                      [run("a1", "2026-10-20T10:00:30Z", "2026-10-20T10:10:00Z")], moves, "main")
        second = staleness.pull_record(SECOND, SECOND_TIMELINE, SECOND_RUNS, moves, "main")
        shots = [{"at": "2026-10-20T10:30:05Z", "pulls": [{"number": 2, "state": "behind"}]}]
        s = staleness.summary([first, second], shots)
        self.assertEqual((s["merged"], s["with_catch_up"], s["check_runs_redone"]), (2, 1, 1))
        self.assertEqual(s["share_runs_redone"], round(1 / 3, 3))
        self.assertEqual(s["by_parallel_work"]["1-2"]["merged"], 2)
        self.assertEqual(s["top_pairs"], [{"landed": 1, "made_stale": 2, "times": 1}])
        self.assertEqual(s["live"]["pulls_seen_behind"], 1)
        self.assertIn("Stale branches", staleness.report({"repository": "o/r", "generated_at": "t",
                                                           "default_branch": "main", "summary": s}))


class Stacked(unittest.TestCase):
    def test_a_catch_up_two_branches_carry_counts_for_the_first_to_land(self):
        a = {"number": 1, "base": "main", "merged": "2026-10-20T10:00:00Z", "closed": "2026-10-20T10:00:00Z",
             "caused_by": [["s", [7]]]}
        b = dict(a, number=2, merged="2026-10-20T11:00:00Z", caused_by=[["s", [7]], ["t", [8]]])
        owned = staleness.owned_catch_ups([b, a])
        self.assertEqual((owned[1], owned[2]), ([("s", [7])], [("t", [8])]))


class FakeApi:
    repo = "o/r"

    def __init__(self, answers):
        self.answers = answers
        self.asked = []

    def get(self, path, params=None):
        self.asked.append(path)
        page = (params or {}).get("page", 1)
        answer = self.answers.get(path)
        if callable(answer):
            return answer()
        return answer if page == 1 else ([] if isinstance(answer, list) else {"workflow_runs": []})


class Collect(unittest.TestCase):
    def api(self):
        return FakeApi({
            "/repos/o/r/pulls": [FIRST, SECOND, pull(3, "claude/c", "2026-10-20T11:00:00Z", state="open")],
            "/repos/o/r/issues/1/timeline": [commit("a1", "2026-10-20T09:59:00Z", ["m0"])],
            "/repos/o/r/issues/2/timeline": SECOND_TIMELINE,
            "/repos/o/r/actions/workflows/ci.yml/runs": {"workflow_runs": SECOND_RUNS},
        })

    def test_a_bound_reads_the_newest_first_and_leaves_the_rest(self):
        record = staleness.collect(self.api(), "main", "ci.yml", max_new=1, log=lambda _: None)
        self.assertEqual([r["number"] for r in record["pulls"]], [2])
        self.assertEqual(record["unread"], 1)
        again = staleness.collect(self.api(), "main", "ci.yml", previous=record, log=lambda _: None)
        self.assertEqual([r["number"] for r in again["pulls"]], [1, 2])
        self.assertEqual(again["unread"], 0)

    def test_a_pull_request_reopened_and_merged_is_read_again(self):
        first = staleness.collect(self.api(), "main", "ci.yml", log=lambda _: None)
        first["pulls"][1]["merged"] = None
        again = staleness.collect(self.api(), "main", "ci.yml", previous=first, log=lambda _: None)
        self.assertEqual(again["pulls"][1]["merged"], "2026-10-20T11:00:00Z")

    def test_kept_records_are_not_read_again(self):
        api = self.api()
        first = staleness.collect(api, "main", "ci.yml", log=lambda _: None)
        api.asked.clear()
        staleness.collect(api, "main", "ci.yml", previous=first, log=lambda _: None)
        self.assertEqual(api.asked, ["/repos/o/r/pulls", "/repos/o/r/actions/workflows/ci.yml/runs"])

    def test_the_default_branch_checks_keep_the_days_before_the_last_read(self):
        api = self.api()
        api.answers["/repos/o/r/actions/workflows/ci.yml/runs"] = {"workflow_runs": [
            run("m2", "2026-10-21T08:00:00Z", "2026-10-21T08:05:00Z", conclusion="failure")]}
        previous = {"pulls": [], "summary": {"default_branch_checks": {"2026-10-19": {"success": 3},
                                                                         "2026-10-21": {"success": 9}}}}
        record = staleness.collect(api, "main", "ci.yml", previous=previous, log=lambda _: None)
        self.assertEqual(record["summary"]["default_branch_checks"],
                         {"2026-10-19": {"success": 3}, "2026-10-21": {"failure": 1}})

    def test_a_snapshot_asks_again_while_github_is_still_working_it_out(self):
        answers = iter([{"mergeable_state": "unknown"}, {"mergeable_state": "dirty"}])
        api = FakeApi({"/repos/o/r/pulls": [pull(3, "claude/c", "2026-10-20T11:00:00Z", state="open")],
                       "/repos/o/r/pulls/3": lambda: next(answers)})
        shot = staleness.snapshot(api, "main", sleep=lambda _: None)
        self.assertEqual(shot["pulls"][0]["state"], "dirty")

    def test_snapshots_file_skips_a_torn_line(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "SNAPSHOTS.jsonl"
            path.write_text(json.dumps({"at": "t", "pulls": []}) + "\n{torn\n")
            self.assertEqual(len(staleness.read_snapshots(path)), 1)


if __name__ == "__main__":
    unittest.main()
