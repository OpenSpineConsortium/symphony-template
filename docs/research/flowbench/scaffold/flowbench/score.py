"""Scoring by SWE-bench's own harness, and nothing else.

The run's patch becomes one prediction line (instance_id,
model_name_or_path, model_patch), and `swebench eval` applies it in the
instance's image, runs eval.sh and parses the log; its verdict is the
benchmark's (PARITY.md, row 1). The harness runs from a virtualenv of its
own, named by --swebench or the environment variable FLOWBENCH_SWEBENCH,
with --task-repo so it reads the instance from the task repository and no
dataset is downloaded; its cwd is the run's score/ directory, where it
writes logs/run_evaluation/<run id>/<model>/<instance>/report.json and the
summary <model>.<run id>.json, both kept with the run. Every attempt
scores under a run id of its own, since the harness caches by run id and
instance and would hand back the first attempt's verdict otherwise.

A fake score (--fake) writes the same files from a rule instead of a
container, so a rehearsal that spends no usage still walks the path:
an empty patch is empty_patch, anything else unresolved.

    python3 flowbench/score.py RUN_DIR --task-repo CHECKOUT [--swebench PATH] [--timeout 1800]
    python3 flowbench/score.py RUN_DIR --fake
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_TIMEOUT = 1800
REASONS = ("resolved", "unresolved", "empty_patch", "error", "infra_failure", "ambiguous_failure", "incomplete")


class ScoreError(RuntimeError):
    pass


def model_name(arm, model):
    """model_name_or_path names the arm and the model, so a harness run
    says what it scored; the harness turns a slash into two underscores
    for its directory names, so none is used here."""
    return f"flowbench-{arm}-{model}".replace("/", "_")


def prediction_line(instance, arm, model, patch):
    return {"instance_id": instance, "model_name_or_path": model_name(arm, model), "model_patch": patch or ""}


def write_prediction(run_dir, instance, arm, model, patch):
    path = Path(run_dir) / "prediction.jsonl"
    path.write_text(json.dumps(prediction_line(instance, arm, model, patch), ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def read_prediction(run_dir):
    path = Path(run_dir) / "prediction.jsonl"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 1:
        raise ScoreError(f"{path}: one prediction line expected, {len(lines)} found")
    return json.loads(lines[0])


def run_id_for(tag, arm, instance, attempt):
    """A run id of the attempt's own, letters, digits, dots, dashes and
    underscores, since the harness makes a directory of it."""
    raw = f"{tag}.{arm}.{instance}.a{attempt}"
    return "".join(ch if ch.isalnum() or ch in ".-_" else "-" for ch in raw)


def summary_path(score_dir, model, run_id):
    return Path(score_dir) / f"{model.replace('/', '__')}.{run_id}.json"


def instance_report_path(score_dir, model, run_id, instance):
    return Path(score_dir) / "logs" / "run_evaluation" / run_id / model.replace("/", "__") / instance / "report.json"


def verdict(summary, instance):
    """(resolved, reason) for the instance from the harness's summary."""
    for reason in REASONS:
        if instance in summary.get(f"{reason}_ids", []):
            return reason == "resolved", reason
    if instance in summary.get("completed_ids", []):
        return False, "unresolved"
    return False, "incomplete"


def harness_command(swebench, prediction_path, run_id, instance, task_repo, timeout):
    return [str(swebench), "eval", "verified", "-p", str(prediction_path), "--run-id", run_id,
            "-i", instance, "-j", "1", "-t", str(timeout), "--task-repo", str(task_repo)]


def score(run_dir, tag, arm, instance, attempt, task_repo=None, swebench=None, timeout=DEFAULT_TIMEOUT, fake=False):
    """Score the run's prediction; the scoring block for result.json."""
    run_dir = Path(run_dir)
    score_dir = run_dir / "score"
    score_dir.mkdir(parents=True, exist_ok=True)
    prediction = read_prediction(run_dir)
    run_id = run_id_for(tag, arm, instance, attempt)
    model = prediction["model_name_or_path"]
    block = {"harness": "fake" if fake else "swebench", "run_id": run_id, "resolved": False, "reason": None,
             "patch_bytes": len(prediction["model_patch"].encode("utf-8")), "command": None, "exit_code": None}
    if fake:
        reason = "empty_patch" if not prediction["model_patch"].strip() else "unresolved"
        summary = {"resolved_ids": [], "unresolved_ids": [instance] if reason == "unresolved" else [],
                   "empty_patch_ids": [instance] if reason == "empty_patch" else [], "completed_ids": [instance],
                   "submitted_ids": [instance], "error_ids": [], "fake": True}
        summary_path(score_dir, model, run_id).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                                         encoding="utf-8")
        block.update({"resolved": False, "reason": reason})
        return block
    if not task_repo:
        raise ScoreError("a real score needs --task-repo, the checkout of SWE-bench/swe-bench-tasks")
    swebench = swebench or os.environ.get("FLOWBENCH_SWEBENCH") or "swebench"
    command = harness_command(swebench, run_dir / "prediction.jsonl", run_id, instance, task_repo, timeout)
    block["command"] = command
    log = score_dir / "harness.log"
    with log.open("w", encoding="utf-8") as out:
        try:
            done = subprocess.run(command, cwd=score_dir, stdout=out, stderr=subprocess.STDOUT,
                                  timeout=timeout + 600, check=False)
            block["exit_code"] = done.returncode
        except FileNotFoundError as error:
            raise ScoreError(f"the harness {swebench} is not there: {error}") from error
        except subprocess.TimeoutExpired as error:
            block.update({"reason": "error", "error": f"the harness ran past {timeout + 600} s"})
            return block
    summary_file = summary_path(score_dir, model, run_id)
    summary = None
    if summary_file.is_file():
        summary = json.loads(summary_file.read_text(encoding="utf-8"))
    if summary is None:
        block.update({"reason": "error", "error": f"the harness wrote no summary at {summary_file.name}; see {log.name}"})
        return block
    resolved, reason = verdict(summary, instance)
    block.update({"resolved": resolved, "reason": reason})
    report_file = instance_report_path(score_dir, model, run_id, instance)
    if report_file.is_file():
        block["report"] = str(report_file.relative_to(run_dir))
    return block


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score one run by SWE-bench's harness.")
    parser.add_argument("run_dir")
    parser.add_argument("--task-repo")
    parser.add_argument("--swebench", help="the harness's executable (default FLOWBENCH_SWEBENCH, then swebench)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="the harness's per-instance seconds")
    parser.add_argument("--fake", action="store_true")
    args = parser.parse_args(argv)
    plan = json.loads((Path(args.run_dir) / "plan.json").read_text(encoding="utf-8"))
    try:
        block = score(args.run_dir, plan["tag"], plan["arm"], plan["instance"], plan["attempt"],
                      args.task_repo, args.swebench, args.timeout, args.fake)
    except (ScoreError, OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print(json.dumps(block, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
