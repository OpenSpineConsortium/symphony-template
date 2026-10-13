"""tools/usage.py: a session's usage read from its transcript and its
helpers', written on each commit as one trailer line by way of a real git
repository's commit-msg hook, and a run in Actions read from the action's
execution file; the switch turns both off, and inside Actions a session
records nothing, so no run counts twice."""

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import usage  # noqa: E402

# The environment the commit tests run in: without git's own variables, which
# would point the hooks' git at another repository, and without the two the
# tool reads to decide whether to record at all, GitHub Actions and the
# metrics switch, which a person may have turned off in their own shell, as
# usage.py's docstring tells them to; a test that wants either sets it itself.
QUIET = {key: value for key, value in os.environ.items()
         if not key.startswith("GIT_") and key not in ("GITHUB_ACTIONS", usage.SWITCH_VARIABLE)}


def assistant(message_id, model, usage_fields, at="2026-10-12T10:00:00Z"):
    return {"type": "assistant", "timestamp": at, "requestId": "r-" + message_id,
            "message": {"id": message_id, "model": model, "usage": usage_fields}}


def used(inp=0, write=0, read=0, out=0, hour=None):
    fields = {"input_tokens": inp, "cache_creation_input_tokens": write, "cache_read_input_tokens": read,
              "output_tokens": out}
    if hour is not None:
        fields["cache_creation"] = {"ephemeral_5m_input_tokens": write - hour, "ephemeral_1h_input_tokens": hour}
    return fields


def write_lines(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e) + "\n" for e in entries) + "not json\n", encoding="utf-8")


class ReadingATranscript(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder, True)
        self.transcript = self.folder / "abcdef12-3456.jsonl"

    def test_each_message_counts_once_and_helpers_count_too(self):
        write_lines(self.transcript, [
            {"type": "user", "timestamp": "2026-10-12T10:00:00Z"},
            assistant("m1", "claude-opus-5-5", used(10, 100, 1000, 5), "2026-10-12T10:00:10Z"),
            assistant("m1", "claude-opus-5-5", used(10, 100, 1000, 5), "2026-10-12T10:00:11Z"),
            assistant("m2", "claude-opus-5-5", used(1, 0, 2000, 7, hour=0), "2026-10-12T10:01:00Z"),
            assistant("s", usage.SYNTHETIC, used(99, 99, 99, 99), "2026-10-12T10:01:01Z"),
            {"type": "user", "timestamp": "2026-10-12T11:00:00Z"},
        ])
        write_lines(self.folder / "abcdef12-3456" / "subagents" / "agent-1.jsonl",
                    [assistant("h1", "claude-haiku-5-5", used(3, 30, 300, 4, hour=10))])
        found = usage.session_usage(self.transcript)
        self.assertEqual(found["models"], {"claude-opus-5-5": [11, 100, 0, 3000, 12],
                                           "claude-haiku-5-5": [3, 20, 10, 300, 4]})
        self.assertEqual(found["seconds"], 61, "the hour's pause is left out")

    def test_what_was_spent_since_the_last_commit(self):
        before = {"models": {"m": [1, 2, 3, 4, 5]}, "seconds": 10}
        now = {"models": {"m": [2, 2, 3, 6, 9], "n": [0, 0, 0, 0, 0], "o": [1, 0, 0, 0, 0]}, "seconds": 25}
        self.assertEqual(usage.since(now, before), {"models": {"m": [1, 0, 0, 2, 4], "o": [1, 0, 0, 0, 0]}, "seconds": 15})

    def test_the_trailer_round_trips(self):
        value = usage.trailer("6e4cb20b-affa", {"models": {"b": [1, 2, 3, 4, 5], "a": [0, 0, 0, 1, 0]}, "seconds": 9})
        self.assertEqual(value, "v1 session=6e4cb20b seconds=9 a=0,0,0,1,0 b=1,2,3,4,5")
        message = f"Do it\n\nWhy.\n\nCo-Authored-By: x\nSymphony-Usage: {value}\n"
        self.assertEqual(usage.parse_trailer(message), [("6e4cb20b", 9, {"a": [0, 0, 0, 1, 0], "b": [1, 2, 3, 4, 5]})])
        self.assertEqual(usage.parse_trailer("symphony-usage: v1 session=x seconds=no m=1,2\n"), [("x", 0, {})])
        self.assertEqual(usage.parse_trailer("Symphony-Usage: v2 later\n"), [])

    def test_a_count_too_long_or_in_other_digits_is_passed_over_as_unreadable(self):
        # Anyone who can push a commit writes its message, and int() refuses
        # a string of more than 4,300 digits with ValueError, which stopped
        # the metrics run; a count is read as the Actions records' are, a
        # whole number below 2 ** 53 in ASCII digits.
        huge = "1" * 4301
        self.assertEqual(usage.parse_trailer(f"Symphony-Usage: v1 session=x seconds={huge} m={huge},0,0,0,0\n"),
                         [("x", 0, {})])
        self.assertEqual(usage.parse_trailer(f"Symphony-Usage: v1 session=x seconds={2 ** 53} m=0,0,0,0,{2 ** 53}\n"),
                         [("x", 0, {})])
        self.assertEqual(usage.parse_trailer("Symphony-Usage: v1 session=x seconds=\u0663 m=\u0663,0,0,0,0\n"),
                         [("x", 0, {})])
        self.assertEqual(usage.parse_trailer(f"Symphony-Usage: v1 session=x seconds={2 ** 53 - 1} m=0,0,0,0,7\n"),
                         [("x", 2 ** 53 - 1, {"m": [0, 0, 0, 0, 7]})])

    def test_a_line_with_a_long_run_of_blanks_is_read_in_one_pass(self):
        # A value read lazily up to optional blanks before the line's end took
        # time that grew with the square of a run of blanks inside the line:
        # a second for 16,000 of them, and the metrics run reads each message
        # more than once, under a 20-minute limit.
        message = "Symphony-Usage: v1 session=x" + " " * 100_000 + "m=1,2,3,4,5" + " " * 100_000 + "\n"
        started = time.monotonic()
        self.assertEqual(usage.parse_trailer(message), [("x", 0, {"m": [1, 2, 3, 4, 5]})])
        self.assertLess(time.monotonic() - started, 1.0)
        self.assertEqual(usage.parse_trailer("Symphony-Usage: v1 \t session=y\t \r\n"), [("y", 0, {})])

    def test_the_trailer_carries_eight_characters_of_the_session_and_nothing_more(self):
        spent = {"models": {"m": [1, 0, 0, 0, 1]}, "seconds": 1}
        self.assertTrue(usage.trailer("session_01AMrLKnvPcvNBSchUXZbDDX", spent).startswith("v1 session=01AMrLKn "))
        self.assertTrue(usage.trailer("6e4cb20b-affa-5339", spent).startswith("v1 session=6e4cb20b "))
        self.assertTrue(usage.trailer("a b;c$d", spent).startswith("v1 session=abcd "))


class Commits(unittest.TestCase):
    """The hook and the commit-msg hook in a real repository."""

    def setUp(self):
        environment = mock.patch.dict(os.environ, QUIET, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        self.folder = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.folder, True)
        self.repo = self.folder / "repo"
        (self.repo / "tools").mkdir(parents=True)
        for name in ("usage.py",):
            shutil.copy(ROOT / "tools" / name, self.repo / "tools" / name)
        shutil.copytree(ROOT / "tools" / "sdlc_protocol", self.repo / "tools" / "sdlc_protocol")
        self.git("init", "-q")
        self.transcript = self.folder / "s1.jsonl"

    def git(self, *args):
        done = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c",
                               "commit.gpgsign=false", *args], cwd=self.repo, capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout.strip()

    def hook(self, command="git commit -m x", session="6e4cb20b-affa-5339"):
        payload = {"session_id": session, "transcript_path": str(self.transcript), "cwd": str(self.repo),
                   "tool_input": {"command": command}}
        self.assertEqual(usage.main(["hook"], stdin=io.StringIO(json.dumps(payload))), 0)

    def commit(self, name):
        (self.repo / name).write_text(name, encoding="ascii")
        self.git("add", name)
        self.git("commit", "-q", "-m", f"Add {name}\n\nCo-Authored-By: someone")
        return self.git("log", "-1", "--format=%B")

    def test_each_commit_carries_what_the_session_spent_since_the_last(self):
        self.assertIn("commit-msg hook in place", usage.install(cwd=self.repo))
        write_lines(self.transcript, [assistant("m1", "claude-opus-5-5", used(10, 0, 100, 5))])
        self.hook()
        first = self.commit("a.txt")
        self.assertEqual(usage.parse_trailer(first), [("6e4cb20b", 0, {"claude-opus-5-5": [10, 0, 0, 100, 5]})])
        self.assertTrue(first.rstrip().endswith("Symphony-Usage: v1 session=6e4cb20b seconds=0 claude-opus-5-5=10,0,0,100,5"))
        self.assertIn("Co-Authored-By: someone", first)
        write_lines(self.transcript, [assistant("m1", "claude-opus-5-5", used(10, 0, 100, 5)),
                                      assistant("m2", "claude-opus-5-5", used(1, 0, 50, 2))])
        self.hook()
        second = self.commit("b.txt")
        self.assertEqual(usage.parse_trailer(second)[0][2], {"claude-opus-5-5": [1, 0, 0, 50, 2]})

    def test_a_commit_no_session_asked_for_carries_nothing(self):
        usage.install(cwd=self.repo)
        self.assertEqual(usage.parse_trailer(self.commit("a.txt")), [])
        write_lines(self.transcript, [assistant("m1", "m", used(1, 0, 0, 1))])
        self.hook(command="git status")
        self.assertEqual(usage.parse_trailer(self.commit("b.txt")), [])

    def test_a_usage_left_too_long_ago_belongs_to_no_commit(self):
        usage.install(cwd=self.repo)
        write_lines(self.transcript, [assistant("m1", "m", used(1, 0, 0, 1))])
        self.hook()
        pending = usage.state_dir(self.repo) / "pending.json"
        data = json.loads(pending.read_text())
        data["at"] = time.time() - usage.PENDING_FRESH - 5
        pending.write_text(json.dumps(data))
        self.assertEqual(usage.parse_trailer(self.commit("a.txt")), [])

    def test_inside_actions_or_with_the_switch_off_nothing_is_recorded(self):
        usage.install(cwd=self.repo)
        write_lines(self.transcript, [assistant("m1", "m", used(1, 0, 0, 1))])
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            self.hook()
        self.assertFalse((usage.state_dir(self.repo) / "pending.json").exists())
        (self.repo / ".github").mkdir()
        (self.repo / usage.SWITCH_FILE).write_text("off\n", encoding="ascii")
        self.hook()
        self.assertFalse((usage.state_dir(self.repo) / "pending.json").exists())
        self.assertIn("switch is off", usage.install(cwd=self.repo))
        self.assertIn("GitHub Actions", usage.install(cwd=self.repo, environ={"GITHUB_ACTIONS": "true"}))

    def test_a_clones_own_commit_msg_hook_is_left_alone(self):
        hooks = Path(self.git("rev-parse", "--absolute-git-dir")) / "hooks"
        hooks.mkdir(exist_ok=True)
        (hooks / "commit-msg").write_text("#!/bin/sh\nexit 0\n", encoding="ascii")
        self.assertIn("left as it is", usage.install(cwd=self.repo))
        self.assertEqual((hooks / "commit-msg").read_text(), "#!/bin/sh\nexit 0\n")

    def test_the_hook_reads_only_a_git_commit(self):
        for command, commits in (("git commit -m x", True), ("git -C . commit -qm x", True),
                                 ("cd x && git commit --amend --no-edit", True), ("echo git commit", False),
                                 ("git log --grep commit", False), ("GIT_EDITOR=true git commit", True),
                                 ("gh pr create", False), ("", False)):
            self.assertEqual(usage.is_commit(command), commits, command)

    def test_a_payload_the_hook_cannot_read_passes(self):
        for text in ("not json", "[]", json.dumps({"tool_input": "git commit"})):
            self.assertEqual(usage.main(["hook"], stdin=io.StringIO(text)), 0)


class AnActionsRun(unittest.TestCase):
    MESSAGES = [
        {"type": "system", "subtype": "init", "model": "claude-sonnet-5-5"},
        assistant("a1", "claude-sonnet-5-5", used(5, 10, 20, 30)),
        {"type": "result", "subtype": "success", "is_error": False, "duration_ms": 61234, "duration_api_ms": 50000,
         "num_turns": 7, "total_cost_usd": 0.42,
         "modelUsage": {"claude-sonnet-5-5": {"inputTokens": 5, "outputTokens": 30, "cacheReadInputTokens": 20,
                                              "cacheCreationInputTokens": 10, "costUSD": 0.4},
                        "claude-haiku-5-5": {"inputTokens": 1, "outputTokens": 2}}},
    ]

    def test_the_record_holds_counts_times_and_where_it_ran(self):
        record = usage.actions_record(self.MESSAGES, "worker", "workers", "nightly", 12, 40, at="2026-10-12T10:00:00Z")
        self.assertEqual(record, {
            "v": 1, "source": "actions", "workflow": "workers", "job": "worker", "worker": "nightly", "issue": 12,
            "pull": 40, "at": "2026-10-12T10:00:00Z", "seconds": 61.2, "api_seconds": 50.0, "turns": 7,
            "reported_usd": 0.42, "error": False,
            "models": {"claude-sonnet-5-5": [5, 10, 0, 20, 30], "claude-haiku-5-5": [1, 0, 0, 0, 2]}})

    def test_without_a_result_the_messages_are_summed_and_the_run_marked(self):
        record = usage.actions_record(self.MESSAGES[:2], "plan", "coordinator")
        self.assertTrue(record["error"])
        self.assertEqual(record["models"], {"claude-sonnet-5-5": [5, 10, 0, 20, 30]})

    def test_the_command_writes_the_record_or_says_why_not(self):
        with tempfile.TemporaryDirectory() as folder:
            execution = Path(folder) / "claude-execution-output.json"
            execution.write_text(json.dumps(self.MESSAGES), encoding="utf-8")
            out = Path(folder) / "usage" / "record.json"
            # The switch that counts is the one in the checkout --root names,
            # here a folder with no switch file, which is on, whatever the
            # repository running this test has turned its own to.
            argv = ["actions", "--execution-file", str(execution), "--out", str(out), "--workflow", "workers",
                    "--job", "worker", "--worker", "nightly", "--issue", "12", "--pull", "", "--root", folder]
            with mock.patch("sys.stdout", io.StringIO()) as printed:
                self.assertEqual(usage.main(argv, environ={}), 0)
            self.assertIn("68 tokens", printed.getvalue())
            record = json.loads(out.read_text())
            self.assertEqual((record["issue"], record["pull"]), (12, None))
            out.unlink()
            with mock.patch("sys.stdout", io.StringIO()) as printed:
                usage.main(argv, environ={"SDLC_METRICS": "off"})
            self.assertFalse(out.exists())
            self.assertIn("switch is off", printed.getvalue())
            missing = list(argv)
            missing[2] = str(Path(folder) / "none.json")
            with mock.patch("sys.stdout", io.StringIO()) as printed:
                self.assertEqual(usage.main(missing, environ={}), 0)
            self.assertIn("no execution file", printed.getvalue())
            (Path(folder) / ".github").mkdir()
            (Path(folder) / usage.SWITCH_FILE).write_text("off\n", encoding="ascii")
            with mock.patch("sys.stdout", io.StringIO()) as printed:
                self.assertEqual(usage.main(argv, environ={}), 0)
            self.assertFalse(out.exists(), "the switch of the checkout --root names says off")
            self.assertIn("switch is off", printed.getvalue())


class NeverInTheWay(unittest.TestCase):
    def test_whatever_goes_wrong_the_hook_and_the_trailer_exit_0(self):
        with mock.patch.object(usage, "run_hook", side_effect=KeyError("surprise")):
            self.assertEqual(usage.main(["hook"], stdin=io.StringIO("{}")), 0)
        with mock.patch.object(usage, "run_trailer", side_effect=TypeError("surprise")):
            self.assertEqual(usage.main(["trailer", "MSG"]), 0)


class Switch(unittest.TestCase):
    def test_the_switch_reads_as_the_metrics_tool_reads_it(self):
        import metrics
        cases = [({}, None), ({"SDLC_METRICS": "off"}, None), ({"SDLC_METRICS": "no"}, None),
                 ({"SDLC_METRICS": "on"}, "off\n"), ({}, "on\n"), ({}, "off\n"), ({}, "maybe\n"), ({}, ""),
                 ({"SDLC_METRICS": ""}, "on please\n")]
        for environ, file_text in cases:
            with tempfile.TemporaryDirectory() as folder:
                if file_text is not None:
                    (Path(folder) / ".github").mkdir()
                    (Path(folder) / usage.SWITCH_FILE).write_text(file_text, encoding="ascii")
                self.assertEqual(usage.sharing_off(folder, environ), metrics.sharing(folder, environ) == metrics.OFF,
                                 (environ, file_text))
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / ".github").mkdir()
            (Path(folder) / ".github" / "sdlc-metrics").write_text("off\n", encoding="ascii")
            self.assertTrue(usage.sharing_off(folder, {}))
        # Both names at once, as in a repository adopted again since the
        # rename: an off in either wins, as tools/metrics.py reads them.
        for new, old in (("on\n", "off\n"), ("off\n", "on\n"), ("on\n", "on\n")):
            with self.subTest(new=new, old=old), tempfile.TemporaryDirectory() as folder:
                (Path(folder) / ".github").mkdir()
                (Path(folder) / usage.SWITCH_FILE).write_text(new, encoding="ascii")
                (Path(folder) / ".github" / "sdlc-metrics").write_text(old, encoding="ascii")
                self.assertEqual(usage.sharing_off(folder, {}), "off" in (new.strip(), old.strip()))
                self.assertEqual(usage.sharing_off(folder, {}), metrics.sharing(folder, {}) == metrics.OFF)


class Wiring(unittest.TestCase):
    """Every Claude session the repository runs leaves what it spent where
    the metrics workflow reads it, and every session of a person's records
    its own on its commits."""

    WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))

    def test_every_claude_step_in_actions_is_recorded_and_kept(self):
        found = 0
        for path in self.WORKFLOWS:
            steps = path.read_text(encoding="utf-8").split("\n      - ")
            for index, step in enumerate(steps):
                if not step.startswith("uses: anthropics/claude-code-action@"):
                    continue
                found += 1
                step_id = re.search(r"\n        id: (\S+)", step)
                self.assertIsNotNone(step_id, f"{path.name}: a Claude step with no id")
                self.assertIn('cp tools/usage.py "$RUNNER_TEMP/usage.py"', steps[index - 1], path.name)
                record, kept = steps[index + 1], steps[index + 2]
                self.assertIn(f"steps.{step_id.group(1)}.outputs.execution_file", record, path.name)
                self.assertIn('python3 "$RUNNER_TEMP/usage.py" actions --root "$GITHUB_WORKSPACE"', record, path.name)
                self.assertIn("continue-on-error: true", record, path.name)
                self.assertIn("uses: actions/upload-artifact@v7", kept, path.name)
                self.assertIn("name: symphony-usage-${{ github.run_id }}-${{ github.run_attempt }}-", kept, path.name)
                self.assertIn("if-no-files-found: ignore", kept, path.name)
        self.assertEqual(found, 6, "workers.yml's one, coordinator.yml's four and claude.yml's one")

    def test_the_metrics_workflow_reads_the_records_and_keeps_what_it_read(self):
        text = (ROOT / ".github" / "workflows" / "metrics.yml").read_text(encoding="utf-8")
        for needed in ("  actions: read\n", "uses: actions/cache/restore@v6", "uses: actions/cache/save@v6",
                       '--usage-cache "$RUNNER_TEMP/usage-records.json"'):
            self.assertIn(needed, text)

    def test_every_session_runs_the_hook_and_installs_the_commit_msg_hook(self):
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        commands = [hook["command"] for entry in settings["hooks"]["PreToolUse"] if entry["matcher"] == "Bash"
                    for hook in entry["hooks"]]
        self.assertIn('python3 "$CLAUDE_PROJECT_DIR"/tools/usage.py hook', commands)
        start = (ROOT / ".claude" / "hooks" / "session-start.sh").read_text(encoding="utf-8")
        self.assertIn("python3 tools/usage.py install >/dev/null 2>&1 || true", start)


if __name__ == "__main__":
    unittest.main()
