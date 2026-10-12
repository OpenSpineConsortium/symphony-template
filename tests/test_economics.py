"""tools/economics.py: prices, what each pull request cost from its commits'
trailers and the Actions runs that name it, the window's totals, and the
comparison of work done alone with work done in parallel, each ratio over
1 when working in parallel did better."""

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import economics  # noqa: E402

T0 = datetime(2026, 10, 1, tzinfo=timezone.utc)


def at(hours):
    return T0 + timedelta(hours=hours)


def commit(message):
    return {"sha": "x", "commit": {"message": message}}


def trailer(session, seconds, **models):
    parts = [f"session={session}", f"seconds={seconds}"]
    parts += [f"{model.replace('_', '-')}={','.join(str(n) for n in counts)}" for model, counts in models.items()]
    return "Work\n\nSymphony-Usage: v1 " + " ".join(parts) + "\n"


def record(models, workflow="workers", job="worker", issue=None, pull=None, seconds=60.0):
    return economics.actions_record({"v": 1, "source": "actions", "workflow": workflow, "job": job, "issue": issue,
                                     "pull": pull, "seconds": seconds, "models": models})


class Prices(unittest.TestCase):
    def test_names_are_read_as_the_table_spells_them(self):
        self.assertEqual(economics.normalized("Claude-Opus-4-1-20250805"), "claude-opus-4-1")
        self.assertEqual(economics.normalized("claude-sonnet-5-5[1m]"), "claude-sonnet-5-5")
        self.assertEqual(economics.family("claude-haiku-5-5"), "haiku")
        self.assertEqual(economics.family("some-model"), "other")

    def test_a_usage_is_priced_by_kind_and_an_unknown_model_counted_apart(self):
        usd, unpriced = economics.priced({"claude-opus-5-5": [1_000_000, 0, 0, 1_000_000, 1_000_000],
                                          "mystery": [5, 0, 0, 0, 5]})
        self.assertAlmostEqual(usd, 4.0 + 0.20 + 20.0)
        self.assertEqual(unpriced, 10)
        usd, _ = economics.priced({"claude-sonnet-5-5": [0, 1_000_000, 1_000_000, 0, 0]})
        self.assertAlmostEqual(usd, 2.5 + 4.0)

    def test_every_price_row_has_five_rates_and_writes_cost_more_than_reads(self):
        for model, rates in economics.PRICES.items():
            self.assertEqual(len(rates), 5, model)
            self.assertLess(rates[3], rates[0], model)
            self.assertLess(rates[1], rates[2], model)


class Attribution(unittest.TestCase):
    def test_a_pull_request_costs_its_trailers_and_the_runs_that_name_it_or_its_claim(self):
        work = economics.Work(40, claim=12, commits=[commit(trailer("aaaa", 30, m=[1, 0, 0, 10, 2])),
                                                      commit(trailer("bbbb", 5, m=[1, 0, 0, 0, 1])), commit("plain")])
        records = [record({"m": [5, 0, 0, 0, 5]}, pull=40), record({"m": [7, 0, 0, 0, 0]}, issue=12),
                   record({"m": [100, 0, 0, 0, 0]}, issue=99)]
        spent = economics.spent_on(work, records)
        self.assertEqual(spent.models, {"m": [14, 0, 0, 10, 8]})
        self.assertEqual((spent.seconds, spent.sessions, spent.runs), (155.0, {"aaaa", "bbbb"}, 2))
        self.assertEqual(economics.unattributed([work], records), [records[2]])

    def test_a_record_that_does_not_hold_together_is_none(self):
        self.assertIsNone(economics.actions_record({"v": 2}))
        self.assertIsNone(economics.actions_record("text"))
        kept = economics.actions_record({"v": 1, "source": "actions", "models": {"m": [1, 2, 3, 4, "5"], "n": [1] * 5},
                                         "seconds": -3, "issue": "12"})
        self.assertEqual((kept["models"], kept["seconds"], kept["issue"]), ({"n": [1] * 5}, 0.0, None))


class Window(unittest.TestCase):
    def test_the_bill_is_the_windows_trailers_and_runs_and_the_delivery_its_pull_requests(self):
        works = [economics.Work(1, commits=[commit(trailer("s1", 100, claude_opus_5_5=[1000, 0, 0, 0, 1000]))],
                                merged=at(5), check_failures=1),
                 economics.Work(2, commits=[commit("x"), commit("y")])]
        records = [record({"claude-haiku-5-5": [10, 0, 0, 0, 10]}, workflow="coordinator", job="plan", issue=50,
                          seconds=20.0)]
        commits = [c for w in works for c in w.commits]
        found = economics.economics(works, commits, records, records, reverts=1, unread=3)
        self.assertEqual(tuple(found), economics.ECONOMICS_KEYS)
        self.assertEqual((found["prices_as_of"], found["actions_runs_unread"]), (economics.PRICES_AS_OF, 3))
        self.assertEqual((found["pull_requests"], found["pull_requests_measured"], found["merged"]), (2, 1, 1))
        self.assertEqual((found["tokens_input"], found["tokens_output"], found["tokens_total"]), (1010, 1010, 2020))
        self.assertEqual(found["tokens_by_family"], {"fable": 0, "opus": 2000, "sonnet": 0, "haiku": 20, "other": 0})
        self.assertAlmostEqual(found["estimated_usd"], 0.024 + 0.000006, places=4)
        self.assertAlmostEqual(found["coordinator_usd"], 0.0, places=4)
        self.assertEqual((found["claude_seconds"], found["commits"], found["check_failures"], found["reverts"]),
                         (120, 3, 1, 1))
        self.assertEqual((found["tokens_per_merge"], found["commits_per_merge"]), (2020, 3))
        self.assertEqual((found["sessions"], found["actions_runs"]), (1, 1))

    def test_nothing_merged_leaves_the_per_merge_figures_empty(self):
        found = economics.economics([economics.Work(1)], [], [], [], unread=None)
        self.assertIsNone(found["usd_per_merge"])
        self.assertIsNone(found["actions_runs_unread"])
        self.assertEqual(found["tokens_total"], 0)

    def test_a_commit_made_before_the_window_is_not_on_its_bill_but_counts_for_its_pull_request(self):
        early = commit(trailer("s9", 50, claude_opus_5_5=[500, 0, 0, 0, 0]))
        late = commit(trailer("s9", 50, claude_opus_5_5=[100, 0, 0, 0, 0]))
        works = [economics.Work(7, commits=[early, late], merged=at(3))]
        found = economics.economics(works, [late], [], [])
        self.assertEqual((found["tokens_total"], found["pull_requests_measured"]), (100, 1))
        self.assertEqual(found["tokens_per_merge"], 100)


class AloneAndParallel(unittest.TestCase):
    NOW = at(100)

    def works(self):
        def work(number, start, end, merged=True, tokens=1000, commits=1, failures=0, first=True, kind="person"):
            message = trailer(f"s{number}", 600, claude_sonnet_5_5=[tokens, 0, 0, 0, 0])
            return economics.Work(number, kind=kind, start=at(start), end=at(end), merged=at(end) if merged else None,
                                  opened=at(start), commits=[commit(message)] + [commit("x")] * (commits - 1),
                                  check_failures=failures, first_check=first)
        alone = [work(1, 0, 10, tokens=4000, commits=4, failures=2, first=False), work(2, 20, 30, tokens=2000)]
        parallel = [work(3, 40, 44, tokens=1000), work(4, 41, 45, tokens=1000, kind="workflow_agents"),
                    work(5, 42, 46, merged=False, tokens=500)]
        bot = [work(6, 0, 50, kind="automation")]
        return alone + parallel + bot

    def test_the_sides_split_by_whether_other_work_went_on_beside(self):
        found = economics.coordination(self.works(), [], self.NOW)
        self.assertEqual((found["alone"]["pull_requests"], found["parallel"]["pull_requests"]), (2, 3))
        self.assertEqual((found["alone"]["merged"], found["parallel"]["merged"]), (2, 2))
        self.assertEqual((found["alone"]["tokens"], found["parallel"]["tokens"]), (6000, 2500))
        self.assertEqual(found["alone"]["active_seconds"], 20 * 3600)
        self.assertEqual(found["parallel"]["active_seconds"], 6 * 3600)
        self.assertEqual(tuple(found["alone"]), economics.GROUP_KEYS)

    def test_each_ratio_is_over_one_where_parallel_did_better(self):
        ratios = economics.coordination(self.works(), [], self.NOW)["ratios"]
        self.assertEqual(tuple(ratios), economics.RATIO_KEYS)
        self.assertAlmostEqual(ratios["tokens_per_merge"], (6000 / 2) / (2500 / 2), places=4)
        self.assertAlmostEqual(ratios["latency"], (10 * 3600) / (4 * 3600), places=4)
        self.assertAlmostEqual(ratios["throughput"], (2 / 6) / (2 / 20), places=4)
        self.assertAlmostEqual(ratios["first_check_pass"], 1.0 / 0.5, places=4)
        self.assertAlmostEqual(ratios["commits_per_merge"], (5 / 2) / (3 / 2), places=4)
        self.assertAlmostEqual(ratios["failures_per_pull_request"], ((2 + 1) / 3) / ((0 + 1) / 4), places=4)

    def test_the_coordinators_runs_cost_the_parallel_side(self):
        records = [record({"claude-sonnet-5-5": [1_000_000, 0, 0, 0, 0]}, workflow="coordinator", job="plan", issue=77)]
        found = economics.coordination(self.works(), records, self.NOW, window_records=records)
        self.assertEqual(found["parallel"]["tokens"], 2500 + 1_000_000)
        self.assertAlmostEqual(found["parallel"]["estimated_usd"], 2.0 + 2500 * 2 / 1e6, places=4)

    def test_only_measured_merges_divide_the_tokens(self):
        works = self.works()
        works[1].commits = [commit("no trailer")]
        found = economics.coordination(works, [], self.NOW)
        self.assertEqual((found["alone"]["merged"], found["alone"]["measured_merged"]), (2, 1))
        self.assertAlmostEqual(found["ratios"]["tokens_per_merge"], (4000 / 1) / (2500 / 2), places=4)

    def test_a_side_with_nothing_gives_no_ratio(self):
        found = economics.coordination(self.works()[:2], [], self.NOW)
        self.assertEqual(found["parallel"]["pull_requests"], 0)
        self.assertTrue(all(value is None for value in found["ratios"].values()))

    def test_work_from_before_the_window_counts_as_beside(self):
        works = self.works()[:1]
        earlier = [economics.Work(9, start=at(-5), end=at(2))]
        found = economics.coordination(works, [], self.NOW, others=earlier)
        self.assertEqual((found["alone"]["pull_requests"], found["parallel"]["pull_requests"]), (0, 1))


if __name__ == "__main__":
    unittest.main()
