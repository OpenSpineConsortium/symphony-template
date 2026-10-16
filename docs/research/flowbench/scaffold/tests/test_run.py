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
LIMITS = {"agent_seconds": 60, "run_seconds": 600, "max_turns": 10, "parallel": 3, "disallowed": run.DISALLOWED_TOOLS}


def fake_run(logs, arm, instance="fake__alpha-1", options=None, tag="t", limits=LIMITS, model="claude-sonnet-5-5",
             keep=False):
    task = tasks.read_task(FIXTURES / "tasks" / instance)
    return run.run_one(logs, tag, arm, task, None, model, options or {}, limits, True, str(FIXTURES), None, None, 60, keep)


class FakeDocker:
    """Records the commands; copy_out puts a prepared repository in place
    of the image's /testbed."""

    def __init__(self, source, failing=None):
        self.source = source
        self.failing = failing
        self.calls = []

    def create(self, image, name):
        self.calls.append(("create", image, name))
        if self.failing == "create":
            raise run.RunError("docker create failed: no such image")

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
        self.assertEqual(result["tokens"]["agents_uncounted"], 0)
        self.assertEqual(result["cost_source"], "estimated from tokens")
        self.assertEqual(result["cost_usd"], record.price(result["tokens"], "claude-sonnet-5-5"))
        self.assertEqual([a["agent"] for a in result["agents"]], ["work"])
        self.assertEqual(result["agents"][0]["tools"], ["Bash", "Read", "Edit", "Write", "Glob", "Grep"])
        self.assertEqual((result["effort"], result["excluded"]), ("medium", False))
        for name in ("plan.json", "result.json", "audit.json", "events.jsonl", "prediction.jsonl", "stages.json",
                     "problem.md", "mcp.json", "test"):
            self.assertTrue((run_dir / name).is_file(), name)
        self.assertFalse((run_dir / "workspace").exists(), "the workspace is removed unless --keep")
        kinds = [json.loads(line)["kind"] for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(kinds[:3], ["prepared", "stage_started", "agent_started"])
        self.assertEqual(kinds[-3:], ["patch_taken", "scored", "finished"])

    def test_the_script_runs_every_stage_and_counts_the_review(self):
        result = fake_run(self.logs, "script", keep=True)
        self.assertEqual([s["name"] for s in result["stages"]], ["build", "stack", "review", "verify", "fix"])
        self.assertFalse(any(s["skipped"] for s in result["stages"]))
        flow = result["flow"]
        self.assertEqual((flow["findings_raised"], flow["findings_confirmed"], flow["findings_fixed"]), (3, 1, 1))
        self.assertEqual(flow["findings_by_lens"], {"conventions": 1, "correctness": 1, "path": 1})
        self.assertEqual((flow["timeouts"], flow["turn_limits"], flow["review_rounds"]), (0, 0, 1))
        self.assertFalse(flow["orchestration_failure"])
        self.assertEqual(len(result["agents"]), 9)
        flow_dir = self.run_dir("script") / "flow"
        names = sorted(p.name for p in flow_dir.iterdir())
        self.assertEqual(names, ["findings-review-conventions.json", "findings-review-correctness.json",
                                 "findings-review-path.json", "fixed-fix.json", "stack.json",
                                 "verdict-verify-conventions-1.json", "verdict-verify-correctness-1.json",
                                 "verdict-verify-path-1.json"])

    def test_with_no_findings_the_verify_and_fix_stages_are_skipped(self):
        result = fake_run(self.logs, "script", options={"fake_findings": "0"})
        skipped = [s["name"] for s in result["stages"] if s["skipped"]]
        self.assertEqual(skipped, ["verify", "fix"])
        self.assertEqual(result["flow"]["findings_raised"], 0)
        self.assertFalse(result["flow"]["orchestration_failure"])

    def test_builders_work_in_copies_on_a_branch_each_and_the_stack_merges_them(self):
        result = fake_run(self.logs, "script", options={"builders": "3"}, keep=True)
        run_dir = self.run_dir("script")
        plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
        self.assertEqual([b["branch"] for b in plan["builders"]], ["builder-1", "builder-2", "builder-3"])
        for k in (1, 2, 3):
            copy = run_dir / f"builder-{k}"
            self.assertTrue((copy / ".git").is_dir(), "a copy with a repository of its own, not a worktree")
            self.assertEqual(run.git(copy, "branch", "--show-current").strip(), f"builder-{k}")
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
        self.assertTrue(any("left no findings-review-path.json" in r for r in reasons), reasons)
        self.assertEqual(result["flow"]["findings_raised"], 2)
        self.assertEqual(result["scoring"]["reason"], "unresolved")

    def test_a_usage_limit_is_the_harness_error_not_the_arms(self):
        result = fake_run(self.logs, "script", options={"fake_limit": "build"})
        self.assertTrue(result["harness_error"])
        audit = json.loads((self.run_dir("script") / "audit.json").read_text(encoding="utf-8"))
        self.assertTrue(audit["harness_error"])
        self.assertTrue(any("usage limit" in reason for reason in audit["reasons"]), audit)
        self.assertEqual(result["agents"][0]["status"], "usage_limit")
        self.assertFalse(result["flow"]["orchestration_failure"])

    def test_symphony_claims_a_branch_opens_the_pull_request_and_answers_the_review(self):
        result = fake_run(self.logs, "symphony", keep=True)
        run_dir = self.run_dir("symphony")
        branches = subprocess.run(["git", "-C", str(run_dir / "workspace"), "branch", "--show-current"],
                                  capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(branches, "claude/1")
        self.assertTrue((run_dir / "flow" / "pull-request.md").is_file())
        answers = json.loads((run_dir / "flow" / "answers-answer.json").read_text(encoding="utf-8"))
        self.assertEqual(len(answers["answers"]), 3)
        self.assertEqual((result["flow"]["review_rounds"], result["flow"]["findings_fixed"], result["flow"]["answers"]), (1, 1, 1))
        self.assertIn("return a + b", (run_dir / "model.patch").read_text(encoding="utf-8"))

    def test_the_second_attempt_gets_its_own_directory(self):
        fake_run(self.logs, "solo")
        fake_run(self.logs, "solo")
        self.assertTrue(self.run_dir("solo", attempt=2).is_dir())
        self.assertEqual(run.next_attempt(self.logs, "t", "solo", "fake__alpha-1"), 3)

    def test_the_prompts_name_neither_the_task_repository_nor_the_gold_patch(self):
        fake_run(self.logs, "script", options={"builders": "2"})
        prompts = list((self.run_dir("script") / "agents").glob("*.prompt.md"))
        self.assertEqual(len(prompts), 10)
        for prompt in prompts:
            text = prompt.read_text(encoding="utf-8")
            self.assertNotIn(str(FIXTURES), text, prompt.name)
            self.assertNotIn("gold", text.lower(), prompt.name)
            self.assertIn("flowbench-", text, prompt.name)
            self.assertIn(str(self.run_dir("script") / "test"), text, "the wrapper script is named")

    def test_a_relative_logs_directory_gives_absolute_paths_to_the_agents_and_the_container(self):
        before = os.getcwd()
        os.chdir(self.temp.name)
        try:
            fake_run("logs", "solo", keep=True)
        finally:
            os.chdir(before)
        plan = json.loads((self.run_dir("solo") / "plan.json").read_text(encoding="utf-8"))
        self.assertTrue(Path(plan["workspace"]).is_absolute())
        self.assertTrue(Path(plan["test_shell"]).is_absolute())

    def test_the_run_time_limit_skips_the_stages_after_it(self):
        limits = dict(LIMITS, run_seconds=0)
        result = fake_run(self.logs, "script", limits=limits)
        self.assertTrue(all(s["skipped"] for s in result["stages"]))
        self.assertEqual(result["patch_bytes"], 0)
        self.assertEqual(result["scoring"]["reason"], "empty_patch")


class TheAudit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.logs = Path(self.temp.name) / "logs"
        self.task = dataclasses.replace(tasks.read_task(FIXTURES / "tasks" / "fake__alpha-1"),
                                        hidden_tests=("tests/test_core.py::test_add_hidden",))

    def tearDown(self):
        self.temp.cleanup()

    def audit(self, stream_text):
        plan = run.prepare(self.logs, "t", "solo", self.task, None, "claude-sonnet-5-5", {}, True)
        agents_dir = Path(plan["run_dir"]) / "agents"
        agents_dir.mkdir()
        (agents_dir / "work.stream.jsonl").write_text(stream_text, encoding="utf-8")
        stages = [{"name": "work", "kind": "work", "agents": [{"agent": "work"}], "missing": [], "skipped": False}]
        return run.audit_streams(plan, stages, run.forbidden_for(self.task, FIXTURES))

    def test_the_task_repositorys_path_and_the_answers_files_are_hits(self):
        hits, network = self.audit(f"cat {FIXTURES.resolve()}/tasks/x/gold.patch\n")
        self.assertEqual(sorted(h["kind"] for h in hits), ["gold_patch", "task_repo"])
        self.assertEqual(network, [])

    def test_a_hidden_tests_name_is_recorded_and_latest_patch_is_no_test_patch(self):
        hits, _ = self.audit("pytest tests/test_core.py::test_add_hidden; cat latest.patch\n")
        self.assertEqual([h["kind"] for h in hits], ["hidden_test"])
        self.assertTrue(all(h["kind"] not in run.EXCLUDING_KINDS for h in hits))

    def test_a_network_command_is_recorded(self):
        hits, network = self.audit('{"command": "pip install requests && curl http://x"}\n')
        self.assertEqual(hits, [])
        self.assertEqual(sorted(n["command"] for n in network), ["curl", "pip install"])

    def test_a_run_that_looked_outside_is_excluded_in_its_record(self):
        plan = run.prepare(self.logs, "t", "solo", self.task, None, "claude-sonnet-5-5", {}, True)
        agents_dir = Path(plan["run_dir"]) / "agents"
        agents_dir.mkdir()
        (agents_dir / "work.stream.jsonl").write_text("ls swe-bench-tasks\n", encoding="utf-8")
        agent = {"agent": "work", "stage": "work", "status": "success", "harness_error": False, "duration_ms": 1,
                 "tokens": None, "cost_usd": None, "end": "success", "result_text": None}
        stages = [{"name": "work", "kind": "work", "agents": [agent], "missing": [], "skipped": False, "duration_ms": 1}]
        result = run.finish(plan, stages, None, None, 60, False, None, None, [], run.forbidden_for(self.task, FIXTURES))
        self.assertTrue(result["excluded"])
        self.assertFalse(result["harness_error"])
        audit = json.loads((Path(plan["run_dir"]) / "audit.json").read_text(encoding="utf-8"))
        self.assertEqual([h["kind"] for h in audit["looked_outside"]], ["task_repo_name"])
        self.assertEqual(result["tokens"]["agents_uncounted"], 1)


class HowAnAgentEnded(unittest.TestCase):
    def test_the_status_reads_the_exit_the_result_event_and_the_clock(self):
        self.assertEqual(run.status_of(0, {"end": "success", "is_error": False}, False), "success")
        self.assertEqual(run.status_of(0, {"end": "success"}, True), "timeout")
        self.assertEqual(run.status_of(1, {"end": "error_max_turns", "is_error": True}, False), "turn_limit")
        self.assertEqual(run.status_of(1, {"end": "error_during_execution", "is_error": True,
                                           "result_text": "You've hit your usage limit."}, False), "usage_limit")
        self.assertEqual(run.status_of(1, {"end": "error_during_execution", "is_error": True, "result_text": "boom"}, False),
                         "error")
        self.assertEqual(run.status_of(None, {"end": "no result event", "is_error": True}, False), "error")

    def test_a_failed_login_is_the_harnesss_error_wherever_it_shows(self):
        self.assertEqual(run.status_of(1, {"end": "success", "is_error": True,
                                           "result_text": "Invalid API key - Please run /login"}, False), "auth_error")
        self.assertEqual(run.status_of(1, {"end": "no result event", "is_error": True}, False,
                                       "Error: not logged in"), "auth_error")
        self.assertIn("auth_error", run.HARNESS_STATUSES)

    def test_only_a_subscription_login_passes(self):
        self.assertIsNone(run.login_problem_of({"loggedIn": True, "authMethod": "oauth_token", "apiProvider": "firstParty"}))
        self.assertIn("not logged in", run.login_problem_of({"loggedIn": False}))
        self.assertIn("API key", run.login_problem_of({"loggedIn": True, "authMethod": "api_key", "apiProvider": "firstParty"}))
        self.assertIn("API key", run.login_problem_of({"loggedIn": True, "authMethod": "oauth_token", "apiProvider": "bedrock"}))

    def test_the_run_token_is_stripped_from_the_result_text(self):
        self.assertEqual(run.strip_token("flowbench-abc\nedited pkg/core.py\n", "flowbench-abc"), "edited pkg/core.py")
        self.assertIsNone(run.strip_token("flowbench-abc", "flowbench-abc"))


class ThePreflight(unittest.TestCase):
    def arguments(self, **given):
        import argparse
        values = {"fake": False, "fake_agents": True, "dataset": None, "swebench": "/no/such/swebench"}
        values.update(given)
        return argparse.Namespace(**values)

    def test_a_real_run_without_the_dataset_or_the_harness_is_refused_before_it_spends_anything(self):
        with self.assertRaises(run.RunError) as caught:
            run.preflight(self.arguments())
        self.assertIn("needs --dataset", str(caught.exception))
        self.assertIn("/no/such/swebench is not there", str(caught.exception))

    def test_a_fake_run_needs_nothing(self):
        run.preflight(self.arguments(fake=True))

    def test_a_lane_that_fails_its_preflight_takes_no_item(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "backlog.jsonl"
            backlog.add(path, "t", ["fake__alpha-1"], ["solo"])
            code = run.main(["lane", "--backlog", str(path), "--lane", "lane-1", "--logs", str(Path(temp) / "logs"),
                             "--task-repo", str(FIXTURES), "--fake-agents", "--swebench", "/no/such/swebench"])
            self.assertEqual(code, 1)
            self.assertEqual([i["state"] for i in backlog.read_items(path)], ["pending"])


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

    def test_a_run_that_cannot_start_is_the_items_harness_error_and_the_lane_goes_on(self):
        with tempfile.TemporaryDirectory() as temp:
            logs = Path(temp) / "logs"
            path = Path(temp) / "backlog.jsonl"
            backlog.add(path, "t", ["fake__alpha-1", "no__such-1", "fake__beta-1"], ["solo"])
            code = run.main(["lane", "--backlog", str(path), "--lane", "lane-1", "--logs", str(logs), "--task-repo",
                             str(FIXTURES), "--fake"])
            self.assertEqual(code, 0)
            items = backlog.read_items(path)
            self.assertEqual([(i["instance"], i["state"], i["harness_error"]) for i in items],
                             [("fake__alpha-1", "done", False), ("no__such-1", "failed", True), ("fake__beta-1", "done", False)])


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

    def test_a_file_the_image_already_held_untracked_is_not_in_the_patch(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "workspace"
            base = run.fake_workspace(workspace, "x")
            (workspace / "built.so").write_bytes(b"\x7fELF")
            untracked = run.exclude_from_patch(workspace)
            self.assertEqual(untracked, ["built.so"])
            (workspace / "after.txt").write_text("made by the agent\n", encoding="utf-8")
            patch = run.take_patch(workspace, base)
            self.assertIn("after.txt", patch)
            self.assertNotIn("built.so", patch)

    def test_a_mode_change_alone_is_no_change(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "workspace"
            base = run.fake_workspace(workspace, "x")
            (workspace / "pkg" / "core.py").chmod(0o755)
            self.assertEqual(run.take_patch(workspace, base), "")


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
        wrapper = Path(plan["test_shell"]).read_text(encoding="utf-8")
        self.assertIn("/opt/miniconda3/bin/activate testbed", wrapper)
        self.assertIn(f"docker exec -i {name}", wrapper)
        self.assertTrue(os.access(plan["test_shell"], os.X_OK))
        self.assertEqual((plan["effort"], plan["untracked_in_image"]), ("medium", 0))

    def test_an_image_whose_repository_does_not_descend_from_the_base_is_a_harness_error(self):
        other = dataclasses.replace(self.task, base_commit="0" * 40)
        docker = FakeDocker(self.source)
        with self.assertRaises(run.RunError) as caught:
            run.prepare(self.logs, "t", "solo", other, None, "claude-sonnet-5-5", {}, False, docker)
        self.assertIn("does not descend", str(caught.exception))
        self.assertEqual([call[0] for call in docker.calls][-1], "rm", "what was started is removed again")

    def test_a_run_that_cannot_start_leaves_a_record_that_says_so(self):
        docker = FakeDocker(self.source, failing="create")
        with self.assertRaises(run.RunError):
            run.run_one(self.logs, "t", "solo", self.task, None, "claude-sonnet-5-5", {}, LIMITS, False, None, None, None,
                        60, False, docker)
        run_dir = run.run_directory(self.logs, "t", "solo", "fake__alpha-1", 1)
        result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        audit = json.loads((run_dir / "audit.json").read_text(encoding="utf-8"))
        self.assertTrue(result["harness_error"])
        self.assertIsNone(result["scoring"])
        self.assertIn("no such image", audit["reasons"][0])

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
        self.assertTrue(all(Path(b["test_shell"]).is_file() for b in plan["builders"]))
        docker.calls.clear()
        run.finish(plan, [], None, None, 60, False, docker, None, ["stopped early"])
        self.assertEqual([call for call in docker.calls if call[0] == "rm"], [("rm", name) for name in plan["containers"]])
        result = json.loads((Path(plan["run_dir"]) / "result.json").read_text(encoding="utf-8"))
        self.assertTrue(result["harness_error"])
        self.assertFalse(Path(plan["workspace"]).exists())
        self.assertFalse(any(Path(b["workspace"]).exists() for b in plan["builders"]))

    def test_the_agents_environment_carries_no_key_and_no_other_provider(self):
        before = {key: os.environ.get(key) for key in ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL")}
        os.environ["ANTHROPIC_API_KEY"] = "not-a-real-key"
        os.environ["ANTHROPIC_BASE_URL"] = "http://elsewhere"
        try:
            environment = run.agent_environment()
        finally:
            for key, value in before.items():
                if value is None:
                    del os.environ[key]
                else:
                    os.environ[key] = value
        self.assertNotIn("ANTHROPIC_API_KEY", environment)
        self.assertNotIn("ANTHROPIC_BASE_URL", environment)

    def test_the_claude_command_is_headless_on_the_login_with_the_web_and_subagents_off(self):
        command = run.claude_command("claude-sonnet-5-5", "high", 50, run.DISALLOWED_TOOLS, "/r/mcp.json")
        self.assertEqual(command[:2], ["claude", "--print"])
        self.assertIn("--output-format=stream-json", command)
        self.assertIn("--strict-mcp-config", command)
        for flag, value in (("--model", "claude-sonnet-5-5"), ("--effort", "high"), ("--max-turns", "50"),
                            ("--setting-sources", "project"), ("--mcp-config", "/r/mcp.json"),
                            ("--disallowedTools", "WebFetch,WebSearch,Task,Agent")):
            self.assertEqual(command[command.index(flag) + 1], value, flag)
        self.assertNotIn("--max-turns", run.claude_command("claude-sonnet-5-5", "medium", 0, run.DISALLOWED_TOOLS, "m"))


if __name__ == "__main__":
    unittest.main()
