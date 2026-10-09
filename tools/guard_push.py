"""Refuse a git push the board rules forbid, before it runs.

Claude Code runs this as a PreToolUse hook on the Bash tool
(.claude/settings.json): the tool call arrives as JSON on stdin, exit
code 2 stops it, and stderr goes back into the session as the reason.
The rules are .claude/rules/board.md's: the default branch takes only
pull requests, the board branch takes only the board workflow's writes,
and the one forced push the protocol allows is --force-with-lease on
one's own claude/ branch after a rebase. A refusal is the rule working;
the answer to one is a pull request, a rebase or another branch, never
a way around the hook.

The hook is the first fence and branch protection on GitHub the second,
so anything this script cannot read it lets through rather than wedging
the session: an unparseable command, a broken payload or a git that
answers nothing all pass, and GitHub still refuses what matters.
"""

import json
import shlex
import subprocess
import sys

# Options of git push that take their value as a separate word; the value
# must not be read as a refspec.
VALUE_OPTIONS = {"--receive-pack", "--repo", "-o", "--push-option"}

# Global options of git itself that take a separate value, between "git"
# and the verb, as in "git -C clone push".
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}


def simple_commands(command):
    """The argument lists of the simple commands inside a shell command.

    shlex with punctuation_chars keeps the shell's operators as their own
    tokens: ;, &&, | and ( ) end one command, a redirection swallows its
    target and the file descriptor digit before it. A command shlex cannot
    read (an unclosed quote) yields nothing, and the caller lets it pass.
    """
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return []
    commands, current, eat_next = [], [], False
    for token in tokens:
        operator = all(ch in "();<>|&" for ch in token)
        if operator and (">" in token or "<" in token):
            if current and current[-1].isdigit():
                current.pop()
            eat_next = True
        elif operator:
            if current:
                commands.append(current)
            current = []
            eat_next = False
        elif eat_next:
            eat_next = False
        else:
            current.append(token)
    if current:
        commands.append(current)
    return commands


def push_arguments(argv):
    """The arguments after "push" when argv is a git push, else None."""
    if not argv or argv[0].rsplit("/", 1)[-1] != "git":
        return None
    i = 1
    while i < len(argv):
        word = argv[i]
        if word in GIT_VALUE_OPTIONS:
            i += 2
        elif word.startswith("-"):
            i += 1
        elif word == "push":
            return argv[i + 1:]
        else:
            return None
    return None


def refusal(args, current_branch, default_branch):
    """Why this push is refused, or None when it is allowed."""
    force = lease = False
    wholesale = None
    positionals = []
    skip = False
    for arg in args:
        if skip:
            skip = False
        elif arg in ("-f", "--force"):
            force = True
        elif arg == "--force-with-lease" or arg.startswith("--force-with-lease="):
            lease = True
        elif arg in ("--all", "--branches", "--mirror"):
            wholesale = arg
        elif arg in VALUE_OPTIONS:
            skip = True
        elif arg.startswith("-"):
            continue
        else:
            positionals.append(arg)
    if wholesale:
        return (f"a push with {wholesale} moves branches wholesale; "
                "push your own claim branch alone (.claude/rules/board.md)")
    if force:
        return ("--force overwrites history another account may hold; the one forced push "
                "the protocol allows is --force-with-lease on your own claude/ branch "
                "after a rebase (.claude/rules/board.md)")
    destinations = []
    for spec in positionals[1:]:
        name = spec.lstrip("+")
        if ":" in name:
            name = name.split(":", 1)[1]
        name = name.removeprefix("refs/heads/")
        if name in ("", "HEAD"):
            name = current_branch
        if name:
            destinations.append(name)
    if not positionals[1:] and current_branch:
        destinations.append(current_branch)
    for name in destinations:
        if name == default_branch:
            return (f"a push to {name} is refused: the default branch takes only "
                    "pull requests (.claude/rules/board.md)")
        if name == "board":
            return ("a push to board is refused: only the board workflow writes that "
                    "branch (.claude/rules/board.md)")
    if lease:
        strays = [name for name in destinations if not name.startswith("claude/")]
        if strays:
            return (f"--force-with-lease to {', '.join(strays)} is refused: a forced push "
                    "is for your own claude/ branch only (.claude/rules/board.md)")
    return None


def git_line(args, cwd):
    """One line from git, or None when git cannot answer."""
    try:
        done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode != 0:
        return None
    return done.stdout.decode("utf-8", "replace").strip() or None


def branches(cwd):
    """The current branch (None when detached) and the default branch."""
    current = git_line(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if current == "HEAD":
        current = None
    head = git_line(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], cwd)
    default = head.removeprefix("origin/") if head else "main"
    return current, default


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if "push" not in command:
        return 0
    pushes = [args for argv in simple_commands(command)
              if (args := push_arguments(argv)) is not None]
    if not pushes:
        return 0
    current, default = branches(payload.get("cwd") or ".")
    for args in pushes:
        reason = refusal(args, current, default)
        if reason:
            print(reason, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
