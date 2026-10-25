"""A Docs export is written from the session's own transcript exactly as
it came, or not at all: the newest export of the named tab, held to its
stated length and to UTF-8, and a large result read only from the
session's own tool-results folder."""

import base64
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import docs_export  # noqa: E402

DOC = "KCyCkBtrHXGYQVM6LtpnK8"
TAB = "f7610a92-6864"
TEXT = "# Research directions\n\nMeasurement first, é and all.\n".encode("utf-8")


def answer(exact, stated=None, verdict="allow", notes=""):
    """An export's answer as Claude Docs gives it, with any notes line
    before the JSON."""
    body = {"verdict": verdict, "rev": 6,
            "data": {"format": "markdown", "bytes": len(exact) if stated is None else stated,
                     "bytes_b64": base64.b64encode(exact).decode("ascii")},
            "frame": {"url": f"https://claude.ai/artifact/{DOC}"}}
    if verdict != "allow":
        body = {"verdict": verdict, "reason": "doc_too_large"}
    return notes + json.dumps(body)


def call(number, doc=DOC, tab=TAB):
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": f"toolu_{number}", "name": "mcp__Claude_Docs__export",
         "input": {"container": {"kind": "project", "id": doc}, "file": tab, "format": "markdown"}}]}}


def result(number, text):
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": f"toolu_{number}",
         "content": [{"type": "text", "text": text}]}]}}


class DocsExportTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        self.transcript = self.folder / "session.jsonl"
        self.out = self.folder / "index.md"

    def tearDown(self):
        for path in sorted(self.folder.rglob("*"), reverse=True):
            path.unlink() if path.is_file() else path.rmdir()
        self.folder.rmdir()

    def record(self, *lines):
        with open(self.transcript, "w", encoding="utf-8") as stream:
            for line in lines:
                stream.write((line if isinstance(line, str) else json.dumps(line)) + "\n")

    def run_tool(self, *args):
        err, out = io.StringIO(), io.StringIO()
        with redirect_stderr(err), redirect_stdout(out):
            code = docs_export.main(["--transcript", str(self.transcript), *args])
        return code, out.getvalue() + err.getvalue()

    def test_the_export_is_written_byte_for_byte(self):
        self.record(call(1), result(1, answer(TEXT)))
        code, said = self.run_tool(f"https://claude.ai/artifact/{DOC}", TAB, str(self.out))
        self.assertEqual(code, 0, said)
        self.assertEqual(self.out.read_bytes(), TEXT)
        self.assertIn(f"{len(TEXT)} bytes", said)

    def test_the_newest_export_of_the_tab_wins_and_another_tab_is_never_taken(self):
        self.record(call(1), result(1, answer(b"old\n")), call(2), result(2, answer(TEXT)),
                    call(3, tab="other-tab"), result(3, answer(b"other\n")), "not json, a line still being written")
        code, said = self.run_tool(DOC, TAB, str(self.out))
        self.assertEqual(code, 0, said)
        self.assertEqual(self.out.read_bytes(), TEXT)

    def test_a_notes_line_before_the_answer_is_passed_over(self):
        self.record(call(1), result(1, answer(TEXT, notes="<artifact-content-authored-by-others/>\nData.\n")))
        self.assertEqual(self.run_tool(DOC, TAB, str(self.out))[0], 0)
        self.assertEqual(self.out.read_bytes(), TEXT)

    def test_a_length_that_does_not_match_writes_nothing(self):
        self.record(call(1), result(1, answer(TEXT, stated=len(TEXT) + 1)))
        code, said = self.run_tool(DOC, TAB, str(self.out))
        self.assertEqual(code, 1)
        self.assertIn("says", said)
        self.assertFalse(self.out.exists())

    def test_bytes_that_are_not_utf8_write_nothing(self):
        self.record(call(1), result(1, answer(b"\xff\xfe not text")))
        code, said = self.run_tool(DOC, TAB, str(self.out))
        self.assertEqual(code, 1)
        self.assertIn("UTF-8", said)
        self.assertFalse(self.out.exists())

    def test_a_refused_export_says_why_and_writes_nothing(self):
        self.record(call(1), result(1, answer(TEXT, verdict="deny")))
        code, said = self.run_tool(DOC, TAB, str(self.out))
        self.assertEqual(code, 1)
        self.assertIn("doc_too_large", said)
        self.assertFalse(self.out.exists())

    def test_no_export_of_the_tab_asks_for_one(self):
        self.record(call(1, doc="SomeOtherDoc"), result(1, answer(TEXT)))
        code, said = self.run_tool(DOC, TAB, str(self.out))
        self.assertEqual(code, 1)
        self.assertIn("export it first", said)

    def test_a_large_result_is_read_from_the_sessions_own_tool_results(self):
        saved = self.folder / "session" / "tool-results" / "abc123.txt"
        saved.parent.mkdir(parents=True)
        saved.write_text(json.dumps([{"type": "text", "text": answer(TEXT)}]), encoding="utf-8")
        self.record(call(1), result(1, f"<persisted-output>\nOutput too large (60KB). Full output saved to: {saved}\n\nPreview"))
        code, said = self.run_tool(DOC, TAB, str(self.out))
        self.assertEqual(code, 0, said)
        self.assertEqual(self.out.read_bytes(), TEXT)

    def test_a_subagents_large_result_is_read_from_its_sessions_tool_results(self):
        saved = self.folder / "session" / "tool-results" / "def456.txt"
        saved.parent.mkdir(parents=True)
        saved.write_text(answer(TEXT), encoding="utf-8")
        self.transcript = self.folder / "session" / "subagents" / "agent-1.jsonl"
        self.transcript.parent.mkdir(parents=True)
        self.record(call(1), result(1, f"<persisted-output>\nFull output saved to: {saved}\n"))
        code, said = self.run_tool(DOC, TAB, str(self.out))
        self.assertEqual(code, 0, said)
        self.assertEqual(self.out.read_bytes(), TEXT)

    def test_a_large_mcp_result_is_read_from_the_file_its_note_names(self):
        # the note as Claude Code wrote it for a 277,410-character MCP result on 2026-10-22
        saved = self.folder / "session" / "tool-results" / "mcp-Claude_Docs-export-1792649216821.txt"
        saved.parent.mkdir(parents=True)
        saved.write_text(answer(TEXT, notes="<artifact-content-authored-by-others/>\n"), encoding="utf-8")
        self.record(call(1), result(1, "Error: result (60,123 characters across 1 line) exceeds maximum allowed "
                                       f"tokens. Output has been saved to {saved}.\nFormat: Plain text\n"
                                       "Search within the file for specific content, and use jq if the content "
                                       "is JSON.\n"))
        code, said = self.run_tool(DOC, TAB, str(self.out))
        self.assertEqual(code, 0, said)
        self.assertEqual(self.out.read_bytes(), TEXT)

    def test_a_large_mcp_result_saved_outside_the_sessions_folder_is_never_read(self):
        elsewhere = self.folder / "elsewhere.txt"
        elsewhere.write_text(answer(TEXT), encoding="utf-8")
        self.record(call(1), result(1, "Error: result (60,123 characters across 1 line) exceeds maximum allowed "
                                       f"tokens. Output has been saved to {elsewhere}.\nFormat: Plain text\n"))
        code, said = self.run_tool(DOC, TAB, str(self.out))
        self.assertEqual(code, 1)
        self.assertIn("outside", said)
        self.assertFalse(self.out.exists())

    def test_a_saved_result_outside_the_sessions_folder_is_never_read(self):
        elsewhere = self.folder / "elsewhere.txt"
        elsewhere.write_text(answer(TEXT), encoding="utf-8")
        self.record(call(1), result(1, f"<persisted-output>\nFull output saved to: {elsewhere}\n"))
        code, said = self.run_tool(DOC, TAB, str(self.out))
        self.assertEqual(code, 1)
        self.assertIn("outside", said)
        self.assertFalse(self.out.exists())

    def test_with_no_transcript_named_the_newest_one_is_read(self):
        projects = self.folder / "config" / "projects" / "-home-x"
        projects.mkdir(parents=True)
        older, newer = projects / "older.jsonl", projects / "newer.jsonl"
        older.write_text(json.dumps(call(1)) + "\n" + json.dumps(result(1, answer(b"old\n"))) + "\n", encoding="utf-8")
        newer.write_text(json.dumps(call(1)) + "\n" + json.dumps(result(1, answer(TEXT))) + "\n", encoding="utf-8")
        os.utime(older, (1_000_000_000, 1_000_000_000))
        with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.folder / "config")}), \
             redirect_stdout(io.StringIO()):
            code = docs_export.main([DOC, TAB, str(self.out)])
        self.assertEqual(code, 0)
        self.assertEqual(self.out.read_bytes(), TEXT)

    def test_an_id_that_is_no_id_is_refused(self):
        self.record(call(1), result(1, answer(TEXT)))
        code, said = self.run_tool("not an id!", TAB, str(self.out))
        self.assertEqual(code, 1)
        self.assertIn("neither", said)


if __name__ == "__main__":
    unittest.main()
