"""run.py takes one (instance, arm) attempt from the image to the record;
here in fake mode, and against a fake docker where the real path differs."""

import dataclasses
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from flowbench import backlog, record, run, tasks

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "tasks"
LIMITS = {"agent_seconds": 60, "run_seconds": 600, "max_turns": 10, "parallel": 3, "disallowed": run.LOCAL_ONLY_DISALLOWED}


def fake_run(logs, arm, instance="fake__alpha-1", options=None, tag="t", limits=LIMITS, model="claude-sonnet-5-5"):
    task = tasks.read_task(FIXTURES / "tasks" / instance)
    return run.run_one(logs, tag, arm, task, None, model, options or {}, limits, True, None, None, 60, False)


class FakeDocker:
    """Records the commands; copy_out puts a prepared repository in place
    of the image's /testbed."""

    def __init__(self, source):
        self.source = source
        self.calls = []

    def create(self, image, name):
        self.calls.append(("create", image, name))

    def copy_out(self, container, source, target):
        self.calls.append(("cp", container, source, str(target)))
        shutil.copytree(self.source, target)

    def remove(self, name):
        self.calls.append(("rm", name))

    def start_workspace(self, image, name, workspace, label):
        self.calls.append(("run", image, name, str(workspace), label))

    def image_id(self, image):
        self.calls.append(("inspect", image))
        return "sha256:fake"


class FakeRuns(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.logs = Path(self.temp.name) / "logs"

    def tearDown(self):
        self.temp.cleanup()

    def run_dir(self, arm, instance="fake__alpha-1", attempt=1, tag="t"):
        return run.run_directory(self.logs, tag, arm, instance, attempt)

    def test_solo_leaves_a_scored_record_with_the_patch_and_the_cost(self):
        result = fake_run(self.logs, "solo")
        run_dir = self.run_dir("solo")
        self.assertEqual((result["scoring"]["reason"], result["harness_error"], result["flow"]["orchestration_failure"]),
                         ("unresolved", False, False))
        self.assertIn("return a + b", (run_dir / "model.patch").read_text(encoding="utf-8"))
        self.assertEqual(result["tokens"]["input"], 1000)
        self.assertEqual(result["cost_source"], "estimated from tokens")
        self.assertEqual(result["cost_usd"], record.price(result["tokens"], "claude-sonnet-5-5"))
        self.assertEqual([a["agent"] for a in result["agents"]], ["work"])
        for name in ("plan.json", "result.json", "audit.json", "events.jsonl", "prediction.jsonl", "stages.json", "problem.md"):
            self.assertTrue((run_dir / name).is_file(), name)
        kinds = [json.loads(line)["kind"] for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(kinds[:3], ["prepared", "stage_started", "agent_started"])
        self.assertEqual(kinds[-3:], ["patch_taken", "scored", "finished"])

    def test_the_script_runs_every_stage_and_counts_the_review(self):
        result = fake_run(self.logs, "script")
        self.assertEqual([s["name"] for s in result["stages"]], ["build", "stack", "review", "verify", "fix"])
        self.assertFalse(any(s["skipped"] for s in result["stages"]))
        flow = result["flow"]
        self.assertEqual((flow["findings_raised"], flow["findings_confirmed"], flow["findings_fixed"]), (3, 1, 1))
        self.assertEqual(flow["findings_by_lens"], {"conventions": 1, "correctness": 1, "path": 1})
        self.assertFalse(flow["orchestration_failure"])
        self.assertEqual(len(result["agents"]), 9)

    def test_with_no_findings_the_verify_and_fix_stages_are_skipped(self):
        result = fake_run(self.logs, "script", options={"fake_findings": "0"})
        skipped = [s["name"] for s in result["stages"] if s["skipped"]]
        self.assertEqual(skipped, ["verify", "fix"])
        self.assertEqual(result["flow"]["findings_raised"], 0)
        self.assertFalse(result["flow"]["orchestration_failure"])

    def test_builders_work_in_worktrees_with_a_container_each_and_the_stack_merges_them(self):
        result = fake_run(self.logs, "script", options={"builders": "3"})
        run_dir = self.run_dir("script")
        plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
        self.assertEqual([b["branch"] for b in plan["builders"]], ["builder-1", "builder-2", "builder-3"])
        self.assertTrue(all((run_dir / f"worktree-{k}").is_dir() for k in (1, 2, 3)))
        self.assertEqual([a["agent"] for a in result["agents"][:3]], ["build-1", "build-2", "build-3"])
        self.assertEqual(result["flow"]["merges"]["merged"], ["builder-1", "builder-2", "builder-3"])
        self.assertIn("return a + b", (run_dir / "model.patch").read_text(encoding="utf-8"))

    def test_a_conflict_between_builders_is_recorded_not_a_failure(self):
        result = fake_run(self.logs, "script", options={"builders": "2", "fake_conflict": "1"})
        merges = result["flow"]["merges"]
        self.assertEqual((merges["merged"], merges["conflicts"]), (["builder-1"], ["builder-2"]))
        self.assertFalse(result["flow"]["orchestration_failure"])

    def test_an_agent_that_fails_is_the_arms_orchestration_failure_and_the_run_is_still_scored(self):
        result = fake_run(self.logs, "script", options={"fake_fail": "review-path"})
        self.assertFalse(result["harness_error"])
        self.assertTrue(result["flow"]["orchestration_failure"])
        reasons = result["flow"]["orchestration_reasons"]
        self.assertTrue(any("review-path: error" in r for r in reasons), reasons)
        self.assertTrue(any("left no findings-path.json" in r for r in reasons), reasons)
        self.assertEqual(result["flow"]["findings_raised"], 2)
        self.assertEqual(result["scoring"]["reason"], "unresolved")

    def test_a_usage_limit_is_the_harness_error_not_the_arms(self):
        result = fake_run(self.logs, "script", options={"fake_limit": "build"})
        self.assertTrue(result["harness_error"])
        audit = json.loads((self.run_dir("script") / "audit.json").read_text(encoding="utf-8"))
        self.assertTrue(audit["harness_error"])
        self.assertTrue(any("usage limit" in reason for reason in audit["reasons"]), audit)
        self.assertFalse(result["flow"]["orchestration_failure"])

    def test_symphony_claims_a_branch_opens_the_pull_request_and_answers_the_review(self):
        result = fake_run(self.logs, "symphony")
        run_dir = self.run_dir("symphony")
        branches = subprocess.run(["git", "-C", str(run_dir / "workspace"), "branch", "--show-current"],
                                  capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(branches, "claude/1")
        self.assertTrue((run_dir / "flow" / "pull-request.md").is_file())
        answers = json.loads((run_dir / "flow" / "answers.json").read_text(encoding="utf-8"))
        self.assertEqual(len(answers["answers"]), 3)
        self.assertEqual((result["flow"]["review_rounds"], result["flow"]["findings_fixed"]), (1, 1))
        self.assertIn("return a + b", (run_dir / "model.patch").read_text(encoding="utf-8"))

    def test_the_second_attempt_gets_its_own_directory(self):
        fake_run(self.logs, "solo")
        fake_run(self.logs, "solo")
        self.assertTrue(self.run_dir("solo", attempt=2).is_file() or self.run_dir("solo", attempt=2).is_dir())
        self.assertEqual(run.next_attempt(self.logs, "t", "solo", "fake__alpha-1"), 3)

    def test_the_prompts_name_neither_the_task_repository_nor_the_gold_patch(self):
        fake_run(self.logs, "script", options={"builders": "2"})
        for prompt in (self.run_dir("script") / "agents").glob("*.prompt.md"):
            text = prompt.read_text(encoding="utf-8")
            self.assertNotIn(str(FIXTURES), text, prompt.name)
            self.assertNotIn("gold", text.lower(), prompt.name)
            self.assertIn("flowbench-", text, prompt.name)

    def test_the_run_time_limit_skips_the_stages_after_it(self):
        limits = dict(LIMITS, run_seconds=0)
        result = fake_run(self.logs, "script", limits=limits)
        self.assertTrue(all(s["skipped"] for s in result["stages"]))
        self.assertEqual(result["patch_bytes"], 0)
        self.assertEqual(result["scoring"]["reason"], "empty_patch")


class TheLane(unittest.TestCase):
    def test_a_lane_runs_the_backlog_and_reports_each_item(self):
        with tempfile.TemporaryDirectory() as temp:
            logs = Path(temp) / "logs"
            path = Path(temp) / "backlog.jsonl"
            backlog.add(path, "t", ["fake__alpha-1", "fake__beta-1"], ["solo"], {"fake_tokens": "10"})
            code = run.main(["lane", "--backlog", str(path), "--lane", "lane-1", "--logs", str(logs), "--task-repo",
                             str(FIXTURES), "--fake", "--agent-minutes", "1"])
            self.assertEqual(code, 0)
            items = backlog.read_items(path)
            self.assertEqual([(i["state"], i["verdict"], i["lane"]) for i in items],
                             [("done", "failed", "lane-1"), ("done", "failed", "lane-1")])
            self.assertTrue(Path(items[1]["run_dir"]).joinpath("result.json").is_file())
            result = json.loads(Path(items[0]["run_dir"]).joinpath("result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["tokens"]["input"], 10)


class ThePatch(unittest.TestCase):
    def test_caches_a_test_run_leaves_are_not_in_the_patch(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "workspace"
            base = run.fake_workspace(workspace, "x")
            run.exclude_from_patch(workspace)
            (workspace / "pkg" / "__pycache__").mkdir()
            (workspace / "pkg" / "__pycache__" / "core.cpython-312.pyc").write_bytes(b"\x00\x01")
            (workspace / ".pytest_cache").mkdir()
            (workspace / ".pytest_cache" / "v").write_text("x", encoding="utf-8")
            (workspace / "pkg" / "core.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
            (workspace / "pkg" / "new.py").write_text("x = 1\n", encoding="utf-8")
            patch = run.take_patch(workspace, base)
            self.assertIn("return a + b", patch)
            self.assertIn("pkg/new.py", patch)
            self.assertNotIn("pycache", patch)
            self.assertNotIn("pytest_cache", patch)


class TheRealPath(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.logs = Path(self.temp.name) / "logs"
        self.source = Path(self.temp.name) / "testbed"
        self.base = run.fake_workspace(self.source, "fake__alpha-1")
        self.task = dataclasses.replace(tasks.read_task(FIXTURES / "tasks" / "fake__alpha-1"), base_commit=self.base)

    def tearDown(self):
        self.temp.cleanup()

    def test_prepare_copies_the_testbed_out_starts_the_container_on_it_and_checks_the_base(self):
        docker = FakeDocker(self.source)
        plan = run.prepare(self.logs, "t", "solo", self.task, None, "claude-sonnet-5-5", {}, False, docker)
        kinds = [call[0] for call in docker.calls]
        self.assertEqual(kinds, ["rm", "create", "cp", "rm", "run", "inspect"])
        name = plan["container"]
        self.assertTrue(name.startswith("flowbench-t-solo-fake__alpha-1-a1"))
        started = next(call for call in docker.calls if call[0] == "run")
        self.assertEqual(started[1:4], (self.task.image, name, plan["workspace"]))
        self.assertEqual(started[4], f"flowbench.run={plan['run_id']}")
        self.assertEqual((plan["image_id"], plan["base_commit"], plan["start_commit"], plan["containers"]),
                         ("sha256:fake", self.base, self.base, [name]))
        self.assertIn("/opt/miniconda3/bin/activate testbed", run.test_shell(name))

    def test_an_image_whose_repository_does_not_descend_from_the_base_is_a_harness_error(self):
        other = dataclasses.replace(self.task, base_commit="0" * 40)
        with self.assertRaises(run.RunError) as caught:
            run.prepare(self.logs, "t", "solo", other, None, "claude-sonnet-5-5", {}, False, FakeDocker(self.source))
        self.assertIn("does not descend", str(caught.exception))

    def test_an_image_with_a_build_commit_on_the_base_takes_the_patch_against_that_commit(self):
        (self.source / "built.txt").write_text("the image build's own file\n", encoding="utf-8")
        run.git(self.source, "add", "-A")
        run.git(self.source, "commit", "-q", "-m", "SWE-bench")
        built = run.git(self.source, "rev-parse", "HEAD").strip()
        plan = run.prepare(self.logs, "t", "solo", self.task, None, "claude-sonnet-5-5", {}, False, FakeDocker(self.source))
        self.assertEqual((plan["base_commit"], plan["start_commit"]), (self.base, built))
        self.assertEqual(run.take_patch(plan["workspace"], plan["start_commit"]), "")
        prompt_fields = run.job_fields(plan, {"name": "work", "kind": "work"}, "work")
        self.assertEqual(prompt_fields["base_commit"], built)

    def test_builders_each_get_a_container_and_finish_removes_them_all(self):
        docker = FakeDocker(self.source)
        plan = run.prepare(self.logs, "t", "script", self.task, None, "claude-sonnet-5-5", {"builders": "2"}, False, docker)
        self.assertEqual(len(plan["containers"]), 3)
        self.assertEqual([b["container"] for b in plan["builders"]], plan["containers"][1:])
        docker.calls.clear()
        run.finish(plan, [], None, None, 60, False, docker, None, ["stopped early"])
        self.assertEqual([call for call in docker.calls if call[0] == "rm"], [("rm", name) for name in plan["containers"]])
        result = json.loads((Path(plan["run_dir"]) / "result.json").read_text(encoding="utf-8"))
        self.assertTrue(result["harness_error"])

    def test_the_agents_environment_carries_no_api_key(self):
        before = os.environ.get("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = "not-a-real-key"
        try:
            environment = run.agent_environment()
        finally:
            if before is None:
                del os.environ["ANTHROPIC_API_KEY"]
            else:
                os.environ["ANTHROPIC_API_KEY"] = before
        self.assertNotIn("ANTHROPIC_API_KEY", environment)

    def test_the_claude_command_is_headless_on_the_model_with_the_web_off(self):
        command = run.claude_command("claude-sonnet-5-5", 50, run.LOCAL_ONLY_DISALLOWED)
        self.assertEqual(command[:2], ["claude", "--print"])
        self.assertIn("--output-format=stream-json", command)
        self.assertEqual(command[command.index("--model") + 1], "claude-sonnet-5-5")
        self.assertEqual(command[command.index("--max-turns") + 1], "50")
        self.assertEqual(command[command.index("--disallowedTools") + 1], "WebFetch,WebSearch")


if __name__ == "__main__":
    unittest.main()
