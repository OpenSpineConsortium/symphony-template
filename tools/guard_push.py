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

import io
import json
import os
import re
import shlex
import subprocess
import sys

# Options of git push that take their value as a separate word; the value
# must not be read as a refspec.
VALUE_OPTIONS = {"--receive-pack", "--repo", "-o", "--push-option"}

# Global options of git itself that take a separate value, between "git"
# and the verb, as in "git -C clone push".
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}

# The shell's control operators, the newline among them: a newline ends a
# command exactly as ; does.
OPERATOR_CHARS = "();<>|&\n"

# The opening of a here-document, <<WORD or <<-'WORD', but not the <<< of
# a here-string.
HEREDOC_OPENER = re.compile(r"(?<!<)<<(?!<)-?[ \t]*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


class CommentKeepsNewline(io.StringIO):
    """shlex skips a comment by reading the rest of its line, newline and
    all; leaving the newline unread lets it still end the command, so a
    comment never joins the line after it to the line before."""

    def readline(self, size=-1):
        line = super().readline(size)
        if line.endswith("\n"):
            self.seek(self.tell() - 1)
            return line[:-1]
        return line


def without_heredoc_bodies(command):
    """The command with each here-document's body and closing line cut
    out: a body is data, and a line in it that reads like a push is not
    one. An opener with no closing line is left as it stands."""
    kept, pos = [], 0
    for opener in HEREDOC_OPENER.finditer(command):
        if opener.start() < pos:
            continue
        line_end = command.find("\n", opener.end())
        if line_end == -1:
            break
        closing = re.compile(rf"^\t*{opener.group(2)}$", re.M).search(command, line_end + 1)
        if closing:
            kept.append(command[pos:line_end + 1])
            pos = closing.end()
    kept.append(command[pos:])
    return "".join(kept)


def shell_tokens(command):
    """The words and operators of a shell command, or None when shlex
    cannot read it (an unclosed quote). A backslash before a newline joins
    the two lines, as the shell does."""
    text = without_heredoc_bodies(command).replace("\\\n", "")
    lexer = shlex.shlex(CommentKeepsNewline(text), posix=True, punctuation_chars=OPERATOR_CHARS)
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return None


def simple_commands(command):
    """The argument lists of the simple commands inside a shell command.

    Operators are their own tokens: ;, &&, |, ( ) and a newline end one
    command, and a redirection swallows its target and the file descriptor
    digit before it. A command shlex cannot read yields nothing, and the
    caller lets it pass.
    """
    tokens = shell_tokens(command)
    if tokens is None:
        return []
    commands, current, eat_next = [], [], False
    for token in tokens:
        operator = all(ch in OPERATOR_CHARS for ch in token)
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


def push_invocation(argv):
    """The arguments after "push" and the directory git -C names (None
    when it names none), when argv is a git push; else None. Several -C
    options stack, each relative to the one before, as git reads them."""
    if not argv or argv[0].rsplit("/", 1)[-1] != "git":
        return None
    directory, i = None, 1
    while i < len(argv):
        word = argv[i]
        if word == "-C" and i + 1 < len(argv):
            directory = os.path.join(directory or "", argv[i + 1])
            i += 2
        elif word in GIT_VALUE_OPTIONS:
            i += 2
        elif word.startswith("-"):
            i += 1
        elif word == "push":
            return argv[i + 1:], directory
        else:
            return None
    return None


def pushes_and_where(command, cwd):
    """Each git push in the command with the directory it runs in: a cd
    earlier in the command moves it, and git -C moves it for one push."""
    found = []
    for argv in simple_commands(command):
        if argv[0] == "cd" and len(argv) > 1 and argv[1] != "-":
            cwd = os.path.join(cwd, os.path.expanduser(argv[1]))
            continue
        invocation = push_invocation(argv)
        if invocation is not None:
            args, directory = invocation
            found.append((args, os.path.join(cwd, directory) if directory else cwd))
    return found


def is_short_cluster_with_f(arg):
    """Whether a cluster of short options, as in -uf, carries -f. An -o
    cluster is left alone, since what follows the o is its value."""
    return (arg.startswith("-") and not arg.startswith("--") and len(arg) > 2
            and not arg.startswith("-o") and "f" in arg[1:])


def refusal(args, current_branch, default_branch):
    """Why this push is refused, or None when it is allowed."""
    force = lease = False
    wholesale = None
    positionals = []
    skip = False
    for arg in args:
        if skip:
            skip = False
        elif arg in ("-f", "--force") or is_short_cluster_with_f(arg):
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
    force = force or any(spec.startswith("+") for spec in positionals[1:])
    if wholesale:
        return (f"a push with {wholesale} moves branches wholesale; "
                "push your own claim branch alone (.claude/rules/board.md)")
    if force:
        return ("a forced push (--force, -f or a +refspec) overwrites history another account "
                "may hold; the one forced push "
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
    if not isinstance(payload, dict):
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if "push" not in command:
        return 0
    for args, where in pushes_and_where(command, payload.get("cwd") or "."):
        current, default = branches(where)
        reason = refusal(args, current, default)
        if reason:
            print(reason, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
