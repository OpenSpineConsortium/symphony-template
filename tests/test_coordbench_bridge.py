"""The bridge is a Streamable HTTP client on behalf of a stdio client that
has no session of its own, so these pin what the transport asks of such
a client when the hub forgets the session: a 404 to a request sent with
Mcp-Session-Id starts a new session (initialize again, then
notifications/initialized, neither shown to the stdio client) and the
request is sent once more. The fake hub here does one thing the real
hub's tests cannot make it do on cue: forget its session."""

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


class ForgetfulHub(BaseHTTPRequestHandler):
    """Just enough of hub.py's /mcp: a session per initialize, 404 for a
    request carrying a session it does not know (the hub's own words),
    and a counter of tool calls on which it forgets its session first."""

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
        return [m.get("method") for _, m in self.server.seen]

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
