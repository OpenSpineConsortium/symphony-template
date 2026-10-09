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
drops comments, joins a backslash-newline and cuts out each here-document
body whose closing line it finds, keeping track of quotes and of the
fresh quoting inside "$(...)" and backquotes; shlex then splits words and
operators, a newline among them. A push is judged against the branch
checked out when the command starts, in the directory the session runs
in, or in the one a leading literal `cd DIR &&` or a literal `git -C DIR`
names. Nothing the command does before the push is followed beyond that,
neither another cd nor a git switch, since following either needs a
shell; a refusal of a push that names no branch says so. A destination
the shell would expand ($, a backquote) cannot be judged and passes.
"""

import json
import os
import shlex
import subprocess
import sys

# git push's long options (git push -h, git 2.43); git takes any
# unambiguous prefix of one, so --dry is --dry-run and --mir is --mirror.
PUSH_LONG_OPTIONS = (
    "--all", "--atomic", "--branches", "--delete", "--dry-run", "--exec",
    "--follow-tags", "--force", "--force-if-includes", "--force-with-lease",
    "--ipv4", "--ipv6", "--mirror", "--no-verify", "--porcelain", "--progress",
    "--prune", "--push-option", "--quiet", "--receive-pack",
    "--recurse-submodules", "--repo", "--set-upstream", "--signed", "--tags",
    "--thin", "--verbose", "--verify",
)

# Long options of git push that take their value as a separate word; the
# value must not be read as a refspec. The short -o does too.
VALUE_OPTIONS = {"--receive-pack", "--exec", "--repo", "--push-option"}

# Global options of git itself that take a separate value, between "git"
# and the verb, as in "git -C clone push".
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}

# The shell's control operators, the newline among them: a newline ends a
# command exactly as ; does.
OPERATOR_CHARS = "();<>|&\n"

# What ends a word: a # right after one of these starts a comment, and a
# here-document's delimiter word stops at one.
WORD_BREAKS = " \t\n;&|()<>"

# Commands that change the directory; a leading cd is followed only when
# the command holds no other.
DIRECTORY_CHANGES = ("cd", "pushd", "popd")

LEADING_CD_ENDS = {"&&", ";", "\n"}
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


def closing_line_end(text, i, delimiter, dash):
    """The index just past the line that closes a here-document whose body
    starts at i, or None when no line does."""
    while i < len(text):
        end = text.find("\n", i)
        line = text[i:] if end == -1 else text[i:end]
        following = len(text) if end == -1 else end + 1
        if (line.lstrip("\t") if dash else line) == delimiter:
            return following
        i = following
    return None


def after_heredoc_bodies(text, start, pending):
    """Where the text resumes once the bodies of the pending here-documents,
    which begin at start and close one after another, are cut out. A body
    whose closing line never comes is left in place: its << may not have
    opened a here-document at all (an arithmetic shift, a nested quote),
    and reading its lines as commands keeps a real push in sight."""
    i = start
    for delimiter, dash in pending:
        closed = closing_line_end(text, i, delimiter, dash)
        if closed is None:
            return i
        i = closed
    return i


class ShellScan:
    """One pass over a command that turns it into plain shell for shlex: a
    stack of open contexts keeps quoting right, and inside "...", a $( )
    or a backquote opens a fresh context in which quotes, comments and
    here-documents mean what they mean at the top."""

    def __init__(self, command):
        self.text = command.replace("\r\n", "\n")
        self.out, self.pending, self.stack = [], [], []
        self.i, self.word_start = 0, True

    def run(self):
        while self.i < len(self.text):
            context = self.stack[-1] if self.stack else None
            if context == "'":
                self.single_quoted()
            elif self.text[self.i] == "\\":
                self.escaped()
            elif context == '"':
                self.double_quoted()
            else:
                self.unquoted(context)
        return "".join(self.out)

    def emit(self, piece, length, word_start):
        self.out.append(piece)
        self.i += length
        self.word_start = word_start

    def single_quoted(self):
        if self.text[self.i] == "'":
            self.stack.pop()
        self.emit(self.text[self.i], 1, False)

    def escaped(self):
        if self.text.startswith("\n", self.i + 1):
            self.i += 2
        else:
            self.emit(self.text[self.i:self.i + 2], 2, False)

    def double_quoted(self):
        if self.text[self.i] == '"':
            self.stack.pop()
            self.emit('"', 1, False)
        elif self.text.startswith("$(", self.i) or self.text[self.i] == "`":
            self.open_substitution()
        else:
            self.emit(self.text[self.i], 1, False)

    def open_substitution(self):
        opener = "$(" if self.text.startswith("$(", self.i) else "`"
        self.stack.append(opener)
        self.emit(opener, len(opener), True)

    def unquoted(self, context):
        text, i = self.text, self.i
        ch = text[i]
        if ch in "'\"":
            self.stack.append(ch)
            self.emit(ch, 1, False)
        elif (ch == "`" and context == "`") or (ch == ")" and context == "$("):
            self.stack.pop()
            self.emit(ch, 1, False)
        elif text.startswith("$(", i) or ch == "`":
            self.open_substitution()
        elif ch == "#" and self.word_start:
            end = text.find("\n", i)
            self.i = len(text) if end == -1 else end
        elif text.startswith("<<<", i):
            self.emit("<<<", 3, True)
        elif text.startswith("<<", i):
            self.heredoc_opener()
        elif ch == "\n":
            self.out.append(" \n ")
            self.i = after_heredoc_bodies(text, i + 1, self.pending)
            self.pending, self.word_start = [], True
        else:
            self.emit(ch, 1, ch in WORD_BREAKS)

    def heredoc_opener(self):
        delimiter, dash, end = heredoc_delimiter(self.text, self.i + 2)
        if not delimiter or delimiter[:1].isdigit():
            self.emit("<<", 2, True)
            return
        self.pending.append((delimiter, dash))
        self.out.append(" << heredoc ")
        self.i, self.word_start = end, True


def plain_shell(command):
    """The command as plain shell for shlex: comments dropped, a
    backslash-newline joined, the here-document bodies that close cut out
    (a body is data, and a line in it that reads like a push is not one),
    and each newline set apart so it stands alone as an operator."""
    return ShellScan(command).run()


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


def literal_directory(word, base):
    """The directory a literal path word names, or None when the word
    needs a shell to expand it ($, a backquote), is an option, or names
    no directory."""
    if not word or word.startswith("-") or any(ch in word for ch in "$`"):
        return None
    try:
        path = os.path.join(base, os.path.expanduser(word))
        return path if os.path.isdir(path) else None
    except ValueError:
        return None


def starting_directory(tokens, cwd):
    """The directory the command's pushes run in: the one a leading
    literal `cd DIR &&` (or `cd DIR;`) names, when the command holds no
    other cd, pushd or popd; otherwise the session's own."""
    if len(tokens) < 3 or tokens[0] != "cd" or tokens[2] not in LEADING_CD_ENDS:
        return cwd
    if sum(token in DIRECTORY_CHANGES for token in tokens) != 1:
        return cwd
    return literal_directory(tokens[1], cwd) or cwd


def judged_pushes(command, cwd):
    """Each git push in the command with the directory it runs in."""
    tokens = shell_tokens(command) or []
    base = starting_directory(tokens, cwd)
    found = []
    for argv in commands_from(tokens):
        invocation = push_invocation(argv)
        if invocation is not None:
            args, directory = invocation
            where = (literal_directory(directory, base) if directory else None) or base
            found.append((args, where))
    return found


def long_option(arg):
    """The git push long option an argument names, its =value set aside;
    git takes any unambiguous prefix, so --dry names --dry-run."""
    name = arg.split("=", 1)[0]
    if name in PUSH_LONG_OPTIONS:
        return name
    matches = [option for option in PUSH_LONG_OPTIONS if option.startswith(name)]
    return matches[0] if len(matches) == 1 else name


def short_option_letters(arg):
    """The letters of a cluster of short options, as in -nv, and whether
    its last letter is an o that takes the next word as its value; what
    follows an o inside the cluster is that value, not more letters."""
    letters, _, value = arg[1:].partition("o")
    takes_next = "o" in arg[1:] and not value
    return set(letters), takes_next


def push_options(args):
    """The options of a git push that matter here, as a set of long names
    (-f counts as --force, -n as --dry-run), and its positional words: the
    remote, then the refspecs."""
    seen, positionals, skip = set(), [], False
    for arg in args:
        if skip:
            skip = False
        elif arg.startswith("--"):
            option = long_option(arg)
            seen.add(option)
            skip = option in VALUE_OPTIONS and "=" not in arg
        elif arg.startswith("-") and len(arg) > 1:
            letters, skip = short_option_letters(arg)
            seen.update(name for letter, name in (("f", "--force"), ("n", "--dry-run"))
                        if letter in letters)
        else:
            positionals.append(arg)
    if any(spec.startswith("+") for spec in positionals[1:]):
        seen.add("--force")
    return seen, positionals


def destinations(positionals, current_branch, tags_only):
    """The branches a push writes, each with whether it was named or only
    implied by the branch checked out (no refspec, HEAD or @). A name the
    shell would expand ($, a backquote) cannot be judged and is left out."""
    found = []
    for spec in positionals[1:]:
        name = spec.lstrip("+")
        if ":" in name:
            name = name.split(":", 1)[1]
        name = name.removeprefix("refs/heads/")
        implied = name in ("", "HEAD", "@")
        name = current_branch if implied else name
        if name and not any(ch in name for ch in "$`"):
            found.append((name, implied))
    if not positionals[1:] and current_branch and not tags_only:
        found.append((current_branch, True))
    return found


def default_branch_refusal(name, implied):
    reason = (f"a push to {name} is refused: the default branch takes only pull "
              "requests (.claude/rules/board.md)")
    if implied:
        reason += (f". The push names no branch, and {name} was checked out when this "
                   "command started; if the command switches branches first, name the "
                   "branch you push, as in git push -u origin claude/N")
    return reason


def refusal(args, current_branch, default_branch):
    """Why this push is refused, or None when it is allowed."""
    seen, positionals = push_options(args)
    if "--dry-run" in seen:
        return None
    wholesale = next((option for option in WHOLESALE if option in seen), None)
    if wholesale:
        return (f"a push with {wholesale} moves branches wholesale; "
                "push your own claim branch alone (.claude/rules/board.md)")
    if "--force" in seen:
        return ("a forced push (--force, -f or a +refspec) overwrites history another account "
                "may hold; the one forced push the protocol allows is --force-with-lease on "
                "your own claude/ branch after a rebase (.claude/rules/board.md)")
    names = destinations(positionals, current_branch, "--tags" in seen)
    for name, implied in names:
        if name == default_branch:
            return default_branch_refusal(name, implied)
        if name == "board":
            return ("a push to board is refused: only the board workflow writes that "
                    "branch (.claude/rules/board.md)")
    strays = [name for name, _ in names if not name.startswith("claude/")]
    if "--force-with-lease" in seen and strays:
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
    except (ValueError, RecursionError):
        return 0
    command, cwd = command_and_cwd(payload)
    if not command or "push" not in command:
        return 0
    for args, where in judged_pushes(command, cwd):
        current, default = branches(where)
        reason = refusal(args, current, default)
        if reason:
            print(reason, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
