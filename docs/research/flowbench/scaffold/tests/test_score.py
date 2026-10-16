"""score.py hands the patch to SWE-bench's harness and reads its verdict."""

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from flowbench import score

# A stand-in for the harness: `eval` writes the summary the real one
# writes, with the instance resolved, and the instance's report, unless
# the patch says it does not apply, when it writes the error and the log
# the real one leaves; `dataset build` writes the parquet's directory.
FAKE_HARNESS = """#!/bin/sh
if [ "$1" = "dataset" ]; then
  mkdir -p "$5/SWE-bench_Verified" && : > "$5/SWE-bench_Verified/test.parquet"
  echo "SWE-bench/SWE-bench_Verified/test: $5/SWE-bench_Verified/test.parquet"
  exit 0
fi
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
dir="logs/run_evaluation/$run_id/$model/$instance"
mkdir -p "$dir"
if grep -q "does not apply" "$prediction"; then
  printf '%s\\n' '>>>>> Patch Apply Failed:' 'error: patch failed' > "$dir/run_instance.log"
  printf '{"resolved_ids": [], "unresolved_ids": [], "completed_ids": [], "error_ids": ["%s"], "infra_failure_ids": [], "failure_reasons": {}}\\n' "$instance" > "$model.$run_id.json"
  exit 0
fi
echo '{"resolved": true}' > "$dir/report.json"
echo 'eval ran' > "$dir/run_instance.log"
printf '{"resolved_ids": ["%s"], "unresolved_ids": [], "completed_ids": ["%s"], "error_ids": []}\\n' "$instance" "$instance" > "$model.$run_id.json"
"""
FAKE_PYTHON = "#!/bin/sh\necho 5.0.2\n"


def executable(path, text):
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


class Names(unittest.TestCase):
    def test_the_model_name_says_the_arm_and_the_model_without_a_slash(self):
        self.assertEqual(score.model_name("script", "anthropic/claude-x"), "flowbench-script-anthropic_claude-x")

    def test_the_run_id_is_the_attempts_own_and_safe_for_a_directory(self):
        self.assertEqual(score.run_id_for("pilot 1", "solo", "django__django-1", 2), "pilot-1.solo.django__django-1.a2")

    def test_the_verdict_takes_the_first_reason_the_summary_gives(self):
        summary = {"resolved_ids": ["a"], "unresolved_ids": ["b", "f"], "empty_patch_ids": ["c"],
                   "completed_ids": ["a", "b", "c", "d"], "error_ids": ["g", "h"], "infra_failure_ids": ["f"]}
        self.assertEqual(score.verdict(summary, "a"), (True, "resolved"))
        self.assertEqual(score.verdict(summary, "b"), (False, "unresolved"))
        self.assertEqual(score.verdict(summary, "c"), (False, "empty_patch"))
        self.assertEqual(score.verdict(summary, "d"), (False, "unresolved"))
        self.assertEqual(score.verdict(summary, "e"), (False, "incomplete"))
        self.assertEqual(score.verdict(summary, "f"), (False, "infra_failure"))
        self.assertEqual(score.verdict(summary, "g"), (False, "error"))
        self.assertEqual(score.verdict(summary, "h", "x\n>>>>> Patch Apply Failed:\nerror\n"), (False, "patch_failed"))

    def test_the_harness_command_scores_one_instance_from_the_compiled_dataset(self):
        command = score.harness_command("/venv/bin/swebench", "/data/SWE-bench_Verified", "/r/prediction.jsonl", "id",
                                        "x__y-1", 1800)
        self.assertEqual(command[:3], ["/venv/bin/swebench", "eval", "/data/SWE-bench_Verified"])
        for flag, value in (("-p", "/r/prediction.jsonl"), ("--run-id", "id"), ("-i", "x__y-1"), ("-j", "1"), ("-t", "1800")):
            self.assertEqual(command[command.index(flag) + 1], value)
        self.assertNotIn("--task-repo", command, "the task repository would make the harness rebuild the image")

    def test_a_relative_harness_path_is_made_absolute_and_a_bare_name_left_to_the_path(self):
        self.assertEqual(score.harness_executable("venv/bin/swebench"), os.path.abspath("venv/bin/swebench"))
        self.assertEqual(score.harness_executable("swebench"), "swebench")

    def test_the_build_command_compiles_the_task_repository(self):
        self.assertEqual(score.build_command("swebench", "/tasks", "/data"), ["swebench", "dataset", "build", "/tasks", "-o", "/data"])


class Scoring(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temp.name) / "run"
        self.run_dir.mkdir()
        self.dataset = Path(self.temp.name) / "data" / "SWE-bench_Verified"
        self.dataset.mkdir(parents=True)
        (self.dataset / "test.parquet").write_bytes(b"")
        self.harness = executable(Path(self.temp.name) / "swebench", FAKE_HARNESS)

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

    def test_a_real_score_needs_the_compiled_dataset(self):
        score.write_prediction(self.run_dir, "x__y-1", "solo", "m", "diff --git a b\n")
        with self.assertRaises(score.ScoreError):
            score.score(self.run_dir, "t", "solo", "x__y-1", 1, swebench=str(self.harness))
        with self.assertRaises(score.ScoreError):
            score.score(self.run_dir, "t", "solo", "x__y-1", 1, dataset=self.temp.name, swebench=str(self.harness))

    def test_a_real_score_reads_the_harness_summary_and_keeps_the_report_and_the_log(self):
        score.write_prediction(self.run_dir, "x__y-1", "solo", "m", "diff --git a b\n")
        block = score.score(self.run_dir, "t", "solo", "x__y-1", 1, dataset=str(self.dataset), swebench=str(self.harness))
        self.assertEqual((block["harness"], block["resolved"], block["reason"], block["exit_code"]), ("swebench", True, "resolved", 0))
        self.assertEqual(block["report"], "score/logs/run_evaluation/t.solo.x__y-1.a1/flowbench-solo-m/x__y-1/report.json")
        self.assertEqual(block["instance_log"], "score/logs/run_evaluation/t.solo.x__y-1.a1/flowbench-solo-m/x__y-1/run_instance.log")
        self.assertEqual(block["command"][2], str(self.dataset.resolve()))
        self.assertTrue((self.run_dir / "score" / "harness.log").is_file())

    def test_a_patch_that_does_not_apply_is_the_arms_failure_not_the_harnesss(self):
        score.write_prediction(self.run_dir, "x__y-1", "solo", "m", "diff --git a b\nthis patch does not apply\n")
        block = score.score(self.run_dir, "t", "solo", "x__y-1", 1, dataset=str(self.dataset), swebench=str(self.harness))
        self.assertEqual((block["resolved"], block["reason"]), (False, "patch_failed"))
        self.assertNotIn("patch_failed", score.HARNESS_FAILURE_REASONS)
        self.assertNotIn("report", block)

    def test_a_harness_that_writes_no_summary_is_an_error_not_a_verdict(self):
        harness = executable(Path(self.temp.name) / "broken", "#!/bin/sh\necho broken >&2\nexit 3\n")
        score.write_prediction(self.run_dir, "x__y-1", "solo", "m", "diff --git a b\n")
        block = score.score(self.run_dir, "t", "solo", "x__y-1", 1, dataset=str(self.dataset), swebench=str(harness))
        self.assertEqual((block["resolved"], block["reason"], block["exit_code"]), (False, "error", 3))
        self.assertIn("no summary", block["error"])

    def test_the_harness_comes_from_the_environment_when_not_named(self):
        score.write_prediction(self.run_dir, "x__y-1", "solo", "m", "diff --git a b\n")
        before = os.environ.get("FLOWBENCH_SWEBENCH")
        os.environ["FLOWBENCH_SWEBENCH"] = str(self.harness)
        try:
            block = score.score(self.run_dir, "t", "solo", "x__y-1", 1, dataset=str(self.dataset))
        finally:
            if before is None:
                del os.environ["FLOWBENCH_SWEBENCH"]
            else:
                os.environ["FLOWBENCH_SWEBENCH"] = before
        self.assertEqual(block["command"][0], str(self.harness))
        self.assertTrue(block["resolved"])

    def test_the_build_writes_the_dataset_and_the_version_is_read_beside_the_harness(self):
        out = Path(self.temp.name) / "out"
        lines = score.build("/tasks", out, swebench=str(self.harness))
        self.assertEqual(lines, [f"SWE-bench/SWE-bench_Verified/test: {out}/SWE-bench_Verified/test.parquet"])
        self.assertTrue((out / "SWE-bench_Verified" / "test.parquet").is_file())
        self.assertIsNone(score.harness_version(str(self.harness)), "no python beside it yet")
        executable(Path(self.temp.name) / "python", FAKE_PYTHON)
        self.assertEqual(score.harness_version(str(self.harness)), "5.0.2")
        self.assertIsNone(score.harness_version("/no/such/swebench"))

    def test_the_command_line_builds_and_scores(self):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = score.main(["build", "/tasks", "-o", str(Path(self.temp.name) / "built"), "--swebench", str(self.harness)])
        self.assertEqual(code, 0)
        self.assertIn("a run names --dataset", out.getvalue())
        (self.run_dir / "plan.json").write_text(json.dumps({"tag": "t", "arm": "solo", "instance": "x__y-1", "attempt": 1}),
                                                encoding="utf-8")
        score.write_prediction(self.run_dir, "x__y-1", "solo", "m", "diff --git a b\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = score.main(["score", str(self.run_dir), "--fake"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["reason"], "unresolved")


if __name__ == "__main__":
    unittest.main()
