"""The bridge is a Streamable HTTP client on behalf of a stdio client that
has no session of its own, so these pin what the transport asks of such
a client when the hub forgets the session: a 404 to a request sent with
Mcp-Session-Id starts a new session (initialize again, then
notifications/initialized, neither shown to the stdio client) and the
request is sent once more; and what the client hears when the hub
refuses a message it cannot read (400 with an id-less JSON-RPC error):
the hub's own error under each id it sent. The fake hub here does one
thing the real hub's tests cannot make it do on cue: forget its
session."""

import json
import queue
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COORDBENCH = ROOT / "experiment" / "coordbench"
sys.path.insert(0, str(COORDBENCH))

import bridge as bridge_module  # noqa: E402

MCP_PATH = "/mcp/run1/agent1"
INIT_PARAMS = {"protocolVersion": "2025-06-18", "capabilities": {},
               "clientInfo": {"name": "stdio-client", "version": "0"}}


def reply(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def text_result(text):
    return {"content": [{"type": "text", "text": text}], "isError": False}


def request(request_id, method, params=None):
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}


def tool_call(request_id, name):
    return request(request_id, "tools/call", {"name": name, "arguments": {}})


def unreadable(message):
    """Whether the hub could not answer the message under an id: a batch
    any of whose requests has an id that is null or a boolean, or one
    such request on its own (MCP allows no null id, and bool is no int)."""
    members = message if isinstance(message, list) else [message]
    return any(isinstance(m, dict) and "method" in m and "id" in m
               and (m["id"] is None or isinstance(m["id"], bool)) for m in members)


class ForgetfulHub(BaseHTTPRequestHandler):
    """Just enough of hub.py's /mcp: a session per initialize, 404 for a
    request carrying a session it does not know (the hub's own words),
    400 with an id-less JSON-RPC error for a request it cannot answer
    under an id, 400 with a plain body when told to refuse plainly, and
    a counter of tool calls on which it forgets its session first."""

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

    def do_POST(self):
        message = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
        self.server.seen.append((self.headers.get("Mcp-Session-Id"), message))
        self.server.authorizations.append(self.headers.get("Authorization"))
        if self.path != MCP_PATH:
            return self.send_json(404, {"error": "no run or agent at this path"})
        if self.server.refuses_plainly and message.get("method") == "tools/call":
            return self.send_json(400, {"error": "the body is not a request"})
        if unreadable(message):
            # As the real hub: a message it cannot answer under an id is
            # 400 with a JSON-RPC error that names no id.
            return self.send_json(400, {"jsonrpc": "2.0", "error": {
                "code": -32600, "message": "the id must be a string or an integer"}})
        method = message.get("method")
        if method == "initialize":
            return self.open_session(message)
        if method == "tools/call" and self.server.forget_calls > 0:
            self.server.forget_calls -= 1
            self.server.session = None
        session = self.headers.get("Mcp-Session-Id")
        # As the real hub: a request without a session passes, one with a
        # session the hub does not know is refused.
        if session is not None and session != self.server.session:
            return self.send_json(404, {"error": "unknown Mcp-Session-Id; send initialize again without one"})
        if "id" not in message:
            self.send_response(202)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if method == "ping":
            return self.send_json(200, reply(message["id"], {}))
        self.send_json(200, reply(message["id"], text_result(f"ran {message['params']['name']}")))

    def open_session(self, message):
        self.server.sessions += 1
        self.server.session = f"session-{self.server.sessions}"
        result = {"protocolVersion": message["params"]["protocolVersion"],
                  "capabilities": {"tools": {}}, "serverInfo": {"name": "fake"}}
        self.send_json(200, reply(message["id"], result), {"Mcp-Session-Id": self.server.session})


class QueuedOutput:
    """The bridge's stdout, one written line per queue entry, so a test
    waits for an answer the way a client reading a pipe would."""

    def __init__(self):
        self.lines = queue.Queue()

    def write(self, text):
        self.lines.put(text)

    def flush(self):
        pass


class ReinitializeTest(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ForgetfulHub)
        self.server.seen, self.server.sessions, self.server.session = [], 0, None
        self.server.authorizations = []
        self.server.forget_calls = 0
        self.server.refuses_plainly = False
        threading.Thread(target=self.server.serve_forever, args=(0.05,), daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}{MCP_PATH}"
        self.out = QueuedOutput()
        self.bridge = bridge_module.Bridge(self.url, out=self.out)

    def tearDown(self):
        self.bridge.serve(())
        self.server.shutdown()
        self.server.server_close()

    def send(self, message):
        """One line from the stdio client; requests are answered on a
        thread, so a test receives each answer before it sends the next
        when the order of what the hub sees matters."""
        self.bridge.take(json.dumps(message) + "\n")

    def receive(self, timeout=15):
        return json.loads(self.out.lines.get(timeout=timeout))

    def methods_seen(self):
        """Every method the hub saw, a batch's members one by one."""
        return [m.get("method") for _, message in self.server.seen
                for m in (message if isinstance(message, list) else [message])]

    def test_a_forgotten_session_is_reopened_and_the_request_retried(self):
        self.server.forget_calls = 1
        self.send(request(1, "initialize", INIT_PARAMS))
        self.assertEqual(self.receive()["id"], 1)
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.send(tool_call(2, "send_message"))
        self.assertEqual(self.receive(), reply(2, text_result("ran send_message")))
        self.send(request(3, "ping"))
        self.assertEqual(self.receive(), reply(3, {}))
        self.assertEqual(self.methods_seen(),
                         ["initialize", "notifications/initialized", "tools/call",
                          "initialize", "notifications/initialized", "tools/call", "ping"])
        sessions = [session for session, _ in self.server.seen]
        self.assertEqual(sessions, [None, "session-1", "session-1", None, "session-2", "session-2",
                                    "session-2"])
        repeated = self.server.seen[3][1]
        self.assertEqual(repeated["params"], INIT_PARAMS)
        self.assertNotEqual(repeated["id"], 1)
        self.assertTrue(self.out.lines.empty(), "the repeated handshake must not reach the client")

    def test_a_second_refusal_is_the_hubs_answer(self):
        # One retry: a hub that forgets the new session as well has said
        # what it has to say, and the client hears the 404.
        self.server.forget_calls = 2
        self.send(request(1, "initialize", INIT_PARAMS))
        self.receive()
        self.send(tool_call(2, "send_message"))
        answer = self.receive()
        self.assertEqual((answer["id"], answer["error"]["code"]), (2, -32603))
        self.assertIn("HTTP 404", answer["error"]["message"])
        self.assertEqual(self.methods_seen().count("initialize"), 2)

    def test_a_404_to_a_request_without_a_session_is_not_retried(self):
        self.bridge = bridge_module.Bridge(self.url.replace("agent1", "agent9"), out=self.out)
        self.send(request(1, "tools/list"))
        answer = self.receive()
        self.assertEqual((answer["id"], answer["error"]["code"]), (1, -32603))
        self.assertIn("HTTP 404", answer["error"]["message"])
        self.assertEqual(self.methods_seen(), ["tools/list"])

    def test_the_agents_token_goes_with_every_post_the_reopening_handshake_included(self):
        # A run the hub made with agent tokens wants the token on every
        # request, so the handshake the bridge repeats on its own carries
        # it too; without a token no Authorization header is sent.
        self.server.forget_calls = 1
        self.bridge = bridge_module.Bridge(self.url, out=self.out, token="the-agent-s-token")
        self.send(request(1, "initialize", INIT_PARAMS))
        self.receive()
        self.send(tool_call(2, "send_message"))
        self.assertEqual(self.receive(), reply(2, text_result("ran send_message")))
        self.assertEqual(self.methods_seen(),
                         ["initialize", "tools/call", "initialize", "notifications/initialized", "tools/call"])
        self.assertEqual(self.server.authorizations, ["Bearer the-agent-s-token"] * 5)
        for plain in (bridge_module.Bridge(self.url), bridge_module.Bridge(self.url, token="")):
            self.assertNotIn("Authorization", plain.headers())

    def test_a_400_carrying_the_hubs_jsonrpc_error_reaches_the_client_as_that_error(self):
        """The hub refuses a request it cannot answer under an id with a
        JSON-RPC error of its own and no id; the stdio client waits on
        the ids it sent, so it hears the hub's code and message under
        each of them, as it would from the hub on stdio, rather than an
        internal error quoting HTTP 400."""
        self.send(request(1, "initialize", INIT_PARAMS))
        self.receive()
        self.send(tool_call(None, "send_message"))
        self.assertEqual(self.receive(), {"jsonrpc": "2.0", "id": None, "error": {
            "code": -32600, "message": "the id must be a string or an integer"}})
        self.send([tool_call(True, "send_message"), request(7, "ping"), {"jsonrpc": "2.0", "method": "note"}])
        answers = self.receive()
        self.assertEqual([a["id"] for a in answers], [True, 7])
        for answer in answers:
            self.assertEqual(answer["error"], {"code": -32600, "message": "the id must be a string or an integer"})
        self.assertEqual(self.methods_seen()[1:], ["tools/call", "tools/call", "ping", "note"])
        self.assertTrue(self.out.lines.empty())

    def test_a_400_without_a_jsonrpc_body_is_a_hub_failure(self):
        self.server.refuses_plainly = True
        self.send(request(1, "initialize", INIT_PARAMS))
        self.receive()
        self.send(tool_call(2, "send_message"))
        answer = self.receive()
        self.assertEqual((answer["id"], answer["error"]["code"]), (2, -32603))
        self.assertIn("HTTP 400 Bad Request", answer["error"]["message"])
        self.assertIn("the body is not a request", answer["error"]["message"])
        self.assertIsNone(bridge_module.jsonrpc_error_in('{"error": "plain"}'))
        self.assertIsNone(bridge_module.jsonrpc_error_in('[{"jsonrpc": "2.0", "error": {"code": 1, "message": "m"}}]'))
        self.assertIsNone(bridge_module.jsonrpc_error_in("not json"))

    def test_parallel_requests_that_lose_the_session_share_one_reopen(self):
        self.server.forget_calls = 1
        self.send(request(1, "initialize", INIT_PARAMS))
        self.receive()
        self.send(tool_call(2, "first"))
        self.send(tool_call(3, "second"))
        answers = {a["id"]: a for a in (self.receive(), self.receive())}
        self.assertEqual(answers[2], reply(2, text_result("ran first")))
        self.assertEqual(answers[3], reply(3, text_result("ran second")))
        self.assertEqual(self.methods_seen().count("initialize"), 2)
        self.assertEqual(self.server.sessions, 2)


if __name__ == "__main__":
    unittest.main()
