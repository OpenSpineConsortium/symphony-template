"""report.py sets the arms side by side from the runs' records."""

import json
import tempfile
import unittest
from pathlib import Path

from flowbench import report, run, tasks

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "tasks"
WORK_STAGES = [{"name": "work", "kind": "work", "skipped": False}]
REVIEW_STAGES = [{"name": "build", "kind": "work", "skipped": False}, {"name": "review", "kind": "review", "skipped": False}]


def result(instance, arm, resolved, repo="alpha/alpha", harness_error=False, reason=None, flow=None, tokens=1000,
           stages=WORK_STAGES, excluded=False, cost_source="estimated from tokens"):
    return {"instance": instance, "repo": repo, "arm": arm, "harness_error": harness_error, "excluded": excluded,
            "scoring": {"resolved": resolved, "reason": reason or ("resolved" if resolved else "unresolved")},
            "tokens": {"input": tokens, "output": 100, "cache_read": 0, "cache_write": 0, "output_lower_bound": 100,
                       "agents_uncounted": 0},
            "cost_usd": 0.5, "cost_source": cost_source, "timings": {"agents_seconds": 60.0}, "stages": stages,
            "flow": flow or {"orchestration_failure": False, "timeouts": 0, "turn_limits": 0}}


def write(logs, tag, arm, instance, attempt, record, audit=None):
    directory = Path(logs) / tag / arm / instance / f"attempt-{attempt}"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "result.json").write_text(json.dumps(record), encoding="utf-8")
    (directory / "audit.json").write_text(json.dumps(audit or {"harness_error": record["harness_error"],
                                                               "excluded": record["excluded"]}), encoding="utf-8")


class Statistics(unittest.TestCase):
    def test_wilson_brackets_the_rate_and_stays_in_bounds(self):
        low, high = report.wilson(5, 10)
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)
        self.assertEqual(report.wilson(0, 0), (0.0, 0.0))
        self.assertEqual(report.wilson(10, 10)[1], 1.0)

    def test_exact_mcnemar_is_one_with_no_discordant_pairs_and_small_when_one_sided(self):
        self.assertEqual(report.mcnemar_exact(0, 0), 1.0)
        self.assertEqual(report.mcnemar_exact(3, 3), 1.0)
        self.assertLess(report.mcnemar_exact(10, 0), 0.01)
        self.assertEqual(report.mcnemar_exact(10, 0), report.mcnemar_exact(0, 10))

    def test_the_bootstrap_is_the_seeds_brackets_the_rate_and_needs_two_repositories(self):
        clusters = [[1, 0, 1], [0, 0], [1, 1, 1, 0]]
        first = report.bootstrap_rate(clusters, iterations=200, seed=1)
        self.assertEqual(first, report.bootstrap_rate(clusters, iterations=200, seed=1))
        self.assertLessEqual(first[0], 5 / 9)
        self.assertGreaterEqual(first[1], 5 / 9)
        self.assertIsNone(report.bootstrap_rate([]))
        self.assertIsNone(report.bootstrap_rate([[1, 0, 1, 1]]), "one repository is one cluster: no interval")


class TheReport(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.logs = Path(self.temp.name)
        tag = "t"
        write(self.logs, tag, "symphony", "i1", 1, result("i1", "symphony", True))
        write(self.logs, tag, "symphony", "i2", 1, result("i2", "symphony", True, repo="beta/beta"))
        write(self.logs, tag, "symphony", "i3", 1, result("i3", "symphony", False, harness_error=True, reason="error"))
        write(self.logs, tag, "symphony", "i3", 2, result("i3", "symphony", False))
        write(self.logs, tag, "symphony", "i4", 1, result("i4", "symphony", False, harness_error=True, reason="error"))
        write(self.logs, tag, "symphony", "i5", 1, result("i5", "symphony", True, excluded=True))
        flow = {"orchestration_failure": True, "findings_raised": 3, "findings_confirmed": 1, "findings_fixed": 1,
                "timeouts": 1, "turn_limits": 0}
        write(self.logs, tag, "script", "i1", 1, result("i1", "script", False, flow=flow, stages=REVIEW_STAGES))
        write(self.logs, tag, "script", "i2", 1, result("i2", "script", True, repo="beta/beta", stages=REVIEW_STAGES,
                                                        cost_source="claude code",
                                                        flow={"orchestration_failure": False, "findings_raised": 0,
                                                              "findings_confirmed": 0, "findings_fixed": 0,
                                                              "timeouts": 0, "turn_limits": 2}))
        write(self.logs, tag, "script", "i3", 1, result("i3", "script", False, flow=flow, stages=REVIEW_STAGES))

    def tearDown(self):
        self.temp.cleanup()

    def test_a_harness_error_is_left_out_and_named_and_a_later_clean_attempt_counts(self):
        data = report.as_data(self.logs, "t", ["symphony", "script"], "symphony")
        symphony = data["arms"]["symphony"]
        self.assertEqual((symphony["n"], symphony["resolved"]), (3, 2))
        self.assertEqual(sorted(symphony["harness_errors"]), ["i3", "i4"])
        self.assertEqual(len(symphony["harness_errors"]["i3"]), 1)

    def test_an_excluded_run_is_left_out_and_named(self):
        data = report.as_data(self.logs, "t", ["symphony"], "symphony")
        self.assertEqual(sorted(data["arms"]["symphony"]["excluded"]), ["i5"])
        self.assertEqual(data["arms"]["symphony"]["n"], 3)
        text = report.render(self.logs, "t", ["symphony"], "symphony")
        self.assertIn("Excluded from symphony, the transcript naming the benchmark's files: i5 (1)", text)

    def test_the_comparison_pairs_the_instances_both_arms_scored(self):
        data = report.as_data(self.logs, "t", ["symphony", "script"], "symphony")
        comparison = data["comparisons"]["script"]
        self.assertEqual((comparison["n"], comparison["only_primary"], comparison["only_other"]), (3, 1, 0))
        self.assertEqual(comparison["p"], 1.0)

    def test_the_review_table_counts_only_runs_that_ran_a_review_stage(self):
        data = report.as_data(self.logs, "t", ["symphony", "script"], "symphony")
        review = data["arms"]["script"]["review"]
        self.assertEqual((review["raised"], review["confirmed"], review["fixed"]), (6, 2, 2))
        self.assertEqual(review["resolved_with_confirmed"], (0, 2))
        self.assertEqual(review["resolved_without"], (1, 1))
        self.assertIsNone(data["arms"]["symphony"]["review"], "no review stage in these records")
        self.assertEqual(data["arms"]["script"]["orchestration_failures"], 2)
        self.assertEqual((data["arms"]["script"]["timeouts"], data["arms"]["script"]["turn_limits"]), (2, 2))
        self.assertEqual(data["arms"]["script"]["cost_sources"], ["claude code", "estimated from tokens"])

    def test_the_paired_cost_is_the_ratio_of_the_sums_over_the_instances_both_measured(self):
        with tempfile.TemporaryDirectory() as temp:
            for instance, repo, a, b in (("i1", "alpha/alpha", 3000, 1000), ("i2", "beta/beta", 1000, 1000),
                                         ("i3", "beta/beta", 2000, 1000)):
                write(temp, "c", "symphony", instance, 1, result(instance, "symphony", True, repo=repo, tokens=a - 100))
                write(temp, "c", "script", instance, 1, result(instance, "script", False, repo=repo, tokens=b - 100))
            data = report.as_data(temp, "c", ["symphony", "script"], "symphony")
            tokens = data["comparisons"]["script"]["tokens"]
            self.assertEqual((tokens["n"], tokens["ratio"]), (3, 2.0))
            low, high = tokens["bootstrap"]
            self.assertLessEqual(low, 2.0)
            self.assertGreaterEqual(high, 2.0)
            self.assertEqual(data["arms"]["symphony"]["tokens_per_resolved"], 2000)
            self.assertIsNone(data["arms"]["script"]["tokens_per_resolved"])
            self.assertIn("| symphony / script | 3 | 2.00 |", report.render(temp, "c", ["symphony", "script"], "symphony"))

    def test_the_sample_rate_counts_an_instance_without_a_clean_run_as_not_resolved(self):
        sample = ["i1", "i2", "i3", "i4", "i9"]
        data = report.as_data(self.logs, "t", ["symphony"], "symphony", sample=sample)
        of_sample = data["arms"]["symphony"]["of_sample"]
        self.assertEqual((of_sample["n"], of_sample["resolved"], of_sample["unfinished"]), (5, 2, ["i4", "i9"]))
        text = report.render(self.logs, "t", ["symphony"], "symphony", sample=sample)
        self.assertIn("| 2/5 (40.0%) |", text)
        self.assertIn("symphony has no clean run for: i4, i9", text)

    def test_the_rendered_report_has_every_section(self):
        text = report.render(self.logs, "t", ["symphony", "script", "solo"], "symphony")
        for heading in ("## Resolved", "## Comparisons", "## Cost and time", "## Cost, paired", "## Review", "## Instances"):
            self.assertIn(heading, text)
        self.assertIn("Harness errors left out of symphony: i3 (1), i4 (1)", text)
        self.assertIn("| solo | 0 |", text)
        self.assertNotIn("No bootstrap interval", text)

    def test_one_repository_gets_no_bootstrap_interval_and_the_report_says_so(self):
        text = report.render(self.logs, "t", ["script"], "script")
        self.assertNotIn("No bootstrap interval", text)
        data = report.as_data(self.logs, "t", ["script"], "script")
        self.assertIsNotNone(data["arms"]["script"]["bootstrap"])
        with tempfile.TemporaryDirectory() as temp:
            write(temp, "u", "solo", "i1", 1, result("i1", "solo", True))
            write(temp, "u", "solo", "i2", 1, result("i2", "solo", False))
            self.assertIn("No bootstrap interval for solo", report.render(temp, "u", ["solo"], "solo"))
            self.assertIsNone(report.as_data(temp, "u", ["solo"], "solo")["arms"]["solo"]["bootstrap"])

    def test_the_command_line_prints_json_when_asked(self):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = report.main(["--logs", str(self.logs), "--tag", "t", "--arms", "symphony,script", "--json",
                                "--instances", "i1,i2"])
        self.assertEqual(code, 0)
        data = json.loads(out.getvalue())
        self.assertEqual(data["arms"]["symphony"]["n"], 3)
        self.assertEqual(data["sample"], ["i1", "i2"])


class FromAFakeRun(unittest.TestCase):
    def test_the_review_table_shows_the_arms_that_reviewed_and_not_the_solo_arm(self):
        limits = {"agent_seconds": 60, "run_seconds": 600, "max_turns": 0, "parallel": 3, "disallowed": run.DISALLOWED_TOOLS}
        with tempfile.TemporaryDirectory() as temp:
            logs = Path(temp) / "logs"
            task = tasks.read_task(FIXTURES / "tasks" / "fake__alpha-1")
            for arm in ("solo", "script", "symphony"):
                run.run_one(logs, "r", arm, task, None, "claude-sonnet-5-5", {}, limits, True, str(FIXTURES), None, None,
                            60, False)
            data = report.as_data(logs, "r", ["symphony", "script", "solo"], "symphony")
            self.assertIsNone(data["arms"]["solo"]["review"])
            self.assertEqual(data["arms"]["script"]["review"]["raised"], 3)
            self.assertEqual(data["arms"]["symphony"]["review"]["raised"], 3)
            text = report.render(logs, "r", ["symphony", "script", "solo"], "symphony")
            self.assertIn("| script | 3 | 1 | 1 |", text)
            self.assertNotIn("| solo | 0 | 0 | 0 |", text)
            self.assertIn("estimated from tokens", text)


if __name__ == "__main__":
    unittest.main()
