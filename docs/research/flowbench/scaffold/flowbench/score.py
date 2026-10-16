"""Scoring by SWE-bench's own harness, and nothing else.

The run's patch becomes one prediction line (instance_id,
model_name_or_path, model_patch), and `swebench eval` applies it in the
instance's image, runs eval.sh and parses the log; its verdict is the
benchmark's (PARITY.md, row 1). The harness runs from a virtualenv of its
own, named by --swebench or the environment variable FLOWBENCH_SWEBENCH,
on a dataset compiled from the task repository by `swebench dataset
build` (the build command below), which it reads from the local parquet
file with no download. It is not given the task repository itself: with
--task-repo the harness rebuilds the instance's image from its Dockerfile
before scoring, and falls back to the published image when that build
fails, so the image scored would not be the image the agent worked in.
Its cwd is the run's score/ directory, where it writes
logs/run_evaluation/<run id>/<model>/<instance>/ (report.json and
run_instance.log) and the summary <model>.<run id>.json, both kept with
the run. Every attempt scores under a run id of its own, since the
harness caches by run id and instance and would hand back the first
attempt's verdict otherwise.

The verdict is read from the summary's sets, and one case apart: a patch
the harness could not apply leaves no report and lands in error_ids, with
">>>>> Patch Apply Failed" in run_instance.log; that is the arm's
failure (a patch that does not apply fixes nothing), named patch_failed,
not a failure of the harness, which the summary's infra_failure_ids and
failure_reasons name.

A fake score (--fake) writes the same files from a rule instead of a
container, so a rehearsal that spends no usage still walks the path:
an empty patch is empty_patch, anything else unresolved.

    python3 flowbench/score.py build TASK_REPO -o DIR [--swebench PATH]
    python3 flowbench/score.py score RUN_DIR --dataset DIR/SWE-bench_Verified [--swebench PATH] [--timeout 1800]
    python3 flowbench/score.py score RUN_DIR --fake
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_TIMEOUT = 1800
# The reasons a score can end in, in the order the verdict looks for them.
REASONS = ("resolved", "empty_patch", "infra_failure", "patch_failed", "error", "unresolved", "incomplete")
HARNESS_FAILURE_REASONS = ("error", "infra_failure")
PATCH_FAILED_MARKER = ">>>>> Patch Apply Failed"
VERSION_COMMAND = ("-c", "import swebench; print(swebench.__version__)")


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


def instance_dir(score_dir, model, run_id, instance):
    return Path(score_dir) / "logs" / "run_evaluation" / run_id / model.replace("/", "__") / instance


def instance_report_path(score_dir, model, run_id, instance):
    return instance_dir(score_dir, model, run_id, instance) / "report.json"


def instance_log_path(score_dir, model, run_id, instance):
    return instance_dir(score_dir, model, run_id, instance) / "run_instance.log"


def verdict(summary, instance, instance_log=""):
    """(resolved, reason) for the instance from the harness's summary, and
    its run_instance.log for a patch that did not apply."""
    if instance in summary.get("resolved_ids", []):
        return True, "resolved"
    if instance in summary.get("empty_patch_ids", []):
        return False, "empty_patch"
    if instance in summary.get("infra_failure_ids", []):
        return False, "infra_failure"
    if instance in summary.get("error_ids", []):
        return False, "patch_failed" if PATCH_FAILED_MARKER in (instance_log or "") else "error"
    if instance in summary.get("unresolved_ids", []) or instance in summary.get("completed_ids", []):
        return False, "unresolved"
    return False, "incomplete"


def harness_executable(swebench=None):
    """The harness named by --swebench, FLOWBENCH_SWEBENCH or the PATH; a
    relative path made absolute, since the harness runs from the run's
    score/ directory, where a relative path would name nothing."""
    name = str(swebench or os.environ.get("FLOWBENCH_SWEBENCH") or "swebench")
    if os.sep in name and not os.path.isabs(name):
        name = os.path.abspath(name)
    return name


def harness_version(swebench=None):
    """The harness's version, asked of the Python beside its executable
    (a virtualenv's); None where it cannot be read, and the record says
    so rather than guessing."""
    executable = shutil.which(harness_executable(swebench))
    if not executable:
        return None
    python = Path(executable).parent / "python"
    if not python.is_file():
        return None
    try:
        done = subprocess.run([str(python), *VERSION_COMMAND], capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout.strip() or None if done.returncode == 0 else None


def harness_command(swebench, dataset, prediction_path, run_id, instance, timeout):
    """One instance, one worker, from the compiled dataset's directory
    (the one holding test.parquet), given as an absolute path since the
    harness runs from the run's score/ directory."""
    return [str(swebench), "eval", str(Path(dataset).resolve()), "-p", str(prediction_path), "--run-id", run_id,
            "-i", instance, "-j", "1", "-t", str(timeout)]


def build_command(swebench, task_repo, out):
    return [str(swebench), "dataset", "build", str(task_repo), "-o", str(out)]


def build(task_repo, out, swebench=None, timeout=1800):
    """The task repository compiled into one parquet per split under out/
    (<out>/SWE-bench_Verified/test.parquet is the one a run names with
    --dataset); the lines the harness printed, one per file written."""
    command = build_command(harness_executable(swebench), task_repo, out)
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError as error:
        raise ScoreError(f"the harness {command[0]} is not there: {error}") from error
    except subprocess.TimeoutExpired as error:
        raise ScoreError(f"the dataset build ran past {timeout} s") from error
    if done.returncode != 0:
        raise ScoreError(f"the dataset build failed ({done.returncode}): {(done.stderr or done.stdout).strip()[-2000:]}")
    return [line for line in done.stdout.splitlines() if line.strip()]


def fake_summary(instance, reason):
    return {"resolved_ids": [], "unresolved_ids": [instance] if reason == "unresolved" else [],
            "empty_patch_ids": [instance] if reason == "empty_patch" else [], "completed_ids": [instance],
            "submitted_ids": [instance], "error_ids": [], "infra_failure_ids": [], "ambiguous_failure_ids": [],
            "failure_reasons": {}, "fake": True}


def score(run_dir, tag, arm, instance, attempt, dataset=None, swebench=None, timeout=DEFAULT_TIMEOUT, fake=False):
    """Score the run's prediction; the scoring block for result.json. The
    run directory is made absolute, since the harness reads the prediction
    from its own working directory, the run's score/."""
    run_dir = Path(run_dir).resolve()
    score_dir = run_dir / "score"
    score_dir.mkdir(parents=True, exist_ok=True)
    prediction = read_prediction(run_dir)
    run_id = run_id_for(tag, arm, instance, attempt)
    model = prediction["model_name_or_path"]
    block = {"harness": "fake" if fake else "swebench", "run_id": run_id, "resolved": False, "reason": None,
             "patch_bytes": len(prediction["model_patch"].encode("utf-8")), "command": None, "exit_code": None,
             "failure_reason": None, "ambiguous_failure": False}
    if fake:
        reason = "empty_patch" if not prediction["model_patch"].strip() else "unresolved"
        summary_path(score_dir, model, run_id).write_text(
            json.dumps(fake_summary(instance, reason), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        block.update({"resolved": False, "reason": reason})
        return block
    if not dataset:
        raise ScoreError("a real score needs --dataset, the directory score.py build wrote (its test.parquet)")
    if not (Path(dataset) / "test.parquet").is_file():
        raise ScoreError(f"{dataset}: no test.parquet there; is it a directory score.py build wrote?")
    swebench = harness_executable(swebench)
    command = harness_command(swebench, dataset, run_dir / "prediction.jsonl", run_id, instance, timeout)
    block["command"] = command
    log = score_dir / "harness.log"
    with log.open("w", encoding="utf-8") as out:
        try:
            done = subprocess.run(command, cwd=score_dir, stdout=out, stderr=subprocess.STDOUT,
                                  timeout=timeout + 600, check=False)
            block["exit_code"] = done.returncode
        except FileNotFoundError as error:
            raise ScoreError(f"the harness {swebench} is not there: {error}") from error
        except subprocess.TimeoutExpired:
            block.update({"reason": "error", "error": f"the harness ran past {timeout + 600} s"})
            return block
    summary_file = summary_path(score_dir, model, run_id)
    summary = None
    if summary_file.is_file():
        summary = json.loads(summary_file.read_text(encoding="utf-8"))
    if summary is None:
        block.update({"reason": "error", "error": f"the harness wrote no summary at {summary_file.name}; see {log.name}"})
        return block
    log_file = instance_log_path(score_dir, model, run_id, instance)
    instance_log = log_file.read_text(encoding="utf-8", errors="replace") if log_file.is_file() else ""
    resolved, reason = verdict(summary, instance, instance_log)
    block.update({"resolved": resolved, "reason": reason,
                  "failure_reason": (summary.get("failure_reasons") or {}).get(instance),
                  "ambiguous_failure": instance in summary.get("ambiguous_failure_ids", [])})
    if reason == "infra_failure":
        block["error"] = f"the harness's infrastructure: {block['failure_reason'] or 'see run_instance.log'}"
    if log_file.is_file():
        block["instance_log"] = str(log_file.relative_to(run_dir))
    report_file = instance_report_path(score_dir, model, run_id, instance)
    if report_file.is_file():
        block["report"] = str(report_file.relative_to(run_dir))
    return block


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score one run by SWE-bench's harness, or compile the dataset it reads.")
    commands = parser.add_subparsers(dest="command", required=True)
    building = commands.add_parser("build", help="compile the task repository into the parquet files the harness reads")
    building.add_argument("task_repo", help="a checkout of github.com/SWE-bench/swe-bench-tasks")
    building.add_argument("-o", "--out", required=True, help="where the per-dataset directories go")
    building.add_argument("--swebench", help="the harness's executable (default FLOWBENCH_SWEBENCH, then swebench)")
    scoring = commands.add_parser("score", help="score one run directory")
    scoring.add_argument("run_dir")
    scoring.add_argument("--dataset", help="the compiled dataset's directory, the one holding test.parquet")
    scoring.add_argument("--swebench", help="the harness's executable (default FLOWBENCH_SWEBENCH, then swebench)")
    scoring.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="the harness's per-instance seconds")
    scoring.add_argument("--fake", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            for line in build(args.task_repo, args.out, args.swebench):
                print(line)
            print(f"a run names --dataset {Path(args.out) / 'SWE-bench_Verified'}")
            return 0
        plan = json.loads((Path(args.run_dir) / "plan.json").read_text(encoding="utf-8"))
        block = score(args.run_dir, plan["tag"], plan["arm"], plan["instance"], plan["attempt"],
                      args.dataset, args.swebench, args.timeout, args.fake)
    except (ScoreError, OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print(json.dumps(block, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
