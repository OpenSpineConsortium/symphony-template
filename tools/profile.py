"""What a Claude Code session spent, read from the transcript it leaves:
its context, call by call; its tool calls, by tool; what it read, and
read again; and where its time went. The first instrument of the research
programme in docs/research/beyond-cooperation/README.md, which measures a
way of working before changing it.

  python3 tools/profile.py TRANSCRIPT [--json FILE] [--paths N]

prints a report and, with --json, writes the record docs/research/
beyond-cooperation/README.md describes, aggregates only: counts, bytes,
seconds and tokens, with tool names and model names, and never a path, a
command, a prompt or any text of the conversation, so a record can be
committed beside the question it answers. --paths N prints the N files
read most often, which stays on the screen.

The transcript is the one Claude Code writes under ~/.claude/projects/,
one JSON object a line, the same file tools/usage.py reads for the usage
trailer, and its helpers' transcripts (the subagents') are read beside it
as usage.py reads them. Each API call is counted once by its message id,
since a message written as several lines, one per block, carries the same
usage on each; a third-party counter that sums every line over-counts.
Three measures are estimates, and say so in the record's keys: the tokens
each tool brought into the context (the context's growth from one call to
the next, less the call's own output, shared among the call's tools by the
size of their results), the seconds in tools (from the line that asked to
the line that answered) and the seconds waiting for the model (from the
last line before a call to the call's last line, which holds its thinking
and its answer; the harness's own count of the thinking is beside it).

Standard library only, like every tool here; the shell commands are split
by the vendored protocol library's reader, the one the push guard uses.
"""

import argparse
import json
import posixpath
import re
import sys
from collections import Counter
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import economics  # noqa: E402
import usage  # noqa: E402
from sdlc_protocol import guard  # noqa: E402

SCHEMA = "symphony-profile/1"
# Programs that print a file: a shell command of one of them is a read of
# the files it names, as a call of the Read tool is.
READERS = ("cat", "head", "tail", "sed", "less", "more", "nl")
# Those that print part of a file, as a Read with an offset or a limit does.
PARTIAL_READERS = ("head", "tail", "sed")
SEARCHERS = ("grep", "rg", "ag", "ack", "egrep", "fgrep")
LISTERS = ("ls", "find", "tree", "wc", "stat", "du", "file")
GIT = ("git", "gh")
# Builtins that read and run nothing worth counting.
QUIET = ("cd", "echo", "printf", "true", "false", "exit", "export", "set", "test", "[", "pwd")
SHELL_USES = ("read", "search", "list", "git", "run")
# The options of the readers whose value is the next word, so it is not
# taken for a file: head -n 20 FILE, sed -e SCRIPT FILE.
VALUED = {"head": ("-n", "-c"), "tail": ("-n", "-c"), "sed": ("-e", "-f", "--expression", "--file")}
# A fall of the context between two consecutive calls by more than this
# share is a drop: a compaction, or the harness trimming what it sends.
DROP = 0.5
GLOB = "*?[$~"
# A here-document: the body after a line with << WORD, up to the line that
# is WORD, is data the command reads, not commands the shell runs.
HEREDOC = re.compile(r"<<-?\s*(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z_][A-Za-z0-9_]*))")
BY_TOOL_KEYS = ("calls", "failed", "input_bytes", "result_bytes", "seconds_in_tool", "context_tokens_estimated")


# --- reading the transcript -----------------------------------------------------

def blocks(message):
    """The content blocks of a message; a string content has none."""
    content = message.get("content") if isinstance(message, dict) else None
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def text_bytes(content):
    """The size of what a tool returned as the model saw it: a string, or
    the text blocks of a list; an image block counts nothing."""
    if isinstance(content, str):
        return len(content.encode("utf-8"))
    if isinstance(content, list):
        return sum(len(str(b.get("text") or "").encode("utf-8")) for b in content
                   if isinstance(b, dict) and b.get("type") == "text")
    return 0


def api_calls(entries):
    """Each API call of a transcript once, in order of its first line, with
    the tool calls it made: a message's lines share its id, and its
    tool_use blocks are told apart by theirs."""
    calls, by_id = [], {}
    for entry in entries:
        message = entry.get("message") if entry.get("type") == "assistant" else None
        if not isinstance(message, dict) or message.get("model") == usage.SYNTHETIC:
            continue
        key = message.get("id") or entry.get("requestId") or entry.get("uuid")
        call = by_id.get(key)
        if call is None:
            counts = usage.counts_of(message.get("usage")) if message.get("usage") else None
            call = {"model": message.get("model") or "unknown", "at": usage.moment(entry.get("timestamp")),
                    "until": usage.moment(entry.get("timestamp")), "counts": counts, "tools": {},
                    "thinking_ms": entry.get("thinkingDurationMs") or 0}
            by_id[key] = call
            calls.append(call)
        at = usage.moment(entry.get("timestamp"))
        if at is not None and (call["until"] is None or at > call["until"]):
            call["until"] = at
        for block in blocks(message):
            if block.get("type") == "tool_use" and block.get("id") and block["id"] not in call["tools"]:
                call["tools"][block["id"]] = {"name": str(block.get("name") or "unknown"),
                                              "input": block.get("input") if isinstance(block.get("input"), dict) else {},
                                              "at": usage.moment(entry.get("timestamp")), "cwd": entry.get("cwd") or "",
                                              "result": None}
    return calls


def tool_results(entries):
    """Each tool's answer by the id of the call it answers: when it came,
    how big it was and whether it was an error."""
    found = {}
    for entry in entries:
        if entry.get("type") != "user":
            continue
        for block in blocks(entry.get("message")):
            if block.get("type") == "tool_result" and block.get("tool_use_id"):
                found[block["tool_use_id"]] = {"at": usage.moment(entry.get("timestamp")),
                                               "bytes": text_bytes(block.get("content")),
                                               "error": bool(block.get("is_error"))}
    return found


def context_of(counts):
    """The tokens an API call sent: uncached input, cache writes and cache reads."""
    return counts[0] + counts[1] + counts[2] + counts[3]


def is_prompt(entry):
    """A person's own message: a user line that is no tool result, no
    attachment the harness added and no summary a compaction wrote."""
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isCompactSummary"):
        return False
    message = entry.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return True
    return bool(blocks(message)) and all(b.get("type") == "text" for b in blocks(message))


def compactions(entries):
    """How many times the context was compacted: the boundary lines the
    harness writes, or, where it writes none, the summaries it starts the
    continued conversation with."""
    boundaries = sum(1 for e in entries if e.get("type") == "system" and e.get("subtype") == "compact_boundary")
    summaries = sum(1 for e in entries if e.get("type") == "user" and e.get("isCompactSummary"))
    return max(boundaries, summaries)


# --- what was read --------------------------------------------------------------

def resolve(path, base):
    """A path as the transcript names it, made absolute against the line's
    working directory where it is a plain path; a pattern or a variable is
    kept as written, since the file it means cannot be told."""
    if not path or path == "-" or any(ch in path for ch in GLOB):
        return None
    if posixpath.isabs(path) or (len(path) > 1 and path[1] == ":"):
        return posixpath.normpath(path)
    return posixpath.normpath(posixpath.join(base or "", path)) if base else path


def program_of(argv):
    """The program a simple command runs, after any VAR=value words."""
    words = list(argv)
    while words and guard.ASSIGNMENT.match(words[0]):
        words.pop(0)
    return (guard.program(words[0]) if words else ""), words[1:]


def files_of(program, arguments):
    """The files a reading command names: its words that are no option
    and no option's value, and for sed, whose first plain word is the
    script, the words after that."""
    files, skip, script_seen = [], False, program != "sed"
    for word in arguments:
        if skip:
            skip = False
        elif word in VALUED.get(program, ()):
            skip = True
            if program == "sed" and word in ("-e", "--expression"):
                script_seen = True
        elif word.startswith("-") and len(word) > 1:
            continue
        elif not script_seen:
            script_seen = True
        else:
            files.append(word)
    return files


def without_heredocs(command):
    """The command with its here-document bodies left out."""
    kept, closing = [], None
    for line in str(command).split("\n"):
        if closing is not None:
            if line.strip() == closing:
                closing = None
            continue
        kept.append(line)
        opened = HEREDOC.search(line)
        if opened:
            closing = next(g for g in opened.groups() if g)
    return "\n".join(kept)


def commands_of(command):
    return guard.simple_commands(without_heredocs(command))


def shell_reads(command, base):
    """The files a shell command prints, as resolve() names them, following
    a cd inside the command; sed -i writes and is no read."""
    paths = []
    for argv in commands_of(command):
        program, arguments = program_of(argv)
        if program == "cd" and len(arguments) == 1:
            base = resolve(arguments[0], base) or base
        elif program in READERS and not (program == "sed" and any(w.startswith("-i") for w in arguments)):
            paths.extend(p for p in (resolve(f, base) for f in files_of(program, arguments)) if p)
    return paths


def shell_uses(command):
    """What each simple command of a shell command is for."""
    uses = Counter()
    for argv in commands_of(command):
        program, arguments = program_of(argv)
        if not program or program in QUIET:
            continue
        if program in READERS and not (program == "sed" and any(w.startswith("-i") for w in arguments)):
            uses["read"] += 1
        elif program in SEARCHERS:
            uses["search"] += 1
        elif program in LISTERS:
            uses["list"] += 1
        elif program in GIT:
            uses["git"] += 1
        else:
            uses["run"] += 1
    return uses


def reads_of(tool):
    """The files one tool call reads, and whether it reads part of them."""
    name, given = tool["name"], tool["input"]
    if name == "Read":
        path = resolve(str(given.get("file_path") or ""), tool["cwd"])
        return ([path] if path else []), bool(given.get("offset") or given.get("limit"))
    if name == "Bash":
        command = str(given.get("command") or "")
        partial = any(program_of(argv)[0] in PARTIAL_READERS for argv in commands_of(command))
        return shell_reads(command, tool["cwd"]), partial
    return [], False


# --- the profile -------------------------------------------------------------------

def empty_tool():
    return dict.fromkeys(BY_TOOL_KEYS, 0)


class Profile:
    """The record as it is built, one transcript at a time."""

    def __init__(self):
        self.models = {}
        self.by_tool = {}
        self.calls = Counter()
        self.shell = Counter(dict.fromkeys(SHELL_USES, 0))
        self.reads = Counter(dict.fromkeys(("calls", "files_named", "rereads", "partial", "bytes", "reread_bytes"), 0))
        self.files = set()
        self.per_path = Counter()
        self.context = {}
        self.seconds = {"span": 0, "active": 0, "in_tools": 0, "waiting_for_model": 0, "thinking": 0}
        self.prompts = 0
        self.attachments = 0
        self.helpers = 0
        self.started = None
        self.ended = None

    def add_transcript(self, entries, main):
        calls, results = api_calls(entries), tool_results(entries)
        for call in calls:
            if call["counts"]:
                usage.add(self.models, call["model"], call["counts"])
            for tool in call["tools"].values():
                tool["result"] = results.get(id_of(call, tool))
        self.add_tools(calls)
        if main:
            self.add_context(calls)
            self.context["compactions"] = compactions(entries)
            self.add_time(entries, calls)
            self.prompts = sum(1 for e in entries if is_prompt(e))
            self.attachments = sum(1 for e in entries if e.get("type") == "attachment")

    def add_tools(self, calls):
        seen = set()
        for call in calls:
            for tool in call["tools"].values():
                row = self.by_tool.setdefault(tool["name"], empty_tool())
                row["calls"] += 1
                row["input_bytes"] += len(json.dumps(tool["input"], sort_keys=True).encode("utf-8"))
                self.calls["total"] += 1
                result = tool["result"]
                if result is None:
                    self.calls["unanswered"] += 1
                else:
                    row["result_bytes"] += result["bytes"]
                    row["failed"] += int(result["error"])
                    self.calls["failed"] += int(result["error"])
                    if result["at"] is not None and tool["at"] is not None and result["at"] >= tool["at"]:
                        row["seconds_in_tool"] += result["at"] - tool["at"]
                        self.seconds["in_tools"] += result["at"] - tool["at"]
                if tool["name"] == "Bash":
                    self.shell.update(shell_uses(str(tool["input"].get("command") or "")))
                self.add_reads(tool, seen)

    def add_reads(self, tool, seen):
        paths, partial = reads_of(tool)
        if not paths:
            return
        new = [p for p in paths if p not in seen]
        self.reads["calls"] += 1
        self.reads["files_named"] += len(paths)
        self.reads["rereads"] += len(paths) - len(new)
        self.reads["partial"] += int(partial)
        size = tool["result"]["bytes"] if tool["result"] else 0
        self.reads["bytes"] += size
        if not new:
            self.reads["reread_bytes"] += size
        seen.update(paths)
        self.files.update(paths)
        self.per_path.update(paths)

    def add_context(self, calls):
        """The context call by call, and its growth shared out to the tools
        whose results it carried."""
        measured = [c for c in calls if c["counts"]]
        sizes = [context_of(c["counts"]) for c in measured]
        cached = sum(c["counts"][3] for c in measured)
        self.context = {"calls": len(sizes), "first": sizes[0] if sizes else 0, "peak": max(sizes, default=0),
                        "last": sizes[-1] if sizes else 0, "mean": round(sum(sizes) / len(sizes)) if sizes else 0,
                        "cached_share": round(cached / sum(sizes), 3) if sum(sizes) else 0,
                        "compactions": 0, "drops": 0, "growth": 0, "growth_from_tools_estimated": 0,
                        "growth_other_estimated": 0}
        for call, size, following in zip(measured, sizes, sizes[1:]):
            if following < size * (1 - DROP):
                self.context["drops"] += 1
                continue
            growth = max(0, following - size - call["counts"][4])
            self.context["growth"] += growth
            self.share_growth(call, growth)

    def share_growth(self, call, growth):
        answered = [t for t in call["tools"].values() if t["result"] is not None]
        if not answered:
            self.context["growth_other_estimated"] += growth
            return
        weights = [t["result"]["bytes"] for t in answered]
        total = sum(weights) or len(answered)
        shared = 0
        for tool, weight in zip(answered, weights if sum(weights) else [1] * len(answered)):
            part = round(growth * weight / total)
            self.by_tool[tool["name"]]["context_tokens_estimated"] += part
            shared += part
        self.context["growth_from_tools_estimated"] += growth
        self.context["growth_other_estimated"] += growth - shared

    def add_time(self, entries, calls):
        times = [t for t in (usage.moment(e.get("timestamp")) for e in entries) if t is not None]
        if times:
            self.started, self.ended = min(times), max(times)
            self.seconds["span"] = round(self.ended - self.started)
        self.seconds["active"] = usage.active_seconds(entries)
        self.seconds["thinking"] = round(sum(c["thinking_ms"] for c in calls) / 1000)
        # From the last line before a call, the answer it waited for or the
        # prompt, to the call's last line: the time the model took, its
        # thinking and its answer, as the transcript's own clock has it.
        waiting, last_answer, pending = 0, None, list(calls)
        for entry in entries:
            at = usage.moment(entry.get("timestamp"))
            if entry.get("type") != "assistant":
                last_answer = at if at is not None else last_answer
                continue
            if pending and pending[0]["at"] == at:
                call = pending.pop(0)
                if last_answer is not None and call["until"] is not None and call["until"] >= last_answer:
                    waiting += call["until"] - last_answer
        self.seconds["waiting_for_model"] = round(waiting)

    def record(self, session):
        usd, unpriced = economics.priced(self.models)
        tokens = economics.by_kind(self.models)
        tokens["total"] = sum(tokens.values())
        by_tool = {name: {k: round(v) for k, v in row.items()} for name, row in sorted(self.by_tool.items())}
        return {
            "schema": SCHEMA, "session": usage.session_token(session), "helpers": self.helpers,
            "started_at": stamp(self.started), "ended_at": stamp(self.ended),
            "prompts": self.prompts, "attachments": self.attachments,
            "seconds": {k: round(v) for k, v in self.seconds.items()},
            "models": {m: list(c) for m, c in sorted(self.models.items())},
            "tokens": tokens, "estimated_usd": round(usd, 4), "tokens_unpriced": unpriced,
            "prices_as_of": economics.PRICES_AS_OF,
            "context": dict(self.context),
            "calls": {"total": self.calls["total"], "failed": self.calls["failed"],
                      "unanswered": self.calls["unanswered"], "by_tool": by_tool},
            "shell": {k: self.shell[k] for k in SHELL_USES},
            "reads": {**{k: self.reads[k] for k in ("calls", "files_named")}, "files": len(self.files),
                      **{k: self.reads[k] for k in ("rereads", "partial", "bytes", "reread_bytes")}},
        }


def id_of(call, tool):
    return next(k for k, v in call["tools"].items() if v is tool)


def stamp(moment):
    if moment is None:
        return None
    from datetime import datetime, timezone
    return datetime.fromtimestamp(moment, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def profile(transcript, helpers=True):
    """The record of one session: its transcript and, by default, its
    helpers' beside it."""
    built = Profile()
    built.add_transcript(list(usage.transcript_lines(transcript)), main=True)
    if helpers:
        for helper in usage.helper_transcripts(transcript):
            built.helpers += 1
            built.add_transcript(list(usage.transcript_lines(helper)), main=False)
    return built.record(Path(transcript).stem), built


# --- the report ---------------------------------------------------------------------

def share(part, whole):
    return f"{100 * part / whole:.0f}%" if whole else "n/a"


def report(record):
    """The record as a person reads it."""
    seconds, context, calls, reads, tokens = (record[k] for k in ("seconds", "context", "calls", "reads", "tokens"))
    lines = [f"Profile of session {record['session']} ({record['started_at']} to {record['ended_at']}, "
             f"{record['helpers']} helper{'s' if record['helpers'] != 1 else ''}, {record['prompts']} prompts, "
             f"{record['attachments']} attachments)",
             f"Time: span {seconds['span']:,} s, active {seconds['active']:,} s, in tools {seconds['in_tools']:,} s "
             f"({share(seconds['in_tools'], seconds['active'])} of active), waiting for the model "
             f"{seconds['waiting_for_model']:,} s ({share(seconds['waiting_for_model'], seconds['active'])}), "
             f"of which thinking {seconds['thinking']:,} s",
             f"Tokens: input {tokens['input']:,}, cache writes {tokens['cache_write']:,}, cache reads "
             f"{tokens['cache_read']:,}, output {tokens['output']:,}; estimated USD {record['estimated_usd']:.2f} "
             f"at list prices of {record['prices_as_of']} ({', '.join(record['models']) or 'no model'})",
             f"Context: {context.get('calls', 0):,} API calls, first {context.get('first', 0):,} tokens, peak "
             f"{context.get('peak', 0):,}, last {context.get('last', 0):,}, mean {context.get('mean', 0):,}; "
             f"{share(context.get('cached_share', 0), 1)} served from cache; {context.get('compactions', 0)} "
             f"compactions, {context.get('drops', 0)} drops; grew by {context.get('growth', 0):,} tokens, "
             f"about {context.get('growth_from_tools_estimated', 0):,} from tool results",
             f"Tool calls: {calls['total']:,}, {calls['failed']:,} failed, {calls['unanswered']:,} unanswered"]
    lines.append(f"  {'tool':34} {'calls':>6} {'failed':>6} {'in KB':>8} {'out KB':>8} {'seconds':>8} {'context':>10}")
    for name, row in calls["by_tool"].items():
        lines.append(f"  {name[:34]:34} {row['calls']:>6,} {row['failed']:>6,} {row['input_bytes'] / 1024:>8.1f} "
                     f"{row['result_bytes'] / 1024:>8.1f} {row['seconds_in_tool']:>8,} "
                     f"{row['context_tokens_estimated']:>10,}")
    shell = record["shell"]
    lines.append("Shell commands: " + ", ".join(f"{k} {shell[k]:,}" for k in SHELL_USES))
    lines.append(f"Reads: {reads['calls']:,} calls naming {reads['files_named']:,} files ({reads['files']:,} "
                 f"distinct), {reads['rereads']:,} re-reads ({share(reads['rereads'], reads['files_named'])}), "
                 f"{reads['partial']:,} partial; {reads['bytes'] / 1024:,.1f} KB returned, "
                 f"{reads['reread_bytes'] / 1024:,.1f} KB of it by calls that only re-read")
    return "\n".join(lines) + "\n"


def most_read(built, count):
    rows = sorted(built.per_path.items(), key=lambda item: (-item[1], item[0]))[:count]
    return "".join(f"{n:>5}  {path}\n" for path, n in rows)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 tools/profile.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("transcript", help="a session's transcript (.jsonl)")
    parser.add_argument("--json", help="write the record here, aggregates only")
    parser.add_argument("--paths", type=int, default=0, help="also print the N files read most often")
    parser.add_argument("--no-helpers", action="store_true", help="leave the helpers' transcripts out")
    args = parser.parse_args(argv)
    if not Path(args.transcript).is_file():
        print(f"profile: no transcript at {args.transcript}", file=sys.stderr)
        return 2
    record, built = profile(args.transcript, helpers=not args.no_helpers)
    sys.stdout.write(report(record))
    if args.paths:
        sys.stdout.write(f"Files read most often (not in the record):\n{most_read(built, args.paths)}")
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="ascii")
        print(f"record written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
