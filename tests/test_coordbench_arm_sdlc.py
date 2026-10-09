"""The sdlc arm is this repository's claim protocol as a coordbench arm, so
the template's way of working can be benchmarked beside CooperBench's
arms. These tests pin the protocol's promises: a claim is exclusive and
first come, first served; an agent claims only its own issue unless the
queue is open; a pull request that merges cleanly lands on main as a merge
commit; one that conflicts answers the board's "main moved" and leaves main
as it was; and once its author merges main in and pushes, it lands. The
merge gate acts on a real bare repository in a temporary directory, with
two working clones playing the two agents, so what is checked is what git
itself did."""

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COORDBENCH = ROOT / "experiment" / "coordbench"
ARM_DIR = COORDBENCH / "arms" / "sdlc"
sys.path.insert(0, str(COORDBENCH))

import hub as hub_module  # noqa: E402
import mcp  # noqa: E402
from arm import SUBMISSION_BLOCK, AgentSpec, Call, Run, ToolError, find_arm  # noqa: E402

MCP_JSON = {"mcpServers": {"coordbench": {"type": "http", "url": "${COORD_MCP_URL}"}}}
ARM_JSON_KEYS = {"entry", "name", "description", "needs", "plugins", "mcp_servers"}
ALIASES = {"board": "sdlc-board", "claim_issue": "sdlc-claim", "open_pull_request": "sdlc-pr",
           "mark_ready": "sdlc-ready", "pull_request_status": "sdlc-status", "send_message": "coop-send",
           "broadcast": "coop-broadcast", "receive_messages": "coop-recv", "peek_messages": "coop-peek",
           "list_agents": "coop-agents", "wait_for_message": ""}
MAIN_MOVED = ("main moved: merge team/main into your branch, resolve the conflicts, push, "
              "and call mark_ready again")
RULE = "\n\n---\n\n"
SPECS = {1: "# Greeting\n\nGreet in English.\n", 2: "# Farewell\n\nSay goodbye.\n",
         3: "# Colours\n\nColour the output.\n"}
BASE_TEXT = "def greet():\n    return 'hello'\n\n\ndef part():\n    return 'base'\n"
GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}


def git(cwd, *args, check=True):
    """git as the agents run it in their containers, with an identity of
    its own so the host's configuration does not matter."""
    result = subprocess.run(["git", "-c", "user.name=agent", "-c", "user.email=agent@coordbench.local",
                             "-c", "commit.gpgsign=false", *args], cwd=cwd, capture_output=True,
                            text=True, timeout=60, env=GIT_ENV)
    if check and result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


class SharedRemote:
    """A bare repository seeded with one commit on main, the base ref, and a
    working clone per agent with the bare repository as its remote `team`."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="coordbench-sdlc-test-")
        self.root = Path(self.tmp.name)
        self.bare = self.root / "team.git"
        git(self.root, "init", "--quiet", "--bare", "--initial-branch=main", str(self.bare))
        seed = self.root / "seed"
        seed.mkdir()
        git(seed, "init", "--quiet", "--initial-branch=main")
        (seed / "app.py").write_text(BASE_TEXT, encoding="utf-8")
        git(seed, "add", "app.py")
        git(seed, "commit", "--quiet", "-m", "base")
        git(seed, "push", "--quiet", str(self.bare), "HEAD:refs/heads/main")
        self.base = git(seed, "rev-parse", "HEAD")

    def clone(self, agent):
        path = self.root / agent
        git(self.root, "clone", "--quiet", "--origin", "team", str(self.bare), str(path))
        return path

    def main(self):
        return git(self.bare, "rev-parse", "refs/heads/main")

    def show(self, ref, path):
        return git(self.bare, "show", f"{ref}:{path}")

    def close(self):
        self.tmp.cleanup()


def start_branch(clone, issue, base):
    git(clone, "checkout", "--quiet", "-b", f"claude/{issue}", base)


def commit_and_push(clone, issue, files, message):
    for name, text in files.items():
        (clone / name).write_text(text, encoding="utf-8")
    git(clone, "add", *files)
    git(clone, "commit", "--quiet", "-m", message)
    git(clone, "push", "--quiet", "team", f"claude/{issue}")


def new_run(features=(1, 2), options=None):
    arm = find_arm(str(ARM_DIR))
    run = Run("r1", arm, arm.layout(list(features)), options)
    arm.setup(run)
    return arm, run


def call(run, agent, tool, **arguments):
    return run.arm.tools_for(run, agent)[tool].handler(Call(run, agent, arguments))


def call_over_mcp(run, agent, tool, **arguments):
    """A tools/call as the hub answers it, so the run records a "tool" event."""
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": tool, "arguments": arguments}}
    result = mcp.handle(request, run, agent)["result"]
    return result["content"][0]["text"], result["isError"]


def frontmatter(text):
    lines = text.split("\n")
    if lines[0] != "---" or "---" not in lines[1:]:
        return None, text
    end = lines.index("---", 1)
    fields = {}
    for line in lines[1:end]:
        key, _, value = line.partition(": ")
        fields[key] = value
    return fields, "\n".join(lines[end + 1:])


class ArmFilesTest(unittest.TestCase):
    """The directory is a Claude Code plugin and a coordbench arm."""

    def read_json(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_the_arm_loads_by_directory_and_by_built_in_name(self):
        for arm in (find_arm(str(ARM_DIR)), find_arm("sdlc")):
            self.assertEqual(type(arm).__name__, "SdlcArm")
            self.assertEqual(arm.name, "sdlc")
            self.assertEqual(arm.config["name"], "sdlc")

    def test_plugin_json_names_the_plugin(self):
        plugin = self.read_json(ARM_DIR / ".claude-plugin" / "plugin.json")
        self.assertEqual(set(plugin), {"name", "version", "description"})
        self.assertEqual(plugin["name"], "coordbench-sdlc")
        self.assertEqual(plugin["version"], "0.1.0")
        self.assertTrue(plugin["description"].strip())

    def test_mcp_json_is_exactly_the_contracts(self):
        self.assertEqual(self.read_json(ARM_DIR / ".mcp.json"), MCP_JSON)

    def test_arm_json_agrees_with_the_arm(self):
        config = self.read_json(ARM_DIR / "arm.json")
        arm = find_arm(str(ARM_DIR))
        self.assertEqual(set(config), ARM_JSON_KEYS)
        self.assertEqual(config["entry"], "arm.py:SdlcArm")
        self.assertEqual(config["description"], arm.description)
        self.assertEqual(config["needs"], ["git_remote"])
        self.assertEqual(tuple(arm.needs), ("git_remote",))
        self.assertEqual(config["plugins"], [])
        self.assertEqual(config["mcp_servers"], {})

    def test_skill_frontmatter_names_the_skill(self):
        skill = ARM_DIR / "skills" / "coordbench-sdlc" / "SKILL.md"
        fields, body = frontmatter(skill.read_text(encoding="utf-8"))
        self.assertIsNotNone(fields, "SKILL.md must open with YAML frontmatter")
        self.assertEqual(set(fields), {"name", "description"})
        self.assertEqual(fields["name"], "coordbench-sdlc")
        self.assertTrue(fields["description"].strip())
        self.assertNotIn(": ", fields["description"])
        self.assertNotIn(" #", fields["description"])
        self.assertTrue(body.strip())

    def test_the_skill_names_every_tool_its_shell_command_and_main_moved(self):
        arm, run = new_run()
        body = (ARM_DIR / "skills" / "coordbench-sdlc" / "SKILL.md").read_text(encoding="utf-8")
        for tool in arm.tools_for(run, "agent1").values():
            self.assertIn(f"`{tool.name}`", body)
            self.assertIn(f"`{tool.alias or 'coord-' + tool.name}", body)
        self.assertIn(" ".join(MAIN_MOVED.split()), " ".join(body.split()))
        self.assertIn("git diff <base ref> team/main > patch.txt", body)

    def test_every_file_is_ascii_with_lf(self):
        for path in sorted(ARM_DIR.rglob("*")):
            if path.is_dir() or "__pycache__" in path.parts:
                continue
            with self.subTest(file=str(path.relative_to(ARM_DIR))):
                data = path.read_bytes()
                self.assertNotIn(b"\r", data)
                self.assertTrue(all(byte < 128 for byte in data))


class LayoutAndToolsTest(unittest.TestCase):
    def test_one_peer_per_feature_numbered_by_sorted_feature(self):
        agents = find_arm("sdlc").layout([2, 1])
        self.assertEqual(agents, [AgentSpec("agent1", "peer", (1,)), AgentSpec("agent2", "peer", (2,))])

    def test_every_agent_gets_the_protocol_tools_and_messaging_with_the_wait(self):
        arm, run = new_run()
        for agent in run.agents:
            tools = arm.tools_for(run, agent)
            self.assertEqual({name: tool.alias for name, tool in tools.items()}, ALIASES)
            for name in ("claim_issue", "open_pull_request", "mark_ready", "pull_request_status"):
                self.assertEqual(tools[name].argv, ("issue",))
                self.assertEqual(tools[name].input_schema["properties"]["issue"]["type"], "integer")


class ClaimTest(unittest.TestCase):
    """Claims touch no git, so these runs have no remote."""

    def test_a_claim_of_your_own_issue_succeeds_once(self):
        _, run = new_run()
        self.assertIn("claimed #1", call(run, "agent1", "claim_issue", issue=1))
        with self.assertRaisesRegex(ToolError, "you already hold #1"):
            call(run, "agent1", "claim_issue", issue=1)

    def test_an_agent_claims_only_its_own_issue(self):
        _, run = new_run()
        with self.assertRaisesRegex(ToolError, "#2 was given to agent2.*yours is #1"):
            call(run, "agent1", "claim_issue", issue=2)
        self.assertIn("claimed #2", call(run, "agent2", "claim_issue", issue=2))

    def test_unknown_and_malformed_issues_are_refused(self):
        _, run = new_run()
        with self.assertRaisesRegex(ToolError, "there is no issue #9; the issues are #1, #2"):
            call(run, "agent1", "claim_issue", issue=9)
        with self.assertRaisesRegex(ToolError, "issue must be an issue number"):
            call(run, "agent1", "claim_issue", issue="one")
        with self.assertRaisesRegex(ToolError, "issue is required"):
            call(run, "agent1", "claim_issue")

    def test_an_issue_may_be_written_as_the_board_writes_it(self):
        _, run = new_run()
        self.assertIn("claimed #1", call(run, "agent1", "claim_issue", issue="#1"))
        self.assertIn("claimed #2", call(run, "agent2", "claim_issue", issue="2"))

    def test_an_open_queue_is_first_come_first_served(self):
        _, run = new_run(options={"open_queue": True})
        self.assertIn("claimed #2", call(run, "agent1", "claim_issue", issue=2))
        with self.assertRaisesRegex(ToolError, "#2 is claimed by agent1: a claim is first come, first served"):
            call(run, "agent2", "claim_issue", issue=2)
        self.assertIn("claimed #1", call(run, "agent2", "claim_issue", issue=1))

    def test_of_agents_racing_for_one_issue_exactly_one_wins(self):
        _, run = new_run((1, 2, 3), {"open_queue": True})
        start = threading.Barrier(len(run.agents))
        answers = {}

        def race(agent):
            start.wait()
            try:
                answers[agent] = call(run, agent, "claim_issue", issue=3)
            except ToolError as refusal:
                answers[agent] = refusal

        threads = [threading.Thread(target=race, args=(agent,)) for agent in run.agents]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(10)
        winners = [agent for agent, answer in answers.items() if isinstance(answer, str)]
        self.assertEqual(len(answers), 3)
        self.assertEqual(len(winners), 1)
        self.assertEqual(run.state["sdlc_queue"].issues[3].claimant, winners[0])

    def test_without_a_remote_the_gate_says_so(self):
        _, run = new_run()
        call(run, "agent1", "claim_issue", issue=1)
        with self.assertRaisesRegex(ToolError, "no git_remote_host"):
            call(run, "agent1", "open_pull_request", issue=1)


class PromptTest(unittest.TestCase):
    def prompt(self, agent="agent1", options=None):
        arm, run = new_run(options=options or {"base_ref": "0a1b2c3d4e", "git_remote": "git://hub/team.git"})
        return arm, run, arm.prompt(run, agent, SPECS)

    def test_the_prompt_is_spec_then_protocol_then_the_submission_block(self):
        _, _, prompt = self.prompt("agent2")
        sections = prompt.split(RULE)
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0], SPECS[2])
        self.assertTrue(sections[1].startswith("## The claim protocol"))
        self.assertEqual(sections[2], SUBMISSION_BLOCK)

    def test_the_protocol_block_states_the_protocol_in_its_own_terms(self):
        _, _, prompt = self.prompt("agent2")
        block = prompt.split(RULE)[1]
        for words in ("You are **agent2**", "Your issue is **#2**", "first come, first served",
                      "One issue, one branch `claude/<issue>`, one pull request",
                      "`sdlc-claim 2`", "`sdlc-pr 2`", "`sdlc-ready 2`", "`sdlc-status 2`",
                      "merge gate", f'answers "{MAIN_MOVED}"', "git merge team/main",
                      "git push team claude/2", "never force-push", "each agent claims only the issue"):
            self.assertIn(words, block)

    def test_the_git_set_up_and_submission_rule_use_the_base_ref(self):
        _, _, prompt = self.prompt("agent1")
        self.assertIn("the remote `team` is the shared repository (`git://hub/team.git`)", prompt)
        self.assertIn("git checkout -b claude/1 0a1b2c3d4e", prompt)
        self.assertIn("git diff 0a1b2c3d4e team/main > patch.txt", prompt)
        self.assertIn("git diff 0a1b2c3d4e HEAD > patch.txt", prompt)
        self.assertLess(prompt.index("team/main > patch.txt"), prompt.index("HEAD > patch.txt"))

    def test_the_prompt_names_each_tool_beside_its_shell_command(self):
        arm, run, prompt = self.prompt()
        for tool in arm.tools_for(run, "agent1").values():
            command = tool.alias or f"coord-{tool.name}"
            self.assertRegex(prompt, rf"\| `{tool.name}`[^|]*\| `{command}")

    def test_an_open_queue_says_so(self):
        _, _, prompt = self.prompt(options={"base_ref": "abc", "open_queue": True})
        self.assertIn("The queue is open", prompt)
        self.assertNotIn("each agent claims only the issue", prompt)


class GateTest(unittest.TestCase):
    """Two agents, two features, one shared bare repository."""

    def setUp(self):
        self.remote = SharedRemote()
        self.addCleanup(self.remote.close)
        self.arm, self.run = new_run(options={"git_remote_host": str(self.remote.bare),
                                              "base_ref": self.remote.base,
                                              "git_remote": "git://host.docker.internal/team.git"})
        self.addCleanup(self.release_gate)
        self.one = self.remote.clone("agent1")
        self.two = self.remote.clone("agent2")

    def release_gate(self):
        gate = self.run.state["sdlc_gate"]
        if gate is not None:
            gate.release()

    def claim_branch_and_open(self, agent, clone, issue, files):
        call(self.run, agent, "claim_issue", issue=issue)
        start_branch(clone, issue, self.remote.base)
        commit_and_push(clone, issue, files, f"feature {issue}")
        return call(self.run, agent, "open_pull_request", issue=issue)

    def both_change_the_same_line(self):
        """agent1 lands first; agent2's change to the same line now conflicts."""
        self.claim_branch_and_open("agent1", self.one, 1,
                                   {"app.py": BASE_TEXT.replace("'hello'", "'hello, world'")})
        self.claim_branch_and_open("agent2", self.two, 2,
                                   {"app.py": BASE_TEXT.replace("'hello'", "'goodbye'")})
        self.assertIn("merged", call(self.run, "agent1", "mark_ready", issue=1))

    def test_a_pull_request_needs_the_claim_and_the_pushed_branch(self):
        with self.assertRaisesRegex(ToolError, "nobody has claimed it"):
            call(self.run, "agent1", "open_pull_request", issue=1)
        call(self.run, "agent1", "claim_issue", issue=1)
        with self.assertRaisesRegex(ToolError, "claude/1 is not on team yet; push it first"):
            call(self.run, "agent1", "open_pull_request", issue=1)
        start_branch(self.one, 1, self.remote.base)
        commit_and_push(self.one, 1, {"one.py": "ONE = 1\n"}, "feature 1")
        self.assertIn("opened the pull request for #1", call(self.run, "agent1", "open_pull_request", issue=1))
        with self.assertRaisesRegex(ToolError, "one issue, one pull request"):
            call(self.run, "agent1", "open_pull_request", issue=1)
        with self.assertRaisesRegex(ToolError, "claimed by agent1"):
            call(self.run, "agent2", "open_pull_request", issue=1)

    def test_a_clean_pull_request_lands_on_main_as_a_merge_commit(self):
        self.claim_branch_and_open("agent1", self.one, 1, {"one.py": "ONE = 1\n"})
        tip = git(self.one, "rev-parse", "HEAD")
        answer = call(self.run, "agent1", "mark_ready", issue=1)
        main = self.remote.main()
        self.assertTrue(answer.startswith(f"merged: claude/1 is in main as {main[:7]}"))
        self.assertIn(f"git diff {self.remote.base} team/main > patch.txt", answer)
        parents = git(self.remote.bare, "rev-list", "--parents", "-n", "1", main).split()[1:]
        self.assertEqual(parents, [self.remote.base, tip], "--no-ff makes a merge commit of main and the branch")
        self.assertEqual(self.remote.show("main", "one.py"), "ONE = 1")
        queue = self.run.state["sdlc_queue"]
        self.assertEqual(queue.pulls[1].state, "merged")
        self.assertEqual(queue.issues[1].label(), "closed")
        with self.assertRaisesRegex(ToolError, "already merged"):
            call(self.run, "agent1", "mark_ready", issue=1)
        with self.assertRaisesRegex(ToolError, "#1 is closed"):
            call(self.run, "agent1", "claim_issue", issue=1)

    def test_a_conflicting_pull_request_answers_main_moved_and_leaves_main(self):
        self.both_change_the_same_line()
        main_before = self.remote.main()
        with self.assertRaises(ToolError) as refusal:
            call(self.run, "agent2", "mark_ready", issue=2)
        answer = str(refusal.exception)
        self.assertTrue(answer.startswith(MAIN_MOVED + "."))
        self.assertIn("Conflicting files: app.py.", answer)
        self.assertIn(f"main is still at {main_before[:7]}", answer)
        self.assertEqual(self.remote.main(), main_before)
        self.assertIn("'hello, world'", self.remote.show("main", "app.py"))
        queue = self.run.state["sdlc_queue"]
        self.assertEqual(queue.pulls[2].state, "main moved")
        self.assertEqual(queue.issues[2].label(), "in-review")
        gate = self.run.state["sdlc_gate"]
        self.assertFalse(os.path.exists(os.path.join(gate.repo, ".git", "MERGE_HEAD")),
                         "the gate aborts the merge it could not finish")

    def test_after_merging_main_in_and_pushing_the_pull_request_merges(self):
        self.both_change_the_same_line()
        with self.assertRaises(ToolError):
            call(self.run, "agent2", "mark_ready", issue=2)
        first_merge = self.remote.main()
        status = call(self.run, "agent2", "pull_request_status", issue=2)
        self.assertIn("by agent2, main moved", status)
        self.assertIn("conflicting", status)
        # What the answer asks for: merge main in, resolve, commit, push.
        git(self.two, "fetch", "--quiet", "team")
        self.assertIn("CONFLICT", git(self.two, "merge", "team/main", check=False))
        resolved = BASE_TEXT.replace("'hello'", "'hello, world'") + "\n\ndef farewell():\n    return 'goodbye'\n"
        (self.two / "app.py").write_text(resolved, encoding="utf-8")
        git(self.two, "add", "app.py")
        git(self.two, "commit", "--quiet", "--no-edit")
        git(self.two, "push", "--quiet", "team", "claude/2")
        self.assertIn("clean, up to date", call(self.run, "agent2", "pull_request_status", issue=2))
        answer = call(self.run, "agent2", "mark_ready", issue=2)
        self.assertTrue(answer.startswith("merged: claude/2 is in main"))
        main = self.remote.main()
        # Main only moved forward: the first merge is still in its history.
        git(self.remote.bare, "merge-base", "--is-ancestor", first_merge, main)
        self.assertEqual(self.remote.show("main", "app.py"), resolved.rstrip("\n"))
        diff = git(self.remote.bare, "diff", self.remote.base, "main")
        self.assertIn("+    return 'hello, world'", diff)
        self.assertIn("+    return 'goodbye'", diff)

    def test_only_the_author_marks_ready_and_only_a_branch_with_new_work(self):
        call(self.run, "agent1", "claim_issue", issue=1)
        start_branch(self.one, 1, self.remote.base)
        git(self.one, "push", "--quiet", "team", "claude/1")
        call(self.run, "agent1", "open_pull_request", issue=1)
        with self.assertRaisesRegex(ToolError, "only its author marks it ready"):
            call(self.run, "agent2", "mark_ready", issue=1)
        with self.assertRaisesRegex(ToolError, "nothing to merge"):
            call(self.run, "agent1", "mark_ready", issue=1)
        queue = self.run.state["sdlc_queue"]
        self.assertEqual(queue.pulls[1].state, "draft")
        self.assertEqual(queue.issues[1].label(), "claimed", "a refused ready keeps the claim")
        with self.assertRaisesRegex(ToolError, "#2 has no pull request"):
            call(self.run, "agent2", "mark_ready", issue=2)

    def test_two_clean_pull_requests_marked_ready_at_once_both_land(self):
        self.claim_branch_and_open("agent1", self.one, 1, {"one.py": "ONE = 1\n"})
        self.claim_branch_and_open("agent2", self.two, 2, {"two.py": "TWO = 2\n"})
        start = threading.Barrier(2)
        answers = {}

        def ready(agent, issue):
            start.wait()
            answers[agent] = call(self.run, agent, "mark_ready", issue=issue)

        threads = [threading.Thread(target=ready, args=pair) for pair in (("agent1", 1), ("agent2", 2))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(60)
        self.assertEqual(sorted(answers), ["agent1", "agent2"])
        self.assertTrue(all(answer.startswith("merged") for answer in answers.values()))
        self.assertEqual(self.remote.show("main", "one.py"), "ONE = 1")
        self.assertEqual(self.remote.show("main", "two.py"), "TWO = 2")
        history = git(self.remote.bare, "rev-list", "--merges", "main").split()
        self.assertEqual(len(history), 2)

    def test_status_reads_how_the_branch_stands_to_main(self):
        self.assertIn("#1 has no pull request yet; the issue is not claimed yet (todo)",
                      call(self.run, "agent1", "pull_request_status", issue=1))
        self.both_change_the_same_line()
        merged = call(self.run, "agent2", "pull_request_status", issue=1)
        self.assertIn("Pull request for #1: claude/1 -> main, by agent1, merged. Merge attempts: 1.", merged)
        self.assertIn("Merged into main as", merged)
        conflicting = call(self.run, "agent2", "pull_request_status", issue=2)
        self.assertIn("by agent2, draft", conflicting)
        self.assertIn("conflicting", conflicting)
        self.assertIn("conflicts in app.py", conflicting)

    def test_status_says_behind_when_main_moved_without_a_conflict(self):
        self.claim_branch_and_open("agent1", self.one, 1, {"one.py": "ONE = 1\n"})
        self.claim_branch_and_open("agent2", self.two, 2, {"two.py": "TWO = 2\n"})
        self.assertIn("clean, up to date", call(self.run, "agent2", "pull_request_status", issue=2))
        call(self.run, "agent1", "mark_ready", issue=1)
        self.assertIn("behind", call(self.run, "agent2", "pull_request_status", issue=2))

    def test_the_board_shows_issues_claims_and_pull_requests(self):
        self.both_change_the_same_line()
        with self.assertRaises(ToolError):
            call(self.run, "agent2", "mark_ready", issue=2)
        text = call(self.run, "agent1", "board")
        main = self.remote.main()
        self.assertIn(f"As of commit {main[:7]} on main; the run began at the base ref {self.remote.base[:7]}",
                      text)
        self.assertIn("| #1 | Feature 1 | agent1 | closed |", text)
        self.assertIn("| #2 | Feature 2 | agent2 | in-review |", text)
        claims = text.split("## Claims")[1].split("## Pull requests")[0]
        self.assertIn("| (none) |", claims, "a ready pull request has released its claim")
        self.assertIn(f"| #1 | claude/1 | agent1 | merged | merged as {main[:7]} | 1 |", text)
        self.assertIn("| #2 | claude/2 | agent2 | main moved | conflicting (app.py) | 1 |", text)
        self.assertIn("| (none) |", text.split("## Queue")[1])

    def test_the_board_lists_held_claims_and_the_queue(self):
        call(self.run, "agent1", "claim_issue", issue=1)
        text = call(self.run, "agent2", "board")
        self.assertIn("| #1 | claude/1 | agent1 | none yet |", text)
        self.assertIn("| #2 | Feature 2 | agent2 |", text.split("## Queue")[1])
        self.assertIn("| (none) |", text.split("## Pull requests")[1].split("## Queue")[0])

    def test_metrics_count_the_protocols_steps(self):
        call_over_mcp(self.run, "agent1", "claim_issue", issue=1)
        call_over_mcp(self.run, "agent2", "claim_issue", issue=2)
        call_over_mcp(self.run, "agent1", "broadcast", text="I take app.py's greet")
        start_branch(self.one, 1, self.remote.base)
        commit_and_push(self.one, 1, {"app.py": BASE_TEXT.replace("'hello'", "'hello, world'")}, "one")
        start_branch(self.two, 2, self.remote.base)
        commit_and_push(self.two, 2, {"app.py": BASE_TEXT.replace("'hello'", "'goodbye'")}, "two")
        call_over_mcp(self.run, "agent1", "open_pull_request", issue=1)
        call_over_mcp(self.run, "agent2", "open_pull_request", issue=2)
        before = self.arm.metrics(self.run)
        self.assertIsNone(before["time_to_first_merge_seconds"])
        self.assertEqual(call_over_mcp(self.run, "agent1", "mark_ready", issue=1)[1], False)
        text, is_error = call_over_mcp(self.run, "agent2", "mark_ready", issue=2)
        self.assertTrue(is_error)
        self.assertTrue(text.startswith(MAIN_MOVED))
        metrics = self.arm.metrics(self.run)
        self.assertEqual({key: metrics[key] for key in ("claims", "prs_opened", "merge_attempts", "merges",
                                                         "merge_conflicts")},
                         {"claims": 2, "prs_opened": 2, "merge_attempts": 2, "merges": 1, "merge_conflicts": 1})
        self.assertGreaterEqual(metrics["time_to_first_merge_seconds"], 0)
        self.assertEqual(metrics["messages_sent"], 1)
        self.assertEqual(metrics["messages_by_agent"], {"agent1": 1})
        self.assertEqual(metrics["tool_calls"]["mark_ready"], 2)
        self.assertEqual(metrics["events"]["merge"], 1)

    def test_closing_the_run_frees_the_scratch_clone(self):
        self.claim_branch_and_open("agent1", self.one, 1, {"one.py": "ONE = 1\n"})
        gate = self.run.state["sdlc_gate"]
        scratch = gate.scratch.name
        self.assertTrue(os.path.isdir(scratch))
        with self.run.lock:
            self.run.closed = True
            self.arm.metrics(self.run)
        deadline = time.monotonic() + 10
        while os.path.isdir(scratch) and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertFalse(os.path.isdir(scratch))
        self.assertIn("Pull request for #1", call(self.run, "agent1", "pull_request_status", issue=1))

    def test_without_a_base_ref_the_remotes_main_at_the_start_stands_in(self):
        _, run = new_run(options={"git_remote_host": str(self.remote.bare)})
        self.assertEqual(run.state["sdlc_queue"].base_ref, self.remote.base)


class HubTest(unittest.TestCase):
    """The arm as agents reach it: through the hub, over HTTP."""

    def setUp(self):
        self.remote = SharedRemote()
        self.addCleanup(self.remote.close)
        self.hub = hub_module.Hub()
        self.server = hub_module.serve_in_background(self.hub)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def post(self, url, body, headers=None):
        request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                         headers={"Content-Type": "application/json",
                                                  "Accept": "application/json", **(headers or {})})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=30) as response:
            return json.loads(response.read())

    def test_the_hub_serves_the_protocol_over_mcp_and_rpc(self):
        options = {"git_remote_host": str(self.remote.bare), "base_ref": self.remote.base}
        answer = self.hub.create_run("sdlc", [2, 1], {"1": SPECS[1], "2": SPECS[2]}, options, "sdlc-run")
        self.assertEqual([(a["id"], a["role"], a["features"]) for a in answer["agents"]],
                         [("agent1", "peer", [1]), ("agent2", "peer", [2])])
        agent1 = answer["agents"][0]
        listed = self.post(agent1["mcp_url"], {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual({tool["name"] for tool in listed["result"]["tools"]}, set(ALIASES))
        claimed = self.post(agent1["rpc_url"], {"tool": "claim_issue", "arguments": {"issue": 1}})
        self.assertFalse(claimed["isError"])
        self.assertIn("claimed #1", claimed["text"])
        refused = self.post(answer["agents"][1]["rpc_url"], {"tool": "claim_issue", "arguments": {"issue": 1}})
        self.assertTrue(refused["isError"])
        self.release(answer)
        self.assertEqual(self.hub.get_run("sdlc-run")["metrics"]["claims"], 1)

    def release(self, answer):
        gate = self.hub.hosted(answer["run_id"]).run.state["sdlc_gate"]
        self.addCleanup(gate.release)


if __name__ == "__main__":
    unittest.main()
