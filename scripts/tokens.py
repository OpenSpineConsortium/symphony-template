#!/usr/bin/env python3
"""Store each of your Claude accounts' subscription tokens as an Actions secret, without ever seeing one.

The Claude runs this repository starts in GitHub Actions (@claude, the
workers in Actions and the coordinator workflow, docs/setup/claude-action.md)
run on the secret CLAUDE_CODE_OAUTH_TOKEN, and a benchmark run in Actions
(OpenSpineConsortium/coordbench's bench.yml) spreads its agents over a pool
of accounts, one secret SYMPHONY_CLAUDE_<slot> each, slots 1 to 8, with the
slots in use listed in the variable SYMPHONY_CLAUDE_ACCOUNTS. Each token
comes from `claude setup-token`, a browser sign-in that prints a token good
for about a year; by hand, each then goes through a clipboard into a
settings page, once per account. This wizard does that part. It runs
`claude setup-token` for you behind a pseudo-terminal, lets the sign-in
through to your browser and your keyboard, takes the token out of what
claude prints before it reaches the screen, and hands it to `gh secret set`
over a pipe, which encrypts it on your machine and sends only the sealed
value. The token is never on the screen, on a command line, in a file, in
a log or in this script's output; what is printed is names, dates and
counts. An API key is refused on sight: runs bill nothing (docs/project.md),
and only a subscription token has the shape claude setup-token prints.

  python3 scripts/tokens.py                   the wizard: the state, then one account at a time
  python3 scripts/tokens.py status            the state alone: which slots are set, since when, renew by when
  python3 scripts/tokens.py add [--slot N] [--label WORD] [--also-main] [--paste]
  python3 scripts/tokens.py main [--paste]    CLAUDE_CODE_OAUTH_TOKEN alone, from one more sign-in
  python3 scripts/tokens.py remove N          a slot's secret and its label, off the list of slots

Where the secrets go: --org ORG puts them on the organization, seen by the
repositories --repos names (gh's "selected" visibility; --visibility all or
private makes every repository see them); --repo OWNER/NAME puts them on one
repository. With neither, the clone's origin decides: a repository of an
organization takes the organization level with that repository on the list,
a personal one its own level. A secret that exists keeps its visibility and
its list, and the list grows by what --repos names; nothing is taken off a
list here. Needs the GitHub CLI signed in (gh auth login) as an admin of the
organization, or of the repository, and Claude Code (claude) on this
machine; `add --paste` and `main --paste` take the token from a hidden
prompt instead, for a machine without claude, or a Windows shell, which has
no pseudo-terminal. A label is
a word of your own so that status can say which account a slot is; it is
stored as the variable SYMPHONY_CLAUDE_<slot>_LABEL, which anyone who reads
the repository's workflows can see, so never an e-mail address. Refuses to
run for a repository in crowd mode, which holds no Claude token
(docs/setup/crowdsourcing.md). Everything that can fail is tried before
the sign-in, since a token minted and not stored is lost with the process.
Exit 0 when done, 1 on a refusal, 2 on a usage error made before any call.
"""

import argparse
import codecs
import getpass
import json
import os
import re
import select
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "docs" / "project.md"
CROWD_ON = re.compile(r"^- Crowd mode: on\.", re.MULTILINE)

GH_TIMEOUT = 600
MAIN_SECRET = "CLAUDE_CODE_OAUTH_TOKEN"
SLOT_PREFIX = "SYMPHONY_CLAUDE_"
LABEL_SUFFIX = "_LABEL"
ACCOUNTS_VARIABLE = SLOT_PREFIX + "ACCOUNTS"
SLOTS = tuple(range(1, 9))
CROWD_VARIABLE = "CLAUDE_CROWD"
TOKEN_LIFE = timedelta(days=365)
RENEW_SOON = timedelta(days=30)
SETUP_TOKEN = ("claude", "setup-token")
VISIBILITIES = ("selected", "all", "private")
# Rows and columns of the terminal claude gets: wide, so it never wraps the
# token over two lines, where no pattern would find it.
TERMINAL_SIZE = (50, 400)
# A held-back tail longer than this is a run of letters, not a token's start;
# a captured run longer than it went on past where a token ends.
HOLD_LIMIT = 400
# A token claude prints is far longer than this; a captured one shorter is
# a piece of one, cut by a terminal narrower than the one claude was given.
TOKEN_SHORTEST = 60
# The shapes are assembled from pieces so that this file never looks like a
# secret to tools/check_docs.py, whose own shapes are built the same way.
# Anything of Anthropic's key shape is kept off the screen; only the
# subscription token's kind is kept.
SECRET_HEAD = "sk-" + "ant-"
TOKEN_HEAD = SECRET_HEAD + "oat"
API_KEY_HEAD = SECRET_HEAD + "api"
SECRET_SHAPE = re.compile(re.escape(SECRET_HEAD) + r"[A-Za-z0-9_-]{20,}")
TOKEN_SHAPE = re.compile(re.escape(TOKEN_HEAD) + r"[0-9]{2}-[A-Za-z0-9_-]{20,}")
# A tail of what claude printed that may be the start of a token whose rest
# is still to come: two characters or more of the head, or the head itself
# with whatever followed it so far.
TOKEN_START = re.compile(
    "(?:" + "|".join(re.escape(SECRET_HEAD[:n]) for n in range(2, len(SECRET_HEAD) + 1))
    + "|" + re.escape(SECRET_HEAD) + r"[A-Za-z0-9_-]*)$"
)
# What the screen shows in a token's place; neither matches a secret's shape.
MASK = TOKEN_HEAD + "**-" + "*" * 16 + " (kept by the wizard, not shown)"
OTHER_MASK = SECRET_HEAD + "****" + " (not a token from claude setup-token; not shown)"
# The rest of a token cut over two lines: a run of a token's characters
# that begins the line after the masked part, past line ends and cursor
# codes; shorter runs are words. A cursor code cut by the chunk's end is
# waited for.
CONTINUATION = re.compile(r"^(?:\r|\n|\x1b\[[0-9;?]*[A-Za-z])*([A-Za-z0-9_-]*)")
CONTINUATION_RUN = 20
PARTIAL_CODE = re.compile(r"\x1b(?:\[[0-9;?]*)?")
# What claude turns on in the terminal and may leave on when it is killed.
TERMINAL_RESET = "\x1b[?2004l\x1b[?1004l\x1b[?1000l\x1b[?1002l\x1b[?1003l\x1b[?1006l\x1b[?2026l\x1b[<u\x1b[?25h\x1b[0m"
LABEL_SHAPE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,39}$")
REPO_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
FULL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+$")
ORIGIN = re.compile(r"github\.com[:/]([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9._-]+?)(?:\.git)?/?$")


class TokensError(Exception):
    """Something the wizard could not do, or refuses to do; the message says
    what to do instead, and never holds a token."""


class UsageError(TokensError):
    """Options that cannot go together, found before gh is asked anything."""


# The GitHub CLI.

class Gh:
    """gh's own commands, each run as a process. A value for a secret goes in
    on the pipe to gh's standard input and nowhere else; gh never prints it,
    so neither does anything here."""

    def run(self, args, stdin=None):
        try:
            return subprocess.run(
                ["gh"] + list(args), input=stdin, capture_output=True,
                text=True, encoding="utf-8", timeout=GH_TIMEOUT,
            )
        except FileNotFoundError:
            raise TokensError("gh is not installed: https://cli.github.com, then run gh auth login") from None
        except subprocess.TimeoutExpired:
            raise TokensError(f"gh {args[0]} gave no answer in {GH_TIMEOUT} seconds") from None

    def must(self, args, stdin=None):
        """gh's output, or the error gh named."""
        done = self.run(args, stdin)
        if done.returncode != 0:
            raise TokensError(f"gh {' '.join(args[:2])}: {first_line(done.stderr) or 'failed'}")
        return done.stdout

    def json(self, args):
        text = self.must(args)
        return json.loads(text) if text.strip() else []

    def read(self, args):
        """A read that may find nothing: (found, output). Any failure but a
        404 is an error, since a guess would store a secret in the wrong
        place or in a crowd repository."""
        done = self.run(args)
        if done.returncode == 0:
            return True, done.stdout
        if "(HTTP 404)" in done.stderr:
            return False, ""
        raise TokensError(f"gh {' '.join(args[:2])}: {first_line(done.stderr) or 'failed'}")


def first_line(text):
    return (text or "").strip().splitlines()[0].strip() if (text or "").strip() else ""


# Where the secrets live.

class Target:
    """An organization, whose secrets a list of repositories sees (or every
    repository, with visibility all or private), or one repository."""

    def __init__(self, level, owner, repos=(), visibility="selected", name=None):
        self.level = level
        self.owner = owner
        self.repos = sorted(set(repos))
        self.visibility = visibility
        self.name = name

    @property
    def flags(self):
        if self.level == "org":
            return ["--org", self.owner]
        return ["--repo", self.full_name]

    @property
    def full_name(self):
        return f"{self.owner}/{self.name}"

    @property
    def api(self):
        if self.level == "org":
            return f"orgs/{self.owner}/actions"
        return f"repos/{self.full_name}/actions"

    def repositories(self):
        """The repositories whose crowd mode is checked: the ones named, or
        the one the secrets go on."""
        if self.level == "org":
            return [f"{self.owner}/{repo}" for repo in self.repos]
        return [self.full_name]

    def describe(self):
        if self.level == "repo":
            return f"the repository {self.full_name}"
        if self.visibility == "selected":
            return f"the organization {self.owner}, seen by " + (", ".join(self.repos) or "no repository yet")
        return f"the organization {self.owner}, seen by {'every' if self.visibility == 'all' else 'every private'} repository"


def origin_repository(root=ROOT):
    """OWNER/NAME from the clone's origin, or None when there is none."""
    try:
        done = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"],
                              capture_output=True, text=True, encoding="utf-8")
    except OSError:
        return None
    match = ORIGIN.search(done.stdout.strip()) if done.returncode == 0 else None
    return (match.group(1), match.group(2)) if match else None


def check_options(args, root=ROOT):
    """The place the options name, as far as it is known without gh:
    (repos, visibility, origin), or why the options cannot go together."""
    repos = parse_repos(args.repos)
    visibility = args.visibility or "selected"
    if args.repo and (repos or args.visibility):
        raise UsageError("--repo puts the secrets on one repository: --repos and --visibility are for --org")
    if repos and visibility != "selected":
        raise UsageError(f"--repos names the repositories that see a selected secret, and --visibility {visibility} "
                         "makes every repository see it: drop one")
    origin = None if args.repo else origin_repository(root)
    if args.org and not repos and visibility == "selected":
        if origin and origin[0].lower() == args.org.lower():
            repos = [origin[1]]
        else:
            raise UsageError("--org needs the repositories that see the secrets: --repos NAME,NAME (or --visibility all)")
    if not args.org and not args.repo and not origin:
        raise UsageError("this clone has no GitHub origin: say where the secrets go with --org ORG --repos NAME or --repo OWNER/NAME")
    return repos, visibility, origin


def target_from(args, gh, root=ROOT):
    """The level and the place the options name, or the origin's."""
    repos, visibility, origin = check_options(args, root)
    if args.repo:
        owner, name = args.repo.split("/")
        return Target("repo", owner, name=name)
    if args.org:
        return Target("org", args.org, repos, visibility)
    owner, name = origin
    kind = gh.must(["api", f"users/{owner}", "--jq", ".type"]).strip()
    if kind == "Organization":
        return Target("org", owner, repos or [name], visibility)
    if repos or args.visibility:
        raise TokensError(f"{owner} is a personal account, whose repository {name} takes its own secrets: --repos and --visibility are for an organization")
    return Target("repo", owner, name=name)


def parse_repos(text):
    repos = [part.strip() for part in (text or "").replace(" ", ",").split(",") if part.strip()]
    for repo in repos:
        if not REPO_NAME.match(repo):
            raise UsageError(f"--repos takes repository names without their owner, not {repo}")
    return repos


# The token, from claude or from a hidden prompt.

class Masker:
    """What claude prints, with every token taken out before it reaches the
    screen and kept here. A token can arrive in pieces, so a tail that may
    be a token's start is held back until the rest comes, and the last
    characters on the screen are kept for matching, since a lone "s" is let
    through and the token it began is then masked from its second
    character on."""

    def __init__(self):
        self.shown = ""
        self.held = ""
        self.tokens = []
        # What followed the last mask, while it may be a cut token's rest.
        self.after = None
        self.cut_over_lines = False

    def feed(self, chunk, final=False):
        """The text to put on the screen for this chunk. A token that runs
        to the chunk's end may go on in the next one, so it is held back
        whole, as a start is, until the text after it shows where it ends;
        one that has run on past any token's length is masked as it is,
        since it is never shown, and refused later by its length."""
        text = self.shown + self.held + chunk
        shown = len(self.shown)
        pieces, position = [], shown
        for match in SECRET_SHAPE.finditer(text):
            if match.end() == len(text) and not final and len(match.group(0)) <= HOLD_LIMIT:
                break
            found = match.group(0)
            if TOKEN_SHAPE.fullmatch(found) and found not in self.tokens:
                self.tokens.append(found)
            pieces.append(text[position:max(match.start(), shown)])
            pieces.append(MASK if TOKEN_SHAPE.fullmatch(found) else OTHER_MASK)
            position = max(match.end(), shown)
        cut = len(text)
        if not final:
            start = TOKEN_START.search(text)
            if start and len(start.group(0)) <= HOLD_LIMIT:
                cut = max(start.start(), position)
        self.held = text[cut:]
        pieces.append(text[position:cut])
        self.watch(pieces)
        emit = "".join(pieces)
        if emit:
            self.shown = (self.shown + emit)[-12:]
        return emit

    def watch(self, pieces):
        """A run of a token's characters that begins the line after a
        masked token is the rest of one cut over two lines by a terminal
        narrower than the one claude was given: the piece kept is then no
        token, and the rest is already on the screen, so it is noted here
        and the run refused."""
        for piece in pieces:
            if piece in (MASK, OTHER_MASK):
                self.after = ""
            elif self.after is not None and piece:
                self.after += piece
                run = CONTINUATION.match(self.after)
                rest = self.after[run.end():]
                if len(run.group(1)) >= CONTINUATION_RUN:
                    self.cut_over_lines = True
                    self.after = None
                elif (rest and not PARTIAL_CODE.fullmatch(rest)) or len(self.after) > HOLD_LIMIT:
                    self.after = None


def pty_available():
    """A pseudo-terminal exists on Linux, macOS and WSL, and not in a
    Windows shell, which takes the pasted route."""
    try:
        import pty  # noqa: F401
        import termios  # noqa: F401
    except ImportError:
        return False
    return True


def pump(master, stdin_fd, on_output):
    """Keystrokes to claude, claude's output to on_output, until claude's
    side of the terminal closes."""
    stdin_open = True
    while True:
        wanted = [master] + ([stdin_fd] if stdin_open else [])
        ready, _, _ = select.select(wanted, [], [])
        if master in ready:
            try:
                data = os.read(master, 4096)
            except OSError:
                data = b""
            if not data:
                return
            on_output(data)
        if stdin_fd in ready:
            data = os.read(stdin_fd, 4096)
            if data:
                os.write(master, data)
            else:
                stdin_open = False


def mint(stdin_fd=None, write=None, command=SETUP_TOKEN):
    """Run claude setup-token behind a pseudo-terminal: the sign-in goes
    through to the browser and the keyboard, everything claude prints
    reaches the screen but the token, and the tokens seen come back with
    claude's exit status and whether one was cut over two lines."""
    import fcntl
    import pty
    import termios
    import tty
    if stdin_fd is None:
        stdin_fd = sys.stdin.fileno()
    if write is None:
        def write(text):
            sys.stdout.write(text)
            sys.stdout.flush()
    pid, master = pty.fork()
    if pid == 0:
        # The width claude wraps at is the terminal's, set here before it
        # starts; a COLUMNS or LINES inherited from the shell would tell a
        # library another width, and a token wrapped over two lines is
        # one no pattern finds whole.
        for name in ("COLUMNS", "LINES"):
            os.environ.pop(name, None)
        fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", *TERMINAL_SIZE, 0, 0))
        try:
            os.execvp(command[0], list(command))
        except OSError:
            os._exit(127)
    masker = Masker()
    decoder = codecs.getincrementaldecoder("utf-8")("replace")
    saved = termios.tcgetattr(stdin_fd) if os.isatty(stdin_fd) else None
    if saved is not None:
        tty.setraw(stdin_fd)
    try:
        pump(master, stdin_fd, lambda data: write(masker.feed(decoder.decode(data))))
    except KeyboardInterrupt:
        os.kill(pid, 15)
        raise
    finally:
        if saved is not None:
            # Keys typed after claude ended are dropped, not fed to the
            # wizard's next question.
            termios.tcsetattr(stdin_fd, termios.TCSAFLUSH, saved)
        os.close(master)
        write(masker.feed(decoder.decode(b"", final=True), final=True))
        if saved is not None:
            # The modes claude turns on (bracketed paste, focus and mouse
            # events, its keyboard protocol) are turned off again, since a
            # claude killed mid-screen leaves them on.
            write(TERMINAL_RESET)
        write("\n")
        _, status = os.waitpid(pid, 0)
    return masker.tokens, status, masker.cut_over_lines


def minted_token(**options):
    """One token from claude setup-token, or why there is none."""
    try:
        tokens, status, cut = mint(**options)
    except KeyboardInterrupt:
        raise TokensError("stopped; nothing was stored") from None
    if cut:
        raise TokensError("claude's output went on with a run of a token's characters on the line after the token, as a token "
                          "cut over two lines by a narrow terminal does: nothing was stored, and the screen may show part of "
                          "it; run claude setup-token yourself in a wide window and use --paste")
    if len(tokens) == 1:
        return whole_token(tokens[0])
    if tokens:
        raise TokensError("claude printed more than one token, so none was stored; run it again")
    code = os.waitstatus_to_exitcode(status) if hasattr(os, "waitstatus_to_exitcode") else status
    if code == 127:
        raise TokensError("claude could not be started: install Claude Code (https://code.claude.com/docs/en/setup), or use --paste")
    raise TokensError(f"claude setup-token ended (exit {code}) without printing a token: the sign-in did not finish, or claude prints it "
                      "in a form this wizard does not know; run it again, or run claude setup-token yourself and use --paste")


def whole_token(token):
    """A token of a token's length: a shorter one is a piece cut by a
    terminal, a longer one a run that went on past where a token ends."""
    if len(token) < TOKEN_SHORTEST:
        raise TokensError(f"the token seen is {len(token)} characters, shorter than any claude setup-token prints, so it was "
                          "cut: nothing was stored; run claude setup-token yourself in a wide window and use --paste")
    if len(token) > HOLD_LIMIT:
        raise TokensError("what claude printed ran on past a token's length with no break, so no token could be told apart "
                          "from it: nothing was stored; run claude setup-token yourself and use --paste")
    return token


def hidden_input(prompt):
    """getpass, or a refusal where it could not hide the input: it warns
    so and would echo, in a window that is no console."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        try:
            return getpass.getpass(prompt)
        except getpass.GetPassWarning:
            raise TokensError("this window cannot hide what you type, so nothing was pasted: run the wizard from a terminal "
                              "(cmd, PowerShell or Windows Terminal; in Git Bash, through winpty), or let it run claude "
                              "setup-token itself") from None


def pasted_token(ask=None):
    """The token from a hidden prompt, as gh's own prompt would take it."""
    ask = ask or hidden_input
    return check_token((ask("Paste the token claude setup-token printed, then Enter (nothing is shown): ") or "").strip())


def check_token(text):
    """The token in what was pasted: claude's own line around it, such as
    its export line, is let through; an API key, or anything else, is not."""
    if not text:
        raise TokensError("nothing was pasted; nothing was stored")
    if API_KEY_HEAD in text:
        raise TokensError("that is an API key, which this project never uses (docs/project.md): make a subscription token with claude setup-token")
    found = TOKEN_SHAPE.findall(text)
    if len(set(found)) != 1:
        raise TokensError(f"that is not a token from claude setup-token (one begins with {TOKEN_HEAD}); nothing was stored")
    return whole_token(found[0])


def claude_command():
    """Where claude is: on PATH, or where Claude Code's own installer puts
    it behind a shell alias, which PATH does not show."""
    found = shutil.which(SETUP_TOKEN[0])
    if found:
        return found
    local = Path.home() / ".claude" / "local" / "claude"
    return str(local) if local.is_file() and os.access(local, os.X_OK) else None


def get_token(args, write=None, stdin_fd=None, ask=None):
    """The token, minted behind the terminal where one exists, pasted where
    asked or where the machine has none."""
    if args.paste:
        return pasted_token(ask)
    if not pty_available():
        print("This shell has no pseudo-terminal, so the token is pasted: run claude setup-token in another window first.")
        return pasted_token(ask)
    claude = claude_command()
    if claude is None:
        print("claude is not on this machine's PATH, so the token is pasted: run claude setup-token where it is, then paste it here.")
        return pasted_token(ask)
    print("Starting claude setup-token. Approve the sign-in in your browser; the token stays out of sight.")
    return minted_token(write=write, stdin_fd=stdin_fd, command=(claude,) + SETUP_TOKEN[1:])


# What is there.

def slot_secret(slot):
    return f"{SLOT_PREFIX}{slot}"


def slot_label(slot):
    return f"{SLOT_PREFIX}{slot}{LABEL_SUFFIX}"


def parse_slots(text):
    """The slots a list names, as the bench reads it: numbers between commas
    or blanks."""
    found = []
    for part in (text or "").replace(",", " ").split():
        if part.isdigit() and int(part) in SLOTS and int(part) not in found:
            found.append(int(part))
    return sorted(found)


class State:
    """The secrets and variables at the target, by name, with the
    repositories each selected one reaches, read when asked."""

    def __init__(self, gh, target):
        self.gh = gh
        self.target = target
        fields = "name,updatedAt,visibility,numSelectedRepos"
        self.secrets = {item["name"]: item for item in gh.json(["secret", "list"] + target.flags + ["--json", fields])}
        self.variables = {item["name"]: item for item in gh.json(["variable", "list"] + target.flags + ["--json", fields + ",value"])}

    def reach(self, kind, name):
        """The repositories a selected organization secret or variable reaches."""
        found, text = self.gh.read(["api", f"{self.target.api}/{kind}/{name}/repositories", "--paginate", "--jq", ".repositories[].name"])
        return sorted(text.split()) if found else []

    def slots_set(self):
        return [slot for slot in SLOTS if slot_secret(slot) in self.secrets]

    def labels(self):
        return {slot: self.variables[slot_label(slot)].get("value", "") for slot in SLOTS if slot_label(slot) in self.variables}

    def accounts(self):
        return parse_slots(self.variables.get(ACCOUNTS_VARIABLE, {}).get("value", ""))


def when(item):
    """The moment GitHub last saw a value stored, or None."""
    text = (item or {}).get("updatedAt") or (item or {}).get("createdAt") or ""
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def age_line(item, now=None):
    """set 2026-10-16, renew by 2027-10-16; a token lasts about a year."""
    stored = when(item)
    if stored is None:
        return "set"
    now = now or datetime.now(timezone.utc)
    renew = stored + TOKEN_LIFE
    note = ""
    if renew <= now:
        note = ", renew now: it is older than a year"
    elif renew - now <= RENEW_SOON:
        note = ", renew soon"
    return f"set {stored.date().isoformat()}, renew by {renew.date().isoformat()}{note}"


def print_status(state, now=None):
    target = state.target
    print(f"Claude tokens on {target.describe()}")
    labels = state.labels()
    for slot in SLOTS:
        name = slot_secret(slot)
        if name not in state.secrets:
            continue
        label = f" ({labels[slot]})" if labels.get(slot) else ""
        print(f"  slot {slot}{label}: {name} {age_line(state.secrets[name], now)}{reach_note(state, 'secrets', name)}")
    free = [slot for slot in SLOTS if slot_secret(slot) not in state.secrets]
    print("  free slots: " + (", ".join(str(slot) for slot in free) if free else "none"))
    accounts = state.accounts()
    print(f"  {ACCOUNTS_VARIABLE}: " + (",".join(str(slot) for slot in accounts) if accounts else "not set"))
    if MAIN_SECRET in state.secrets:
        print(f"  {MAIN_SECRET}: {age_line(state.secrets[MAIN_SECRET], now)}{reach_note(state, 'secrets', MAIN_SECRET)} (the workflows' token)")
    else:
        print(f"  {MAIN_SECRET}: not set here, so @claude, the workers in Actions and the coordinator workflow do nothing")
    stale = [slot for slot in labels if slot_secret(slot) not in state.secrets]
    for slot in stale:
        print(f"  the label of slot {slot} ({labels[slot]}) outlives its secret; remove {slot} clears it")
    if target.level == "org":
        print_repository_own(state)


def reach_note(state, kind, name):
    item = state.secrets.get(name) if kind == "secrets" else state.variables.get(name)
    if state.target.level != "org" or (item or {}).get("visibility") != "selected":
        return ""
    try:
        reach = state.reach(kind, name)
    except TokensError as error:
        return f", seen by repositories this login could not list ({error})"
    return ", seen by " + (", ".join(reach) if reach else "no repository")


def print_repository_own(state):
    """A repository's own secret of the same name outranks the
    organization's, so the named repositories' own are listed too."""
    for full in state.target.repositories():
        try:
            own = {item["name"]: item for item in state.gh.json(["secret", "list", "--repo", full, "--json", "name,updatedAt"])}
        except TokensError as error:
            print(f"  {full}: its own secrets could not be read ({error})")
            continue
        mine = [name for name in own if name == MAIN_SECRET or name.startswith(SLOT_PREFIX)]
        for name in mine:
            print(f"  {full} holds its own {name} ({age_line(own[name])}), which outranks the organization's")


# Writes.

def scope_args(state, kind, name):
    """The visibility a write at the organization sends: what the secret or
    variable has, its list grown by the target's, or the target's for a new
    one. gh's default would be "private", which a write with no visibility
    would quietly set on an existing one."""
    target = state.target
    if target.level != "org":
        return []
    have = state.secrets.get(name) if kind == "secrets" else state.variables.get(name)
    visibility = (have or {}).get("visibility") or target.visibility
    if visibility != "selected":
        return ["--visibility", visibility]
    repos = sorted(set(target.repos) | set(state.reach(kind, name) if have else []))
    if not repos:
        raise TokensError(f"{name} would be seen by no repository: name them with --repos")
    return ["--visibility", "selected", "--repos", ",".join(repos)]


def store_secret(state, name, token, scope):
    """The value goes to gh on its standard input, where gh reads it without
    echo or a command line; the arguments carry the name and the place, the
    scope found before the token was."""
    args = ["secret", "set", name] + state.target.flags + scope
    state.gh.must(args, stdin=token)
    print(f"  {name}: stored")


def set_variable(state, name, value, scope=None):
    scope = scope_args(state, "variables", name) if scope is None else scope
    args = ["variable", "set", name] + state.target.flags + scope + ["--body", value]
    state.gh.must(args)
    print(f"  {name}: {value}")


def delete_secret(state, name):
    state.gh.must(["secret", "delete", name] + state.target.flags)
    print(f"  {name}: deleted")


def delete_variable(state, name):
    state.gh.must(["variable", "delete", name] + state.target.flags)
    print(f"  {name}: deleted")


def verify(state, names):
    """GitHub lists each stored name, by name alone, with a date later than
    the one it had: GitHub's own dates on both sides, so a clock that is off
    on this machine proves nothing."""
    fresh = State(state.gh, state.target)
    for name in names:
        before, after = when(state.secrets.get(name)), when(fresh.secrets.get(name))
        if after is None:
            raise TokensError(f"GitHub does not list {name} after storing it; open the secrets page and look")
        if before is not None and after <= before:
            raise TokensError(f"GitHub lists {name} as updated {after.isoformat()}, as before the store; it did not take")
        print(f"  {name}: GitHub lists it, updated {after.strftime('%Y-%m-%d %H:%M')} UTC")
    return fresh


def update_accounts(state, scope=None):
    """The variable names every slot whose secret exists, as the bench reads
    it, and is written only when that changed."""
    wanted = ",".join(str(slot) for slot in state.slots_set())
    have = state.variables.get(ACCOUNTS_VARIABLE)
    if have is not None and parse_slots(have.get("value", "")) == state.slots_set():
        print(f"  {ACCOUNTS_VARIABLE}: {wanted or 'empty'} (unchanged)")
        return
    if not wanted:
        if have is not None:
            delete_variable(state, ACCOUNTS_VARIABLE)
        return
    set_variable(state, ACCOUNTS_VARIABLE, wanted, scope)


def refuse_crowd(gh, target, project=None):
    """Each repository named is one this login can see, and none holds a
    Claude token for being in crowd mode (docs/setup/crowdsourcing.md):
    this clone's mode line and each repository's variable say so."""
    try:
        text = (PROJECT if project is None else project).read_text(encoding="utf-8")
    except OSError:
        text = ""
    if CROWD_ON.search(text):
        raise TokensError("crowd mode is on in this clone's docs/project.md: a crowd repository holds no Claude token, so nothing was stored")
    for full in target.repositories():
        found, _ = gh.read(["api", f"repos/{full}", "--jq", ".full_name"])
        if not found:
            raise TokensError(f"GitHub lists no repository {full} for this login: check the name, or --repos")
        found, value = gh.read(["api", f"repos/{full}/actions/variables/{CROWD_VARIABLE}", "--jq", ".value"])
        if found and value.strip().lower() == "true":
            raise TokensError(f"{full} is in crowd mode (its variable {CROWD_VARIABLE} is true): it holds no Claude token, so nothing was stored")


def auth_status(gh):
    """gh auth status for the active github.com account alone: the plain
    command fails on a stale account of any host it knows, and lists that
    host first; a gh too old for --active takes the host alone."""
    done = gh.run(["auth", "status", "--hostname", "github.com", "--active"])
    if done.returncode != 0 and "unknown flag" in (done.stderr or ""):
        done = gh.run(["auth", "status", "--hostname", "github.com"])
    return done


def check_signed_in(gh):
    """What gh says of the github.com account, once it says one is signed in."""
    done = auth_status(gh)
    if done.returncode != 0:
        raise TokensError("gh is not signed in to github.com: run gh auth login (https://cli.github.com/manual/gh_auth_login), then run this again")
    return (done.stdout or "") + (done.stderr or "")


def check_scopes(status, target):
    """An organization's secrets need gh's token to carry admin:org, which
    gh auth login does not grant by default; better found here than after
    a sign-in. gh quotes each scope of an OAuth token; a token of another
    kind (a fine-grained token in GH_TOKEN) lists none, and gh says itself
    what such a token lacks when a call is refused."""
    if target.level != "org":
        return
    line = re.search(r"Token scopes: (.*)", status)
    scopes = re.findall(r"'([^']+)'", line.group(1)) if line else []
    if scopes and "admin:org" not in scopes:
        raise TokensError("gh's token lacks the admin:org scope an organization's secrets need: run gh auth refresh -h github.com -s admin:org, "
                          "approve it in the browser, then run this again")


def check_label(label):
    if label and not LABEL_SHAPE.match(label):
        raise TokensError("a label is a word of your own, up to 40 letters, digits, spaces, dots or dashes, and never an e-mail address")


def first_free(state):
    for slot in SLOTS:
        if slot_secret(slot) not in state.secrets:
            return slot
    raise TokensError(f"every slot from 1 to {SLOTS[-1]} is set; remove one, or name one to replace with --slot")


# The commands.

def sign_in_note(slot):
    print(f"Slot {slot}: in your browser, sign in to claude.ai as the account this slot is for.")
    print("  If another account is signed in there, sign out first, or open the sign-in link in a private window.")
    print("  The page that opens names the account it will approve; approve it there and the token is stored.")


def add(gh, target, slot=None, label="", also_main=False, paste=False, write=None, stdin_fd=None, ask=None, noted=False):
    """One account into a slot. Every read and every scope is settled before
    the sign-in: a token minted and then not stored is a year's token lost
    with the process, so what can fail fails first."""
    refuse_crowd(gh, target)
    check_label(label)
    state = State(gh, target)
    slot = slot or first_free(state)
    name = slot_secret(slot)
    names = [name] + ([MAIN_SECRET] if also_main else [])
    scopes = {each: scope_args(state, "secrets", each) for each in names}
    label_scope = scope_args(state, "variables", slot_label(slot)) if label else None
    accounts_scope = scope_args(state, "variables", ACCOUNTS_VARIABLE)
    if name in state.secrets:
        print(f"Slot {slot} is set ({age_line(state.secrets[name])}); the new token replaces it.")
    if not noted:
        sign_in_note(slot)
    token = get_token(argparse.Namespace(paste=paste), write=write, stdin_fd=stdin_fd, ask=ask)
    for each in names:
        store_secret(state, each, token, scopes[each])
    token = None
    if label:
        set_variable(state, slot_label(slot), label, label_scope)
    state = verify(state, names)
    update_accounts(state, accounts_scope)
    return state


def main_token(gh, target, paste=False, write=None, stdin_fd=None, ask=None):
    refuse_crowd(gh, target)
    state = State(gh, target)
    scope = scope_args(state, "secrets", MAIN_SECRET)
    if MAIN_SECRET in state.secrets:
        print(f"{MAIN_SECRET} is set ({age_line(state.secrets[MAIN_SECRET])}); the new token replaces it.")
    print(f"{MAIN_SECRET}: in your browser, sign in to claude.ai as the account whose plan @claude, the workers in Actions and the coordinator workflow should draw on.")
    token = get_token(argparse.Namespace(paste=paste), write=write, stdin_fd=stdin_fd, ask=ask)
    store_secret(state, MAIN_SECRET, token, scope)
    token = None
    return verify(state, [MAIN_SECRET])


def remove(gh, target, slot):
    state = State(gh, target)
    name = slot_secret(slot)
    if name in state.secrets:
        delete_secret(state, name)
    else:
        print(f"  {name}: not set")
    if slot_label(slot) in state.variables:
        delete_variable(state, slot_label(slot))
    update_accounts(State(gh, target))


def chosen_slot(state, ask):
    """The slot to fill: the first free one by default, a set one to
    replace by its number, none to stop."""
    free = [slot for slot in SLOTS if slot_secret(slot) not in state.secrets]
    if free:
        answer = (ask(f"Which slot gets the next account? [{free[0]}; a set slot's number replaces it; n to stop] ") or "").strip().lower()
    else:
        answer = (ask("Every slot is set. Which one to replace? [its number, or Enter to stop] ") or "").strip().lower()
    if not answer:
        return free[0] if free else None
    if answer in ("n", "no", "q", "quit", "stop"):
        return None
    if answer.isdigit() and int(answer) in SLOTS:
        return int(answer)
    raise TokensError(f"a slot is a number from 1 to {SLOTS[-1]}")


def yes(answer, default):
    text = (answer or "").strip().lower()
    return default if not text else text in ("y", "yes")


def wizard(gh, target, ask=input, write=None, stdin_fd=None):
    """One account at a time: the state, then a slot, a label, the sign-in,
    the store, the check, until the person says no more."""
    refuse_crowd(gh, target)
    state = State(gh, target)
    print_status(state)
    while True:
        slot = chosen_slot(state, ask)
        if slot is None:
            break
        label = (ask("A word of your own for this slot, so status says which account it is (never an e-mail; Enter for none): ") or "").strip()
        check_label(label)
        sign_in_note(slot)
        ask("Press Enter once the browser is signed in to that account ")
        also_main = MAIN_SECRET not in state.secrets and yes(
            ask(f"Store the same token as {MAIN_SECRET} too, the one @claude, the workers in Actions and the coordinator workflow run on? [y/N] "), False)
        state = add(gh, target, slot, label, also_main, write=write, stdin_fd=stdin_fd, noted=True)
        if not yes(ask("Another account? [y/N] "), False):
            break
    print_status(state)


def add_place_options(parser, default):
    """Where the secrets go, accepted before the command and after it: the
    options after the command set nothing when absent, so the main parser's
    values stand."""
    parser.add_argument("--org", default=default, help="the organization the secrets go on, seen by --repos")
    parser.add_argument("--repos", default=default, help="repository names (without the owner, comma-separated) that see the organization's secrets")
    parser.add_argument("--visibility", default=default, choices=VISIBILITIES, help="for a new organization secret: selected (the default, --repos), all, or private")
    parser.add_argument("--repo", default=default, help="one repository, OWNER/NAME, that holds the secrets itself")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python3 scripts/tokens.py",
        description="Store your Claude accounts' subscription tokens as Actions secrets without seeing one; with no command, the wizard.",
    )
    add_place_options(parser, None)
    commands = parser.add_subparsers(dest="command")
    status = commands.add_parser("status", help="which slots are set, since when, and renew by when")
    adding = commands.add_parser("add", help="one account into a slot")
    adding.add_argument("--slot", type=int, choices=SLOTS, help="the slot, 1 to 8; by default the first free one")
    adding.add_argument("--label", default="", help="a word of your own for the slot, never an e-mail address")
    adding.add_argument("--also-main", action="store_true", help=f"store the same token as {MAIN_SECRET} too")
    adding.add_argument("--paste", action="store_true", help="take the token from a hidden prompt instead of running claude setup-token")
    main_command = commands.add_parser("main", help=f"{MAIN_SECRET} alone, the token the Claude workflows run on")
    main_command.add_argument("--paste", action="store_true", help="take the token from a hidden prompt instead of running claude setup-token")
    removing = commands.add_parser("remove", help="a slot's secret and its label")
    removing.add_argument("slot", type=int, choices=SLOTS)
    for command in (status, adding, main_command, removing):
        add_place_options(command, argparse.SUPPRESS)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.repo and not FULL_NAME.match(args.repo):
        parser.error("--repo takes OWNER/NAME")
    if args.repo and args.org:
        parser.error("--org or --repo, not both")
    try:
        check_options(args)
    except UsageError as error:
        parser.error(str(error))
    gh = Gh()
    try:
        status = check_signed_in(gh)
        target = target_from(args, gh)
        check_scopes(status, target)
        if args.command == "status":
            print_status(State(gh, target))
        elif args.command == "add":
            add(gh, target, args.slot, args.label, args.also_main, args.paste)
        elif args.command == "main":
            main_token(gh, target, args.paste)
        elif args.command == "remove":
            remove(gh, target, args.slot)
        else:
            wizard(gh, target)
    except TokensError as error:
        print(f"tokens: {error}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("tokens: stopped", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
