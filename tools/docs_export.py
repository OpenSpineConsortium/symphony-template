"""A Claude Docs export written to a file exactly as the export returned it.

Claude Docs' export hands a tab back inline as base64 (data.bytes_b64,
with the decoded length in data.bytes), and a session that copies that
text into a file by hand can drop or change a character that no check of
Markdown would see. The session's own transcript keeps every tool result
as it came, so this reads the export from there instead: the export call
that named the doc and the tab, its result (in the transcript, or in the
file Claude Code saved a large result to beside it), decoded, held to its
stated length and to UTF-8, and written. The export-artifacts skill
(.claude/skills/export-artifacts) runs it for each tab of each Docs
artifact.

  python3 tools/docs_export.py <doc link or id> <tab id> <file>
      the newest export of that tab in this session's transcript, written
      to <file>; --transcript <path> names the transcript where the newest
      one under ~/.claude/projects (or $CLAUDE_CONFIG_DIR/projects) is not
      this session's
"""

import base64
import binascii
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ID = re.compile(r"[A-Za-z0-9_-]{1,64}")
# Claude Code notes a large result of one of its own tools in the first
# form, and a large result of an MCP tool, as Claude Docs' export is, in the
# second, whose sentence ends with a full stop after the path
SAVED = re.compile(r"<persisted-output>.*?saved to: (\S+)"
                   r"|exceeds maximum allowed tokens\. Output has been saved to (\S+)", re.S)


class Refused(Exception):
    """The export cannot be written exactly; the message says why."""


def doc_id(text):
    """The doc's id from its link (claude.ai/artifact/<id> or
    claude.ai/code/artifact/<uuid>) or from the id itself."""
    candidate = str(text).rstrip("/").rsplit("/", 1)[-1]
    if not ID.fullmatch(candidate):
        raise Refused(f"{text!r} is neither a doc's link nor its id")
    return candidate


def newest_transcript():
    """The transcript written to last, which is the running session's,
    since a session writes its own on every turn; the subagents' are in
    folders of their own and never match."""
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    found = sorted((home / "projects").glob("*/*.jsonl"), key=lambda path: path.stat().st_mtime)
    if not found:
        raise Refused(f"no transcript under {home / 'projects'}; name one with --transcript")
    return found[-1]


def entries(transcript):
    """Each JSON object of the transcript, passing over a line still being
    written."""
    with open(transcript, "rb") as stream:
        for line in stream:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if isinstance(entry, dict):
                yield entry


def blocks(entry):
    content = (entry.get("message") or {}).get("content")
    return [block for block in content if isinstance(block, dict)] if isinstance(content, list) else []


def is_export_of(block, doc, tab):
    """Whether a tool call is a Claude Docs export of this doc's tab."""
    name = str(block.get("name") or "").lower()
    given = block.get("input") or {}
    container = given.get("container") if isinstance(given, dict) else None
    return (block.get("type") == "tool_use" and name.endswith("__export") and "docs" in name
            and isinstance(container, dict) and str(container.get("id")) == doc
            and str(given.get("file")) == tab)


def text_of(content):
    """A tool result's text, whether a string or a list of text blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(part.get("text") or "") for part in content if isinstance(part, dict))
    return ""


def newest_result(transcript, doc, tab):
    """The text of the last result that answered an export of the tab."""
    calls, answer = set(), None
    for entry in entries(transcript):
        for block in blocks(entry):
            if is_export_of(block, doc, tab):
                calls.add(block.get("id"))
            elif block.get("type") == "tool_result" and block.get("tool_use_id") in calls:
                answer = text_of(entry.get("toolUseResult")) or text_of(block.get("content"))
    if answer is None:
        raise Refused(f"this transcript holds no export of tab {tab} of {doc}; export it first")
    return saved_output(transcript, answer)


def results_folder(transcript):
    """The session's own tool-results folder: beside the session's
    transcript, and the same folder for a subagent of it, whose transcript
    is under the session's subagents/ and whose large results Claude Code
    saves with the session's."""
    transcript = Path(transcript)
    if transcript.parent.name == "subagents":
        return (transcript.parent.parent / "tool-results").resolve()
    return (transcript.with_suffix("") / "tool-results").resolve()


def saved_output(transcript, text):
    """The whole result where Claude Code saved a large one to a file and
    kept only a preview or a note: read only from this session's own
    tool-results folder, whatever path the note names."""
    found = SAVED.search(text)
    if not found:
        return text
    folder = results_folder(transcript)
    path = Path((found.group(1) or found.group(2)).rstrip(".")).resolve()
    if path.parent != folder or not path.is_file():
        raise Refused(f"the result was saved to {path}, outside {folder}; export it again")
    saved = path.read_text(encoding="utf-8")
    parsed = maybe_json(saved)
    return text_of(parsed) if isinstance(parsed, list) else saved


def maybe_json(text):
    try:
        return json.loads(text)
    except ValueError:
        return text


def answer_of(text):
    """The JSON object of an export's answer, which may follow a line of
    notes about who wrote the doc."""
    for line in str(text).splitlines(keepends=True):
        if line.startswith("{"):
            try:
                found, _ = json.JSONDecoder().raw_decode(text[text.index(line):])
            except ValueError:
                continue
            return found
    return None


def payload(text):
    """The exported bytes, held to the length and the encoding the export
    states."""
    answer = answer_of(text)
    if not isinstance(answer, dict):
        raise Refused("the export's answer is not the JSON Claude Docs gives")
    if answer.get("verdict") != "allow":
        raise Refused(f"the export was refused: {answer.get('reason') or answer.get('verdict')}")
    data = answer.get("data") or {}
    try:
        exact = base64.b64decode(str(data.get("bytes_b64") or ""), validate=True)
    except (binascii.Error, ValueError) as error:
        raise Refused(f"the export's base64 does not decode: {error}") from None
    if len(exact) != data.get("bytes"):
        raise Refused(f"the export decodes to {len(exact)} bytes and says {data.get('bytes')}")
    try:
        exact.decode("utf-8")
    except UnicodeDecodeError:
        raise Refused("the export is not UTF-8") from None
    return exact


def write(path, exact):
    """The bytes into path, through a file beside it, so a failed write
    leaves no half of one."""
    target = Path(path)
    part = target.with_name(target.name + ".part")
    part.write_bytes(exact)
    part.replace(target)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    transcript = None
    if args[:1] == ["--transcript"] and len(args) >= 2:
        transcript, args = Path(args[1]), args[2:]
    if len(args) != 3:
        print(__doc__[__doc__.index("  python3"):].rstrip(), file=sys.stderr)
        return 2
    link, tab, out = args
    try:
        exact = payload(newest_result(transcript or newest_transcript(), doc_id(link), tab))
        write(out, exact)
    except (Refused, OSError) as error:
        print(f"docs_export: {error}", file=sys.stderr)
        return 1
    print(f"wrote {out}: {len(exact)} bytes, sha256 {hashlib.sha256(exact).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
