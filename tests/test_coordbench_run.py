"""The runner and the drivers are what turn an arm into scored CooperBench
results, so these pin what they do to docker, to the hub and to the logs.
Docker is a fake that records every command and answers the few whose
output the runner reads; the hub is the real one, in this process on an
ephemeral port; CooperBench's scorer is a fake with the shape of its
results. Nothing here starts a container or a Claude."""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
COORDBENCH = ROOT / "experiment" / "coordbench"
sys.path.insert(0, str(COORDBENCH))

import drivers  # noqa: E402
import hub as hub_module  # noqa: E402
import run as runner  # noqa: E402

REAL_COOPERBENCH_TEST = runner.cooperbench_test

# Distinctive, so a leak is found by a plain search, and shaped like no
# real credential, so the repository's own secret check lets it be.
SECRET = "coordbench-fake-oauth-token-7f3a9c2e51d0"
BASE = "0123456789abcdef0123456789abcdef01234567"
REPO, TASK = "pallets_click_task", 2068
IMAGE = "akhatua/cooperbench-pallets-click:task2068"
PATCHES = {
    "agent1": "diff --git a/src/a.py b/src/a.py\n--- a/src/a.py\n+++ b/src/a.py\n@@ -1 +1 @@\n-a\n+A\n",
    "agent2": "diff --git a/src/b.py b/src/b.py\n--- a/src/b.py\n+++ b/src/b.py\n@@ -1 +1 @@\n-b\n+B\n",
}
SAMPLE_STREAM = "\n".join(json.dumps(event) for event in [
    {"type": "system", "subtype": "init", "session_id": "s1", "tools": ["Bash"]},
    {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Working."}]}},
    "not json at all",
    {"type": "result", "subtype": "success", "is_error": False, "num_turns": 12, "total_cost_usd": 0.42,
     "result": "Done.", "usage": {"input_tokens": 1200, "output_tokens": 340,
                                  "cache_read_input_tokens": 50000, "cache_creation_input_tokens": 7000}},
]) + "\n"
MERGED_RESULT = {
    "apply_status": {"agent1": "clean", "agent2": "clean"},
    "merge": {"status": "clean", "strategy": "naive", "diff": ""},
    "feature1": {"feature_id": 1, "passed": True, "tests_passed": 3, "tests_failed": 0, "test_output": "ok"},
    "feature2": {"feature_id": 6, "passed": True, "tests_passed": 2, "tests_failed": 0, "test_output": "ok"},
    "both_passed": True, "error": None,
}
SOLO_RESULT = {"setting": "solo", "patch_lines": 6, "feature1": {"passed": True, "test_output": "ok"},
               "feature2": {"passed": False, "test_output": "1 failed"}, "both_passed": False, "error": None}
RESULT_KEYS = {"repo", "task_id", "features", "setting", "run_id", "run_name", "agent_framework", "model", "arm",
               "driver", "started_at", "ended_at", "duration_seconds", "agents", "metrics"}
AGENT_KEYS = {"feature_id", "role", "status", "input_tokens", "output_tokens", "cache_read_tokens",
              "cache_write_tokens", "steps", "error"}
COOP_EVAL_KEYS = ["repo", "task_id", "features", "setting", "apply_status", "merge", "feature1", "feature2",
                  "both_passed", "error", "evaluated_at"]
SOLO_EVAL_KEYS = ["repo", "task_id", "features", "setting", "merge", "feature1", "feature2", "both_passed",
                  "error", "evaluated_at"]
NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def env_value(arguments, name):
    """The value a docker command passes for -e NAME=value."""
    for index, word in enumerate(arguments[:-1]):
        if word == "-e" and arguments[index + 1].startswith(f"{name}="):
            return arguments[index + 1].split("=", 1)[1]
    return None


def call_tool(rpc_url, tool, arguments):
    body = json.dumps({"tool": tool, "arguments": arguments}).encode()
    request = urllib.request.Request(rpc_url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with NO_PROXY.open(request, timeout=10) as response:
        return json.loads(response.read())


class FakeDocker:
    """Stands in for drivers.docker: records every command and answers the
    ones whose output the runner reads, the way docker would."""

    def __init__(self, python=True, mountpoint="/var/lib/docker/volumes/v/_data", fail_seed=False):
        self.stream = SAMPLE_STREAM
        self.calls = []
        self.lock = threading.Lock()
        self.python = python
        self.mountpoint = mountpoint
        self.fail_seed = fail_seed
        self.claude_times_out = False
        self.on_claude = None

    def __call__(self, *args, input=None, timeout=None, output=None):
        args = [str(arg) for arg in args]
        with self.lock:
            self.calls.append({"args": args, "input": input, "output": output})
        code, out = self.answer(args, output)
        return subprocess.CompletedProcess(["docker", *args], code, out, "" if code == 0 else "fake failure")

    def answer(self, args, output):
        if output is not None:
            return self.run_claude(args, output)
        if args[:2] in (["network", "inspect"], ["container", "inspect"]):
            return 1, ""
        if args[:2] == ["run", "--rm"]:
            return (1, "") if self.fail_seed else (0, BASE + "\n")
        if args[:2] == ["volume", "inspect"]:
            return 0, self.mountpoint + "\n"
        if args[0] == "cp" and args[1].endswith(":/workspace/repo"):
            return self.copy_repository(Path(args[2]))
        if args[0] == "exec" and args[-1] == "command -v python3":
            return (0, "/usr/bin/python3\n") if self.python else (1, "")
        if args[0] == "exec" and args[-2:] == ["cat", "/workspace/repo/patch.txt"]:
            return self.patch_of(args[1])
        return 0, ""

    def run_claude(self, args, output):
        if self.claude_times_out:
            raise subprocess.TimeoutExpired(args, 1)
        if self.on_claude:
            self.on_claude(args)
        Path(output).write_text(self.stream, encoding="utf-8")
        return 0, None

    def copy_repository(self, destination):
        (destination / ".git" / "info").mkdir(parents=True)
        (destination / "README.md").write_text("the task's repository\n", encoding="utf-8")
        return 0, ""

    def patch_of(self, container):
        for agent, patch in PATCHES.items():
            if container.endswith("-" + agent):
                return 0, patch
        return 1, ""

    def commands(self):
        with self.lock:
            return [call["args"] for call in self.calls]

    def matching(self, *head):
        return [args for args in self.commands() if args[:len(head)] == list(head)]


class FakeScorer:
    """Stands in for run.cooperbench_test, CooperBench's test_solo and test_merged."""

    def __init__(self):
        self.calls = []

    def __call__(self, kind, arguments, cooperbench_dir):
        self.calls.append((kind, arguments, str(cooperbench_dir)))
        return dict(SOLO_RESULT if kind == "solo" else MERGED_RESULT)


class RecordingDriver:
    """A driver that starts nothing, for tests of provisioning alone."""

    name = "recording"
    framework = "test"
    host_workspace = False
    resumable = False

    def __init__(self):
        self.jobs = []

    def start(self, job):
        self.jobs.append(job)
        return job

    def wait(self, job):
        return drivers.AgentOutcome(status="Submitted", patch=PATCHES.get(job.agent, ""))


def write_dataset(cooperbench_dir):
    task = cooperbench_dir / "dataset" / REPO / f"task{TASK}"
    for feature in (1, 2, 6, 10):
        (task / f"feature{feature}").mkdir(parents=True)
        (task / f"feature{feature}" / "feature.md").write_text(f"**Title**: Feature {feature}\n\nDo {feature}.\n",
                                                                encoding="utf-8")
    subsets = cooperbench_dir / "dataset" / "subsets"
    subsets.mkdir(parents=True)
    flash = {"name": "flash", "tasks": [{"repo": "other_task", "task_id": 1, "pairs": [[1, 2]]},
                                        {"repo": REPO, "task_id": TASK, "pairs": [[6, 1], [2, 10]]}]}
    (subsets / "flash.json").write_text(json.dumps(flash), encoding="utf-8")


class RunnerCase(unittest.TestCase):
    """A temporary CooperBench tree, a live hub in this process, and docker
    and the scorer replaced by fakes for the length of each test."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="coordbench-run-test-"))
        self.cooperbench = self.tmp / "cooperbench"
        write_dataset(self.cooperbench)
        self.logs = self.cooperbench / "logs"
        self.hub = hub_module.Hub()
        self.server = hub_module.serve_in_background(self.hub)
        self.hub_url = self.hub.bound_url
        self.docker = FakeDocker(mountpoint=str(self.tmp / "volume"))
        self.scorer = FakeScorer()
        for patcher in (mock.patch.object(drivers, "docker", self.docker),
                        mock.patch.object(runner, "cooperbench_test", self.scorer),
                        mock.patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": SECRET})):
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def settings(self, arm, **overrides):
        return {"arm": arm, "driver": "recording", "model": "claude-test", "run_name": "t",
                "log_dir": self.logs, "cooperbench_dir": self.cooperbench, "hub": self.hub_url,
                "timeout_s": 60.0, "max_turns": None, "keep": False, "force": False, "options": {}, **overrides}

    def prepare(self, arm, driver=None, **overrides):
        driver = driver or RecordingDriver()
        plan, handles = runner.prepare_pair(self.settings(arm, **overrides), runner.HubClient(self.hub_url),
                                            driver, REPO, TASK, [1, 6])
        return plan, handles, driver

    def main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = runner.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def run_arguments(self, arm, *extra):
        return ["run", "--arm", arm, "--repo", REPO, "--task", str(TASK), "--hub", self.hub_url,
                "--cooperbench-dir", str(self.cooperbench), "--name", "t", "--model", "claude-test", *extra]

    def pair(self, setting="coop", features="f1_f6"):
        return self.logs / "t" / setting / REPO / str(TASK) / features

    def options_of(self, plan):
        return self.hub.runs[plan["run_id"]].run.options

    def assert_secret_nowhere(self):
        for call in self.docker.commands():
            self.assertNotIn(SECRET, " ".join(call))
        for call in self.docker.calls:
            self.assertNotIn(SECRET, call["input"] or "")
        for path in self.tmp.rglob("*"):
            if path.is_file():
                self.assertNotIn(SECRET.encode(), path.read_bytes(), str(path))


class TheDataset(RunnerCase):
    def test_specs_are_read_from_each_features_feature_md(self):
        specs = runner.read_specs(self.cooperbench / "dataset", REPO, TASK, [1, 6])
        self.assertEqual(specs, {1: "**Title**: Feature 1\n\nDo 1.\n", 6: "**Title**: Feature 6\n\nDo 6.\n"})

    def test_a_missing_spec_names_its_path(self):
        with self.assertRaisesRegex(FileNotFoundError, "feature7"):
            runner.read_specs(self.cooperbench / "dataset", REPO, TASK, [1, 7])

    def test_a_subset_gives_every_pair_of_the_task_sorted(self):
        pairs = runner.subset_pairs(self.cooperbench / "dataset", "flash", REPO, TASK)
        self.assertEqual(pairs, [[1, 6], [2, 10]])
        with self.assertRaises(ValueError):
            runner.subset_pairs(self.cooperbench / "dataset", "flash", REPO, 9999)

    def test_image_names_follow_cooperbench(self):
        self.assertEqual(runner.image_name(REPO, TASK), IMAGE)
        self.assertEqual(runner.image_name("dottxt_ai_outlines_task", 1655),
                         "akhatua/cooperbench-dottxt-ai-outlines:task1655")


class Provisioning(RunnerCase):
    def test_an_arm_with_no_needs_gets_a_container_per_agent_with_coordbench_inside(self):
        plan, _, driver = self.prepare("coop")
        commands = self.docker.commands()
        self.assertIn(["network", "create", "coordbench"], commands)
        self.assertFalse([c for c in commands if "coordbench-git" in c or c[0] == "volume"])
        self.assertEqual([a["id"] for a in plan["agents"]], ["agent1", "agent2"])
        for agent in plan["agents"]:
            container = agent["container"]
            started = [c for c in self.docker.matching("run", "-d", "--name", container)]
            self.assertEqual(len(started), 1)
            arguments = started[0]
            for pair in (["--network", "coordbench"], ["--add-host", "host.docker.internal:host-gateway"],
                         ["--entrypoint", "sh"]):
                self.assertIn(pair, [arguments[i:i + 2] for i in range(len(arguments) - 1)])
            self.assertEqual(env_value(arguments, "COORD_MCP_URL"), agent["mcp_url"])
            self.assertEqual(env_value(arguments, "COORD_RPC_URL"), agent["rpc_url"])
            self.assertEqual(arguments[-3:-1], [IMAGE, "-c"])
            self.assertIn("sleep infinity", arguments[-1])
            self.assertIn(["cp", f"{COORDBENCH}/.", f"{container}:/opt/coordbench"], commands)
            self.assertIn(["exec", container, "python3", "/opt/coordbench/cli.py", "install", "/usr/local/bin"],
                          commands)
        self.assertFalse([c for c in commands if "bash" in c and "-lc" in c])
        self.assertEqual(self.options_of(plan), {})
        self.assertEqual([job.agent for job in driver.jobs], ["agent1", "agent2"])
        self.assertEqual(driver.jobs[0].env, {"COORD_MCP_URL": plan["agents"][0]["mcp_url"],
                                              "COORD_RPC_URL": plan["agents"][0]["rpc_url"]})
        self.assertIn("Feature 1", driver.jobs[0].prompt)

    def test_an_image_without_python_runs_without_shell_commands(self):
        self.docker.python = False
        plan, _, _ = self.prepare("coop")
        self.assertFalse([c for c in self.docker.commands() if "/opt/coordbench/cli.py" in c])
        self.assertTrue(any("no python3" in warning for warning in plan["warnings"]))

    def test_a_git_remote_is_a_seeded_repository_on_the_shared_git_server(self):
        plan, _, _ = self.prepare("coop-git")
        run_id = plan["run_id"]
        url = f"git://coordbench-git:9418/{run_id}/repo.git"
        commands = self.docker.commands()
        server = self.docker.matching("run", "-d", "--name", "coordbench-git")[0]
        self.assertIn("127.0.0.1:9418:9418", server)
        self.assertIn("coordbench-git-data:/git", server)
        self.assertEqual(server[-1], "cooperbench-git-server:local")
        init = [c for c in self.docker.matching("exec", "coordbench-git", "sh", "-c")
                if f"/git/{run_id}/repo.git" in c[-1]][0]
        self.assertIn("git init -q --bare", init[-1])
        seed = self.docker.matching("run", "--rm")[0]
        self.assertEqual(seed[:8], ["run", "--rm", "--network", "coordbench", "--entrypoint", "sh", IMAGE, "-c"])
        self.assertIn(f"git push -q {url} HEAD:refs/heads/main", seed[-1])
        for agent in ("agent1", "agent2"):
            self.assertIn(["exec", "coordbench-git", "git", "-C", f"/git/{run_id}/repo.git", "branch", agent, "main"],
                          commands)
        setups = [c for c in self.docker.matching("exec", "-w", "/workspace/repo") if c[-2] == "-lc"]
        self.assertEqual(len(setups), 2)
        self.assertIn(f"git remote add team {url}", setups[0][-1])
        self.assertIn("git checkout -b agent1", setups[0][-1])
        self.assertIn("git push -u team agent2 --force", setups[1][-1])
        self.assertEqual(self.options_of(plan), {"git_remote": url, "base_ref": BASE,
                                                 "git_remote_host": f"git://127.0.0.1:9418/{run_id}/repo.git"})
        first_agent = self.docker.matching("run", "-d", "--name", plan["agents"][0]["container"])[0]
        self.assertLess(commands.index(seed), commands.index(first_agent))
        runner.teardown(plan)
        self.assertIn(["exec", "coordbench-git", "rm", "-rf", f"/git/{run_id}"], self.docker.commands())

    def test_a_shared_volume_is_one_volume_per_run_at_workspace_shared(self):
        plan, _, _ = self.prepare("team")
        volume = f"coordbench-shared-{plan['run_id']}"
        self.assertIn(["volume", "create", volume], self.docker.commands())
        for agent in plan["agents"]:
            started = self.docker.matching("run", "-d", "--name", agent["container"])[0]
            self.assertIn(f"{volume}:/workspace/shared", started)
        self.assertEqual(self.options_of(plan), {"shared_dir": "/workspace/shared",
                                                 "shared_dir_host": str(self.tmp / "volume")})
        self.assertFalse([c for c in self.docker.commands() if "coordbench-git" in c])
        runner.teardown(plan)
        self.assertIn(["volume", "rm", "-f", volume], self.docker.commands())
        self.assertIn(["rm", "-f", *[a["container"] for a in plan["agents"]]], self.docker.commands())

    def test_an_arm_from_elsewhere_brings_its_plugins_and_mcp_servers(self):
        arm_dir = self.tmp / "arms" / "myarm"
        shutil.copytree(COORDBENCH / "arms" / "coop", arm_dir, ignore=shutil.ignore_patterns("__pycache__"))
        (arm_dir / "extra-plugin" / ".claude-plugin").mkdir(parents=True)
        (arm_dir / "extra-plugin" / ".claude-plugin" / "plugin.json").write_text('{"name": "extra"}')
        config = json.loads((arm_dir / "arm.json").read_text())
        servers = {"docs": {"type": "http", "url": "http://docs.example/mcp"}}
        config.update(name="myarm", plugins=["extra-plugin"], mcp_servers=servers)
        (arm_dir / "arm.json").write_text(json.dumps(config))
        plan, _, driver = self.prepare(str(arm_dir))
        container = plan["agents"][0]["container"]
        commands = self.docker.commands()
        self.assertIn(["cp", f"{arm_dir}/.", f"{container}:/opt/coordbench/arms/myarm"], commands)
        self.assertIn(["cp", f"{arm_dir / 'extra-plugin'}/.", f"{container}:/opt/coordbench-plugins/0-extra-plugin"],
                      commands)
        job = driver.jobs[0]
        self.assertEqual(job.plugins, ["/opt/coordbench-plugins/0-extra-plugin"])
        self.assertEqual(job.mcp_servers, servers)
        flags = drivers.claude_flags(job)
        self.assertIn("/opt/coordbench/arms/myarm", flags)
        self.assertIn("/opt/coordbench-plugins/0-extra-plugin", flags)

    def test_a_failed_provision_is_recorded_as_an_error_and_torn_down(self):
        self.docker.fail_seed = True
        code, _, err = self.main(*self.run_arguments("coop-git", "--features", "1,6"))
        self.assertEqual(code, 1)
        self.assertIn("error", err)
        result = json.loads((self.pair() / "result.json").read_text())
        self.assertIn("seeding the shared repository", result["error"])
        self.assertEqual({a["status"] for a in result["agents"].values()}, {"Error"})
        self.assertFalse((self.pair() / "eval.json").exists())
        self.assertTrue([c for c in self.docker.commands() if c[:4] == ["exec", "coordbench-git", "rm", "-rf"]])
        self.assertEqual(self.scorer.calls, [])


class TheClaudeCliDriver(RunnerCase):
    def job(self, **overrides):
        fields = {"run_id": "r1", "agent": "agent1", "role": "peer", "features": (1,), "container": "c-agent1",
                  "prompt": "Implement feature 1.\n", "env": {"COORD_MCP_URL": "http://h:1/mcp/r1/agent1",
                                                              "COORD_RPC_URL": "http://h:1/rpc/r1/agent1"},
                  "arm_dir": str(COORDBENCH / "arms" / "coop"), "plugins": ["/opt/coordbench-plugins/0-extra"],
                  "mcp_servers": {"docs": {"type": "http", "url": "http://docs"}},
                  "model": "anthropic/claude-test", "timeout_s": 30, "max_turns": 40,
                  "log_path": str(self.tmp / "agent1_stream.jsonl")}
        fields.update(overrides)
        return drivers.AgentJob(**fields)

    def test_it_runs_headless_claude_with_the_arm_as_a_plugin(self):
        driver = drivers.ClaudeCliDriver()
        outcome = driver.wait(driver.start(self.job()))
        writes = self.docker.matching("exec", "-i", "c-agent1", "sh", "-c")
        self.assertEqual([(c[-1]) for c in writes], ["cat > /tmp/coord-prompt.txt", "cat > /tmp/coord-mcp.json"])
        inputs = [call["input"] for call in self.docker.calls if call["args"] in writes]
        self.assertEqual(inputs[0], "Implement feature 1.\n")
        self.assertEqual(json.loads(inputs[1]), {"mcpServers": {"docs": {"type": "http", "url": "http://docs"}}})
        runs = [call for call in self.docker.calls if call["output"]]
        self.assertEqual(len(runs), 1)
        arguments = runs[0]["args"]
        self.assertEqual(runs[0]["output"], str(self.tmp / "agent1_stream.jsonl"))
        self.assertEqual(arguments[:3], ["exec", "-w", "/workspace/repo"])
        self.assertEqual(arguments[-4:-1], ["c-agent1", "bash", "-lc"])
        for name, value in (("ANTHROPIC_MODEL", "claude-test"), ("CLAUDE_CONFIG_DIR", "/tmp/claude-cfg"),
                            ("IS_SANDBOX", "1"), ("COORD_MCP_URL", "http://h:1/mcp/r1/agent1"),
                            ("COORD_RPC_URL", "http://h:1/rpc/r1/agent1")):
            self.assertEqual(env_value(arguments, name), value)
        self.assertIn(["-e", "CLAUDE_CODE_OAUTH_TOKEN"], [arguments[i:i + 2] for i in range(len(arguments) - 1)])
        script = arguments[-1]
        self.assertIn("claude --verbose --output-format=stream-json --permission-mode=bypassPermissions "
                      "--plugin-dir /opt/coordbench/arms/coop --plugin-dir /opt/coordbench-plugins/0-extra "
                      "--mcp-config /tmp/coord-mcp.json --max-turns 40 "
                      '--print -- "$(cat /tmp/coord-prompt.txt)"', script)
        self.assertIn("cd /workspace/repo", script)
        self.assertEqual(outcome.status, "Submitted")
        self.assertEqual((outcome.input_tokens, outcome.output_tokens, outcome.steps), (1200, 340, 12))
        self.assertEqual(outcome.patch, PATCHES["agent1"])
        self.assertIn(["exec", "c-agent1", "cat", "/workspace/repo/patch.txt"], self.docker.commands())
        self.assert_secret_nowhere()

    def test_the_token_is_not_passed_when_it_is_not_set(self):
        os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN")
        driver = drivers.ClaudeCliDriver()
        driver.wait(driver.start(self.job(mcp_servers={}, plugins=[], max_turns=None)))
        arguments = [call for call in self.docker.calls if call["output"]][0]["args"]
        self.assertNotIn("CLAUDE_CODE_OAUTH_TOKEN", arguments)
        self.assertNotIn("--mcp-config", arguments[-1])
        self.assertNotIn("--max-turns", arguments[-1])
        self.assertEqual(len(self.docker.matching("exec", "-i", "c-agent1")), 1)

    def test_an_agent_past_its_time_is_an_error_and_is_stopped(self):
        self.docker.claude_times_out = True
        driver = drivers.ClaudeCliDriver()
        outcome = driver.wait(driver.start(self.job()))
        self.assertEqual(outcome.status, "Error")
        self.assertIn("timed out", outcome.error)
        self.assertTrue([c for c in self.docker.matching("exec", "c-agent1", "sh", "-c") if "pkill" in c[-1]])


    def test_a_stream_cut_short_keeps_its_last_line_as_the_error(self):
        self.docker.stream = '{"type": "system"}\nInvalid API key. Please run /login\n'
        driver = drivers.ClaudeCliDriver()
        outcome = driver.wait(driver.start(self.job()))
        self.assertEqual(outcome.status, "Error")
        self.assertIn("Invalid API key", outcome.error)


class StreamParsing(unittest.TestCase):
    def result(self, **fields):
        return json.dumps({"type": "result", "subtype": "success", "num_turns": 3,
                           "usage": {"input_tokens": 10, "output_tokens": 5}, **fields}) + "\n"

    def test_the_final_result_event_gives_usage_and_turns(self):
        outcome = drivers.summarize_stream(SAMPLE_STREAM)
        self.assertEqual(outcome.status, "Submitted")
        self.assertEqual((outcome.input_tokens, outcome.output_tokens, outcome.cache_read_tokens,
                          outcome.cache_write_tokens, outcome.steps), (1200, 340, 50000, 7000, 12))
        self.assertIsNone(outcome.error)

    def test_a_turn_limit_is_limits_exceeded_and_other_failures_are_errors(self):
        limited = drivers.summarize_stream(self.result(subtype="error_max_turns", is_error=True))
        self.assertEqual((limited.status, limited.steps, limited.input_tokens), ("LimitsExceeded", 3, 10))
        failed = drivers.summarize_stream(self.result(is_error=True, result="Usage limit reached"))
        self.assertEqual(failed.status, "Error")
        self.assertIn("Usage limit", failed.error)

    def test_a_stream_without_a_result_is_an_error_with_nothing_counted(self):
        outcome = drivers.summarize_stream('{"type": "assistant"}\ngarbage\n')
        self.assertEqual((outcome.status, outcome.input_tokens, outcome.steps), ("Error", 0, 0))

    def test_patches_are_normalized_as_cooperbench_normalizes_them(self):
        self.assertEqual(drivers.normalize_patch("\n\ndiff\n \n\n"), "diff\n \n")
        self.assertEqual(drivers.normalize_patch("  \n"), "")


class TheSessionDriver(RunnerCase):
    def job(self):
        workspace = self.tmp / "run" / "workspaces" / "agent1"
        workspace.mkdir(parents=True)
        return drivers.AgentJob(run_id="r1", agent="agent1", role="peer", features=(1,), container="c-agent1",
                                prompt="THE ARM'S PROMPT", env={}, arm_dir=str(COORDBENCH / "arms" / "coop"),
                                timeout_s=0.2, log_path=str(self.tmp / "run" / "agent1_stream.jsonl"),
                                workspace=str(workspace))

    def test_the_prompt_says_where_to_work_how_to_run_and_how_to_finish(self):
        job = self.job()
        handle = drivers.SessionDriver().start(job)
        prompt_file = self.tmp / "run" / "agent1.session-prompt.md"
        self.assertEqual(handle["prompt_file"], str(prompt_file))
        json.dumps(handle)
        text = prompt_file.read_text()
        self.assertTrue(text.startswith("# coordbench: you are agent1 in run r1"))
        self.assertIn(f"Your workspace is `{job.workspace}`", text)
        self.assertIn("docker exec -w /workspace/repo c-agent1 bash -lc '<command>'", text)
        self.assertIn(str(self.tmp / "run" / "bin" / "agent1"), text)
        self.assertIn(f"Do not read or change the other agents' workspaces (the other\n  directories under "
                      f"`{self.tmp / 'run' / 'workspaces'}`)", text)
        self.assertIn(f"As the very last step, after `patch.txt` is written, create the file\n"
                      f"  `{job.workspace}/.coordbench-done`", text)
        self.assertTrue(text.endswith("\n\n---\n\nTHE ARM'S PROMPT"))
        self.assertEqual(self.docker.calls, [])

    def test_wait_returns_once_the_marker_appears_with_the_patch(self):
        job = self.job()
        driver = drivers.SessionDriver(poll_seconds=0.01)
        handle = driver.start(job)
        (Path(job.workspace) / "patch.txt").write_text("\n" + PATCHES["agent1"] + "\n\n")
        (Path(job.workspace) / ".coordbench-done").touch()
        outcome = driver.wait(handle)
        self.assertEqual((outcome.status, outcome.patch), ("Submitted", PATCHES["agent1"]))
        logged = json.loads(Path(job.log_path).read_text().splitlines()[-1])
        self.assertEqual(logged["status"], "Submitted")

    def test_wait_gives_up_at_the_deadline(self):
        driver = drivers.SessionDriver(poll_seconds=0.01)
        started = time.time()
        outcome = driver.wait(driver.start(self.job()))
        self.assertLess(time.time() - started, 5)
        self.assertEqual(outcome.status, "Error")
        self.assertIn(".coordbench-done", outcome.error)

    def test_drivers_load_by_name_or_from_a_file(self):
        self.assertIsInstance(drivers.load_driver("session"), drivers.SessionDriver)
        path = self.tmp / "mine.py"
        path.write_text("class Mine:\n    name = 'mine'\n    def start(self, job): return job\n"
                        "    def wait(self, handle): return None\n")
        self.assertEqual(drivers.load_driver(f"{path}:Mine").name, "mine")
        with self.assertRaises(ValueError):
            drivers.load_driver("nonesuch")


class Runs(RunnerCase):
    def test_a_coop_pair_leaves_cooperbench_s_layout(self):
        def agent_sends_a_message(arguments):
            if env_value(arguments, "COORD_RPC_URL").endswith("/agent1"):
                call_tool(env_value(arguments, "COORD_RPC_URL"), "send_message", {"to": "agent2", "text": "hi"})

        self.docker.on_claude = agent_sends_a_message
        code, _, err = self.main(*self.run_arguments("coop", "--features", "6,1"))
        self.assertEqual(code, 0, err)
        pair = self.pair()
        for name in ("result.json", "eval.json", "agent1.patch", "agent6.patch", "agent1_stream.jsonl",
                     "agent2_stream.jsonl", "agent1_prompt.md", "events.jsonl", "metrics.json"):
            self.assertTrue((pair / name).is_file(), name)
        self.assertEqual((pair / "agent1.patch").read_text(), PATCHES["agent1"])
        self.assertEqual((pair / "agent6.patch").read_text(), PATCHES["agent2"])
        result = json.loads((pair / "result.json").read_text())
        self.assertEqual(set(result), RESULT_KEYS)
        self.assertEqual((result["setting"], result["arm"], result["driver"], result["agent_framework"]),
                         ("coop", "coop", "claude-cli", "claude_code"))
        self.assertEqual((result["repo"], result["task_id"], result["features"], result["model"]),
                         (REPO, TASK, [1, 6], "claude-test"))
        self.assertEqual(set(result["agents"]), {"agent1", "agent2"})
        for agent, feature in (("agent1", 1), ("agent2", 6)):
            record = result["agents"][agent]
            self.assertEqual(set(record), AGENT_KEYS)
            self.assertEqual((record["feature_id"], record["status"], record["input_tokens"], record["steps"]),
                             (feature, "Submitted", 1200, 12))
        self.assertEqual(result["metrics"]["messages_sent"], 1)
        self.assertEqual(json.loads((pair / "metrics.json").read_text()), result["metrics"])
        events = [json.loads(line) for line in (pair / "events.jsonl").read_text().splitlines()]
        self.assertIn("message", [event["kind"] for event in events])
        evaluation = json.loads((pair / "eval.json").read_text())
        self.assertEqual(list(evaluation), COOP_EVAL_KEYS)
        self.assertEqual((evaluation["both_passed"], evaluation["setting"], evaluation["features"]),
                         (True, "coop", [1, 6]))
        kind, arguments, cooperbench_dir = self.scorer.calls[0]
        self.assertEqual(kind, "merged")
        self.assertEqual(arguments, {"repo_name": REPO, "task_id": TASK, "feature1_id": 1, "feature2_id": 6,
                                     "backend": "docker", "dataset_dir": str(self.cooperbench / "dataset"),
                                     "patch1": PATCHES["agent1"], "patch2": PATCHES["agent2"]})
        self.assertEqual(cooperbench_dir, str(self.cooperbench))
        containers = [c["container"] for c in json.loads((pair / "plan.json").read_text())["agents"]]
        self.assertIn(["rm", "-f", *containers], self.docker.commands())
        self.assertTrue(self.hub.runs[result["run_id"]].run.closed)
        self.assert_secret_nowhere()

    def test_a_solo_pair_is_scored_as_one_patch(self):
        code, _, err = self.main(*self.run_arguments("solo", "--features", "1,6"))
        self.assertEqual(code, 0, err)
        pair = self.pair("solo")
        self.assertEqual((pair / "solo.patch").read_text(), PATCHES["agent1"])
        result = json.loads((pair / "result.json").read_text())
        self.assertEqual(result["setting"], "solo")
        self.assertEqual(result["agents"]["agent1"]["feature_id"], [1, 6])
        evaluation = json.loads((pair / "eval.json").read_text())
        self.assertEqual(list(evaluation), SOLO_EVAL_KEYS)
        self.assertIsNone(evaluation["merge"])
        kind, arguments, _ = self.scorer.calls[0]
        self.assertEqual((kind, arguments["patch"]), ("solo", PATCHES["agent1"]))

    def test_a_subset_runs_every_pair_and_finished_pairs_are_kept(self):
        code, _, err = self.main(*self.run_arguments("coop", "--subset", "flash"))
        self.assertEqual(code, 0, err)
        self.assertTrue((self.pair(features="f1_f6") / "eval.json").exists())
        self.assertTrue((self.pair(features="f2_f10") / "eval.json").exists())
        before = len(self.docker.calls)
        code, _, err = self.main(*self.run_arguments("coop", "--subset", "flash"))
        self.assertEqual(code, 0)
        self.assertEqual(len(self.docker.calls), before)
        self.assertIn("skipped", err)

    def test_a_finished_pair_without_eval_json_is_only_scored_again(self):
        self.main(*self.run_arguments("coop", "--features", "1,6"))
        (self.pair() / "eval.json").unlink()
        before = len(self.docker.calls)
        code, _, _ = self.main(*self.run_arguments("coop", "--features", "1,6"))
        self.assertEqual(code, 0)
        self.assertEqual(len(self.docker.calls), before)
        self.assertEqual(len(self.scorer.calls), 2)
        self.assertTrue((self.pair() / "eval.json").exists())

    def test_prepare_then_finish_with_the_session_driver(self):
        code, out, err = self.main("prepare", "--arm", "coop", "--repo", REPO, "--task", str(TASK),
                                   "--features", "1,6", "--hub", self.hub_url, "--name", "t",
                                   "--cooperbench-dir", str(self.cooperbench))
        self.assertEqual(code, 0, err)
        plan = json.loads(out)
        pair = self.pair()
        self.assertEqual(plan["run_dir"], str(pair))
        self.assertEqual([a["id"] for a in plan["agents"]], ["agent1", "agent2"])
        saved = json.loads((pair / "plan.json").read_text())
        for agent, entry in zip(saved["agents"], plan["agents"]):
            workspace = Path(agent["workspace"])
            self.assertEqual(workspace, pair / "workspaces" / agent["id"])
            self.assertIn(".coordbench-done", (workspace / ".git" / "info" / "exclude").read_text())
            started = self.docker.matching("run", "-d", "--name", agent["container"])[0]
            self.assertIn(f"{workspace}:/workspace/repo", started)
            self.assertEqual(entry["prompt_file"], str(pair / f"{agent['id']}.session-prompt.md"))
            self.assertIn("Do 1." if agent["id"] == "agent1" else "Do 6.", Path(entry["prompt_file"]).read_text())
            wrapper = pair / "bin" / agent["id"] / "coop-send"
            self.assertIn(f"{self.hub_url}/rpc/{saved['run_id']}/{agent['id']}", wrapper.read_text())
        sent = subprocess.run([str(pair / "bin" / "agent1" / "coop-send"), "agent2", "hello", "there"],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(sent.returncode, 0, sent.stderr)
        for agent in saved["agents"]:
            workspace = Path(agent["workspace"])
            (workspace / "patch.txt").write_text(PATCHES[agent["id"]])
            (workspace / ".coordbench-done").touch()

        code, out, err = self.main("finish", "--run-dir", str(pair))
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out), {"run_dir": str(pair), "verdict": "pass"})
        result = json.loads((pair / "result.json").read_text())
        self.assertEqual((result["driver"], result["agent_framework"]), ("session", "claude_code_subagent"))
        self.assertEqual({a["status"] for a in result["agents"].values()}, {"Submitted"})
        self.assertEqual(result["metrics"]["messages_sent"], 1)
        self.assertEqual((pair / "agent6.patch").read_text(), PATCHES["agent2"])
        self.assertEqual(list(json.loads((pair / "eval.json").read_text())), COOP_EVAL_KEYS)
        self.assertFalse((pair / "workspaces").exists())
        self.assertIn(["rm", "-f", *[a["container"] for a in saved["agents"]]], self.docker.commands())
        self.assert_secret_nowhere()


class Scoring(unittest.TestCase):
    def test_cooperbench_s_own_test_functions_are_called_from_its_src(self):
        with tempfile.TemporaryDirectory() as scratch:
            sandbox = Path(scratch) / "src" / "cooperbench" / "eval"
            sandbox.mkdir(parents=True)
            (sandbox.parent / "__init__.py").write_text("")
            (sandbox / "__init__.py").write_text("")
            (sandbox / "sandbox.py").write_text(
                "import os\n"
                "def test_merged(**kw):\n"
                "    return {'called': 'merged', 'kw': kw, 'token': os.environ.get('CLAUDE_CODE_OAUTH_TOKEN')}\n"
                "def test_solo(**kw):\n"
                "    return {'called': 'solo', 'kw': kw}\n")
            with mock.patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": SECRET}):
                merged = REAL_COOPERBENCH_TEST("merged", {"repo_name": REPO, "patch1": "p1"}, scratch)
            solo = REAL_COOPERBENCH_TEST("solo", {"patch": "p"}, scratch)
        self.assertEqual(merged, {"called": "merged", "kw": {"repo_name": REPO, "patch1": "p1"}, "token": None})
        self.assertEqual(solo, {"called": "solo", "kw": {"patch": "p"}})

    def test_a_scorer_that_fails_says_why(self):
        with tempfile.TemporaryDirectory() as scratch:
            with self.assertRaisesRegex(RuntimeError, "CooperBench's evaluation failed"):
                REAL_COOPERBENCH_TEST("solo", {}, scratch)


class TheHubProcess(unittest.TestCase):
    def test_start_hub_serves_on_a_free_port_and_tells_agents_the_docker_host(self):
        with tempfile.TemporaryDirectory() as scratch:
            process, url = runner.start_hub(Path(scratch), host="127.0.0.1")
            try:
                self.assertTrue(runner.HubClient(url).healthy())
                port = url.rsplit(":", 1)[1]
                first = next(Path(scratch).glob("hub-*.out")).read_text().splitlines()[0]
                self.assertEqual(first, f"http://host.docker.internal:{port}")
            finally:
                runner.stop_hub(process)
            self.assertIsNotNone(process.poll())


if __name__ == "__main__":
    unittest.main()
