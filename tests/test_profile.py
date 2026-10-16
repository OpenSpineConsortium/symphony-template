"""tools/profile.py: a session's profile from its transcript, each API call
counted once, each tool call with its answer, the files read and read
again, the context's growth shared out to the tools, the time in tools and
waiting for the model; and a record that carries counts alone."""

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import profile  # noqa: E402

CWD = "/work/repo"


def at(seconds):
    """A timestamp seconds after the start of a session that began at 10:00."""
    minute, second = divmod(seconds, 60)
    return f"2026-10-15T10:{minute:02d}:{second:06.3f}Z"


def assistant(message_id, usage_fields, blocks, seconds, model="claude-opus-5-5", thinking=None):
    """One assistant message as the transcript writes it: one line per
    block, each carrying the whole message's usage, the lines a second
    apart."""
    lines = []
    for index, block in enumerate(blocks):
        line = {"type": "assistant", "timestamp": at(seconds + index), "cwd": CWD, "uuid": f"u-{message_id}-{index}",
                "message": {"id": message_id, "model": model, "usage": usage_fields, "content": [block]}}
        if thinking is not None and index == 0:
            line["thinkingDurationMs"] = thinking
        lines.append(line)
    return lines


def used(inp, write, read, out):
    return {"input_tokens": inp, "cache_creation_input_tokens": write, "cache_read_input_tokens": read,
            "output_tokens": out}


def tool_use(block_id, name, **given):
    return {"type": "tool_use", "id": block_id, "name": name, "input": given}


def result(block_id, content, seconds, error=False):
    block = {"type": "tool_result", "tool_use_id": block_id, "content": content}
    if error:
        block["is_error"] = True
    return {"type": "user", "timestamp": at(seconds), "cwd": CWD, "message": {"role": "user", "content": [block]}}


def prompt(text, seconds):
    return {"type": "user", "timestamp": at(seconds), "cwd": CWD, "message": {"role": "user", "content": text}}


def write_lines(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e) + "\n" for e in entries) + "half a line\n", encoding="utf-8")


def session_entries():
    """A session of three API calls: a prompt; a call that reads a file
    with Read and two with the shell, one of them for the second time; a
    call with a failing command and a search; a last call that answers
    with text alone."""
    return [
        prompt("Please look at the code.", 0),
        *assistant("m1", used(100, 900, 0, 50), [
            {"type": "text", "text": "Reading."},
            tool_use("t1", "Read", file_path="/work/repo/a.py"),
            tool_use("t2", "Bash", command="cat b.py docs/c.md && head -n 20 a.py | grep x"),
        ], 10, thinking=1500),
        result("t1", "a" * 400, 14),
        result("t2", [{"type": "text", "text": "b" * 600}], 16),
        # The context grew by 1250 (2250 - 1000) less the 50 output tokens:
        # 1200 tokens, shared 400:600 between the two tools.
        *assistant("m2", used(0, 1250, 1000, 20), [
            tool_use("t3", "Bash", command="python3 -m unittest\nsed -n '1,5p' b.py"),
            tool_use("t4", "Grep", pattern="def"),
        ], 20),
        result("t3", "boom", 25, error=True),
        result("t4", "a.py:1:def f", 26),
        *assistant("m3", used(0, 100, 2250, 30), [{"type": "text", "text": "Done."}], 30),
        {"type": "attachment", "timestamp": at(31), "attachment": {"type": "hook_success"}},
    ]


class ReadingATranscript(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder, True)
        self.transcript = self.folder / "abcdef12-3456-7890.jsonl"
        write_lines(self.transcript, session_entries())
        self.record, self.built = profile.profile(self.transcript)

    def test_each_api_call_counts_once_whatever_its_lines(self):
        self.assertEqual(self.record["context"]["calls"], 3)
        self.assertEqual(self.record["models"], {"claude-opus-5-5": [100, 1250 + 900 + 100, 0, 3250, 100]})
        self.assertEqual(self.record["tokens"]["total"], 100 + 2250 + 3250 + 100)
        self.assertEqual(self.record["session"], "abcdef12")
        self.assertEqual(self.record["prompts"], 1)
        self.assertEqual(self.record["attachments"], 1)

    def test_the_context_is_read_call_by_call_and_its_growth_shared_out(self):
        context = self.record["context"]
        self.assertEqual((context["first"], context["peak"], context["last"]), (1000, 2350, 2350))
        self.assertEqual(context["mean"], round((1000 + 2250 + 2350) / 3))
        self.assertEqual(context["cached_share"], round(3250 / (1000 + 2250 + 2350), 3))
        # 2250 - 1000 - 50 from the first call's tools, 2350 - 2250 - 20 from the second's.
        self.assertEqual(context["growth"], 1200 + 80)
        self.assertEqual(context["growth_from_tools_estimated"], 1200 + 80)
        by_tool = self.record["calls"]["by_tool"]
        self.assertEqual(by_tool["Read"]["context_tokens_estimated"], 480)
        self.assertEqual(by_tool["Bash"]["context_tokens_estimated"], 720 + 80 * 4 // 16)
        self.assertEqual(by_tool["Grep"]["context_tokens_estimated"], 80 * 12 // 16)
        self.assertEqual((context["compactions"], context["drops"]), (0, 0))

    def test_tool_calls_by_tool_with_their_answers(self):
        calls = self.record["calls"]
        self.assertEqual((calls["total"], calls["failed"], calls["unanswered"]), (4, 1, 0))
        self.assertEqual(calls["by_tool"]["Bash"]["calls"], 2)
        self.assertEqual(calls["by_tool"]["Bash"]["failed"], 1)
        self.assertEqual(calls["by_tool"]["Bash"]["result_bytes"], 600 + 4)
        self.assertEqual(calls["by_tool"]["Read"]["result_bytes"], 400)
        # From the line that asked (t1 at 11 s, t2 at 12 s) to the line that answered.
        self.assertEqual(calls["by_tool"]["Read"]["seconds_in_tool"], 3)
        self.assertEqual(calls["by_tool"]["Bash"]["seconds_in_tool"], 4 + 5)
        self.assertEqual(self.record["shell"], {"read": 3, "search": 1, "list": 0, "git": 0, "run": 1})

    def test_reads_and_rereads(self):
        reads = self.record["reads"]
        # Read a.py; cat b.py docs/c.md and head a.py (a.py again); sed b.py (again).
        self.assertEqual(reads["calls"], 3)
        self.assertEqual(reads["files_named"], 1 + 3 + 1)
        self.assertEqual(reads["files"], 3)
        self.assertEqual(reads["rereads"], 2)
        self.assertEqual(reads["partial"], 2)
        self.assertEqual(reads["bytes"], 400 + 600 + 4)
        self.assertEqual(reads["reread_bytes"], 4)
        self.assertEqual(self.built.per_path["/work/repo/a.py"], 2)
        self.assertEqual(self.built.per_path["/work/repo/docs/c.md"], 1)

    def test_time_in_tools_and_waiting_for_the_model(self):
        seconds = self.record["seconds"]
        self.assertEqual(seconds["span"], 31)
        # t1 asked at 11 s and answered at 14, t2 12 to 16, t3 20 to 25, t4 21 to 26.
        self.assertEqual(seconds["in_tools"], 3 + 4 + 5 + 5)
        # The prompt at 0 to m1's last line at 12; t2's answer at 16 to m2's
        # last line at 21; t4's answer at 26 to m3's line at 30.
        self.assertEqual(seconds["waiting_for_model"], 12 + 5 + 4)
        self.assertEqual(seconds["thinking"], 2)

    def test_the_record_carries_no_path_command_or_text(self):
        text = json.dumps(self.record)
        for secret in ("a.py", "b.py", "docs/c.md", "cat ", "unittest", "Please", "Done", "boom", CWD):
            self.assertNotIn(secret, text)
        self.assertEqual(self.record["schema"], "symphony-profile/1")
        self.assertEqual(self.record["started_at"], "2026-10-15T10:00:00Z")

    def test_the_report_reads_the_record(self):
        text = profile.report(self.record)
        self.assertIn("Profile of session abcdef12", text)
        self.assertIn("Tool calls: 4, 1 failed, 0 unanswered", text)
        self.assertIn("Reads: 3 calls naming 5 files (3 distinct), 2 re-reads (40%), 2 partial", text)
        self.assertIn("Shell commands: read 3, search 1, list 0, git 0, run 1", text)
        self.assertIn("compactions", text)
        self.assertTrue(text.isascii())


class HelpersAndCompactions(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder, True)
        self.transcript = self.folder / "abcdef12-3456-7890.jsonl"

    def test_a_helpers_calls_count_and_its_context_does_not(self):
        write_lines(self.transcript, session_entries())
        helper = self.folder / "abcdef12-3456-7890" / "subagents" / "agent-1.jsonl"
        write_lines(helper, [
            *assistant("h1", used(10, 0, 0, 5), [tool_use("h-t1", "Read", file_path="/work/repo/a.py")], 100,
                       model="claude-sonnet-5-5"),
            result("h-t1", "a" * 400, 102),
        ])
        record, built = profile.profile(self.transcript)
        self.assertEqual(record["helpers"], 1)
        self.assertEqual(record["calls"]["total"], 5)
        self.assertEqual(record["models"]["claude-sonnet-5-5"], [10, 0, 0, 0, 5])
        self.assertEqual(record["context"]["calls"], 3)
        # The helper reads a.py for the first time in its own context.
        self.assertEqual(record["reads"]["rereads"], 2)
        self.assertEqual(record["reads"]["files"], 3)
        self.assertEqual(profile.profile(self.transcript, helpers=False)[0]["calls"]["total"], 4)

    def test_a_compaction_is_counted_and_the_drop_is_no_growth(self):
        entries = [
            *assistant("m1", used(0, 5000, 0, 100), [tool_use("t1", "Bash", command="ls")], 10),
            result("t1", "x" * 10, 12),
            {"type": "system", "subtype": "compact_boundary", "timestamp": at(13),
             "compactMetadata": {"trigger": "auto", "preTokens": 5100}},
            {"type": "user", "timestamp": at(14), "isCompactSummary": True,
             "message": {"role": "user", "content": "This session is being continued"}},
            *assistant("m2", used(1200, 0, 0, 10), [{"type": "text", "text": "Going on."}], 15),
        ]
        write_lines(self.transcript, entries)
        record, _ = profile.profile(self.transcript)
        self.assertEqual(record["context"]["compactions"], 1)
        self.assertEqual(record["context"]["drops"], 1)
        self.assertEqual(record["context"]["growth"], 0)
        self.assertEqual(record["prompts"], 0)

    def test_a_synthetic_message_and_a_message_without_usage_are_no_api_calls(self):
        entries = [
            *assistant("s1", used(0, 0, 0, 0), [{"type": "text", "text": "No response requested."}], 1,
                       model="<synthetic>"),
            {"type": "assistant", "timestamp": at(2), "message": {"id": "n1", "model": "claude-opus-5-5",
                                                                    "content": [tool_use("t9", "Bash", command="ls")]}},
            result("t9", "", 3),
        ]
        write_lines(self.transcript, entries)
        record, _ = profile.profile(self.transcript)
        self.assertEqual(record["context"]["calls"], 0)
        self.assertEqual(record["models"], {})
        self.assertEqual(record["calls"]["total"], 1)


class ReadingShellCommands(unittest.TestCase):
    def test_the_files_a_command_prints(self):
        self.assertEqual(profile.shell_reads("cat a b", "/r"), ["/r/a", "/r/b"])
        self.assertEqual(profile.shell_reads("head -n 20 a; tail -5 b; tail -c 10 c", "/r"), ["/r/a", "/r/b", "/r/c"])
        self.assertEqual(profile.shell_reads("sed -n '1,20p' tools/x.py", "/r"), ["/r/tools/x.py"])
        self.assertEqual(profile.shell_reads("sed -e 's/a/b/' -n x.py y.py", "/r"), ["/r/x.py", "/r/y.py"])
        self.assertEqual(profile.shell_reads("sed -i 's/a/b/' x.py", "/r"), [])
        self.assertEqual(profile.shell_reads("cat -; cat '*.py'; cat $HOME/x; cat ~/y", "/r"), [])
        self.assertEqual(profile.shell_reads("cd /elsewhere && cat a && cd sub && cat b", "/r"),
                         ["/elsewhere/a", "/elsewhere/sub/a".replace("/a", "/b")])
        self.assertEqual(profile.shell_reads("FOO=1 cat /abs/../x", "/r"), ["/x"])
        self.assertEqual(profile.shell_reads("cat a", ""), ["a"])
        self.assertEqual(profile.shell_reads("echo 'unclosed", "/r"), [])

    def test_a_here_document_is_data_not_commands(self):
        command = "python3 - x <<'EOF'\ncat secret\nls\nEOF\ngit status"
        self.assertEqual(profile.shell_reads(command, "/r"), [])
        self.assertEqual(profile.shell_uses(command), {"run": 1, "git": 1})
        self.assertEqual(profile.without_heredocs("cat <<EOF > f\nline\nEOF"), "cat <<EOF > f")
        self.assertEqual(profile.without_heredocs('a <<"X"\nb\nX\nc'), "a <<\"X\"\nc")

    def test_what_each_command_is_for(self):
        self.assertEqual(profile.shell_uses("cd /r && ls -la | grep x; git log; python3 t.py; wc -l a; echo hi"),
                         {"list": 2, "search": 1, "git": 1, "run": 1})
        self.assertEqual(profile.shell_uses("rg -n def tools/ && find . -name '*.py'"), {"search": 1, "list": 1})
        self.assertEqual(profile.shell_uses(""), {})


class TheCommandLine(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.folder, True)
        self.transcript = self.folder / "abcdef12-3456-7890.jsonl"
        write_lines(self.transcript, session_entries())

    def test_prints_the_report_and_writes_the_record(self):
        out = self.folder / "out" / "profile.json"
        printed = io.StringIO()
        with redirect_stdout(printed):
            code = profile.main([str(self.transcript), "--json", str(out), "--paths", "2"])
        self.assertEqual(code, 0)
        self.assertIn("Profile of session abcdef12", printed.getvalue())
        self.assertIn("Files read most often (not in the record):", printed.getvalue())
        self.assertIn("    2  /work/repo/a.py", printed.getvalue())
        record = json.loads(out.read_text(encoding="ascii"))
        self.assertEqual(record["calls"]["total"], 4)
        self.assertNotIn("a.py", out.read_text())

    def test_a_missing_transcript_is_said(self):
        printed = io.StringIO()
        with redirect_stdout(printed):
            self.assertEqual(profile.main([str(self.folder / "none.jsonl")]), 2)


if __name__ == "__main__":
    unittest.main()
