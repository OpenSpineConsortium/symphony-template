"""The handoff at the weekly limit: a session that sees its Claude account
at 90 percent of its seven-day window is told, once, to write a handoff a
fresh account resumes from, so swapping a whole account costs one read of
one committed file (docs/research/automatic-handoff.md).

Three parts, each a word of this script:

  The sensor. Claude Code gives a session's usage to two places a
  repository can reach: the status line's input, whose rate_limits carry
  five_hour and seven_day with used_percentage and resets_at, and the
  rate_limit_event of a headless run's stream-json, which hpcworker's
  auto mode already keeps on the grid as <account folder>.use.json beside
  the CLAUDE_CONFIG_DIR it runs in. `handoff.py statusline` is the status
  line command (.claude/settings.json): it keeps the reading in the git
  directory, as symphony-limits.json, and prints one short line. The
  grid's file is read where it is. A cloud session on claude.ai gets
  neither: its window is shown to the person and to no hook, so there the
  person says the word and the session runs the handoff skill by hand.

  The nudge. `handoff.py hook` runs on Stop, UserPromptSubmit and
  PostToolUse on Bash. When the newest reading that has not reset says the
  window is at or past the threshold, or the grid has written
  <account folder>.handoff-due because it is about to move the worker to
  another account, it tells the session once per window: as context while
  the session works, or, at the end of a turn, by holding the stop once so
  the session writes the handoff before it goes quiet. Nothing is said in
  GitHub Actions, where a run ends by itself and tools/pool.py's pick
  already passes over a slot at 90 percent.

  The handoff. `handoff.py new` writes the skeleton under
  docs/checkpoints/<date>/, with what git knows filled in and the rest
  marked to fill; the handoff skill (.claude/skills/handoff) fills it and
  lands it by pull request; `handoff.py done PATH` records it, refusing a
  file with a part left to fill, and on the grid writes
  <account folder>.handoff.json, which tells hpcworker the move may go
  ahead. `handoff.py latest` names the newest handoff for the session-start
  hook, so a session on the next account reads it first.

The switches, in the environment: SYMPHONY_HANDOFF=off stops the nudge;
SYMPHONY_HANDOFF_AT is the threshold in percent (default 90);
SYMPHONY_HANDOFF_WINDOW is seven_day (the default), five_hour or any.
No word of the conversation, no credential and no e-mail is read or kept:
the readings are percentages and reset times. A hook or the status line
never stops the session: whatever it cannot read it leaves alone, and it
exits 0.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WINDOWS = ("five_hour", "seven_day")
READING_FILE = "symphony-limits.json"
STATE_FILE = "symphony-handoff.json"
FILL = "<!-- fill -->"
STALE = timedelta(days=8)
RECENT = timedelta(hours=72)
HANDOFF_NAME = re.compile(r"^handoff(-\d{4})?\.md$")
DAY_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}[a-z]?(-[a-z0-9-]+)?$")


# Times and numbers.

def utc_now():
    return datetime.now(timezone.utc)


def iso(moment):
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(value):
    """An ISO time or unix seconds, as Claude Code and hpcworker write them, or None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str) and len(value) <= 40:
        try:
            moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
    return None


def fraction(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value:
        return None
    return max(0.0, min(float(value), 10.0))


def percent(used):
    return f"{round(used * 100)}%"


# Where things are kept.

def git_dir(root):
    """The clone's common git directory, which its worktrees share, or None."""
    try:
        found = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=root,
                               capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    path = found.stdout.strip()
    return Path(path) if found.returncode == 0 and path else None


def project_root(given=None):
    return Path(given or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def account_folder():
    """The grid's account folder, accounts/<N>, when Claude Code runs in one (hpcworker framework 21)."""
    folder = os.environ.get("CLAUDE_CONFIG_DIR")
    if not folder:
        return None
    path = Path(folder)
    return path if path.parent.name == "accounts" and path.name.isdigit() else None


def load_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            found = json.load(handle)
    except (OSError, ValueError):
        return None
    return found if isinstance(found, dict) else None


def write_json(path, record):
    """Written whole or not at all, so a reader never sees half a file."""
    part = Path(str(path) + ".part")
    part.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(part, path)


# Readings: {"source", "at", "windows": {name: {"utilization", "resetsAt"}}}.

def from_statusline(data, now):
    """The status line's rate_limits, whose percentages are 0 to 100, as a reading, or None."""
    limits = data.get("rate_limits") if isinstance(data, dict) else None
    if not isinstance(limits, dict):
        return None
    windows = {}
    for name in WINDOWS:
        each = limits.get(name)
        if not isinstance(each, dict):
            continue
        given = each.get("used_percentage")
        used = fraction(given / 100) if isinstance(given, (int, float)) and not isinstance(given, bool) else None
        resets = parse_time(each.get("resets_at"))
        if used is None:
            continue
        windows[name] = {"utilization": round(used, 4)}
        if resets is not None:
            windows[name]["resetsAt"] = iso(resets)
    return {"source": "statusline", "at": iso(now), "windows": windows} if windows else None


def from_grid(record):
    """hpcworker's <account folder>.use.json, which has tools/pool.py's shape, as a reading, or None."""
    if not isinstance(record, dict) or not isinstance(record.get("windows"), dict):
        return None
    windows = {}
    for name in WINDOWS:
        each = record["windows"].get(name)
        used = fraction(each.get("utilization")) if isinstance(each, dict) else None
        if used is None:
            continue
        windows[name] = {"utilization": round(used, 4)}
        resets = parse_time(each.get("resetsAt"))
        if resets is not None:
            windows[name]["resetsAt"] = iso(resets)
    at = parse_time(record.get("read_at"))
    if not windows or at is None:
        return None
    return {"source": "grid", "at": iso(at), "windows": windows}


def live(reading, now):
    """The reading less its windows that have reset, or None when it is too old or nothing is left."""
    if not isinstance(reading, dict):
        return None
    at = parse_time(reading.get("at"))
    if at is None or now - at > STALE or not isinstance(reading.get("windows"), dict):
        return None
    windows = {}
    for name, each in reading["windows"].items():
        if name not in WINDOWS or not isinstance(each, dict) or fraction(each.get("utilization")) is None:
            continue
        resets = parse_time(each.get("resetsAt"))
        if resets is not None and resets <= now:
            continue
        windows[name] = each
    return dict(reading, windows=windows) if windows else None


def readings(root, now):
    """Every live reading this session can see, the newest first."""
    found = []
    gdir = git_dir(root)
    if gdir is not None:
        found.append(load_json(gdir / READING_FILE))
    folder = account_folder()
    if folder is not None:
        found.append(from_grid(load_json(str(folder) + ".use.json")))
    found = [each for each in (live(reading, now) for reading in found) if each]
    return sorted(found, key=lambda each: each["at"], reverse=True)


# Whether the handoff is due.

def threshold():
    try:
        value = float(os.environ.get("SYMPHONY_HANDOFF_AT", "90"))
    except ValueError:
        value = 90.0
    return min(max(value, 1.0), 100.0) / 100


def watched_windows():
    word = os.environ.get("SYMPHONY_HANDOFF_WINDOW", "seven_day").strip()
    if word == "any":
        return WINDOWS
    return (word,) if word in WINDOWS else ("seven_day",)


def grid_due(now):
    """The grid's word that it is about to move this worker to another account, or None."""
    folder = account_folder()
    if folder is None:
        return None
    record = load_json(str(folder) + ".handoff-due")
    at = parse_time(record.get("at")) if record else None
    if at is None or now - at > STALE:
        return None
    done = load_json(str(folder) + ".handoff.json")
    done_at = parse_time(done.get("at")) if done else None
    if done_at is not None and done_at >= at:
        return None
    return {"window": "grid", "key": "grid:" + iso(at), "why": "the grid is about to move this worker to another account"}


def due(root, now, limit=None):
    """What makes the handoff due, or None: the grid's word first, else the fullest watched window."""
    word = grid_due(now)
    if word:
        return word
    limit = threshold() if limit is None else limit
    found = readings(root, now)
    if not found:
        return None
    newest = found[0]
    best = None
    for name in watched_windows():
        each = newest["windows"].get(name)
        used = fraction(each.get("utilization")) if each else None
        if used is not None and used >= limit and (best is None or used > best[1]):
            best = (name, used, each.get("resetsAt", ""))
    if best is None:
        return None
    name, used, resets = best
    label = "weekly" if name == "seven_day" else "five-hour"
    when = f", resetting {resets}" if resets else ""
    return {"window": name, "key": f"{name}:{resets}", "used": used,
            "why": f"this account's {label} limit is at {percent(used)}{when} ({newest['source']} reading)"}


# The nudge.

def message(word):
    return ("Symphony handoff: " + word["why"] + ". Before anything else, write the handoff a fresh account "
            "resumes from, with the handoff skill (.claude/skills/handoff): python3 tools/handoff.py new, fill "
            "every part it marks, land it by pull request, then python3 tools/handoff.py done <its path>. "
            "This is said once for this window.")


def state(gdir):
    found = load_json(gdir / STATE_FILE) if gdir else None
    found = found or {}
    for key in ("told", "done"):
        if not isinstance(found.get(key), dict):
            found[key] = {}
    return found


def hook(data, root, now):
    """The hook's answer as a dict to print, or None to say nothing."""
    if os.environ.get("SYMPHONY_HANDOFF", "").strip().lower() == "off" or os.environ.get("GITHUB_ACTIONS"):
        return None
    event = data.get("hook_event_name") if isinstance(data, dict) else None
    if event not in ("Stop", "UserPromptSubmit", "PostToolUse"):
        return None
    if event == "Stop" and data.get("stop_hook_active"):
        return None
    word = due(root, now)
    gdir = git_dir(root)
    if not word or gdir is None:
        return None
    kept = state(gdir)
    if word["key"] in kept["done"]:
        return None
    session = str(data.get("session_id") or "")[:36] or "unknown"
    told = kept["told"].get(session)
    if isinstance(told, list) and word["key"] in told:
        return None
    kept["told"][session] = (told if isinstance(told, list) else [])[-7:] + [word["key"]]
    kept["told"] = dict(list(kept["told"].items())[-50:])
    write_json(gdir / STATE_FILE, kept)
    if event == "Stop":
        return {"decision": "block", "reason": message(word)}
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": message(word)}}


# The status line.

def status_text(data, reading, word):
    model = data.get("model") if isinstance(data, dict) else None
    name = model.get("display_name") if isinstance(model, dict) else None
    parts = [name] if isinstance(name, str) and name else []
    for window, label in (("five_hour", "5h"), ("seven_day", "7d")):
        each = (reading or {}).get("windows", {}).get(window)
        if each:
            parts.append(f"{label} {percent(each['utilization'])}")
    if word:
        parts.append("handoff due")
    return " | ".join(parts)


def statusline(data, root, now):
    reading = from_statusline(data, now)
    gdir = git_dir(root)
    if reading and gdir is not None:
        write_json(gdir / READING_FILE, reading)
    return status_text(data, reading, due(root, now) if reading else None)


# The handoff file.

def git_line(root, *args):
    try:
        found = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return ""
    return found.stdout.strip() if found.returncode == 0 else ""


def where_git_stands(root):
    branch = git_line(root, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    head = git_line(root, "rev-parse", "--short", "HEAD") or "unknown"
    upstream = git_line(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    if upstream:
        ahead = git_line(root, "rev-list", "--count", f"{upstream}..HEAD") or "?"
        pushed = f"{ahead} commit(s) not yet on {upstream}"
    else:
        pushed = "no upstream set, so nothing of it is known to be pushed"
    changed = [line for line in git_line(root, "status", "--porcelain").splitlines() if line.strip()]
    return [f"- Branch {branch} at {head}; {pushed}.",
            f"- {len(changed)} file(s) changed and not committed" + (": " + ", ".join(
                line[3:] for line in changed[:10]) if changed else "") + "."]


def new_path(root, now):
    folder = root / "docs" / "checkpoints" / now.strftime("%Y-%m-%d")
    path = folder / "handoff.md"
    if path.exists():
        path = folder / f"handoff-{now.strftime('%H%M')}.md"
    return path


def skeleton(root, now, word):
    worker = os.environ.get("SYMPHONY_WORKER") or "this session"
    why = word["why"] if word else "a handoff asked for by hand"
    lines = [
        f"# Handoff of {now.strftime('%Y-%m-%d')} at {now.strftime('%H:%M')} UTC, for another account",
        "",
        f"Source: {worker}, written with tools/handoff.py because {why}. A session on the next account reads "
        "this page first (the session-start hook names it), then the board. No secret, token or e-mail is "
        "written here.",
        "",
        "## Where this session stands",
        "",
        *where_git_stands(root),
        f"- {FILL} The pull requests this session opened, each with its state (draft, ready, green, merged).",
        "",
        "## Open work",
        "",
        f"{FILL} One item per piece of work still open: what it is, where its own record is (an issue, a "
        "claim branch, a research note), the state at this minute, and the next steps as a numbered list. "
        "Grid jobs by their Slurm ids, with the word that reads their status.",
        "",
        "## Waiting on the owner",
        "",
        f"{FILL} Each step that is the owner's, with its exact link and what to click; or 'Nothing.'",
        "",
        "## Resume",
        "",
        "1. Open a session on this repository with the next account (a Project of its own on claude.ai, or "
        "a grid worker moved to it).",
        "2. Read this page and the research notes it names; then fetch and read the board.",
        "3. Take the open work above in its order; a claim still held by this session's worker name is "
        "carried on in its own branch.",
        "",
    ]
    return "\n".join(lines)


def new(root, now):
    path = new_path(root, now)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(skeleton(root, now, due(root, now)), encoding="ascii", errors="replace")
    return path


def done(path, root, now):
    """Records a filled handoff; returns the words to print, or raises ValueError."""
    file = Path(path)
    if not file.is_absolute():
        file = root / file
    if not file.is_file():
        raise ValueError(f"{path}: no such file")
    if FILL in file.read_text(encoding="utf-8", errors="replace"):
        raise ValueError(f"{path}: a part is still marked {FILL}; fill it first")
    gdir = git_dir(root)
    word = due(root, now)
    key = word["key"] if word else "by-hand:" + iso(now)
    relative = os.path.relpath(file, root)
    if gdir is not None:
        kept = state(gdir)
        kept["done"][key] = relative
        kept["done"] = dict(list(kept["done"].items())[-20:])
        write_json(gdir / STATE_FILE, kept)
    folder = account_folder()
    if folder is not None:
        write_json(str(folder) + ".handoff.json", {"v": 1, "at": iso(now), "path": relative,
                                                  "commit": git_line(root, "rev-parse", "HEAD")})
    return f"handoff recorded: {relative}"


def latest(root, now, recent=RECENT):
    """The newest handoff under docs/checkpoints/ committed within `recent`, as a path, or None."""
    base = root / "docs" / "checkpoints"
    if not base.is_dir():
        return None
    found = sorted((path for day in base.iterdir() if day.is_dir() and DAY_NAME.match(day.name)
                    for path in day.iterdir() if HANDOFF_NAME.match(path.name)),
                   key=lambda path: (path.parent.name[:10], path.name), reverse=True)
    for path in found[:3]:
        relative = str(path.relative_to(root))
        when = parse_time(git_line(root, "log", "-1", "--format=%cI", "--", relative))
        if when is not None and now - when <= recent:
            return relative
    return None


# The words.

def stdin_json():
    try:
        found = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}
    return found if isinstance(found, dict) else {}


USAGE = "handoff.py statusline | hook | status | new | done PATH | latest"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    word = argv[0] if argv else ""
    now = utc_now()
    root = project_root()
    try:
        if word == "hook":
            answer = hook(stdin_json(), root, now)
            if answer:
                print(json.dumps(answer))
        elif word == "statusline":
            data = stdin_json()
            root = project_root((data.get("workspace") or {}).get("project_dir") if isinstance(
                data.get("workspace"), dict) else None)
            print(statusline(data, root, now))
        elif word == "status":
            found = readings(root, now)
            print(json.dumps({"readings": found, "due": due(root, now)}, indent=2))
        elif word == "new":
            print(new(root, now).relative_to(root))
        elif word == "done" and len(argv) == 2:
            print(done(argv[1], root, now))
        elif word == "latest":
            path = latest(root, now)
            if path:
                print(path)
        else:
            print(USAGE, file=sys.stderr)
            return 2
    except ValueError as problem:
        print(problem, file=sys.stderr)
        return 1
    except Exception as problem:  # a hook or the status line never stops the session
        if word in ("hook", "statusline"):
            return 0
        if not isinstance(problem, OSError):
            raise
        print(problem, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
