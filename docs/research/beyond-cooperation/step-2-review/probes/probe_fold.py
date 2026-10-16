"""Can a server's or a program's own tool name reach the record, the --json
file or the report by any route: the session's own calls, a helper's
transcript beside it, a helper inside an execution file, a run's usage
record, or the commit line?"""
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

TREE = Path(__file__).resolve().parent / "tree"
sys.path.insert(0, str(TREE / "tests"))
import test_profile as P  # noqa: E402

profile = P.profile
SECRET_NAMES = ("mcp__acme-crm__lookup_customer", "acme_private_tool", "mcp__plugin_x_y__z", "Bash ", "bash")


def main_entries():
    return [
        *P.assistant("m1", P.used(100, 900, 0, 50), [
            P.tool_use("t1", SECRET_NAMES[0], customer="x"),
            P.tool_use("t2", SECRET_NAMES[1], id=1),
            P.tool_use("t3", "Agent", prompt="go"),
        ], 10),
        P.result("t1", "a" * 40, 12), P.result("t2", "b" * 60, 13), P.result("t3", "done", 30),
        *P.assistant("m2", P.used(0, 100, 1000, 10), [{"type": "text", "text": "Done."}], 40),
    ]


def helper():
    return [
        *P.assistant("h1", P.used(10, 90, 0, 5), [P.tool_use("u1", SECRET_NAMES[2], q="x"),
                                                  P.tool_use("u2", SECRET_NAMES[3], command="ls"),
                                                  P.tool_use("u3", SECRET_NAMES[4], command="ls")], 15),
        P.result("u1", "c", 16), P.result("u2", "d", 17), P.result("u3", "e", 18),
        *P.assistant("h2", P.used(0, 10, 100, 1), [{"type": "text", "text": "ok"}], 19),
    ]


with tempfile.TemporaryDirectory() as folder:
    transcript = Path(folder) / "0123abcd-0000-0000-0000-000000000000.jsonl"
    P.write_lines(transcript, main_entries())
    helpers = transcript.with_suffix("") / "subagents"
    helpers.mkdir(parents=True)
    P.write_lines(helpers / "agent-1.jsonl", helper())
    out = Path(folder) / "record.json"
    printed = io.StringIO()
    with redirect_stdout(printed):
        profile.main([str(transcript), "--json", str(out)])
    text = out.read_text() + printed.getvalue()
    print("session file: by_tool keys:", sorted(json.loads(out.read_text())["calls"]["by_tool"]))
    print("   any secret name in record or report:", [n for n in SECRET_NAMES if n.strip() in text and n != "bash"])
    print("   report mentions mcp__:", "mcp__" in printed.getvalue())

    # An execution file: one JSON array, a helper's entries carrying parent_tool_use_id.
    execution = Path(folder) / "claude-execution-output.json"
    entries = main_entries() + [dict(e, parent_tool_use_id="t3") for e in helper()]
    execution.write_text(json.dumps(entries))
    record, built = profile.profile(execution)
    print("execution file: by_tool keys:", sorted(record["calls"]["by_tool"]))
    print("   counts the run's record keeps:", profile.since(profile.session_counts(execution), {}))
    print("   names in memory only:", sorted(built.by_tool))
