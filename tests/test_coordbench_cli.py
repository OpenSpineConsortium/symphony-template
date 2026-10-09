"""The shell surface and the stdio bridge are what an agent without an HTTP
MCP client sees of the hub, so these pin both against a small fake of the
hub's /rpc and /mcp endpoints served on an ephemeral port: the commands'
argument mapping and exit codes, the wrappers install writes, and the
bridge's session handling, streaming, and errors."""

import io
import json
import os
import queue
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
COORDBENCH = ROOT / "experiment" / "coordbench"
sys.path.insert(0, str(COORDBENCH))

import cli  # noqa: E402

TEXT = {"type": "string"}
TOOLS = [
    {"name": "send_message", "description": "Send a message to one peer, by agent id.",
     "inputSchema": {"type": "object", "properties": {"to": TEXT, "text": TEXT}},
     "alias": "coop-send", "argv": ["to", "text..."]},
    {"name": "broadcast", "description": "Send a message to every other agent.",
     "inputSchema": {"type": "object", "properties": {"text": TEXT}},
     "alias": "coop-broadcast", "argv": ["text..."]},
    {"name": "receive_messages", "description": "Drain your inbox.",
     "inputSchema": {"type": "object", "properties": {}}, "alias": "coop-recv", "argv": []},
    {"name": "claim_task", "description": "Claim a task by number.",
     "inputSchema": {"type": "object", "properties": {"task_id": {"type": "integer"}}},
     "alias": "", "argv": ["task_id"]},
    {"name": "wait_for_message", "description": "Block until a message arrives.\nPrefer it to polling.",
     "inputSchema": {"type": "object", "properties": {"timeout_ms": {"type": "integer"}}},
     "alias": "", "argv": []},
    {"name": "refuse", "description": "Always refuses.",
     "inputSchema": {"type": "object", "properties": {}}, "alias": "", "argv": []},
]
PROMPT = "You are agent1. Implement feature 1."
RPC_PATH = "/rpc/run1/agent1"
MCP_PATH = "/mcp/run1/agent1"
SESSION_ID = "session-abc"


class FakeHub(BaseHTTPRequestHandler):
    """Just enough of hub.py's HTTP API to exercise the clients: /rpc
    echoes each call back as JSON, and /mcp answers by tool name."""

    def log_message(self, *args):
        pass

    def send_json(self, status, payload, headers=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        return self.rfile.read(int(self.headers.get("Content-Length") or 0))

    def do_GET(self):
        if self.path != RPC_PATH:
            return self.send_json(404, {"error": "no run or agent at this path"})
        self.send_json(200, {"agent": "agent1", "role": "peer", "tools": TOOLS, "prompt": PROMPT})

    def do_POST(self):
        if self.path == RPC_PATH:
            return self.answer_rpc(json.loads(self.body()))
        if self.path == MCP_PATH:
            return self.answer_mcp(json.loads(self.body()))
        self.send_json(404, {"error": "no run or agent at this path"})

    def answer_rpc(self, request):
        self.server.calls.append(request)
        name, arguments = request["tool"], request.get("arguments", {})
        if name not in {t["name"] for t in TOOLS}:
            return self.send_json(400, {"error": f"unknown tool {name!r}"})
        if name == "refuse":
            return self.send_json(200, {"text": "not allowed", "isError": True})
        echo = json.dumps({"tool": name, "arguments": arguments}, sort_keys=True)
        self.send_json(200, {"text": echo, "isError": False})

    def answer_mcp(self, message):
        self.server.mcp_requests.append((self.headers, message))
        if "method" not in message or "id" not in message:
            self.send_response(202)
            self.end_headers()
            return
        method, request_id = message["method"], message["id"]
        if method == "initialize":
            result = {"protocolVersion": message["params"]["protocolVersion"],
                      "capabilities": {"tools": {}}, "serverInfo": {"name": "fake"}}
            return self.send_json(200, reply(request_id, result), {"Mcp-Session-Id": SESSION_ID})
        if method == "ping":
            return self.send_json(200, reply(request_id, {}))
        tool = message.get("params", {}).get("name")
        if tool == "streamed":
            return self.stream(request_id)
        if tool == "explode":
            return self.send_json(500, {"error": "boom"})
        self.send_json(200, reply(request_id, self.result_of(tool)))

    def result_of(self, tool):
        if tool == "slow":
            released = self.server.release.wait(timeout=10)
            return text_result("released" if released else "timed out")
        if tool == "release":
            self.server.release.set()
        return text_result(f"ran {tool}")

    def stream(self, request_id):
        """An SSE answer: a comment, a notification, an event that is not
        JSON, then the response split over two data lines."""
        progress = {"jsonrpc": "2.0", "method": "notifications/progress",
                    "params": {"progressToken": 1, "progress": 0.5}}
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        chunks = [": keep-alive\n\n",
                  f"event: message\ndata: {json.dumps(progress)}\n\n",
                  "data: not json at all\n\n",
                  f'data: {{"jsonrpc": "2.0", "id": {json.dumps(request_id)},\n'
                  f'data: "result": {json.dumps(text_result("streamed answer"))}}}\n\n']
        for chunk in chunks:
            self.wfile.write(chunk.encode("utf-8"))
            self.wfile.flush()


def reply(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def text_result(text):
    return {"content": [{"type": "text", "text": text}], "isError": False}


def closed_port_url(path):
    """A URL on 127.0.0.1 where nothing listens: bind a port, then free it."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    return f"http://127.0.0.1:{port}{path}"


class HubTestCase(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeHub)
        self.server.calls, self.server.mcp_requests = [], []
        self.server.release = threading.Event()
        threading.Thread(target=self.server.serve_forever, args=(0.05,), daemon=True).start()
        base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.rpc_url, self.mcp_url = base + RPC_PATH, base + MCP_PATH
        environment = mock.patch.dict(os.environ)
        environment.start()
        os.environ.pop("COORD_RPC_URL", None)
        self.addCleanup(environment.stop)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()


class TerminalInput(io.StringIO):
    def isatty(self):
        return True


def run_cli(*argv, stdin="", tty=False):
    out, err = io.StringIO(), io.StringIO()
    source = TerminalInput(stdin) if tty else io.StringIO(stdin)
    with mock.patch.object(sys, "stdin", source), redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CommandTest(HubTestCase):
    def call_arguments(self, stdout):
        return json.loads(stdout)["arguments"]

    def test_call_with_a_json_object(self):
        code, out, err = run_cli("--url", self.rpc_url, "call", "send_message",
                                 '{"to": "agent2", "text": "hi there"}')
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out), {"tool": "send_message",
                                           "arguments": {"to": "agent2", "text": "hi there"}})

    def test_call_with_key_value_words_typed_by_the_schema(self):
        code, out, _ = run_cli("--url", self.rpc_url, "call", "send_message", "to=agent2", "text=a=b")
        self.assertEqual(code, 0)
        self.assertEqual(self.call_arguments(out), {"to": "agent2", "text": "a=b"})
        code, out, _ = run_cli("--url", self.rpc_url, "call", "wait_for_message", "timeout_ms=1500")
        self.assertEqual(self.call_arguments(out), {"timeout_ms": 1500})

    def test_call_takes_the_url_from_the_environment(self):
        os.environ["COORD_RPC_URL"] = self.rpc_url
        code, out, _ = run_cli("call", "receive_messages")
        self.assertEqual((code, self.call_arguments(out)), (0, {}))

    def test_tools_lists_each_tool_with_its_command_and_description(self):
        code, out, _ = run_cli("--url", self.rpc_url, "tools")
        self.assertEqual(code, 0)
        self.assertIn("send_message  (shell: coop-send <to> <text...>)\n"
                      "    Send a message to one peer, by agent id.", out)
        self.assertIn("claim_task  (shell: coord-claim_task <task_id>)", out)
        self.assertIn("wait_for_message  (shell: coord-wait_for_message [key=value ...])\n"
                      "    Block until a message arrives.\n    Prefer it to polling.", out)
        self.assertIn("receive_messages  (shell: coop-recv)", out)

    def test_prompt_prints_the_agents_prompt(self):
        self.assertEqual(run_cli("--url", self.rpc_url, "prompt"), (0, PROMPT + "\n", ""))

    def test_alias_run_maps_words_onto_argv_and_joins_the_rest(self):
        code, out, _ = run_cli("--url", self.rpc_url, "alias-run", "send_message",
                               "agent2", "hello", "there", "-n")
        self.assertEqual(code, 0)
        self.assertEqual(self.call_arguments(out), {"to": "agent2", "text": "hello there -n"})
        code, out, _ = run_cli("--url", self.rpc_url, "alias-run", "claim_task", "7")
        self.assertEqual(self.call_arguments(out), {"task_id": 7})

    def test_alias_run_reads_missing_text_from_stdin(self):
        code, out, _ = run_cli("--url", self.rpc_url, "alias-run", "send_message", "agent2",
                               stdin="from stdin\n")
        self.assertEqual(code, 0)
        self.assertEqual(self.call_arguments(out), {"to": "agent2", "text": "from stdin\n"})

    def test_alias_run_leaves_a_terminal_alone(self):
        code, out, _ = run_cli("--url", self.rpc_url, "alias-run", "send_message", "agent2",
                               stdin="typed", tty=True)
        self.assertEqual(self.call_arguments(out), {"to": "agent2"})

    def test_alias_run_reads_no_stdin_while_an_earlier_word_is_missing(self):
        code, out, _ = run_cli("--url", self.rpc_url, "alias-run", "send_message", stdin="text")
        self.assertEqual(self.call_arguments(out), {})

    def test_alias_run_refuses_extra_words(self):
        code, out, err = run_cli("--url", self.rpc_url, "alias-run", "claim_task", "7", "8")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("too many words; usage: coord-claim_task <task_id>", err)
        self.assertEqual(self.server.calls, [])

    def test_a_tool_error_goes_to_stderr_with_exit_1(self):
        self.assertEqual(run_cli("--url", self.rpc_url, "call", "refuse"), (1, "", "not allowed\n"))

    def test_an_unreachable_hub_is_one_line_with_exit_2(self):
        code, out, err = run_cli("--url", closed_port_url(RPC_PATH), "call", "receive_messages")
        self.assertEqual((code, out), (2, ""))
        self.assertTrue(err.startswith("coordbench: cannot reach the coordbench hub at "), err)
        self.assertEqual(err.count("\n"), 1)

    def test_an_http_error_names_the_hubs_reason_with_exit_2(self):
        code, _, err = run_cli("--url", self.rpc_url, "call", "no_such_tool")
        self.assertEqual(code, 2)
        self.assertIn("HTTP 400: unknown tool 'no_such_tool'", err)
        code, _, err = run_cli("--url", self.rpc_url.replace("agent1", "agent9"), "prompt")
        self.assertEqual(code, 2)
        self.assertIn("HTTP 404: no run or agent at this path", err)

    def test_no_url_at_all_is_exit_2(self):
        code, _, err = run_cli("tools")
        self.assertEqual(code, 2)
        self.assertIn("COORD_RPC_URL", err)


class InstallTest(HubTestCase):
    def setUp(self):
        super().setUp()
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.bin_dir = Path(scratch.name) / "bin"

    def run_command(self, name, *words, stdin="", rpc_url=None):
        environment = {k: v for k, v in os.environ.items() if k != "COORD_RPC_URL"}
        if rpc_url:
            environment["COORD_RPC_URL"] = rpc_url
        return subprocess.run([str(self.bin_dir / name), *words], input=stdin, env=environment,
                              capture_output=True, text=True, timeout=30)

    def test_install_writes_one_wrapper_per_alias_and_per_tool(self):
        code, _, _ = run_cli("install", str(self.bin_dir), "--url", self.rpc_url)
        self.assertEqual(code, 0)
        names = {p.name for p in self.bin_dir.iterdir()}
        expected = {"coop-send", "coop-broadcast", "coop-recv"} | {f"coord-{t['name']}" for t in TOOLS}
        self.assertEqual(names, expected)
        for path in self.bin_dir.iterdir():
            self.assertTrue(os.access(path, os.X_OK), path)
        script = (self.bin_dir / "coop-send").read_text().splitlines()
        self.assertEqual(script[0], "#!/bin/sh")
        self.assertEqual(script[1], f"export COORD_RPC_URL={self.rpc_url}")
        self.assertTrue(script[2].endswith(f'{COORDBENCH / "cli.py"} alias-run send_message "$@"'), script)

    def test_wrappers_with_a_baked_url_reach_the_hub(self):
        run_cli("install", str(self.bin_dir), "--url", self.rpc_url)
        sent = self.run_command("coop-send", "agent2", "hello", "from", "a", "wrapper")
        self.assertEqual(sent.returncode, 0, sent.stderr)
        self.assertEqual(json.loads(sent.stdout)["arguments"],
                         {"to": "agent2", "text": "hello from a wrapper"})
        piped = self.run_command("coop-broadcast", stdin="piped text\n")
        self.assertEqual(json.loads(piped.stdout)["arguments"], {"text": "piped text\n"})
        refused = self.run_command("coord-refuse")
        self.assertEqual((refused.returncode, refused.stdout, refused.stderr), (1, "", "not allowed\n"))

    def test_wrappers_without_a_url_use_the_environment(self):
        os.environ["COORD_RPC_URL"] = self.rpc_url
        run_cli("install", str(self.bin_dir))
        self.assertNotIn("export", (self.bin_dir / "coop-recv").read_text())
        received = self.run_command("coop-recv", rpc_url=self.rpc_url)
        self.assertEqual(received.returncode, 0, received.stderr)
        self.assertEqual(json.loads(received.stdout)["tool"], "receive_messages")
        lost = self.run_command("coop-recv", rpc_url=closed_port_url(RPC_PATH))
        self.assertEqual(lost.returncode, 2)
        self.assertIn("cannot reach", lost.stderr)


class BridgeProcess:
    """bridge.py as an MCP client would run it, with its stdout read on a
    thread so a test can wait for a line without blocking forever."""

    def __init__(self, url):
        environment = dict(os.environ, COORD_MCP_URL=url)
        self.process = subprocess.Popen([sys.executable, str(COORDBENCH / "bridge.py")],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, env=environment, text=True)
        self.lines = queue.Queue()
        self.pumping = threading.Thread(target=self.pump, daemon=True)
        self.pumping.start()

    def pump(self):
        for line in self.process.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def send(self, message):
        line = message if isinstance(message, str) else json.dumps(message)
        self.process.stdin.write(line + "\n")
        self.process.stdin.flush()

    def receive(self, timeout=15):
        line = self.lines.get(timeout=timeout)
        if line is None:
            raise AssertionError("the bridge ended before answering")
        return json.loads(line)

    def stop(self):
        """Make sure the process is gone and its pipes closed, whatever
        state a test left it in."""
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=15)
        self.pumping.join(timeout=15)
        self.process.stdin.close()
        self.process.stdout.close()

    def finish(self):
        """Close stdin and return what the bridge still wrote before it ended."""
        self.process.stdin.close()
        self.process.wait(timeout=15)
        rest = []
        while (line := self.lines.get(timeout=15)) is not None:
            rest.append(line)
        return rest


def request(request_id, method, params=None):
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}


def tool_call(request_id, name):
    return request(request_id, "tools/call", {"name": name, "arguments": {}})


class BridgeTest(HubTestCase):
    def start_bridge(self, url=None):
        bridge = BridgeProcess(url or self.mcp_url)
        self.addCleanup(bridge.stop)
        return bridge

    def initialize(self, bridge):
        bridge.send(request(1, "initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                              "clientInfo": {"name": "test", "version": "0"}}))
        return bridge.receive()

    def test_initialize_teaches_the_session_id_and_version(self):
        bridge = self.start_bridge()
        answer = self.initialize(bridge)
        self.assertEqual(answer["result"]["protocolVersion"], "2025-03-26")
        bridge.send(request(2, "ping"))
        self.assertEqual(bridge.receive()["id"], 2)
        (first_headers, _), (second_headers, _) = self.server.mcp_requests
        self.assertNotIn("Mcp-Session-Id", first_headers)
        self.assertEqual(second_headers["Mcp-Session-Id"], SESSION_ID)
        self.assertEqual(second_headers["MCP-Protocol-Version"], "2025-03-26")
        self.assertEqual(second_headers["Content-Type"], "application/json")
        self.assertEqual(second_headers["Accept"], "application/json, text/event-stream")
        self.assertEqual(bridge.finish(), [])
        self.assertEqual(bridge.process.returncode, 0)

    def test_a_notification_writes_nothing(self):
        bridge = self.start_bridge()
        self.initialize(bridge)
        bridge.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        bridge.send(request(3, "ping"))
        self.assertEqual(bridge.receive(), reply(3, {}))
        self.assertEqual(self.server.mcp_requests[1][1]["method"], "notifications/initialized")
        self.assertEqual(bridge.finish(), [])

    def test_an_event_stream_answer_is_forwarded_message_by_message(self):
        bridge = self.start_bridge()
        self.initialize(bridge)
        bridge.send(tool_call(4, "streamed"))
        self.assertEqual(bridge.receive()["method"], "notifications/progress")
        self.assertEqual(bridge.receive(), reply(4, text_result("streamed answer")))
        self.assertEqual(bridge.finish(), [])

    def test_a_slow_call_does_not_hold_up_the_next(self):
        bridge = self.start_bridge()
        self.initialize(bridge)
        bridge.send(tool_call(5, "slow"))
        bridge.send(tool_call(6, "release"))
        answers = {a["id"]: a["result"]["content"][0]["text"] for a in (bridge.receive(), bridge.receive())}
        self.assertEqual(answers, {5: "released", 6: "ran release"})

    def test_a_line_that_is_not_json_is_a_parse_error(self):
        bridge = self.start_bridge()
        bridge.send("this is not json")
        answer = bridge.receive()
        self.assertEqual((answer["id"], answer["error"]["code"]), (None, -32700))
        self.assertEqual(self.server.mcp_requests, [])

    def test_an_http_error_is_an_internal_error_for_that_request(self):
        bridge = self.start_bridge()
        self.initialize(bridge)
        bridge.send(tool_call(7, "explode"))
        answer = bridge.receive()
        self.assertEqual((answer["id"], answer["error"]["code"]), (7, -32603))
        self.assertIn("HTTP 500", answer["error"]["message"])

    def test_an_unreachable_hub_fails_requests_and_ignores_notifications(self):
        bridge = self.start_bridge(closed_port_url(MCP_PATH))
        bridge.send(request(8, "tools/list"))
        answer = bridge.receive()
        self.assertEqual((answer["id"], answer["error"]["code"]), (8, -32603))
        self.assertIn("cannot reach the coordbench hub", answer["error"]["message"])
        bridge.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        bridge.send(request(9, "ping"))
        self.assertEqual(bridge.receive()["id"], 9)
        self.assertEqual(bridge.finish(), [])


if __name__ == "__main__":
    unittest.main()
