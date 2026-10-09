"""The hub is what every agent of every arm talks to, so these pin its HTTP
API and its MCP transport against the contract the runner, the bridge and
the arms code against. They use a small arm of their own, written to a
temporary directory, so they hold whatever the built-in arms become."""

import contextlib
import http.client
import io
import json
import re
import select
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
COORDBENCH = ROOT / "experiment" / "coordbench"
sys.path.insert(0, str(COORDBENCH))

import hub as hub_module  # noqa: E402
from arm import Arm, Tool, ToolError  # noqa: E402

ARM_JSON = {"entry": "arm.py:TestArm", "name": "testarm", "description": "messages and two odd tools",
            "needs": [], "plugins": [], "mcp_servers": {}}

ARM_PY = '''
from arm import Arm, Tool, ToolError
import kit


def refuse(call):
    raise ToolError("refused on purpose")


def crash(call):
    raise RuntimeError("a bug in the arm")


class TestArm(Arm):
    name = "testarm"

    def tools(self, run, agent):
        return kit.messaging_tools() + [Tool("refuse", "Always refuses.", refuse),
                                        Tool("crash", "Always crashes.", crash)]

    def metrics(self, run):
        return {**super().metrics(run), **kit.message_metrics(run)}
'''

SPECS = {"1": "Add the first feature.", "2": "Add the second feature."}
INIT_PARAMS = {"protocolVersion": "2025-06-18", "capabilities": {},
               "clientInfo": {"name": "test", "version": "0"}}


def write_test_arm(directory):
    directory.mkdir()
    (directory / "arm.json").write_text(json.dumps(ARM_JSON), encoding="utf-8")
    (directory / "arm.py").write_text(ARM_PY, encoding="utf-8")


def rpc_message(method, params=None, request_id=1):
    message = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if request_id is not None:
        message["id"] = request_id
    return message


class Answer:
    def __init__(self, response):
        self.status = response.status
        self.headers = response.headers
        self.raw = response.read()

    @property
    def json(self):
        return json.loads(self.raw)


class HubServerCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.arm_dir = self.dir / "testarm"
        write_test_arm(self.arm_dir)
        self.hub = hub_module.Hub(log_dir=self.dir / "logs", arm_dirs=[self.dir])
        self.server = hub_module.serve_in_background(self.hub, "127.0.0.1", 0)
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        try:
            data = body if isinstance(body, (bytes, type(None))) else json.dumps(body).encode()
            all_headers = {"Content-Type": "application/json"} if data is not None else {}
            all_headers.update(headers or {})
            connection.request(method, path, body=data, headers=all_headers)
            return Answer(connection.getresponse())
        finally:
            connection.close()

    def create(self, run_id="pair1", features=(1, 2)):
        answer = self.request("POST", "/api/runs", {"arm": str(self.arm_dir), "run_id": run_id,
                                                    "features": list(features), "specs": SPECS})
        self.assertEqual(answer.status, 201, answer.raw)
        return answer.json

    def mcp(self, body, agent="agent1", run_id="pair1", headers=None):
        all_headers = {"Accept": "application/json, text/event-stream"}
        all_headers.update(headers or {})
        return self.request("POST", f"/mcp/{run_id}/{agent}", body, all_headers)

    def initialize(self, agent="agent1"):
        answer = self.mcp(rpc_message("initialize", INIT_PARAMS), agent)
        self.assertEqual(answer.status, 200, answer.raw)
        return answer

    def call_tool(self, name, arguments=None, agent="agent1", request_id=7):
        params = {"name": name, "arguments": arguments or {}}
        return self.mcp(rpc_message("tools/call", params, request_id), agent)

    def rpc(self, tool, arguments=None, agent="agent1", run_id="pair1"):
        return self.request("POST", f"/rpc/{run_id}/{agent}", {"tool": tool, "arguments": arguments or {}})


class ApiTest(HubServerCase):
    def test_health_counts_runs(self):
        self.assertEqual(self.request("GET", "/api/health").json, {"ok": True, "runs": 0})
        self.create()
        self.assertEqual(self.request("GET", "/api/health").json, {"ok": True, "runs": 1})

    def test_create_answers_agents_with_urls_and_prompts(self):
        created = self.create()
        base = f"http://127.0.0.1:{self.port}"
        self.assertEqual(created["run_id"], "pair1")
        self.assertEqual(created["arm"], "testarm")
        first, second = created["agents"]
        self.assertEqual((first["id"], first["role"], first["features"]), ("agent1", "peer", [1]))
        self.assertEqual(second["features"], [2])
        self.assertEqual(first["mcp_url"], base + "/mcp/pair1/agent1")
        self.assertEqual(first["rpc_url"], base + "/rpc/pair1/agent1")
        self.assertIn("Add the first feature.", first["prompt"])
        self.assertIn("patch.txt", first["prompt"])
        self.assertNotIn("Add the second feature.", first["prompt"])

    def test_get_and_close_a_run(self):
        self.create()
        self.assertEqual(self.rpc("send_message", {"to": "agent2", "text": "hi"}).status, 200)
        state = self.request("GET", "/api/runs/pair1").json
        self.assertEqual(state["run_id"], "pair1")
        self.assertFalse(state["closed"])
        self.assertNotIn("prompt", state["agents"][0])
        self.assertEqual(state["agents"][0]["mcp_url"], f"http://127.0.0.1:{self.port}/mcp/pair1/agent1")
        self.assertEqual(state["metrics"]["messages_sent"], 1)
        closed = self.request("POST", "/api/runs/pair1/close")
        self.assertEqual(closed.status, 200)
        self.assertEqual(closed.json["metrics"]["messages_sent"], 1)
        self.assertTrue(self.request("GET", "/api/runs/pair1").json["closed"])

    def test_events_endpoint_lists_the_run_events(self):
        self.create()
        self.rpc("send_message", {"to": "agent2", "text": "hi"})
        kinds = [event["kind"] for event in self.request("GET", "/api/runs/pair1/events").json["events"]]
        self.assertEqual(kinds, ["tool", "message"])

    def test_duplicate_run_id_is_409(self):
        self.create()
        again = self.request("POST", "/api/runs", {"arm": str(self.arm_dir), "run_id": "pair1",
                                                   "features": [1, 2], "specs": SPECS})
        self.assertEqual(again.status, 409)
        self.assertIn("error", again.json)

    def test_run_id_is_generated_when_absent(self):
        answer = self.request("POST", "/api/runs", {"arm": str(self.arm_dir), "features": [1, 2],
                                                    "specs": SPECS})
        self.assertEqual(answer.status, 201)
        self.assertRegex(answer.json["run_id"], r"^r[0-9a-f]{8}$")

    def test_bad_create_requests_are_400(self):
        missing_spec = {"arm": str(self.arm_dir), "features": [1, 3], "specs": SPECS}
        unknown_arm = {"arm": str(self.dir / "nowhere"), "features": [1], "specs": SPECS}
        bad_id = {"arm": str(self.arm_dir), "run_id": "../up", "features": [1], "specs": SPECS}
        for body in (missing_spec, unknown_arm, bad_id):
            answer = self.request("POST", "/api/runs", body)
            self.assertEqual(answer.status, 400, body)
            self.assertIn("error", answer.json)
        self.assertEqual(self.request("GET", "/api/health").json["runs"], 0)

    def test_unknown_run_and_routes_are_404(self):
        self.create()
        self.assertEqual(self.request("GET", "/api/runs/nope").status, 404)
        self.assertEqual(self.request("POST", "/api/runs/nope/close").status, 404)
        self.assertEqual(self.request("GET", "/elsewhere").status, 404)
        self.assertEqual(self.mcp(rpc_message("ping"), run_id="nope").status, 404)
        self.assertEqual(self.mcp(rpc_message("ping"), agent="agent9").status, 404)
        self.assertIn("error", self.mcp(rpc_message("ping"), agent="agent9").json)

    def test_events_are_written_under_the_log_dir(self):
        self.create()
        self.rpc("send_message", {"to": "agent2", "text": "hello"})
        path = self.dir / "logs" / "pair1" / "events.jsonl"
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([e["kind"] for e in events], ["tool", "message"])
        self.assertEqual(events[1]["to"], "agent2")


class McpTest(HubServerCase):
    def setUp(self):
        super().setUp()
        self.create()

    def test_handshake_and_a_message_between_agents(self):
        hello = self.initialize("agent1")
        session = hello.headers["Mcp-Session-Id"]
        self.assertRegex(session, r"^[0-9a-f]{32}$")
        result = hello.json["result"]
        self.assertEqual(result["protocolVersion"], "2025-06-18")
        self.assertIn("tools", result["capabilities"])
        self.assertIn("agent1", result["instructions"])
        self.assertIn("testarm", result["instructions"])
        with_session = {"Mcp-Session-Id": session}
        initialized = self.mcp(rpc_message("notifications/initialized", request_id=None),
                               headers=with_session)
        self.assertEqual(initialized.status, 202)
        self.assertEqual(initialized.raw, b"")
        listed = self.mcp(rpc_message("tools/list", request_id=2), headers=with_session).json
        names = [tool["name"] for tool in listed["result"]["tools"]]
        self.assertIn("send_message", names)
        self.assertIn("inputSchema", listed["result"]["tools"][0])
        sent = self.mcp(rpc_message("tools/call", {"name": "send_message",
                                                   "arguments": {"to": "agent2", "text": "I take parser.py"}},
                                    request_id=3), headers=with_session).json
        self.assertEqual(sent["result"]["content"][0]["text"], "sent to agent2")
        self.assertFalse(sent["result"]["isError"])
        self.initialize("agent2")
        received = self.call_tool("receive_messages", agent="agent2").json["result"]
        messages = json.loads(received["content"][0]["text"])
        self.assertEqual([(m["from"], m["content"]) for m in messages], [("agent1", "I take parser.py")])

    def test_each_initialize_gets_its_own_session(self):
        first = self.initialize().headers["Mcp-Session-Id"]
        second = self.initialize().headers["Mcp-Session-Id"]
        self.assertNotEqual(first, second)
        self.assertEqual(self.mcp(rpc_message("ping"), headers={"Mcp-Session-Id": first}).status, 200)

    def test_ping(self):
        answer = self.mcp(rpc_message("ping", request_id="p"))
        self.assertEqual(answer.json, {"jsonrpc": "2.0", "id": "p", "result": {}})
        self.assertNotIn("Mcp-Session-Id", answer.headers)

    def test_a_batch_answers_each_request(self):
        batch = [rpc_message("ping", request_id=1), rpc_message("notifications/initialized", request_id=None),
                 rpc_message("tools/list", request_id=2)]
        answers = self.mcp(batch).json
        self.assertEqual([a["id"] for a in answers], [1, 2])
        self.assertIn("tools", answers[1]["result"])

    def test_unknown_method(self):
        answer = self.mcp(rpc_message("resources/list", request_id=4))
        self.assertEqual(answer.status, 200)
        self.assertEqual(answer.json["error"]["code"], -32601)

    def test_unknown_tool(self):
        self.assertEqual(self.call_tool("no_such_tool").json["error"]["code"], -32602)

    def test_a_refusing_tool_is_an_error_result(self):
        result = self.call_tool("refuse").json["result"]
        self.assertTrue(result["isError"])
        self.assertEqual(result["content"][0]["text"], "refused on purpose")

    def test_a_crashing_tool_fails_that_call_only_without_traceback(self):
        # A bug in an arm is the arm's, not the agent's: the call comes back
        # as a failed result naming the tool, the session goes on, and the
        # traceback stays in the hub's log.
        with contextlib.redirect_stderr(io.StringIO()) as log:
            answer = self.call_tool("crash", request_id=9)
        self.assertEqual(answer.status, 200)
        self.assertEqual(answer.json["id"], 9)
        self.assertTrue(answer.json["result"]["isError"])
        self.assertIn("crash tool failed", answer.json["result"]["content"][0]["text"])
        self.assertNotIn(b"Traceback", answer.raw)
        self.assertNotIn(b"a bug in the arm", answer.raw)
        self.assertIn("a bug in the arm", log.getvalue())
        self.assertEqual(self.call_tool("peek_messages", request_id=10).status, 200)

    def test_unknown_session_is_404(self):
        self.initialize()
        answer = self.mcp(rpc_message("ping"), headers={"Mcp-Session-Id": "0" * 32})
        self.assertEqual(answer.status, 404)
        other_agents = self.initialize("agent2").headers["Mcp-Session-Id"]
        self.assertEqual(self.mcp(rpc_message("ping"), headers={"Mcp-Session-Id": other_agents}).status, 404)

    def test_get_and_delete_are_405(self):
        for method in ("GET", "DELETE"):
            answer = self.request(method, "/mcp/pair1/agent1", headers={"Accept": "text/event-stream"})
            self.assertEqual(answer.status, 405, method)
            self.assertEqual(answer.headers["Allow"], "POST")

    def test_origin_must_be_local(self):
        for origin in ("http://evil.example", "null", "https://localhost.evil.example"):
            answer = self.mcp(rpc_message("ping"), headers={"Origin": origin})
            self.assertEqual(answer.status, 403, origin)
        hostile = {"Origin": "http://evil.example"}
        self.assertEqual(self.request("GET", "/api/health", headers=hostile).status, 403)
        for origin in ("http://localhost:3000", "https://127.0.0.1", "http://host.docker.internal:8765"):
            self.assertEqual(self.mcp(rpc_message("ping"), headers={"Origin": origin}).status, 200, origin)

    def test_accept_must_take_json(self):
        self.assertEqual(self.mcp(rpc_message("ping"), headers={"Accept": "text/html"}).status, 406)
        self.assertEqual(self.mcp(rpc_message("ping"), headers={"Accept": "*/*"}).status, 200)
        self.assertEqual(self.mcp(rpc_message("ping"), headers={"Accept": "application/json"}).status, 200)

    def test_a_body_over_a_megabyte_is_413(self):
        # Only the headers go out: the hub refuses on Content-Length alone
        # and closes, and an unsent body keeps that close clean.
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        try:
            connection.putrequest("POST", "/mcp/pair1/agent1")
            connection.putheader("Content-Type", "application/json")
            connection.putheader("Content-Length", str(hub_module.MAX_BODY + 1))
            connection.endheaders()
            answer = Answer(connection.getresponse())
        finally:
            connection.close()
        self.assertEqual(answer.status, 413)
        self.assertEqual(answer.headers["Connection"], "close")

    def test_one_connection_serves_requests_after_a_refusal(self):
        # MCP clients keep their connection open, so a refused request must
        # leave nothing of its body behind to be read as the next request.
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        accept = {"Accept": "application/json", "Content-Type": "application/json"}
        try:
            for path, status in (("/mcp/nope/agent1", 404), ("/mcp/pair1/agent1", 200)):
                connection.request("POST", path, body=json.dumps(rpc_message("ping")), headers=accept)
                answer = Answer(connection.getresponse())
                self.assertEqual(answer.status, status, path)
        finally:
            connection.close()

    def test_a_body_that_is_not_json_is_a_parse_error(self):
        answer = self.mcp(b"{not json")
        self.assertEqual(answer.json["error"]["code"], -32700)

    def test_wait_for_message_blocks_only_its_caller(self):
        self.initialize("agent2")
        outcome = {}

        def wait():
            started = time.monotonic()
            answer = self.call_tool("wait_for_message", {"timeout_ms": 20000}, agent="agent2")
            outcome["elapsed"] = time.monotonic() - started
            outcome["answer"] = answer.json

        waiter = threading.Thread(target=wait)
        waiter.start()
        time.sleep(0.3)
        self.assertTrue(waiter.is_alive(), "wait_for_message returned before any message")
        started = time.monotonic()
        sent = self.rpc("send_message", {"to": "agent2", "text": "done with parser.py"})
        self.assertEqual(sent.status, 200)
        self.assertLess(time.monotonic() - started, 2.0)
        waiter.join(timeout=10)
        self.assertFalse(waiter.is_alive())
        self.assertLess(outcome["elapsed"], 5.0)
        message = json.loads(outcome["answer"]["result"]["content"][0]["text"])
        self.assertEqual((message["from"], message["content"]), ("agent1", "done with parser.py"))


class RpcTest(HubServerCase):
    def setUp(self):
        super().setUp()
        self.create()

    def test_get_describes_the_agent_and_its_tools(self):
        answer = self.request("GET", "/rpc/pair1/agent1")
        self.assertEqual(answer.status, 200)
        described = answer.json
        self.assertEqual((described["agent"], described["role"]), ("agent1", "peer"))
        self.assertIn("Add the first feature.", described["prompt"])
        tools = {tool["name"]: tool for tool in described["tools"]}
        send = tools["send_message"]
        self.assertEqual(send["alias"], "coop-send")
        self.assertEqual(send["argv"], ["to", "text..."])
        self.assertEqual(send["inputSchema"]["required"], ["to", "text"])
        self.assertTrue(send["description"])
        self.assertEqual(tools["refuse"]["alias"], "")

    def test_post_calls_a_tool(self):
        answer = self.rpc("send_message", {"to": "agent2", "text": "hi"})
        self.assertEqual(answer.json, {"text": "sent to agent2", "isError": False})
        self.assertEqual(self.rpc("peek_messages", agent="agent2").json["text"], "1")

    def test_a_tool_error_is_is_error(self):
        self.assertEqual(self.rpc("refuse").json, {"text": "refused on purpose", "isError": True, "exitCode": 1})
        missing = self.rpc("send_message", {"text": "to nobody"}).json
        self.assertTrue(missing["isError"])
        self.assertIn("to is required", missing["text"])

    def test_unknown_tool_is_400(self):
        answer = self.rpc("no_such_tool")
        self.assertEqual(answer.status, 400)
        self.assertIn("error", answer.json)

    def test_unknown_run_or_agent_is_404(self):
        self.assertEqual(self.rpc("list_agents", agent="agent9").status, 404)
        self.assertEqual(self.rpc("list_agents", run_id="nope").status, 404)
        self.assertEqual(self.request("GET", "/rpc/pair1/agent9").status, 404)

    def test_a_crashing_tool_is_a_failed_call_without_traceback(self):
        with contextlib.redirect_stderr(io.StringIO()):
            answer = self.rpc("crash")
        self.assertEqual(answer.status, 200)
        self.assertTrue(answer.json["isError"])
        self.assertNotIn(b"Traceback", answer.raw)


class InProcessTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.arm_dir = Path(self.tmp.name) / "testarm"
        write_test_arm(self.arm_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_get_close_without_a_server(self):
        hub = hub_module.Hub(public_url="http://host.docker.internal:9000/", arm_dirs=[self.arm_dir])
        created = hub.create_run(str(self.arm_dir), [1, 2], SPECS, {"base_ref": "abc"}, "x1")
        self.assertEqual(created["agents"][0]["mcp_url"], "http://host.docker.internal:9000/mcp/x1/agent1")
        self.assertEqual(hub.hosted("x1").run.options, {"base_ref": "abc"})
        with self.assertRaises(hub_module.HubError) as refused:
            hub.create_run(str(self.arm_dir), [1], SPECS, run_id="x1")
        self.assertEqual(refused.exception.status, 409)
        self.assertFalse(hub.get_run("x1")["closed"])
        self.assertIn("events", hub.close_run("x1"))
        self.assertTrue(hub.get_run("x1")["closed"])
        self.assertEqual(hub.events("x1"), [])

    def test_a_failed_create_frees_its_run_id(self):
        class BrokenArm(Arm):
            def setup(self, run):
                raise RuntimeError("setup failed")

        hub = hub_module.Hub(arm_dirs=[self.arm_dir])
        with self.assertRaises(RuntimeError):
            hub.create_run(BrokenArm(), [1], {"1": "spec"}, run_id="y1")
        self.assertEqual(hub.run_count(), 0)
        with self.assertRaises(hub_module.HubError) as unknown:
            hub.get_run("y1")
        self.assertEqual(unknown.exception.status, 404)
        created = hub.create_run(str(self.arm_dir), [1], {"1": "spec"}, run_id="y1")
        self.assertEqual(created["run_id"], "y1")


class GuardTest(unittest.TestCase):
    """Loading an arm runs its code in the hub, and agents can reach the
    hub, so only allowed arms load; the management API can want a token;
    a run must have what its arm needs; teardown runs once."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.arm_dir = Path(self.tmp.name) / "testarm"
        write_test_arm(self.arm_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def test_an_arm_outside_the_allowed_directories_is_refused(self):
        hub = hub_module.Hub()
        with self.assertRaises(hub_module.HubError) as refused:
            hub.create_run(str(self.arm_dir), [1], {"1": "spec"})
        self.assertEqual(refused.exception.status, 403)
        self.assertEqual(hub.create_run("coop", [1, 2], SPECS)["arm"], "coop")

    def test_a_run_without_what_its_arm_needs_is_refused(self):
        hub = hub_module.Hub()
        with self.assertRaises(hub_module.HubError) as refused:
            hub.create_run("coop-git", [1, 2], SPECS)
        self.assertEqual(refused.exception.status, 400)
        self.assertIn("git_remote", refused.exception.message)
        created = hub.create_run("coop-git", [1, 2], SPECS, {"git_remote": "git://g/r.git"})
        self.assertEqual(len(created["agents"]), 2)

    def test_teardown_runs_once_and_specs_reach_the_run(self):
        calls = []

        class Holding(Arm):
            def setup(self, run):
                calls.append(("setup", dict(run.specs)))

            def teardown(self, run):
                calls.append(("teardown", run.id))

        hub = hub_module.Hub()
        hub.create_run(Holding(), [1], {"1": "spec"}, run_id="t1")
        hub.close_run("t1")
        hub.close_run("t1")
        self.assertEqual(calls, [("setup", {1: "spec"}), ("teardown", "t1")])

    def test_the_management_api_wants_the_token_when_one_is_set(self):
        hub = hub_module.Hub(admin_token="s3cret")
        server = hub_module.serve_in_background(hub, "127.0.0.1", 0)
        try:
            def post(headers):
                connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=10)
                body = json.dumps({"arm": "coop", "features": [1, 2], "specs": SPECS})
                connection.request("POST", "/api/runs", body, {"Content-Type": "application/json", **headers})
                status = connection.getresponse().status
                connection.close()
                return status
            self.assertEqual(post({}), 401)
            self.assertEqual(post({"Authorization": "Bearer wrong"}), 401)
            self.assertEqual(post({"Authorization": "Bearer s3cret"}), 201)
        finally:
            server.shutdown()
            server.server_close()

    def test_a_refusal_carries_its_exit_code_and_tools_their_flags(self):
        class Coded(Arm):
            def tools(self, run, agent):
                def lose(call):
                    raise ToolError("someone else holds it", exit_code=2)
                return [Tool("claim", "Claim it.", lose, flags={"--force": "force"})]

        hub = hub_module.Hub()
        hub.create_run(Coded(), [1], {"1": "spec"}, run_id="c1")
        run = hub.hosted("c1").run
        self.assertEqual(hub.call(run, "agent1", "claim", {}),
                         {"text": "someone else holds it", "isError": True, "exitCode": 2})
        self.assertEqual(hub.describe_tools(run, "agent1")[0]["flags"], {"--force": "force"})


class CommandLineTest(unittest.TestCase):
    def test_it_prints_its_url_then_serves(self):
        with tempfile.TemporaryDirectory() as logs:
            process = subprocess.Popen(
                [sys.executable, str(COORDBENCH / "hub.py"), "--host", "127.0.0.1", "--port", "0",
                 "--log-dir", logs], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                ready, _, _ = select.select([process.stdout], [], [], 20)
                self.assertTrue(ready, "the hub printed nothing")
                url = process.stdout.readline().strip()
                self.assertRegex(url, r"^http://127\.0\.0\.1:\d+$")
                self.assertNotEqual(urlsplit(url).port, 0)
                connection = http.client.HTTPConnection("127.0.0.1", urlsplit(url).port, timeout=10)
                connection.request("GET", "/api/health")
                self.assertEqual(json.loads(connection.getresponse().read()), {"ok": True, "runs": 0})
                connection.close()
            finally:
                process.terminate()
                process.communicate(timeout=10)


if __name__ == "__main__":
    unittest.main()
