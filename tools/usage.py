"""What Claude spends on this repository's work, recorded beside the work,
for the metrics workflow to add up (docs/setup/metrics.md, Economics).

Two kinds of run spend tokens here, and each leaves its usage where the
metrics workflow can read it with GITHUB_TOKEN alone:

  A session, a person's or a routine's, local or in the cloud. Claude
  Code runs `python3 tools/usage.py hook` as a PreToolUse hook on Bash
  (.claude/settings.json). When the call is a git commit, it reads the
  session's transcript, and its helpers' (the subagents' transcripts
  beside it), and leaves the session's usage so far in the git directory;
  the commit-msg hook, which the session-start hook installs where no
  other commit-msg hook is, then runs `python3 tools/usage.py trailer
  FILE`, which adds the usage since the session's last commit to the
  commit as one trailer line:

      Symphony-Usage: v1 session=6e4cb20b seconds=842 claude-opus-5-5=120,3400,0,52000,9100

  per model, the uncached input tokens, the cache writes kept five
  minutes and an hour, the cache reads and the output tokens; seconds is
  the time the session was at work between the two commits, gaps of more
  than five minutes left out. The line travels with the commit, so it
  needs no API, which a cloud session or a routine does not have, and the
  metrics workflow reads it from the pull request's commits. What a
  session spends after its last commit is not on any commit, and so not
  counted. The same two hooks add a second line, Symphony-Profile, the
  session's profile since its last commit by tools/profile.py, whose
  docstring gives it: counts of calls, reads, the context and seconds in
  tools, for the research programme in docs/research/beyond-cooperation/.
  It never stands in the usage line's way: the hook leaves the usage
  before it reads the profile, which takes longer, and a profile that
  cannot be read leaves that one commit without the line, the next
  commit's line counting from the last commit that carried one; a last
  commit whose profile is not known, made before the line existed, leaves
  the next commit without it. The counts written on a session's last
  commit are kept in the clone's common git directory, which its linked
  worktrees share, so a session that commits from two of them counts
  nothing twice.

  A run in GitHub Actions: a worker's, the coordinator's or @claude's.
  After claude-code-action the workflow runs `python3 tools/usage.py
  actions`, which reads the action's execution file, the Agent SDK's
  messages, and writes the run's record as JSON, which the workflow
  uploads as an artifact whose name starts with symphony-usage-; the
  metrics workflow lists and reads those artifacts. The workflow runs a
  copy of this file made before Claude starts, with --root naming the
  checkout, since the run may leave the checkout on a branch older than
  this file; profile.py, economics.py and the protocol library are copied
  beside it where the checkout has them, and the record then carries the
  run's profile too, the counts of a commit's Symphony-Profile line over
  the whole run. Inside Actions the hook and the trailer record nothing,
  so a run is never counted twice.

Nothing is recorded while the metrics switch is off (the word off in
.github/symphony-metrics, or SDLC_METRICS=off in the environment). No
word of the conversation is kept: token counts by model, seconds, turns,
the profile's counts, the first eight characters of the session's id,
and, for a run in Actions, which job ran and for which worker, issue and
pull request. A hook never stops the session or the commit: whatever it
cannot read, it leaves alone, and it always exits 0.
"""

import functools
import importlib.util
import json
import os
import re
import shlex
import stat
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

TRAILER_KEY = "Symphony-Usage"
TRAILER_VERSION = "v1"
# The trailer's line, its value read to the line's end and split on
# blanks: a lazy value followed by optional blanks before the end of the
# line would be tried at every blank of a long run of them, and anyone who
# can push writes a commit's message, which the metrics run reads.
TRAILER_LINE = re.compile(r"(?im)^[ \t]*symphony-usage:[ \t]*v1[ \t]+(.+)$")
# The five counts of a model's usage, in the order the trailer writes them.
FIELDS = ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")
# A model's name as a trailer or an Actions run's record may give it:
# letters, digits, dots, colons, dashes and a tag in brackets such as [1m],
# at most 81 characters, as the SDK names its models. A record anyone
# uploads may name anything, and reading a name for the price table
# (economics.normalized) takes time with the square of a run of brackets.
MODEL_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:\[\]-]{0,80}")
# A pause longer than this between two lines of a transcript is time
# nobody was at work, and is left out of a session's seconds.
IDLE_GAP = 300
# A usage left by the hook belongs to the commit that follows it within
# this long; an older one is a commit that never happened.
PENDING_FRESH = 600
# How far past a << its delimiter is looked for: a delimiter is one word,
# and reading the rest of a long line for each << on it took time with the
# square of the line.
DELIMITER_REACH = 1024
# git's scissors line, below which a commit made with -v or commit.verbose
# carries its diff in the editor's template and where git cuts the message:
# the comment string, then 24 dashes, >8 and 24 dashes.
SCISSORS = re.compile(r"(?m)^\S{1,16} -{24} >8 -{24}$")
SWITCH_FILES = (".github/symphony-metrics", ".github/sdlc-metrics")
SWITCH_FILE = SWITCH_FILES[0]
SWITCH_VARIABLE = "SDLC_METRICS"
HOOK_MARKER = "symphony-usage"
SYNTHETIC = "<synthetic>"
COMMIT_MSG_HOOK = """#!/bin/sh
# symphony-usage: adds the Claude Code session's usage and profile since
# its last commit to this commit as the Symphony-Usage and Symphony-Profile
# trailers (tools/usage.py). It never stops a commit.
root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -f "$root/tools/usage.py" ] || exit 0
python3 "$root/tools/usage.py" trailer "$1" >/dev/null 2>&1 || true
exit 0
"""


# --- the switch ---------------------------------------------------------------

def first_word(text):
    words = (text or "").split()
    return words[0].lower() if words else ""


def sharing_off(root=ROOT, environ=None):
    """Whether the metrics switch is off, by the rule tools/metrics.py
    reads it with (its sharing): the variable SDLC_METRICS, in the
    environment, is off with any word but on; the file, the new name or
    the old, is on only with the word on first, says nothing when missing,
    and is off when it says anything else or cannot be read, an off in
    either file winning over an on in the other. A person who wants no
    usage of theirs on their commits sets SDLC_METRICS=off in their own
    environment. Not imported from metrics, since this runs before every
    git commit and must stay quick."""
    environ = os.environ if environ is None else environ
    said = first_word(environ.get(SWITCH_VARIABLE))
    if said and said != "on":
        return True
    for name in SWITCH_FILES:
        try:
            text = (Path(root) / name).read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        except (OSError, UnicodeDecodeError):
            return True
        if first_word(text) != "on":
            return True
    return False


def in_actions(environ=None):
    environ = os.environ if environ is None else environ
    return environ.get("GITHUB_ACTIONS") == "true"


# --- reading usage ------------------------------------------------------------

def zero():
    return [0] * len(FIELDS)


def counts_of(usage):
    """The five counts of one message's usage, as the API reports it: the
    cache writes split by how long they are kept where the API says so,
    and all at five minutes where it does not."""
    usage = usage or {}
    written = usage.get("cache_creation_input_tokens") or 0
    split = usage.get("cache_creation") or {}
    hour = split.get("ephemeral_1h_input_tokens") or 0
    five = split.get("ephemeral_5m_input_tokens")
    five = written - hour if five is None else five
    return [int(usage.get("input_tokens") or 0), int(five or 0), int(hour or 0),
            int(usage.get("cache_read_input_tokens") or 0), int(usage.get("output_tokens") or 0)]


def add(totals, model, counts):
    row = totals.setdefault(model, zero())
    for index, value in enumerate(counts):
        row[index] += value


def transcript_lines(path):
    """Every JSON object of a transcript, one a line; a line that is not
    one, a transcript still being written, is passed over, and so is a
    line with a byte that is not UTF-8, as where a read ends inside a
    character Claude Code is still writing, which would otherwise stop the
    whole read."""
    try:
        with open(path, "rb") as stream:
            for line in stream:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if isinstance(entry, dict):
                    yield entry
    except OSError:
        return


def message_usage(entries):
    """Each assistant message's model and counts, by the message's id: a
    message written as several lines, one per block, carries the same usage
    on each, so it counts once."""
    found = {}
    for entry in entries:
        message = entry.get("message") if entry.get("type") == "assistant" else None
        if not isinstance(message, dict) or not message.get("usage"):
            continue
        model = message.get("model") or "unknown"
        if model == SYNTHETIC:
            continue
        key = message.get("id") or entry.get("requestId") or entry.get("uuid")
        found[key] = (model, counts_of(message.get("usage")))
    return found


def helper_transcripts(transcript):
    """The subagents' transcripts of a session, kept in a folder named for
    the session beside its own transcript."""
    folder = Path(transcript).with_suffix("") / "subagents"
    return sorted(folder.glob("*.jsonl")) if folder.is_dir() else []


def active_seconds(entries):
    """The seconds a session was at work: the time between consecutive
    lines, pauses longer than IDLE_GAP left out."""
    times = sorted(t for t in (moment(e.get("timestamp")) for e in entries) if t is not None)
    return int(sum(gap for gap in (b - a for a, b in zip(times, times[1:])) if gap <= IDLE_GAP))


def moment(text):
    try:
        return datetime.fromisoformat(str(text).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def session_usage(transcript):
    """A session's usage so far: by model, the five counts summed over its
    messages and its helpers', and its seconds at work."""
    main = list(transcript_lines(transcript))
    messages = message_usage(main)
    for helper in helper_transcripts(transcript):
        messages.update(message_usage(transcript_lines(helper)))
    totals = {}
    for model, counts in messages.values():
        add(totals, model, counts)
    return {"models": totals, "seconds": active_seconds(main)}


def since(now, before):
    """What a session spent since the usage last written on a commit."""
    models = {}
    for model, counts in now["models"].items():
        earlier = (before.get("models") or {}).get(model) or zero()
        delta = [max(0, a - b) for a, b in zip(counts, earlier)]
        if any(delta):
            models[model] = delta
    return {"models": models, "seconds": max(0, now["seconds"] - int(before.get("seconds") or 0))}


# --- the trailer ----------------------------------------------------------------

def session_token(session):
    """The eight characters of a session's id the trailer carries, enough to
    tell a repository's sessions apart and no more: the id without a
    leading session_, as a claude.ai one has, and only its letters, digits
    and dashes."""
    return re.sub(r"[^A-Za-z0-9-]", "", re.sub(r"^session_", "", str(session or "")))[:8]


def trailer(session, spent):
    """The trailer's value for what a session spent, models in name order."""
    parts = [TRAILER_VERSION, f"session={session_token(session)}", f"seconds={spent['seconds']}"]
    parts += [f"{model}={','.join(str(n) for n in counts)}" for model, counts in sorted(spent["models"].items())]
    return " ".join(parts)


def count_in(text):
    """A trailer's count as a whole number, or None when it spells none: ASCII
    digits below 2 ** 53, the bound the Actions records are read with
    (economics.actions_record), since anyone who can push writes a commit's
    message and int() refuses more than 4,300 digits with an error."""
    return int(text) if re.fullmatch(r"[0-9]{1,16}", text) and int(text) < 2 ** 53 else None


def parse_trailer(text):
    """Every Symphony-Usage trailer in a commit message, as (session,
    seconds, {model: counts}); a part that cannot be read is passed over."""
    found = []
    for match in TRAILER_LINE.finditer(text or ""):
        session, seconds, models = "", 0, {}
        for part in match.group(1).split():
            key, _, value = part.partition("=")
            if key == "session":
                session = value
            elif key == "seconds" and count_in(value) is not None:
                seconds = count_in(value)
            elif MODEL_KEY.fullmatch(key):
                counts = [count_in(n) for n in value.split(",")]
                if len(counts) == len(FIELDS) and None not in counts:
                    models[key] = counts
        found.append((session, seconds, models))
    return found


def git(*args, cwd=None):
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=30)
    if done.returncode != 0:
        raise OSError(done.stderr.strip() or f"git {args[0]} failed")
    return done.stdout.strip()


def state_dir(cwd=None):
    """Where the hook leaves what it read for the commit that follows,
    inside the git directory, so no clone ever commits it."""
    folder = Path(git("rev-parse", "--absolute-git-dir", cwd=cwd)) / "symphony" / "usage"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def kept_dir(cwd=None):
    """Where the counts written on a session's last commit are kept: the
    clone's common git directory, the same folder as state_dir's in the
    clone's own worktree, and shared by its linked worktrees, each of
    which has a git directory of its own, so that a session committing
    from two of them counts each call once."""
    try:
        common = git("rev-parse", "--git-common-dir", cwd=cwd)
    except OSError:
        return state_dir(cwd)
    folder = (Path(cwd or os.getcwd()) / common).resolve() / "symphony" / "usage"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def write_json(path, data):
    temporary = Path(str(path) + ".part")
    temporary.write_text(json.dumps(data), encoding="utf-8")
    temporary.replace(path)


def read_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


# --- the hook and the commit-msg hook -------------------------------------------

def without_heredocs(command):
    """The command with its here-document bodies left out, since they are
    data the command reads, not commands the shell runs: a commit message
    written in one, with an apostrophe in it, would read as a quote left
    open and hide the git commit that follows it. (A body whose delimiter
    is not quoted can still run a $( ) of its own, left out with it.) A
    command with no << has none and is not read, since reading a long one a
    character at a time is most of what a here-document costs
    tools/profile.py's reading of a session."""
    text = str(command)
    if "<<" not in text:
        return text
    kept, at = [], 0
    for start, end in heredoc_bodies(text):
        kept.append(text[at:start])
        at = end
    kept.append(text[at:])
    return "".join(kept)


@dataclass(slots=True)
class Frame:
    """What the reading of a command holds open at one depth of $( ): the
    quote, how deep in arithmetic it is, how many ( it has open, and the
    here-documents opened at this depth, each a delimiter and whether its
    body's leading tabs go (<<-), whose bodies wait for a newline."""
    quote: str | None = None
    arithmetic: int = 0
    parens: int = 0
    waiting: list = field(default_factory=list)


def heredoc_bodies(text):
    """Where the bodies of a command's here-documents lie, each span from
    the newline after the operators to the end of the last delimiter. The
    command is read whole, as bash reads it: a << in quotes, in a <<<
    here-string, in arithmetic, $(( )) or (( )), or in a comment opens
    nothing, on a line a string carries on from an earlier one too; each $(
    reads quotes and operators anew, inside double quotes too, where Claude
    Code writes its commit messages; and the bodies of the here-documents a
    $( opens follow the first newline inside it, or, where it closes on the
    line that opens them, the newline after it."""
    from sdlc_protocol import guard
    frames, i, word_start = [Frame()], 0, True
    while i < len(text):
        frame, ch = frames[-1], text[i]
        if ch == "\\" and frame.quote != "'":
            # An escaped character is part of a word; a backslash-newline is
            # the line continuation the shell takes out, word and all.
            word_start = word_start and text.startswith("\n", i + 1)
            i += 2
            continue
        if frame.quote:
            step = inside_quotes(text, i, frames)
        elif ch == "#" and word_start:
            step = line_end(text, i) - i
        elif ch == "\n" and frame.waiting:
            end, frame.waiting = past_bodies(text, i + 1, frame.waiting, len(frames) > 1)
            yield i, end
            step = end - i
        else:
            step = outside_quotes(text, i, frames)
        word_start = text[i + step - 1] in guard.WORD_BREAKS
        i += step


def inside_quotes(text, i, frames):
    """One step of the reading inside quotes, and its length: the quote's
    own character closes it, and inside double quotes $( opens a frame,
    while $(( is arithmetic."""
    frame = frames[-1]
    if frame.quote == '"' and text.startswith("$((", i):
        return 3
    if frame.quote == '"' and text.startswith("$(", i):
        frames.append(Frame())
        return 2
    if text[i] == frame.quote:
        frame.quote = None
    return 1


def outside_quotes(text, i, frames):
    """One step of the reading outside quotes, and its length: a quote
    opens; $( opens a frame, and the ) that closes it hands the
    here-documents it left waiting to the frame around it; arithmetic and
    ( nest; and a << that is neither a <<< nor in arithmetic opens a
    here-document, whose delimiter is looked for within reach on its line."""
    frame, ch = frames[-1], text[i]
    if ch in "'\"":
        frame.quote = ch
    elif text.startswith("$((", i):
        frame.arithmetic += 1
        return 3
    elif text.startswith("$(", i):
        frames.append(Frame())
        return 2
    elif text.startswith("((", i):
        frame.arithmetic += 1
        return 2
    elif frame.arithmetic and text.startswith("))", i):
        frame.arithmetic -= 1
        return 2
    elif ch == "(":
        frame.parens += 1
    elif ch == ")" and frame.parens:
        frame.parens -= 1
    elif ch == ")" and len(frames) > 1:
        frames.pop()
        frames[-1].waiting.extend(frame.waiting)
    elif text.startswith("<<<", i):
        return 3
    elif text.startswith("<<", i) and not frame.arithmetic:
        heredoc = delimiter_of(text[i + 2:i + 2 + DELIMITER_REACH].split("\n", 1)[0])
        if heredoc:
            frame.waiting.append(heredoc)
        return 2
    return 1


def line_end(text, i):
    """Where the line holding text[i] ends: its newline, or the text's end."""
    end = text.find("\n", i)
    return len(text) if end == -1 else end


def past_bodies(text, at, waiting, in_substitution):
    """Where the command goes on after the bodies of the here-documents
    waiting at a newline, the first body starting at at, and those still
    waiting: the bodies follow in order, each up to its delimiter's line,
    the last ending at its delimiter, and one the command ends inside runs
    to its end; inside $( ) a body may also end at its delimiter followed by
    the ) that closes it, as bash 5.2 takes it, and the command goes on
    there, any here-documents after it left for the frame around."""
    end = at
    for index, (word, dashed) in enumerate(waiting):
        while True:
            if at >= len(text):
                return len(text), []
            stop = line_end(text, at)
            closing = delimiter_length(text[at:stop], word, dashed, in_substitution)
            if closing is not None:
                break
            at = stop + 1
        end = at + closing
        if end < stop:
            return end, waiting[index + 1:]
        at = stop + 1
    return end, []


def delimiter_length(line, word, dashed, in_substitution):
    """How much of a line closes a here-document's body, or None: the whole
    line where it is the delimiter alone, after its leading tabs for <<-,
    and inside $( ) the delimiter that blanks and a ) follow."""
    body = line.lstrip("\t") if dashed else line
    if body == word:
        return len(line)
    if in_substitution and body.startswith(word) and body[len(word):].lstrip(" \t").startswith(")"):
        return len(line) - len(body) + len(word)
    return None


def delimiter_of(rest):
    """The word after a <<, as the shell reads it, and whether a - joined to
    the << (<<-) takes the body's leading tabs away; None where no word
    follows. Its quotes or a backslash only make the body literal, and a
    carriage return, as a command written with CRLF line ends has, is part
    of the word, as it is to bash."""
    dashed = rest.startswith("-")
    lexer = shlex.shlex(rest[1:] if dashed else rest, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.whitespace = " \t"
    lexer.commenters = ""
    try:
        word = next(iter(lexer), "")
    except ValueError:
        return None
    if not word or all(ch in "();<>|&" for ch in word):
        return None
    return word, dashed


def is_commit(command):
    """Whether a shell command runs git commit, in any simple command of it,
    its here-documents' bodies left out as data."""
    return commit_arguments(command) is not None


def commit_arguments(command):
    """The words after commit in the first simple command of a shell
    command that runs git commit, or None where none does."""
    from sdlc_protocol import guard
    for argv in guard.simple_commands(without_heredocs(command or "")):
        words = [word for word in argv if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", word)]
        if not words or os.path.basename(words[0]) != "git":
            continue
        rest = words[1:]
        while rest and rest[0].startswith("-"):
            rest = rest[2:] if rest[0] in ("-c", "-C") else rest[1:]
        if rest and rest[0] == "commit":
            return rest[1:]
    return None


def strips_comments(arguments):
    """Whether git takes the comment lines out of the message of a commit
    made with these arguments: as its --cleanup says, else where git opens
    the editor, for a commit given no message by -m or -F or told to edit
    one, whose message is then the editor's template; a message given keeps
    them, a line such as "#42 fix login" its subject. Short options run
    together count, as -am does, with the flags that take no value first,
    an e among them opening the editor as -e does."""
    cleanup, given, edits = None, False, False
    words = iter(arguments)
    for word in words:
        if word == "--":
            break
        if word == "--cleanup":
            cleanup = next(words, None)
        elif word.startswith("--cleanup="):
            cleanup = word.partition("=")[2]
        elif word in ("-e", "--edit"):
            edits = True
        elif word in ("--message", "--file") or word.startswith(("--message=", "--file=")):
            given = True
        elif run := re.fullmatch(r"-([apsenqvioz]*)[mF].*", word):
            given, edits = True, edits or "e" in run[1]
    if cleanup in ("strip", "scissors"):
        return True
    if cleanup in ("verbatim", "whitespace"):
        return False
    return edits or not given


def run_hook(payload, environ=None):
    """The PreToolUse hook: before a git commit, leave the session's usage
    so far for the commit-msg hook, then its profile so far beside it.
    Silent, and never in the way: the usage is left first, so that a hook
    stopped while it reads the profile, at Claude Code's timeout for a
    hook, still leaves the usage for the commit."""
    if not isinstance(payload, dict) or in_actions(environ):
        return
    command = (payload.get("tool_input") or {}).get("command") if isinstance(payload.get("tool_input"), dict) else ""
    transcript, session = payload.get("transcript_path"), payload.get("session_id")
    arguments = commit_arguments(command) if transcript and session else None
    if arguments is None:
        return
    cwd = payload.get("cwd") or None
    root = git("rev-parse", "--show-toplevel", cwd=cwd)
    if sharing_off(root, environ):
        return
    pending = state_dir(cwd) / "pending.json"
    left = {"session": str(session), "at": time.time(), "strips": strips_comments(arguments),
            **session_usage(transcript)}
    write_json(pending, left)
    profiled = profile_so_far(transcript)
    # Another session's hook in the same clone may have left its own usage
    # while this one read the profile; that one's commit comes next.
    again = read_json(pending) or {}
    if profiled is not None and (again.get("session"), again.get("at")) == (left["session"], left["at"]):
        write_json(pending, {**left, "profile": profiled})


def run_trailer(message_file, cwd=None, environ=None, now=None):
    """The commit-msg hook's step: add to the commit the usage and the
    profile the hook left since the session's last commit, and remember
    them as written. A commit with nothing spent since the last carries no
    line. It remembers nothing when its hook read nothing at all, a
    transcript not there for that one hook, so the next line counts from
    the last; and it remembers the counts read when they fell below those
    remembered, a transcript replaced under the session, so the lines after
    it count on from there rather than wait for the session to spend past
    the old counts."""
    if in_actions(environ):
        return
    folder = state_dir(cwd)
    pending = read_json(folder / "pending.json")
    now = time.time() if now is None else now
    if not pending or now - float(pending.get("at") or 0) > PENDING_FRESH:
        return
    if says_nothing(message_file, cwd, strips=pending.get("strips") is not False):
        return
    (folder / "pending.json").unlink(missing_ok=True)
    session = re.sub(r"[^A-Za-z0-9-]", "", str(pending.get("session")))
    if not session:
        return
    written = kept_dir(cwd) / f"{session}.json"
    before = read_json(written) or {}
    spent = since(pending, before)
    if not spent["models"] and not pending.get("models"):
        return
    profiled, profile_kept = profile_line(session, pending.get("profile"), before)
    state = {"models": pending.get("models") or {}, "seconds": pending.get("seconds") or 0}
    if profile_kept is not None:
        state["profile"] = profile_kept
    write_json(written, state)
    if not spent["models"]:
        return
    lines = [f"{TRAILER_KEY}: {trailer(session, spent)}"]
    if profiled:
        lines.append(profiled)
    add_trailers(message_file, lines, cwd)


def says_nothing(message_file, cwd=None, strips=True):
    """Whether a commit's message says nothing as git reads it: blanks
    alone, or, where git takes the comments out (strips_comments), blanks
    and comments above its scissors line, as a bare git commit's message is
    where the editor is true, as in Claude Code's shell. git refuses such a
    commit once the hooks are done, but the lines added to it would give it
    a message, the usage line its subject; so nothing is added, and the
    usage waits for the commit that follows. git strips by its own rules,
    with the comment string its config names; the text goes to it as UTF-8
    whatever the locale, since nothing is written back from it."""
    try:
        text = Path(message_file).read_text(encoding="utf-8", errors="replace")
        if not strips:
            return not text.strip()
        done = subprocess.run(["git", "stripspace", "--strip-comments"], input=SCISSORS.split(text, maxsplit=1)[0],
                              cwd=cwd, capture_output=True, encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return done.returncode == 0 and not done.stdout.strip()


def add_trailers(message_file, lines, cwd=None):
    """Add the trailer lines to the commit's message by git's own rules for
    a trailer block, or at its end where git cannot. A message whose last
    line has no newline, as git merge leaves a merge's, is given one first:
    git interpret-trailers would join the lines to that line, with no blank
    line between, the usage line part of the merge's subject."""
    end_last_line(message_file)
    try:
        git("interpret-trailers", "--in-place", *[arg for line in lines for arg in ("--trailer", line)],
            str(message_file), cwd=cwd)
    except OSError:
        with open(message_file, "a", encoding="utf-8") as stream:
            stream.write("\n" + "".join(f"{line}\n" for line in lines))


def end_last_line(path):
    try:
        data = Path(path).read_bytes()
        if data and not data.endswith(b"\n"):
            with open(path, "ab") as stream:
                stream.write(b"\n")
    except OSError:
        pass


# --- the profile beside the usage -------------------------------------------------

@functools.lru_cache(maxsize=None)
def profiler():
    """tools/profile.py, which reads a session's profile for its line,
    loaded once by its path beside this file, since the standard library
    has a module of the same name, which a test run under cProfile has
    already imported; loaded only when a profile is read, so that this
    file alone still records a run in Actions, from the copy each workflow
    makes of it."""
    spec = importlib.util.spec_from_file_location("symphony_profile", TOOLS / "profile.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def profile_so_far(transcript):
    """The session's profile counts so far, or None when they cannot be read."""
    try:
        return profiler().session_counts(transcript)
    except Exception:
        return None


def run_profile(execution_file):
    """A run's profile, the same counts as a commit's line over the whole
    execution file, or None when they cannot be read, as where the workflow
    copied this file without profile.py; the file has no clock, so its
    seconds in tools are nothing."""
    try:
        profile = profiler()
        return profile.since(profile.session_counts(execution_file), {})
    except Exception:
        return None


def profile_line(session, now, before):
    """The Symphony-Profile line for the profile since the session's last
    commit that carried one, and the counts to keep for the next commit.
    No profile read now gives no line and keeps the counts kept before, so
    the next line counts this commit's calls too. A last commit recorded
    without a profile, by a hook older than the line, gives no line, since
    the counts since it are not known and this line would claim them all,
    and starts the count from now; so do counts kept before that cannot be
    read."""
    earlier = before.get("profile") if before else {}
    earlier = earlier if isinstance(earlier, dict) else None
    if not isinstance(now, dict):
        return None, earlier
    try:
        profile = profiler()
        kept = profile.kept(now)
        if earlier is None or not profile.known(earlier):
            return None, kept
        return f"{profile.TRAILER_KEY}: {profile.trailer(session, profile.since(now, earlier))}", kept
    except Exception:
        return None, earlier


def hooks_dir(cwd=None):
    """Where git looks for this clone's hooks: core.hooksPath when set,
    else the git directory's hooks."""
    try:
        configured = git("config", "core.hooksPath", cwd=cwd)
    except OSError:
        configured = ""
    if configured:
        top = git("rev-parse", "--show-toplevel", cwd=cwd)
        return (Path(top) / Path(configured).expanduser()).resolve()
    return Path(git("rev-parse", "--absolute-git-dir", cwd=cwd)) / "hooks"


def install(cwd=None, environ=None):
    """Put the commit-msg hook in place, unless the switch is off, the run is
    in GitHub Actions, whose runs record their usage as an artifact, or the
    clone has a commit-msg hook of its own, which is left as it is. What
    was done, in a line."""
    if in_actions(environ):
        return "usage: in GitHub Actions the run's record is uploaded instead; no commit-msg hook"
    root = git("rev-parse", "--show-toplevel", cwd=cwd)
    if sharing_off(root, environ):
        return "usage: the metrics switch is off; no commit-msg hook"
    path = hooks_dir(cwd) / "commit-msg"
    if path.exists() and HOOK_MARKER not in path.read_text(encoding="utf-8", errors="replace"):
        return f"usage: {path} is the clone's own commit-msg hook; left as it is, and no usage is recorded"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(COMMIT_MSG_HOOK, encoding="ascii")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return f"usage: commit-msg hook in place at {path}"


# --- a run in Actions -------------------------------------------------------------

def result_of(messages):
    """The SDK's result message, the last of the run's messages, or {}."""
    for message in reversed(messages if isinstance(messages, list) else []):
        if isinstance(message, dict) and message.get("type") == "result":
            return message
    return {}


def run_models(messages, result):
    """A run's counts by model: the result's modelUsage where the SDK gives
    it, with its cache writes at five minutes, else the assistant messages'
    own usage, summed once per message."""
    by_model = result.get("modelUsage")
    if isinstance(by_model, dict) and by_model:
        totals = {}
        for model, used in by_model.items():
            if isinstance(used, dict):
                add(totals, model, [int(used.get("inputTokens") or 0), int(used.get("cacheCreationInputTokens") or 0), 0,
                                    int(used.get("cacheReadInputTokens") or 0), int(used.get("outputTokens") or 0)])
        return totals
    totals = {}
    for model, counts in message_usage(m for m in messages if isinstance(m, dict)).values():
        add(totals, model, counts)
    return totals


def actions_record(messages, job, workflow, worker="", issue=None, pull=None, at=None):
    """The record of one run in Actions, from the execution file's messages."""
    result = result_of(messages)
    return {
        "v": 1, "source": "actions", "workflow": workflow, "job": job, "worker": worker or "",
        "issue": issue, "pull": pull,
        "at": at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "seconds": round((result.get("duration_ms") or 0) / 1000, 1),
        "api_seconds": round((result.get("duration_api_ms") or 0) / 1000, 1),
        "turns": int(result.get("num_turns") or 0),
        "reported_usd": float(result.get("total_cost_usd") or 0),
        "error": bool(result.get("is_error")) or not result,
        "models": run_models(messages if isinstance(messages, list) else [], result),
    }


def number_or_none(text):
    return int(text) if str(text or "").isdecimal() else None


# --- the command line -------------------------------------------------------------

def main(argv=None, stdin=None, environ=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    command = argv[0] if argv else ""
    try:
        if command == "hook":
            try:
                payload = json.load(stdin or sys.stdin)
            except ValueError:
                return 0
            run_hook(payload, environ)
        elif command == "trailer" and len(argv) == 2:
            run_trailer(argv[1], environ=environ)
        elif command == "install":
            print(install(environ=environ))
        elif command == "actions":
            return run_actions(argv[1:], environ)
        else:
            print("usage: python3 tools/usage.py hook|trailer FILE|install|actions --execution-file F --out F "
                  "--workflow W --job J [--worker W] [--issue N] [--pull N] [--root DIR]", file=sys.stderr)
            return 2
    # A hook never stands in a session's way, whatever went wrong.
    except Exception as problem:
        if command == "install":
            print(f"usage: {problem}")
    return 0


def run_actions(argv, environ=None):
    """Write the record of the run whose execution file is named, unless
    the switch is off; never a failure of the workflow."""
    import argparse
    parser = argparse.ArgumentParser(prog="python3 tools/usage.py actions")
    parser.add_argument("--execution-file", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--worker", default="")
    parser.add_argument("--issue", default="")
    parser.add_argument("--pull", default="")
    parser.add_argument("--root", default=str(ROOT),
                        help="the checkout whose metrics switch counts, when this file runs from a copy")
    args = parser.parse_args(argv)
    if sharing_off(args.root, environ):
        print("usage: the metrics switch is off; no record")
        return 0
    try:
        messages = json.loads(Path(args.execution_file).read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        print("usage: no execution file to read; no record")
        return 0
    record = actions_record(messages, args.job, args.workflow, args.worker,
                            number_or_none(args.issue), number_or_none(args.pull))
    profiled = run_profile(args.execution_file)
    if profiled is not None:
        record["profile"] = profiled
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="ascii")
    tokens = sum(sum(counts) for counts in record["models"].values())
    print(f"usage: {args.workflow}/{args.job}: {tokens} tokens in {record['seconds']} s, recorded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
