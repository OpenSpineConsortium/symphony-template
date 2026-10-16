"""score.py hands the patch to SWE-bench's harness and reads its verdict."""

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from flowbench import score

# A stand-in for the harness: a script that writes the summary the real
# one writes, with the instance resolved, and the instance's report.
FAKE_HARNESS = """#!/bin/sh
run_id=""
instance=""
prediction=""
while [ $# -gt 0 ]; do
  case "$1" in
    --run-id) run_id="$2"; shift ;;
    -i) instance="$2"; shift ;;
    -p) prediction="$2"; shift ;;
  esac
  shift
done
model=$(python3 -c "import json,sys; print(json.loads(open(sys.argv[1]).readline())['model_name_or_path'])" "$prediction")
mkdir -p "logs/run_evaluation/$run_id/$model/$instance"
echo '{"resolved": true}' > "logs/run_evaluation/$run_id/$model/$instance/report.json"
printf '{"resolved_ids": ["%s"], "unresolved_ids": [], "completed_ids": ["%s"], "error_ids": []}\\n' "$instance" "$instance" > "$model.$run_id.json"
"""


class Names(unittest.TestCase):
    def test_the_model_name_says_the_arm_and_the_model_without_a_slash(self):
        self.assertEqual(score.model_name("script", "anthropic/claude-x"), "flowbench-script-anthropic_claude-x")

    def test_the_run_id_is_the_attempts_own_and_safe_for_a_directory(self):
        self.assertEqual(score.run_id_for("pilot 1", "solo", "django__django-1", 2), "pilot-1.solo.django__django-1.a2")

    def test_the_verdict_takes_the_first_reason_the_summary_gives(self):
        summary = {"resolved_ids": ["a"], "unresolved_ids": ["b"], "empty_patch_ids": ["c"], "completed_ids": ["a", "b", "c", "d"]}
        self.assertEqual(score.verdict(summary, "a"), (True, "resolved"))
        self.assertEqual(score.verdict(summary, "b"), (False, "unresolved"))
        self.assertEqual(score.verdict(summary, "c"), (False, "empty_patch"))
        self.assertEqual(score.verdict(summary, "d"), (False, "unresolved"))
        self.assertEqual(score.verdict(summary, "e"), (False, "incomplete"))

    def test_the_harness_command_scores_one_instance_from_the_task_repository(self):
        command = score.harness_command("/venv/bin/swebench", "/r/prediction.jsonl", "id", "x__y-1", "/tasks", 1800)
        self.assertEqual(command[:3], ["/venv/bin/swebench", "eval", "verified"])
        for flag, value in (("-p", "/r/prediction.jsonl"), ("--run-id", "id"), ("-i", "x__y-1"), ("-j", "1"),
                            ("-t", "1800"), ("--task-repo", "/tasks")):
            self.assertEqual(command[command.index(flag) + 1], value)


class Scoring(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temp.name) / "run"
        self.run_dir.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_the_prediction_is_one_line_the_harness_reads(self):
        score.write_prediction(self.run_dir, "x__y-1", "solo", "m", "diff --git a b\n")
        line = score.read_prediction(self.run_dir)
        self.assertEqual(line, {"instance_id": "x__y-1", "model_name_or_path": "flowbench-solo-m", "model_patch": "diff --git a b\n"})

    def test_a_fake_score_calls_an_empty_patch_empty_and_any_other_unresolved(self):
        score.write_prediction(self.run_dir, "x__y-1", "solo", "m", "")
        block = score.score(self.run_dir, "t", "solo", "x__y-1", 1, fake=True)
        self.assertEqual((block["harness"], block["resolved"], block["reason"]), ("fake", False, "empty_patch"))
        score.write_prediction(self.run_dir, "x__y-1", "solo", "m", "diff --git a b\n")
        block = score.score(self.run_dir, "t", "solo", "x__y-1", 1, fake=True)
        self.assertEqual(block["reason"], "unresolved")
        self.assertTrue(score.summary_path(self.run_dir / "score", "flowbench-solo-m", block["run_id"]).is_file())

    def test_a_real_score_needs_the_task_repository(self):
        score.write_prediction(self.run_dir, "x__y-1", "solo", "m", "diff --git a b\n")
        with self.assertRaises(score.ScoreError):
            score.score(self.run_dir, "t", "solo", "x__y-1", 1)

    def test_a_real_score_reads_the_harness_summary_and_keeps_the_report(self):
        harness = Path(self.temp.name) / "swebench"
        harness.write_text(FAKE_HARNESS, encoding="utf-8")
        harness.chmod(harness.stat().st_mode | stat.S_IXUSR)
        score.write_prediction(self.run_dir, "x__y-1", "solo", "m", "diff --git a b\n")
        block = score.score(self.run_dir, "t", "solo", "x__y-1", 1, task_repo="/tasks", swebench=str(harness))
        self.assertEqual((block["harness"], block["resolved"], block["reason"], block["exit_code"]), ("swebench", True, "resolved", 0))
        self.assertEqual(block["report"], "score/logs/run_evaluation/t.solo.x__y-1.a1/flowbench-solo-m/x__y-1/report.json")
        self.assertTrue((self.run_dir / "score" / "harness.log").is_file())

    def test_a_harness_that_writes_no_summary_is_an_error_not_a_verdict(self):
        harness = Path(self.temp.name) / "swebench"
        harness.write_text("#!/bin/sh\necho broken >&2\nexit 3\n", encoding="utf-8")
        harness.chmod(harness.stat().st_mode | stat.S_IXUSR)
        score.write_prediction(self.run_dir, "x__y-1", "solo", "m", "diff --git a b\n")
        block = score.score(self.run_dir, "t", "solo", "x__y-1", 1, task_repo="/tasks", swebench=str(harness))
        self.assertEqual((block["resolved"], block["reason"], block["exit_code"]), (False, "error", 3))
        self.assertIn("no summary", block["error"])

    def test_the_harness_comes_from_the_environment_when_not_named(self):
        harness = Path(self.temp.name) / "swebench"
        harness.write_text(FAKE_HARNESS, encoding="utf-8")
        harness.chmod(harness.stat().st_mode | stat.S_IXUSR)
        score.write_prediction(self.run_dir, "x__y-1", "solo", "m", "diff --git a b\n")
        before = os.environ.get("FLOWBENCH_SWEBENCH")
        os.environ["FLOWBENCH_SWEBENCH"] = str(harness)
        try:
            block = score.score(self.run_dir, "t", "solo", "x__y-1", 1, task_repo="/tasks")
        finally:
            if before is None:
                del os.environ["FLOWBENCH_SWEBENCH"]
            else:
                os.environ["FLOWBENCH_SWEBENCH"] = before
        self.assertEqual(block["command"][0], str(harness))
        self.assertTrue(block["resolved"])


if __name__ == "__main__":
    unittest.main()
