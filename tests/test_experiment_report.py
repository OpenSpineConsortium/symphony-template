"""The experiment's report counts a pair an agent left in Error apart from
the failures, and compares arms only on the pairs both scored, so these
pin both against a small tree shaped like CooperBench's logs."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiment"))

import report  # noqa: E402


def write_pair(logs, run, setting, pair, passed=None, error=False):
    pair_dir = logs / run / setting / "pallets_click_task" / "2068" / pair
    pair_dir.mkdir(parents=True)
    status = "Error" if error else "Submitted"
    agents = {"agent1": {"status": status, "input_tokens": 100, "output_tokens": 10}}
    (pair_dir / "result.json").write_text(json.dumps({"agents": agents, "duration_seconds": 120}))
    if passed is not None:
        (pair_dir / "eval.json").write_text(json.dumps({"both_passed": passed}))


class ReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.logs = Path(self.tmp.name)
        write_pair(self.logs, "flash-solo-t", "solo", "f1_f6", passed=True)
        write_pair(self.logs, "flash-solo-t", "solo", "f2_f10", passed=False)
        write_pair(self.logs, "flash-team-t", "team", "f1_f6", passed=False)
        write_pair(self.logs, "flash-team-t", "team", "f2_f10", error=True)

    def tearDown(self):
        self.tmp.cleanup()

    def arms(self):
        return {arm: report.arm_outcomes(self.logs, f"flash-{arm}-t") for arm in report.ARMS}

    def test_an_errored_pair_is_counted_apart_from_failures(self):
        text = report.render(self.arms())
        self.assertIn("| solo | 1/2 | 50% |", text)
        self.assertIn("| team | 0/1 | 0% |", text)
        self.assertIn("| 1 | 110 | 2.0 | 31/50 |", text)

    def test_arms_are_compared_on_the_pairs_both_scored(self):
        text = report.render(self.arms())
        self.assertIn("| solo vs team | 1 | 1 | 0 | 1.000 |", text)
        self.assertIn("| pallets_click_task/2068/f2_f10 | fail | - | - | error |", text)

    def test_the_statistics(self):
        low, high = report.wilson(31, 50)
        self.assertEqual((round(low), round(high)), (48, 74))
        self.assertAlmostEqual(report.mcnemar_exact(10, 2), 158 / 4096)
        self.assertEqual(report.mcnemar_exact(0, 0), 1.0)


if __name__ == "__main__":
    unittest.main()
