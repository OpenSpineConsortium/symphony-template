"""report.py sets the arms side by side from the runs' records."""

import json
import tempfile
import unittest
from pathlib import Path

from flowbench import report


def result(instance, arm, resolved, repo="alpha/alpha", harness_error=False, reason=None, flow=None, tokens=1000):
    return {"instance": instance, "repo": repo, "arm": arm, "harness_error": harness_error,
            "scoring": {"resolved": resolved, "reason": reason or ("resolved" if resolved else "unresolved")},
            "tokens": {"input": tokens, "output": 100, "cache_read": 0, "cache_write": 0, "output_lower_bound": 100},
            "cost_usd": 0.5, "timings": {"agents_seconds": 60.0}, "flow": flow or {"orchestration_failure": False}}


def write(logs, tag, arm, instance, attempt, record, audit=None):
    directory = Path(logs) / tag / arm / instance / f"attempt-{attempt}"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "result.json").write_text(json.dumps(record), encoding="utf-8")
    (directory / "audit.json").write_text(json.dumps(audit or {"harness_error": record["harness_error"]}), encoding="utf-8")


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

    def test_the_bootstrap_is_the_seeds_and_brackets_the_rate(self):
        clusters = [[1, 0, 1], [0, 0], [1, 1, 1, 0]]
        first = report.bootstrap_rate(clusters, iterations=200, seed=1)
        self.assertEqual(first, report.bootstrap_rate(clusters, iterations=200, seed=1))
        self.assertLessEqual(first[0], 5 / 9)
        self.assertGreaterEqual(first[1], 5 / 9)
        self.assertEqual(report.bootstrap_rate([]), (0.0, 0.0))


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
        flow = {"orchestration_failure": True, "findings_raised": 3, "findings_confirmed": 1, "findings_fixed": 1}
        write(self.logs, tag, "script", "i1", 1, result("i1", "script", False, flow=flow))
        write(self.logs, tag, "script", "i2", 1, result("i2", "script", True, repo="beta/beta",
                                                        flow={"orchestration_failure": False, "findings_raised": 0,
                                                              "findings_confirmed": 0, "findings_fixed": 0}))
        write(self.logs, tag, "script", "i3", 1, result("i3", "script", False, flow=flow))

    def tearDown(self):
        self.temp.cleanup()

    def test_a_harness_error_is_left_out_and_named_and_a_later_clean_attempt_counts(self):
        data = report.as_data(self.logs, "t", ["symphony", "script"], "symphony")
        symphony = data["arms"]["symphony"]
        self.assertEqual((symphony["n"], symphony["resolved"]), (3, 2))
        self.assertEqual(sorted(symphony["harness_errors"]), ["i3", "i4"])
        self.assertEqual(len(symphony["harness_errors"]["i3"]), 1)

    def test_the_comparison_pairs_the_instances_both_arms_scored(self):
        data = report.as_data(self.logs, "t", ["symphony", "script"], "symphony")
        comparison = data["comparisons"]["script"]
        self.assertEqual((comparison["n"], comparison["only_primary"], comparison["only_other"]), (3, 1, 0))
        self.assertEqual(comparison["p"], 1.0)

    def test_the_review_table_reads_the_flow_fields(self):
        data = report.as_data(self.logs, "t", ["symphony", "script"], "symphony")
        review = data["arms"]["script"]["review"]
        self.assertEqual((review["raised"], review["confirmed"], review["fixed"]), (6, 2, 2))
        self.assertEqual(review["resolved_with_confirmed"], (0, 2))
        self.assertEqual(review["resolved_without"], (1, 1))
        self.assertIsNone(data["arms"]["symphony"]["review"])
        self.assertEqual(data["arms"]["script"]["orchestration_failures"], 2)

    def test_the_rendered_report_has_every_section(self):
        text = report.render(self.logs, "t", ["symphony", "script", "solo"], "symphony")
        for heading in ("## Resolved", "## Comparisons", "## Cost and time", "## Review", "## Instances"):
            self.assertIn(heading, text)
        self.assertIn("Harness errors left out of symphony: i3 (1), i4 (1)", text)
        self.assertIn("| solo | 0 |", text)

    def test_the_command_line_prints_json_when_asked(self):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = report.main(["--logs", str(self.logs), "--tag", "t", "--arms", "symphony,script", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["arms"]["symphony"]["n"], 3)


if __name__ == "__main__":
    unittest.main()
