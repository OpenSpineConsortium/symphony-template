"""The team arm is CooperBench's team mode re-made as a plug-in, and the
best arm of the authors' ablation, so a run through coordbench is worth
setting beside theirs only if the arm is theirs. These tests pin what
makes it so: the lead is chosen and the list seeded as runner/team.py
does, a claim is atomic and refuses another agent's task as coop_task.py
does, updates, listing and typed requests behave and print as the
in-container commands do, each tool answers to CooperBench's command, the
prompt is build_team_instruction's text (checked against CooperBench's own
function when its source is at hand), the metrics are metrics.py's, and
the directory is a well-formed Claude Code plugin as well as an arm."""

import importlib.util
import json
import os
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
COORDBENCH = ROOT / "experiment" / "coordbench"
TEAM = COORDBENCH / "arms" / "team"
sys.path.insert(0, str(COORDBENCH))

import cli  # noqa: E402
import hub as hub_module  # noqa: E402
import mcp  # noqa: E402
from arm import SUBMISSION_BLOCK, Call, Run, find_arm  # noqa: E402

RULE = "\n\n---\n\n"
DASH = "\u2014"
# Unstripped, with a trailing newline, as CooperBench reads feature.md.
SPECS = {3: "# Verbose flag\n\nAdd a --verbose flag.\n", 7: "# TOML\n\nRead TOML configs.\n",
         9: "# Colours\n\nColour the help.\n"}

ALIASES = {"task_create": "coop-task-create", "task_claim": "coop-task-claim",
           "task_update": "coop-task-update", "task_list": "coop-task-list",
           "request": "coop-request", "respond": "coop-respond", "pending": "coop-pending",
           "send_message": "coop-send", "broadcast": "coop-broadcast",
           "receive_messages": "coop-recv", "peek_messages": "coop-peek",
           "list_agents": "coop-agents", "wait_for_message": ""}
ARGV = {"task_create": ["words..."], "task_claim": ["task_id"],
        "task_update": ["task_id", "status", "flag", "note"], "task_list": ["flag", "second_flag"],
        "request": ["recipient", "kind", "words..."], "respond": ["request_id", "body..."],
        "pending": []}
TASK_FIELDS = ["id", "title", "owner", "status", "created_by", "created_at", "last_note", "metadata"]

# team_harness/prompt.py's _TEAM_LIST_USAGE, copied here so the test does
# not take the arm's word for it.
TEAM_LIST_USAGE = """Available shell commands (Redis-backed, atomic):

```bash
coop-task-create "<title>"                 # creates an open, unassigned task; prints task_id
coop-task-create --assign <agent> "<title>" # creates and pre-assigns; agent must still claim
coop-task-claim <task_id>                   # exit 0 if you got it, 2 if someone else owns it
coop-task-update <task_id> <status> [-n "<note>"]
                                            # statuses: open | in_progress | blocked | done
coop-task-list                              # JSON list of every task in the team
coop-task-list --mine                       # tasks you own
coop-task-list --open                       # open, unassigned tasks
```

Messaging (`coop-send` / `coop-recv` / `coop-broadcast` / `coop-peek`)
also works and is the right tool for short questions that don't
warrant a new task."""

MCP_SENTENCE = (
    "Every coop-* command is also a tool of the MCP server `coordbench`, with the same task list "
    "and inbox behind it: `coop-task-create` is `task_create`, `coop-task-claim` is `task_claim`, "
    "`coop-task-update` is `task_update`, `coop-task-list` is `task_list`, `coop-request` is "
    "`request`, `coop-respond` is `respond`, `coop-pending` is `pending`, `coop-send` is "
    "`send_message`, `coop-broadcast` is `broadcast`, `coop-recv` is `receive_messages`, "
    "`coop-peek` is `peek_messages`, and `coop-agents` is `list_agents`.")

LEAD_EXCERPTS = [
    "## You are the team-lead\n\nYou are **agent1** \u2014 the team-lead.  Members reporting to you:\n"
    "`agent2`, `agent3`.",
    "### The integration step is the WHOLE point of your job \u2014 DO NOT SKIP IT",
    "2. Break the spec into 2-4 concrete tasks and assign one per member\n"
    "   with `coop-task-create --assign <agent> \"...\"`.",
    "- [ ] `git diff` now shows BOTH features \u2014 your own and every\n"
    "      member's \u2014 present in the working tree.",
    "A shared scratchpad volume is mounted at `/workspace/shared/` for\n"
    "coordination \u2014 files there are NOT evaluated.  Drop design notes,\n"
    "interface contracts, or member-produced patches there so the whole\n"
    "team can see them with `ls /workspace/shared/`.",
]
MEMBER_EXCERPTS = [
    "## You are a team member\n\nYou are **agent2**.  The team-lead is **agent1**, who will\n"
    "organize work into tasks for you to claim.",
    "2. `coop-task-claim <task_id>`.  If you lose the race (exit code 2),\n   pick another.",
    "   `coop-send agent1 \"blocked on task <id>: ...\"`.",
    "   cd /workspace/repo && git diff > /workspace/shared/agent2.patch",
    "### Final submission \u2014 REQUIRED",
    "A shared scratchpad volume is mounted at `/workspace/shared/` for\n"
    "coordination \u2014 files there are NOT evaluated.  Use it for anything\n"
    "your peers might need to see \u2014 partial diffs, interface sketches,\n"
    "error logs from your reproduction script.",
]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TEAM_MODULE = load_module("coordbench_arm_team_under_test", TEAM / "arm.py")


def cooperbench_team_prompt():
    """CooperBench's team_harness/prompt.py, from a checkout named by
    COOPERBENCH_DIR (the variable experiment/setup.sh uses) or at
    ~/cooperbench, with the one module it imports (_coop/prompt.py) put in
    place of CooperBench's package, whose own imports need redis and
    modal. Returns the module and the stand-in modules its git branch
    imports at call time, or None when the source is not here."""
    for root in (os.environ.get("COOPERBENCH_DIR"), str(Path.home() / "cooperbench")):
        source = Path(root or "/nonexistent") / "src" / "cooperbench"
        coop_file = source / "agents" / "_coop" / "prompt.py"
        team_file = source / "team_harness" / "prompt.py"
        if coop_file.is_file() and team_file.is_file():
            packages = ("cooperbench", "cooperbench.agents", "cooperbench.agents._coop")
            stand_ins = {name: types.ModuleType(name) for name in packages}
            stand_ins["cooperbench.agents._coop.prompt"] = load_module("cooperbench_coop_prompt", coop_file)
            with mock.patch.dict(sys.modules, stand_ins):
                return load_module("cooperbench_team_prompt", team_file), stand_ins
    return None


COOPERBENCH = cooperbench_team_prompt()


def new_run(features=(3, 7, 9), options=None, run_id="r1"):
    arm = find_arm(str(TEAM))
    run = Run(run_id, arm, arm.layout(list(features)), options)
    arm.setup(run)
    return arm, run


def call(run, agent, tool, **arguments):
    """A tool call as the hub makes it, answered as /rpc answers it."""
    return hub_module.Hub().call(run, agent, tool, arguments)


def text_of(run, agent, tool, **arguments):
    answer = call(run, agent, tool, **arguments)
    if answer["isError"]:
        raise AssertionError(f"{tool} refused: {answer['text']}")
    return answer["text"]


def shell(run, agent, tool, *words):
    """A shell command as cli.py runs it: its words mapped onto the tool's
    argv as the hub describes it, then the same /rpc call."""
    hub = hub_module.Hub()
    description = next(t for t in hub.describe_tools(run, agent) if t["name"] == tool)
    with mock.patch.object(cli, "stdin_has_text", return_value=False):
        arguments = cli.words_to_arguments(description, list(words))
    return hub.call(run, agent, tool, arguments)


def tasks_of(run, agent="agent1", **filters):
    return json.loads(text_of(run, agent, "task_list", **filters))


def task_titled(run, title):
    return next(task for task in tasks_of(run) if task["title"] == title)


def board(run):
    return run.state["team"]


class LayoutAndSeeding(unittest.TestCase):
    def test_the_agent_with_the_lowest_feature_is_the_lead(self):
        arm = find_arm(str(TEAM))
        layout = [(a.id, a.role, a.features) for a in arm.layout([9, 3, 7])]
        self.assertEqual(layout, [("agent1", "lead", (3,)), ("agent2", "member", (7,)),
                                  ("agent3", "member", (9,))])

    def test_the_hub_creates_a_team_run_by_its_name(self):
        answer = hub_module.Hub().create_run("team", [7, 3], {3: "a", 7: "b"})
        self.assertEqual(answer["arm"], "team")
        self.assertEqual([(a["id"], a["role"], a["features"]) for a in answer["agents"]],
                         [("agent1", "lead", [3]), ("agent2", "member", [7])])

    def test_each_member_gets_its_feature_assigned_and_the_lead_its_integration_task(self):
        _, run = new_run()
        self.assertEqual([(t["title"], t["owner"]) for t in board(run).tasks.values()], [
            ("Implement feature 7", "agent2"), ("Implement feature 9", "agent3"),
            ("Lead-only: integrate and submit feature 3", "agent1")])
        for task in tasks_of(run):
            self.assertEqual(list(task), TASK_FIELDS)
            self.assertEqual((task["status"], task["created_by"], task["last_note"]),
                             ("open", "bench-runner", ""))
            self.assertIsInstance(task["created_at"], float)
        self.assertEqual(task_titled(run, "Implement feature 7")["metadata"],
                         {"feature_id": 7, "assigned_to": "agent2"})
        self.assertEqual(task_titled(run, "Lead-only: integrate and submit feature 3")["metadata"],
                         {"feature_id": 3, "assigned_to": "agent1", "lead_task": True})

    def test_seeding_is_in_the_audit_log_and_the_events(self):
        _, run = new_run()
        self.assertEqual([(e["kind"], e["by"]) for e in board(run).log], [("create", "bench-runner")] * 3)
        self.assertEqual([e["kind"] for e in run.events], ["task_create"] * 3)

    def test_a_team_of_one_has_only_the_leads_task(self):
        _, run = new_run(features=(4,))
        self.assertEqual([t["title"] for t in tasks_of(run)], ["Lead-only: integrate and submit feature 4"])


class Claims(unittest.TestCase):
    def test_a_claim_makes_the_caller_owner_and_moves_the_task_on(self):
        _, run = new_run()
        task_id = text_of(run, "agent1", "task_create", title="Write the parser")
        self.assertEqual(text_of(run, "agent3", "task_claim", task_id=task_id), "")
        task = task_titled(run, "Write the parser")
        self.assertEqual((task["owner"], task["status"]), ("agent3", "in_progress"))

    def test_exactly_one_of_many_racing_agents_wins(self):
        _, run = new_run(features=tuple(range(1, 13)))
        agents = list(run.agents)
        for _ in range(10):
            task_id = text_of(run, "agent1", "task_create", title="contested")
            start = threading.Barrier(len(agents))
            answers = {}

            def race(agent):
                start.wait()
                request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                           "params": {"name": "task_claim", "arguments": {"task_id": task_id}}}
                answers[agent] = mcp.handle(request, run, agent)["result"]

            threads = [threading.Thread(target=race, args=(agent,)) for agent in agents]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(10)
            winners = [agent for agent, answer in answers.items() if not answer["isError"]]
            self.assertEqual(len(answers), len(agents))
            self.assertEqual(len(winners), 1)
            self.assertEqual(board(run).tasks[task_id]["owner"], winners[0])
            losses = {a["content"][0]["text"] for a in answers.values() if a["isError"]}
            self.assertEqual(losses, {f"task {task_id} owned by {winners[0]}"})
            claims = [e for e in board(run).log if e["kind"] == "claim" and e["task_id"] == task_id]
            self.assertEqual([e["by"] for e in claims], winners)

    def test_a_task_assigned_to_another_agent_cannot_be_claimed(self):
        _, run = new_run()
        task = task_titled(run, "Implement feature 7")
        for intruder in ("agent3", "agent1"):
            answer = call(run, intruder, "task_claim", task_id=task["id"])
            self.assertEqual(answer, {"text": f"task {task['id']} owned by agent2", "isError": True})
        after = task_titled(run, "Implement feature 7")
        self.assertEqual((after["owner"], after["status"]), ("agent2", "open"))
        self.assertNotIn("claim", [e["kind"] for e in board(run).log])

    def test_the_assignee_claims_its_task_and_may_claim_it_again(self):
        _, run = new_run()
        task_id = task_titled(run, "Implement feature 7")["id"]
        text_of(run, "agent2", "task_claim", task_id=task_id)
        text_of(run, "agent2", "task_claim", task_id=task_id)
        self.assertEqual(task_titled(run, "Implement feature 7")["status"], "in_progress")
        self.assertEqual(run.arm.metrics(run)["claims_per_agent"], {"agent2": 2})

    def test_an_unknown_task_cannot_be_claimed(self):
        _, run = new_run()
        self.assertEqual(call(run, "agent2", "task_claim", task_id="nope"),
                         {"text": "task nope does not exist", "isError": True})


class UpdatesAndListing(unittest.TestCase):
    def setUp(self):
        _, self.run = new_run()
        self.task_id = task_titled(self.run, "Implement feature 7")["id"]
        text_of(self.run, "agent2", "task_claim", task_id=self.task_id)

    def test_the_owner_sets_status_and_note(self):
        text_of(self.run, "agent2", "task_update", task_id=self.task_id, status="done",
                note="patch at /workspace/shared/agent2.patch")
        task = task_titled(self.run, "Implement feature 7")
        self.assertEqual((task["status"], task["last_note"]), ("done", "patch at /workspace/shared/agent2.patch"))
        self.assertEqual(board(self.run).log[-1]["note"], "patch at /workspace/shared/agent2.patch")

    def test_a_status_without_a_note_keeps_the_last_note(self):
        text_of(self.run, "agent2", "task_update", task_id=self.task_id, status="blocked", note="need the API")
        text_of(self.run, "agent2", "task_update", task_id=self.task_id, status="in_progress")
        self.assertEqual(task_titled(self.run, "Implement feature 7")["last_note"], "need the API")
        self.assertNotIn("note", board(self.run).log[-1])

    def test_only_the_owner_updates(self):
        answer = call(self.run, "agent1", "task_update", task_id=self.task_id, status="done")
        self.assertEqual(answer, {"text": f"task {self.task_id} owned by 'agent2', not you", "isError": True})

    def test_an_unknown_status_or_task_is_refused(self):
        answer = call(self.run, "agent2", "task_update", task_id=self.task_id, status="finished")
        self.assertEqual(answer["text"],
                         "invalid status 'finished'; expected one of ['blocked', 'done', 'in_progress', 'open']")
        answer = call(self.run, "agent2", "task_update", task_id="nope", status="done")
        self.assertEqual(answer, {"text": "task nope does not exist", "isError": True})

    def test_list_holds_every_task_in_id_order(self):
        ids = [task["id"] for task in tasks_of(self.run)]
        self.assertEqual(ids, sorted(board(self.run).tasks))
        self.assertEqual(len(ids), 3)

    def test_list_filters_mine_and_open(self):
        mine = tasks_of(self.run, "agent2", mine=True)
        self.assertEqual([t["id"] for t in mine], [self.task_id])
        still_open = {t["title"] for t in tasks_of(self.run, "agent2", open=True)}
        self.assertEqual(still_open, {"Implement feature 9", "Lead-only: integrate and submit feature 3"})
        self.assertEqual(tasks_of(self.run, "agent2", mine=True, open=True), [])


class ShellCommands(unittest.TestCase):
    def test_each_tool_answers_to_cooperbenchs_command(self):
        _, run = new_run()
        for agent in run.agents:
            described = hub_module.Hub().describe_tools(run, agent)
            self.assertEqual({t["name"]: t["alias"] for t in described}, ALIASES)
            self.assertEqual({t["name"]: t["argv"] for t in described if t["name"] in ARGV}, ARGV)

    def test_create_with_and_without_assign(self):
        _, run = new_run()
        for words, owner in ((["Write the parser"], ""),
                             (["--assign", "agent2", "Write the parser"], "agent2"),
                             (["Write the parser", "--assign=agent3"], "agent3")):
            answer = shell(run, "agent1", "task_create", *words)
            self.assertFalse(answer["isError"], answer)
            task = board(run).tasks[answer["text"]]
            self.assertEqual((task["title"], task["owner"], task["created_by"]),
                             ("Write the parser", owner, "agent1"))

    def test_create_needs_a_title(self):
        _, run = new_run()
        self.assertEqual(shell(run, "agent1", "task_create", "--assign", "agent2")["text"],
                         "the following arguments are required: title")

    def test_update_takes_its_note_anywhere(self):
        _, run = new_run()
        task_id = task_titled(run, "Implement feature 7")["id"]
        shell(run, "agent2", "task_claim", task_id)
        answer = shell(run, "agent2", "task_update", task_id, "done", "-n", "patch at /workspace/shared/agent2.patch")
        self.assertFalse(answer["isError"], answer)
        answer = shell(run, "agent2", "task_update", "-n", "waiting on agent1", task_id, "blocked")
        self.assertFalse(answer["isError"], answer)
        task = board(run).tasks[task_id]
        self.assertEqual((task["status"], task["last_note"]), ("blocked", "waiting on agent1"))

    def test_update_refuses_the_words_argparse_refuses(self):
        _, run = new_run()
        task_id = task_titled(run, "Implement feature 7")["id"]
        self.assertEqual(shell(run, "agent2", "task_update", task_id, "done", "-n")["text"],
                         "argument -n: expected one argument")
        self.assertEqual(shell(run, "agent2", "task_update", task_id, "done", "a note")["text"],
                         "unrecognized arguments: a note")
        with self.assertRaises(cli.Failure):
            shell(run, "agent2", "task_update", task_id, "done", "-n", "a", "note")

    def test_an_mcp_note_is_never_read_as_flags(self):
        _, run = new_run()
        task_id = task_titled(run, "Implement feature 7")["id"]
        text_of(run, "agent2", "task_claim", task_id=task_id)
        text_of(run, "agent2", "task_update", task_id=task_id, status="blocked", note="run pytest -n 4 --open")
        self.assertEqual(board(run).tasks[task_id]["last_note"], "run pytest -n 4 --open")

    def test_list_flags(self):
        _, run = new_run()
        mine = json.loads(shell(run, "agent2", "task_list", "--mine")["text"])
        self.assertEqual([t["title"] for t in mine], ["Implement feature 7"])
        both = json.loads(shell(run, "agent2", "task_list", "--open", "--mine")["text"])
        self.assertEqual([t["title"] for t in both], ["Implement feature 7"])
        self.assertEqual(len(json.loads(shell(run, "agent2", "task_list")["text"])), 3)
        self.assertEqual(shell(run, "agent2", "task_list", "--all")["text"], "unrecognized arguments: --all")

    def test_request_with_a_body_of_many_words_and_a_wait(self):
        _, run = new_run()
        answers = {}
        waiting = threading.Thread(target=lambda: answers.update(shell(
            run, "agent2", "request", "agent1", "plan_approval", "may I", "take", "cli.py?", "--wait", "10")))
        waiting.start()
        self.assertTrue(run.wait_until(lambda: bool(board(run).requests), 5))
        pending = json.loads(shell(run, "agent1", "pending")["text"])
        self.assertEqual([(p["from"], p["kind"], p["body"]) for p in pending],
                         [("agent2", "plan_approval", "may I take cli.py?")])
        self.assertEqual(shell(run, "agent1", "respond", pending[0]["id"], "yes,", "take", "it"),
                         {"text": "", "isError": False})
        waiting.join(10)
        response = json.loads(answers["text"])
        self.assertEqual((response["from"], response["to"], response["body"]), ("agent1", "agent2", "yes, take it"))


class Requests(unittest.TestCase):
    def setUp(self):
        _, self.run = new_run()

    def test_a_request_waits_in_the_recipients_pending_list(self):
        request_id = text_of(self.run, "agent2", "request", recipient="agent1", kind="review", body="look at x")
        self.assertRegex(request_id, r"^[0-9a-f]{10}$")
        pending = json.loads(text_of(self.run, "agent1", "pending"))
        self.assertEqual([(p["id"], p["from"], p["to"], p["kind"], p["body"]) for p in pending],
                         [(request_id, "agent2", "agent1", "review", "look at x")])
        self.assertIsInstance(pending[0]["ts"], float)
        self.assertEqual(json.loads(text_of(self.run, "agent3", "pending")), [])

    def test_only_the_addressee_responds_and_only_once(self):
        request_id = text_of(self.run, "agent2", "request", recipient="agent1", kind="review", body="x")
        self.assertEqual(call(self.run, "agent3", "respond", request_id=request_id, body="no"),
                         {"text": f"request {request_id} not addressed to agent3", "isError": True})
        self.assertEqual(text_of(self.run, "agent1", "respond", request_id=request_id, body="fine"), "")
        self.assertEqual(json.loads(text_of(self.run, "agent1", "pending")), [])
        self.assertEqual(call(self.run, "agent1", "respond", request_id=request_id, body="again"),
                         {"text": f"unknown request {request_id}", "isError": True})

    def test_a_waiting_request_gets_its_response(self):
        answers = {}
        waiting = threading.Thread(target=lambda: answers.update(call(
            self.run, "agent2", "request", recipient="agent1", kind="plan_approval", body="plan", wait=10)))
        waiting.start()
        self.assertTrue(self.run.wait_until(lambda: bool(board(self.run).requests), 5))
        request_id = next(iter(board(self.run).requests))
        text_of(self.run, "agent1", "respond", request_id=request_id, body="approved")
        waiting.join(10)
        self.assertFalse(answers["isError"], answers)
        response = json.loads(answers["text"])
        self.assertEqual(list(response), ["id", "from", "to", "body", "ts"])
        self.assertEqual((response["id"], response["body"]), (request_id, "approved"))

    def test_a_wait_times_out_with_cooperbenchs_message(self):
        answer = call(self.run, "agent2", "request", recipient="agent1", kind="k", body="b", wait=0.1)
        request_id = next(iter(board(self.run).requests))
        self.assertEqual(answer, {"text": f"timed out waiting for response to {request_id}", "isError": True})

    def test_closing_the_run_ends_a_wait(self):
        hub = hub_module.Hub()
        hub.create_run("team", [1, 2], {1: "a", 2: "b"}, run_id="closing")
        run = hub.hosted("closing").run
        answers = {}
        waiting = threading.Thread(target=lambda: answers.update(hub.call(
            run, "agent2", "request", {"recipient": "agent1", "kind": "k", "wait": 60})))
        waiting.start()
        run.wait_until(lambda: bool(board(run).requests), 5)
        hub.close_run("closing")
        waiting.join(10)
        self.assertFalse(waiting.is_alive())
        self.assertTrue(answers["isError"])
        self.assertTrue(answers["text"].startswith("timed out waiting for response to "))

    def test_a_request_to_nobody_or_with_a_bad_wait_is_refused(self):
        answer = call(self.run, "agent2", "request", recipient="agent9", kind="k", body="b")
        self.assertEqual(answer, {"text": "no agent named 'agent9'; the agents are agent1, agent2, agent3",
                                  "isError": True})
        answer = call(self.run, "agent2", "request", recipient="agent1", kind="k", wait="soon")
        self.assertEqual(answer["text"], "argument --wait: invalid float value: 'soon'")
        self.assertEqual(board(self.run).requests, {})

    def test_requests_are_audited_but_do_not_count_as_task_activity(self):
        request_id = text_of(self.run, "agent2", "request", recipient="agent1", kind="k", body="b")
        text_of(self.run, "agent1", "respond", request_id=request_id, body="r")
        log = board(self.run).log[-2:]
        self.assertEqual([(e["kind"], e["by"], e["to"]) for e in log], [("request", "agent2", "agent1"),
                                                                       ("response", "agent1", "agent2")])
        self.assertEqual(log[0]["request_kind"], "k")
        metrics = self.run.arm.metrics(self.run)
        self.assertEqual((metrics["claims_per_agent"], metrics["updates_per_agent"]), ({}, {}))


class Prompts(unittest.TestCase):
    def prompts(self, features=(3, 7, 9), options=None):
        arm, run = new_run(features, options)
        return {agent: arm.prompt(run, agent, SPECS) for agent in run.agents}

    def test_the_lead_gets_the_task_the_submission_block_and_the_lead_block(self):
        lead = self.prompts()["agent1"]
        self.assertTrue(lead.startswith(SPECS[3] + RULE + SUBMISSION_BLOCK + RULE + "## You are the team-lead"))
        for excerpt in LEAD_EXCERPTS:
            self.assertIn(excerpt, lead)
        self.assertIn(TEAM_LIST_USAGE + "\n\n" + MCP_SENTENCE + "\n\nA shared scratchpad volume", lead)
        self.assertNotIn("## You are a team member", lead)

    def test_a_member_gets_the_member_block_naming_the_lead(self):
        member = self.prompts()["agent2"]
        self.assertTrue(member.startswith(SPECS[7] + RULE + SUBMISSION_BLOCK + RULE + "## You are a team member"))
        for excerpt in MEMBER_EXCERPTS:
            self.assertIn(excerpt, member)
        self.assertIn(TEAM_LIST_USAGE + "\n\n" + MCP_SENTENCE + "\n\nA shared scratchpad volume", member)

    def test_no_git_block_without_a_shared_remote(self):
        for prompt in self.prompts().values():
            self.assertNotIn("## Git collaboration", prompt)
            self.assertEqual(prompt.count(RULE), 2)

    def test_a_shared_remote_adds_cooperbenchs_git_block_last(self):
        lead = self.prompts(options={"git_remote": "git://host/team.git"})["agent1"]
        git = lead.split(RULE)[-1]
        self.assertTrue(git.startswith(f"## Git collaboration {DASH} MERGE IS REQUIRED BEFORE SUBMITTING"))
        self.assertIn("- Partner branches: `team/agent2`, `team/agent3`", git)
        self.assertIn("git push team agent1 --force || true", git)
        self.assertIn("  git fetch team && git merge --no-edit team/agent3 || true   # pull in agent3's work", git)

    def test_a_team_of_one_gets_the_solo_prompt(self):
        self.assertEqual(self.prompts(features=(3,))["agent1"], SPECS[3] + RULE + SUBMISSION_BLOCK)

    @unittest.skipIf(COOPERBENCH is None, "CooperBench's source is not here; set COOPERBENCH_DIR to its checkout")
    def test_prompts_are_cooperbenchs_but_for_the_mcp_sentence(self):
        team, stand_ins = COOPERBENCH
        for git in (False, True):
            arm, run = new_run(options={"git_remote": "git://host/team.git"} if git else {})
            for agent, spec in run.agents.items():
                with self.subTest(agent=agent, git=git), mock.patch.dict(sys.modules, stand_ins):
                    theirs = team.build_team_instruction(
                        SPECS[spec.features[0]], agents=list(run.agents), agent_id=agent,
                        team_role=spec.role, git_enabled=git)
                    ours = arm.prompt(run, agent, SPECS)
                    self.assertEqual(ours.replace("\n\n" + MCP_SENTENCE, "", 1), theirs)


class Metrics(unittest.TestCase):
    def test_metrics_follow_cooperbenchs_definitions(self):
        _, run = new_run(features=(3, 7))
        member_task = task_titled(run, "Implement feature 7")["id"]
        lead_task = task_titled(run, "Lead-only: integrate and submit feature 3")["id"]
        text_of(run, "agent1", "task_create", title="nobody's yet")
        text_of(run, "agent2", "task_claim", task_id=member_task)
        text_of(run, "agent2", "task_update", task_id=member_task, status="done", note="patch")
        text_of(run, "agent1", "task_claim", task_id=lead_task)
        text_of(run, "agent1", "task_update", task_id=lead_task, status="in_progress", note="merging")
        text_of(run, "agent2", "send_message", to="agent1", text="patch is up")
        metrics = run.arm.metrics(run)
        self.assertEqual({key: metrics[key] for key in ("tasks_total", "tasks_done", "unowned_at_end",
                                                         "claims_per_agent", "updates_per_agent")},
                         {"tasks_total": 3, "tasks_done": 1, "unowned_at_end": 1,
                          "claims_per_agent": {"agent2": 1, "agent1": 1},
                          "updates_per_agent": {"agent2": 1, "agent1": 1}})
        self.assertGreaterEqual(metrics["time_to_first_claim_seconds"], 0)
        self.assertEqual((metrics["messages_sent"], metrics["messages_by_agent"]), (1, {"agent2": 1}))
        self.assertEqual(metrics["tool_calls"]["task_claim"], 2)

    def test_time_to_first_claim_runs_from_the_first_create_to_the_first_claim(self):
        events = [{"kind": "create", "ts": 100.0, "by": "bench-runner"},
                  {"kind": "create", "ts": 101.0, "by": "bench-runner"},
                  {"kind": "claim", "ts": 104.5, "by": "agent2"},
                  {"kind": "claim", "ts": 103.25, "by": "agent1"}]
        metrics = TEAM_MODULE.compute_metrics(events, [{"owner": "agent1", "status": "done"}, {"owner": ""}])
        self.assertEqual(metrics, {"tasks_total": 2, "tasks_done": 1, "unowned_at_end": 1,
                                   "time_to_first_claim_seconds": 3.25,
                                   "claims_per_agent": {"agent2": 1, "agent1": 1}, "updates_per_agent": {}})

    def test_no_claim_means_no_time_to_first_claim(self):
        _, run = new_run()
        self.assertIsNone(run.arm.metrics(run)["time_to_first_claim_seconds"])

    def test_closing_through_the_hub_answers_the_metrics(self):
        hub = hub_module.Hub()
        hub.create_run("team", [1, 2], {1: "a", 2: "b"}, run_id="m")
        self.assertEqual(hub.close_run("m")["tasks_total"], 2)


class Mirror(unittest.TestCase):
    def test_listing_mirrors_the_list_into_the_shared_directory(self):
        with tempfile.TemporaryDirectory() as shared:
            _, run = new_run(options={"shared_dir_host": shared})
            (Path(shared) / "tasks").mkdir()
            (Path(shared) / "tasks" / "gone.json").write_text("{}", encoding="utf-8")
            listed = tasks_of(run, "agent2")
            mirror = Path(shared) / "tasks"
            self.assertEqual(sorted(p.name for p in mirror.iterdir()),
                             sorted([f"{t['id']}.json" for t in listed] + ["_index.json", "_log.jsonl"]))
            self.assertEqual(json.loads((mirror / f"{listed[0]['id']}.json").read_text()), listed[0])
            self.assertEqual(json.loads((mirror / "_index.json").read_text())["ids"], [t["id"] for t in listed])
            self.assertEqual(len((mirror / "_log.jsonl").read_text().splitlines()), 3)

    def test_without_a_shared_directory_nothing_is_written(self):
        _, run = new_run()
        mirror = mock.Mock()
        # The module find_arm loaded, which is not TEAM_MODULE: each load
        # of an arm is a module of its own.
        with mock.patch.dict(type(run.arm).setup.__globals__, {"mirror_task_list": mirror}):
            tasks_of(run)
        mirror.assert_not_called()


class PluginFiles(unittest.TestCase):
    def read_json(self, relative):
        return json.loads((TEAM / relative).read_text(encoding="utf-8"))

    def test_plugin_json(self):
        plugin = self.read_json(".claude-plugin/plugin.json")
        self.assertEqual((plugin["name"], plugin["version"]), ("coordbench-team", "0.1.0"))
        self.assertTrue(plugin["description"])

    def test_mcp_json_points_at_this_agents_hub_endpoint(self):
        self.assertEqual(self.read_json(".mcp.json"),
                         {"mcpServers": {"coordbench": {"type": "http", "url": "${COORD_MCP_URL}"}}})

    def test_arm_json(self):
        config = self.read_json("arm.json")
        self.assertEqual(set(config), {"entry", "name", "description", "needs", "plugins", "mcp_servers"})
        self.assertEqual((config["entry"], config["name"], config["needs"], config["plugins"], config["mcp_servers"]),
                         ("arm.py:TeamArm", "team", ["shared_volume"], [], {}))
        arm = find_arm("team")
        self.assertEqual((type(arm).__name__, tuple(arm.needs)), ("TeamArm", ("shared_volume",)))

    def test_skill_has_frontmatter_and_names_every_tool_and_command(self):
        text = (TEAM / "skills" / "coordbench-team" / "SKILL.md").read_text(encoding="utf-8")
        lines = text.split("\n")
        self.assertEqual(lines[0], "---")
        end = lines.index("---", 1)
        fields = dict(line.split(": ", 1) for line in lines[1:end])
        self.assertEqual(set(fields), {"name", "description"})
        self.assertEqual(fields["name"], "coordbench-team")
        self.assertNotIn(": ", fields["description"])
        body = "\n".join(lines[end + 1:])
        for name, alias in ALIASES.items():
            self.assertIn(f"`{name}`", body)
            if alias:
                self.assertIn(f"`{alias}", body)

    def test_every_file_is_ascii_with_lf(self):
        for path in [p for p in TEAM.rglob("*") if p.is_file() and "__pycache__" not in p.parts]:
            raw = path.read_bytes()
            with self.subTest(path=path.name):
                raw.decode("ascii")
                self.assertNotIn(b"\r", raw)
                self.assertTrue(raw.endswith(b"\n"))

    def test_every_agent_lists_every_tool_over_mcp(self):
        _, run = new_run()
        for agent in run.agents:
            request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
            names = [t["name"] for t in mcp.handle(request, run, agent)["result"]["tools"]]
            self.assertEqual(names, list(ALIASES))


if __name__ == "__main__":
    unittest.main()
