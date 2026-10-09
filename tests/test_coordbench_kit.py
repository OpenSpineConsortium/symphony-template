"""kit.py is the messaging every arm but solo serves, ported from CooperBench's
coop_msg.py, and the long poll its team mode registers. These tests pin
the port against coop_msg.py's own behaviour (a message to any name is
queued, an empty or missing text is sent, a missing recipient is refused
as argparse refuses it, "sent to" is marked for stderr and broadcast says
nothing, every entry has timestamp_iso), the long poll's text and schema
against mcp_server.py's (read from CooperBench's source when it is at
hand), and the long poll's safety: the wait and the pop in one hold of the
lock, a closed run that wakes it, and a timeout refused rather than
crashed on."""

import ast
import json
import os
import sys
import threading
import time
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COORDBENCH = ROOT / "experiment" / "coordbench"
sys.path.insert(0, str(COORDBENCH))

import kit  # noqa: E402
from arm import AgentSpec, Arm, Call, Run, ToolError  # noqa: E402

AGENTS = ("agent1", "agent2", "agent3")
# mcp_server.py's text at 63b9d44, copied here so a drift in kit.py shows
# even where CooperBench's source is not at hand.
COOPERBENCH_DESCRIPTION = ("Block server-side until a message arrives in your team inbox, "
                           "or until timeout_ms elapses.  Returns the message text on hit, "
                           "or a 'no message' marker on timeout.  Prefer this to busy-polling "
                           "coop-recv when you're idle between substantive actions.")
COOPERBENCH_TIMEOUT = {"type": "integer", "minimum": 100, "maximum": 30000, "default": 5000,
                       "description": "How long to block before giving up."}
MARKER = "(no message arrived within the timeout)"
ENTRY_KEYS = {"from", "to", "content", "timestamp", "timestamp_iso"}


def cooperbench_wait_tool():
    """CooperBench's wait_for_message as mcp_server.py lists it, from a
    checkout named by COOPERBENCH_DIR or at ~/cooperbench, else None. The
    listing is read from the file with ast rather than imported, since
    the module imports redis at its top and the literal needs nothing."""
    roots = [os.environ.get("COOPERBENCH_DIR"), str(Path.home() / "cooperbench")]
    for root in filter(None, roots):
        path = Path(root) / "src" / "cooperbench" / "team_harness" / "mcp_server.py"
        if path.is_file():
            return tools_list_literal(path)["tools"][0]
    return None


def tools_list_literal(path):
    module = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef) and node.name == "_tools_list":
            returned = next(n for n in ast.walk(node) if isinstance(n, ast.Return))
            return ast.literal_eval(returned.value)
    raise AssertionError(f"{path} has no _tools_list")


COOPERBENCH_TOOL = cooperbench_wait_tool()


def tools(wait=True):
    return {tool.name: tool for tool in kit.messaging_tools(wait=wait)}


class DrainedBetween(threading.Condition):
    """A condition whose wait, once it holds, empties the agent's inbox
    before handing control back: the race between a wait and its pop (a
    receive_messages by the same agent slipping in), made certain."""

    def __init__(self, run, agent):
        super().__init__()
        self.run, self.agent = run, agent

    def wait_for(self, predicate, timeout=None):
        held = super().wait_for(predicate, timeout)
        kit.inbox(self.run, self.agent).clear()
        return held


class KitTest(unittest.TestCase):
    def setUp(self):
        self.run = Run("r1", Arm(), [AgentSpec(agent, "peer", (n,)) for n, agent in enumerate(AGENTS, 1)])

    def call(self, agent, name, **arguments):
        return tools()[name].handler(Call(self.run, agent, arguments))

    def refused(self, agent, name, **arguments):
        with self.assertRaises(ToolError) as caught:
            self.call(agent, name, **arguments)
        return caught.exception

    def contents(self, agent):
        return [entry["content"] for entry in kit.inbox(self.run, agent)]

    def message_events(self):
        return [event for event in self.run.events if event["kind"] == "message"]

    def in_a_thread(self, agent, name, **arguments):
        """Run the tool on a thread; the result and the seconds it took are
        read back through the list the thread fills."""
        outcome = []
        started = time.monotonic()

        def work():
            outcome.append(self.call(agent, name, **arguments))
            outcome.append(time.monotonic() - started)

        thread = threading.Thread(target=work, daemon=True)
        thread.start()
        return thread, outcome


class SendTest(KitTest):
    """The commands as coop_msg.py has them."""

    def test_a_message_to_any_name_is_queued_without_refusal(self):
        # coop_msg.py pushes to <recipient>:inbox whatever the name is;
        # list_agents is how an agent learns the names.
        self.assertEqual(self.call("agent1", "send_message", to="agent9", text="hi"), "sent to agent9")
        self.assertEqual(self.contents("agent9"), ["hi"])
        self.assertEqual(kit.inbox(self.run, "agent9")[0]["to"], "agent9")
        self.assertEqual([e["to"] for e in self.message_events()], ["agent9"])
        self.assertEqual(self.contents("agent2"), [])

    def test_an_empty_or_missing_text_is_sent_as_empty(self):
        # coop_msg.py's content is optional and read from stdin when
        # missing, which at its end is "".
        self.call("agent1", "send_message", to="agent2", text="")
        self.call("agent1", "send_message", to="agent2")
        self.assertEqual(self.contents("agent2"), ["", ""])
        self.assertEqual(self.call("agent1", "broadcast"), "")
        self.assertEqual((self.contents("agent2"), self.contents("agent3")), (["", "", ""], [""]))
        self.assertEqual([e["chars"] for e in self.message_events()], [0, 0, 0, 0])

    def test_a_missing_recipient_is_refused_as_argparse_refuses_it(self):
        for arguments in ({"text": "hi"}, {"to": None, "text": "hi"}):
            with self.subTest(arguments=arguments):
                problem = self.refused("agent1", "send_message", **arguments)
                self.assertEqual(str(problem), "the following arguments are required: recipient")
                self.assertEqual(problem.exit_code, 2)
        self.assertEqual(self.run.state.get("inboxes", {}), {})
        self.assertEqual(self.message_events(), [])

    def test_a_recipient_or_text_that_is_not_a_string_is_refused_before_anything_is_queued(self):
        # An integer text used to be delivered and then reported to the
        # sender as a hub crash when len() failed; a list as the recipient
        # crashed on the inbox lookup.
        for arguments in ({"to": ["agent2"], "text": "hi"}, {"to": "agent2", "text": 5},
                          {"to": 2, "text": "hi"}, {"to": "agent2", "text": ["hi"]}):
            with self.subTest(arguments=arguments):
                self.refused("agent1", "send_message", **arguments)
        self.assertEqual(self.run.state.get("inboxes", {}), {})
        self.assertEqual(self.message_events(), [])

    def test_a_broadcast_of_a_bad_text_reaches_nobody(self):
        # The text is checked before the first peer, so it is all or none.
        self.refused("agent2", "broadcast", text=5)
        self.assertEqual(self.run.state.get("inboxes", {}), {})
        self.assertEqual(self.message_events(), [])

    def test_broadcast_says_nothing_and_reaches_every_peer(self):
        self.assertEqual(self.call("agent2", "broadcast", text="config.py is mine"), "")
        self.assertEqual([self.contents(a) for a in AGENTS], [["config.py is mine"], [], ["config.py is mine"]])

    def test_every_entry_carries_both_timestamps(self):
        before = datetime.now()
        self.call("agent1", "send_message", to="agent2", text="now")
        entry = kit.inbox(self.run, "agent2")[0]
        self.assertEqual(set(entry), ENTRY_KEYS)
        self.assertIsInstance(entry["timestamp"], float)
        stamped = datetime.fromisoformat(entry["timestamp_iso"])
        self.assertLessEqual(before, stamped)
        self.assertLessEqual(stamped, datetime.now())

    def test_the_commands_take_coop_msgs_positionals(self):
        # coop-send <recipient> [content], coop-broadcast [content]: one
        # word each, the content optional, so an unquoted extra word is a
        # word too many, as argparse says.
        send, cast = tools()["send_message"], tools()["broadcast"]
        self.assertEqual((send.argv, cast.argv), (("to", "text"), ("text",)))
        self.assertEqual(send.input_schema["required"], ["to"])
        self.assertEqual(cast.input_schema["required"], [])

    def test_send_is_marked_to_print_on_stderr_and_nothing_else_is(self):
        marks = {name: tool.input_schema.get("x-coordbench-prints") for name, tool in tools().items()}
        self.assertEqual(marks, {"send_message": "stderr", "broadcast": None, "receive_messages": None,
                                 "peek_messages": None, "list_agents": None, "wait_for_message": None})


class WaitTest(KitTest):
    """The long poll: CooperBench's tool in text and schema, coordbench's in
    behaviour, and safe under concurrent calls."""

    def test_the_tool_is_cooperbenchs_in_text_and_schema(self):
        tool = tools()["wait_for_message"]
        self.assertEqual(tool.description, COOPERBENCH_DESCRIPTION)
        self.assertEqual(tool.input_schema["properties"], {"timeout_ms": COOPERBENCH_TIMEOUT})
        self.assertNotIn("wait_for_message", tools(wait=False))

    @unittest.skipIf(COOPERBENCH_TOOL is None,
                     "CooperBench's source is not here; set COOPERBENCH_DIR to its checkout")
    def test_the_tool_matches_mcp_servers_listing(self):
        tool = tools()["wait_for_message"]
        self.assertEqual(COOPERBENCH_TOOL["name"], tool.name)
        self.assertEqual(COOPERBENCH_TOOL["description"], tool.description)
        self.assertEqual(COOPERBENCH_TOOL["inputSchema"]["properties"], tool.input_schema["properties"])

    def test_the_marker_is_cooperbenchs(self):
        self.assertEqual(kit.NO_MESSAGE, MARKER)

    def test_hands_over_the_oldest_and_leaves_the_rest(self):
        for text in ("one", "two"):
            self.call("agent2", "send_message", to="agent1", text=text)
        handed = json.loads(self.call("agent1", "wait_for_message", timeout_ms=100))
        self.assertEqual((handed["from"], handed["content"]), ("agent2", "one"))
        self.assertEqual(self.contents("agent1"), ["two"])
        self.assertEqual([e["count"] for e in self.run.events if e["kind"] == "receive"], [1])

    def test_returns_the_marker_once_the_timeout_passes(self):
        started = time.monotonic()
        self.assertEqual(self.call("agent1", "wait_for_message", timeout_ms=100), MARKER)
        self.assertGreaterEqual(time.monotonic() - started, 0.09)

    def test_wakes_when_a_message_arrives(self):
        thread, outcome = self.in_a_thread("agent1", "wait_for_message", timeout_ms=10000)
        time.sleep(0.2)
        self.call("agent3", "send_message", to="agent1", text="wake")
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive(), "the wait slept on past the message")
        self.assertEqual(json.loads(outcome[0])["content"], "wake")
        self.assertLess(outcome[1], 5)

    def test_a_closed_run_wakes_the_wait_at_once(self):
        # The wait used to look only at the inbox, so a close woke it and
        # it slept on until its timeout.
        thread, outcome = self.in_a_thread("agent1", "wait_for_message", timeout_ms=10000)
        time.sleep(0.2)
        with self.run.lock:
            self.run.closed = True
            self.run.lock.notify_all()
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive(), "the wait slept on past the close")
        self.assertEqual(outcome[0], MARKER)
        self.assertLess(outcome[1], 5)

    def test_an_inbox_drained_between_the_wait_and_the_pop_gives_the_marker(self):
        # The wait and the pop used to be two holds of the lock, and a
        # receive_messages between them left pop(0) an empty list.
        self.run.lock = DrainedBetween(self.run, "agent1")
        self.call("agent2", "send_message", to="agent1", text="gone")
        self.assertEqual(self.call("agent1", "wait_for_message", timeout_ms=100), MARKER)

    def test_a_timeout_that_is_not_a_finite_number_is_refused(self):
        for value in ("soon", "", float("inf"), float("-inf"), "nan", [5000], {"ms": 5000}):
            with self.subTest(timeout_ms=value):
                self.refused("agent1", "wait_for_message", timeout_ms=value)

    def test_the_timeout_is_read_as_a_number_and_held_to_the_schemas_range(self):
        self.assertEqual(kit.wait_seconds("5000.0"), 5.0)
        self.assertEqual(kit.wait_seconds(2500), 2.5)
        self.assertEqual(kit.wait_seconds(10), 0.1)
        self.assertEqual(kit.wait_seconds("1e9"), 30.0)
        started = time.monotonic()
        self.assertEqual(self.call("agent1", "wait_for_message", timeout_ms="0.5"), MARKER)
        self.assertGreaterEqual(time.monotonic() - started, 0.09)

    def test_a_null_or_absent_timeout_means_the_default(self):
        self.assertEqual(kit.wait_seconds(kit.DEFAULT_WAIT_MS), 5.0)
        self.call("agent2", "send_message", to="agent1", text="ready")
        for arguments in ({}, {"timeout_ms": None}):
            with self.subTest(arguments=arguments):
                self.call("agent2", "send_message", to="agent1", text="ready")
                self.assertEqual(json.loads(self.call("agent1", "wait_for_message", **arguments))["content"],
                                 "ready")


if __name__ == "__main__":
    unittest.main()
