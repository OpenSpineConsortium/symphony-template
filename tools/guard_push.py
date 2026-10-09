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

The command is read the way the shell would split it: a small scanner
drops comments, joins a backslash-newline, cuts here-document bodies out
and keeps all of that from happening inside quotes, and shlex then splits
words and operators, a newline among them. A push is judged in the
directory the session runs in, or in the one a leading literal `cd DIR &&`
or a literal `git -C DIR` names. A cd anywhere else is not followed,
since following it through a subshell, a pipeline or `cd -` needs a
shell. A `git switch` or `git checkout -b` earlier in the command names
the branch a later plain push sends, since a branch, unlike a directory,
outlives any subshell.
"""

import json
import os
import shlex
import subprocess
import sys

# Options of git push that take their value as a separate word; the value
# must not be read as a refspec.
VALUE_OPTIONS = {"--receive-pack", "--exec", "--repo", "-o", "--push-option"}

# Global options of git itself that take a separate value, between "git"
# and the verb, as in "git -C clone push".
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}

# The shell's control operators, the newline among them: a newline ends a
# command exactly as ; does.
OPERATOR_CHARS = "();<>|&\n"

# What ends a word: a # right after one of these starts a comment, and a
# here-document's delimiter word stops at one.
WORD_BREAKS = " \t\n;&|()<>"

# Options that name the branch a git switch or git checkout creates.
SWITCH_NAME_OPTIONS = {"-c", "-C", "--create", "--force-create", "--orphan"}
CHECKOUT_NAME_OPTIONS = {"-b", "-B"}

LEADING_CD_ENDS = {"&&", ";", "\n"}
DRY_RUN = {"-n", "--dry-run"}
WHOLESALE = ("--all", "--branches", "--mirror")


def heredoc_delimiter(text, i):
    """Read the word after a << that ends just before i: the delimiter
    with its quoting taken off, whether <<- lets the closing line carry
    leading tabs, and the index just past the word."""
    dash = text.startswith("-", i)
    i += 1 if dash else 0
    while i < len(text) and text[i] in " \t":
        i += 1
    word = []
    while i < len(text) and text[i] not in WORD_BREAKS:
        if text[i] in "'\"":
            end = text.find(text[i], i + 1)
            end = len(text) if end == -1 else end
            word.append(text[i + 1:end])
            i = end + 1
        elif text[i] == "\\":
            word.append(text[i + 1:i + 2])
            i += 2
        else:
            word.append(text[i])
            i += 1
    return "".join(word), dash, i


def after_heredoc_bodies(text, start, pending):
    """Where the text resumes once the bodies of the pending here-documents,
    which begin at start, have run one after another to their closing
    lines. A body never closed runs to the end, as in the shell."""
    i = start
    for delimiter, dash in pending:
        while i < len(text):
            end = text.find("\n", i)
            line = text[i:] if end == -1 else text[i:end]
            i = len(text) if end == -1 else end + 1
            if (line.lstrip("\t") if dash else line) == delimiter:
                break
    return i


def plain_shell(command):
    """The command as plain shell for shlex: comments dropped, a
    backslash-newline joined, here-document bodies cut out (a body is
    data, and a line in it that reads like a push is not one), and each
    newline set apart so it stands alone as an operator. None of this
    happens inside quotes. A << whose word starts with a digit, as in
    $((1<<2)), is a shift, not a here-document."""
    text = command.replace("\r\n", "\n")
    out, pending, quote, i = [], [], None, 0
    while i < len(text):
        ch = text[i]
        if quote == "'":
            out.append(ch)
            quote = None if ch == "'" else quote
            i += 1
        elif ch == "\\":
            if not text.startswith("\n", i + 1):
                out.append(text[i:i + 2])
            i += 2
        elif quote == '"':
            out.append(ch)
            quote = None if ch == '"' else quote
            i += 1
        elif ch in "'\"":
            out.append(ch)
            quote = ch
            i += 1
        elif ch == "#" and (not out or out[-1][-1:] in WORD_BREAKS):
            end = text.find("\n", i)
            i = len(text) if end == -1 else end
        elif text.startswith("<<<", i):
            out.append("<<<")
            i += 3
        elif text.startswith("<<", i):
            delimiter, dash, end = heredoc_delimiter(text, i + 2)
            if delimiter[:1].isdigit() or not delimiter:
                out.append("<<")
                i += 2
            else:
                pending.append((delimiter, dash))
                out.append(" << heredoc ")
                i = end
        elif ch == "\n":
            out.append(" \n ")
            i = after_heredoc_bodies(text, i + 1, pending)
            pending = []
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def shell_tokens(command):
    """The words and operators of a shell command, or None when shlex
    cannot read it (an unclosed quote)."""
    lexer = shlex.shlex(plain_shell(command), posix=True, punctuation_chars=OPERATOR_CHARS)
    lexer.whitespace = " \t\r"
    lexer.commenters = ""
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return None


def commands_from(tokens):
    """The argument lists of the simple commands in a token list. An
    operator that holds ;, |, a parenthesis, a newline, or & outside a
    redirection ends a command; one that holds < or > is a redirection
    and swallows its target and the file descriptor digit before it."""
    commands, current, eat_next = [], [], False
    for token in tokens:
        if not all(ch in OPERATOR_CHARS for ch in token):
            if eat_next:
                eat_next = False
            else:
                current.append(token)
            continue
        redirect = "<" in token or ">" in token
        if any(ch in token for ch in ";|()\n") or (not redirect and "&" in token):
            if current:
                commands.append(current)
            current, eat_next = [], False
        elif redirect and current and current[-1].isdigit():
            current.pop()
        eat_next = eat_next or redirect
    if current:
        commands.append(current)
    return commands


def simple_commands(command):
    """The argument lists of the simple commands inside a shell command; a
    command shlex cannot read yields nothing, and the caller lets it pass."""
    return commands_from(shell_tokens(command) or [])


def is_git(argv):
    return bool(argv) and argv[0].rsplit("/", 1)[-1] == "git"


def push_invocation(argv):
    """The arguments after "push" and the directory git -C names (None
    when it names none), when argv is a git push; else None. Several -C
    options stack, each relative to the one before, as git reads them."""
    if not is_git(argv):
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


def switched_branch(argv):
    """The branch a git switch, or a git checkout -b, leaves checked out;
    None for any other command or when the branch is not certain."""
    if not is_git(argv) or len(argv) < 3 or argv[1] not in ("switch", "checkout"):
        return None
    rest = argv[2:]
    names = SWITCH_NAME_OPTIONS if argv[1] == "switch" else CHECKOUT_NAME_OPTIONS
    for option, value in zip(rest, rest[1:]):
        if option in names:
            return value
    if argv[1] == "checkout" or "--detach" in rest or "-d" in rest:
        return None
    words = [word for word in rest if not word.startswith("-")]
    return words[0] if words else None


def literal_directory(word, base):
    """The directory a literal path word names, or None when the word
    needs a shell to expand it ($, a backquote), is an option, or names
    no directory."""
    if not word or word.startswith("-") or any(ch in word for ch in "$`"):
        return None
    path = os.path.join(base, os.path.expanduser(word))
    return path if os.path.isdir(path) else None


def starting_directory(tokens, cwd):
    """The directory the command's pushes run in: the one a leading
    literal `cd DIR &&` (or `cd DIR;`) names, when the command holds no
    other cd; otherwise the session's own."""
    if len(tokens) < 3 or tokens[0] != "cd" or tokens[2] not in LEADING_CD_ENDS:
        return cwd
    if tokens.count("cd") != 1:
        return cwd
    return literal_directory(tokens[1], cwd) or cwd


def judged_pushes(command, cwd):
    """Each git push in the command, with the directory it runs in and the
    branch a git switch before it left checked out there (None: ask git)."""
    tokens = shell_tokens(command) or []
    base = starting_directory(tokens, cwd)
    found, switched = [], None
    for argv in commands_from(tokens):
        branch = switched_branch(argv)
        if branch:
            switched = branch
            continue
        invocation = push_invocation(argv)
        if invocation is None:
            continue
        args, directory = invocation
        where = (literal_directory(directory, base) if directory else None) or base
        found.append((args, where, switched if where == base else None))
    return found


def is_short_cluster_with_f(arg):
    """Whether a cluster of short options, as in -uf, carries -f. An -o
    cluster is left alone, since what follows the o is its value."""
    return (arg.startswith("-") and not arg.startswith("--") and len(arg) > 2
            and not arg.startswith("-o") and "f" in arg[1:])


def push_options(args):
    """The options of a git push that matter here, as a set of names, and
    its positional words: the remote, then the refspecs."""
    seen, positionals, skip = set(), [], False
    for arg in args:
        if skip:
            skip = False
        elif arg in VALUE_OPTIONS:
            skip = True
        elif arg.startswith("--force-with-lease"):
            seen.add("lease")
        elif arg in ("-f", "--force") or is_short_cluster_with_f(arg):
            seen.add("force")
        elif arg in DRY_RUN or arg in WHOLESALE or arg == "--tags":
            seen.add(arg)
        elif not arg.startswith("-"):
            positionals.append(arg)
    if any(spec.startswith("+") for spec in positionals[1:]):
        seen.add("force")
    return seen, positionals


def destinations(positionals, current_branch, tags_only):
    """The branch names a push writes: each refspec's destination, or the
    current branch when no refspec is given and --tags is not either."""
    names = []
    for spec in positionals[1:]:
        name = spec.lstrip("+")
        if ":" in name:
            name = name.split(":", 1)[1]
        name = name.removeprefix("refs/heads/")
        if name in ("", "HEAD"):
            name = current_branch
        if name:
            names.append(name)
    if not positionals[1:] and current_branch and not tags_only:
        names.append(current_branch)
    return names


def refusal(args, current_branch, default_branch):
    """Why this push is refused, or None when it is allowed."""
    seen, positionals = push_options(args)
    if seen & DRY_RUN:
        return None
    wholesale = next((option for option in WHOLESALE if option in seen), None)
    if wholesale:
        return (f"a push with {wholesale} moves branches wholesale; "
                "push your own claim branch alone (.claude/rules/board.md)")
    if "force" in seen:
        return ("a forced push (--force, -f or a +refspec) overwrites history another account "
                "may hold; the one forced push the protocol allows is --force-with-lease on "
                "your own claude/ branch after a rebase (.claude/rules/board.md)")
    names = destinations(positionals, current_branch, "--tags" in seen)
    for name in names:
        if name == default_branch:
            return (f"a push to {name} is refused: the default branch takes only "
                    "pull requests (.claude/rules/board.md)")
        if name == "board":
            return ("a push to board is refused: only the board workflow writes that "
                    "branch (.claude/rules/board.md)")
    strays = [name for name in names if not name.startswith("claude/")]
    if "lease" in seen and strays:
        return (f"--force-with-lease to {', '.join(strays)} is refused: a forced push "
                "is for your own claude/ branch only (.claude/rules/board.md)")
    return None


def git_line(args, cwd):
    """One line from git, or None when git cannot answer."""
    try:
        done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, timeout=10)
    except (OSError, ValueError, subprocess.TimeoutExpired):
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


def command_and_cwd(payload):
    """The shell command and the session's directory from a hook payload,
    or (None, None) when the payload is not one this hook reads."""
    if not isinstance(payload, dict):
        return None, None
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    cwd = payload.get("cwd")
    return (command if isinstance(command, str) else None,
            cwd if isinstance(cwd, str) and cwd else ".")


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    command, cwd = command_and_cwd(payload)
    if not command or "push" not in command:
        return 0
    for args, where, switched in judged_pushes(command, cwd):
        current, default = branches(where)
        reason = refusal(args, switched or current, default)
        if reason:
            print(reason, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
