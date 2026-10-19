"""One Claude account's subscription token, minted in GitHub Actions for the control panel.

The Tokens page's Add a Claude account (https://openspineconsortium.com/
symphony/control/tokens.html) used to open a Codespace, which took minutes
to start. This is the same sign-in on an Actions runner, which starts in
seconds: .github/workflows/token.yml installs Claude Code and runs this
script, which runs `claude setup-token` behind a pseudo-terminal as
scripts/tokens.py does. With no browser to open, claude prints its sign-in
link and waits for the code claude.ai shows after the sign-in. The script
posts the link on the issue the page opened, the page shows it as a
button, the person signs in and the page posts the code back on the issue
as the person; the script hands it to claude, takes the token out of what
claude prints (tokens.py's Masker, so no line of claude's reaches the log
with it), seals it for the secrets public key the page gave
(tools/sealbox.py) and posts only the sealed value. The page stores that
value as the slot's secret with GitHub's secrets API, which opens it; the
token itself is never on the page, in the log or in the issue.

The code alone mints nothing: claude's sign-in is PKCE, so only the claude
that printed the link, holding its verifier, can exchange it, and only
once. Only a comment by the person who started the run counts as the code,
and the script deletes it once read.

For someone who may write to the repository but may not write its
organization's secrets, which GitHub leaves to the organization's owners,
the run stores the token itself (the owner's choice of 2026-10-18): the
workflow's job in the environment token-store mints the SymphonyBoard App's
installation token, and the script puts the token into the first free slot
of the organization's pool, never one that holds a token, adds the slot to
SYMPHONY_CLAUDE_ACCOUNTS, marks it in SYMPHONY_CLAUDE_SETTINGS as the
person's own and posts only the slot's number.

  python3 tools/token_run.py         with ISSUE, KEY, KEY_ID, ACTOR, GITHUB_REPOSITORY and GITHUB_TOKEN set,
                                     or STORE_ORG and TOKEN_FILE in place of KEY and KEY_ID
  python3 tools/token_run.py store   then, with APP_TOKEN and REPO_ID too, once claude has gone
  python3 tools/token_run.py fail    where a step before the script failed, FAIL_WHY saying why
"""

import base64
import codecs
import json
import os
import re
import select
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sealbox  # noqa: E402
import tokens  # noqa: E402

LINK_MARK = "<!-- symphony-token: sign-in -->"
CODE_MARK = "<!-- symphony-token: code -->"
SEALED_MARK = "<!-- symphony-token: sealed -->"
STORED_MARK = "<!-- symphony-token: stored -->"
FAILED_MARK = "<!-- symphony-token: failed -->"
SIGN_IN_LINK = re.compile(r"https://claude\.(?:ai|com)/[A-Za-z0-9/._-]*oauth/authorize\?[A-Za-z0-9%&=._~+-]+")
CODE_SHAPE = re.compile(r"^[A-Za-z0-9_.~#-]{8,512}$")
ISSUE_SHAPE = re.compile(r"^[1-9][0-9]{0,8}$")
KEY_ID_SHAPE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
WAIT_FOR_LINK = 90
WAIT_FOR_CODE = 600
WAIT_FOR_TOKEN = 60
# claude asks for the code under the link, and a terminal switched to raw
# mode after a key arrived throws that key away, so the code waits for the
# question; past this long it is typed anyway, as the question may be worded
# otherwise in a later claude.
WAIT_FOR_PROMPT = 30
PROMPT = "Paste code here"
# claude's screen takes a chunk of input holding more than one key as a
# paste, a line break in it included, so the code and the Enter that sends
# it go in two writes with this pause between.
PASTE_SETTLE = 1.0
POLL_EVERY = 3
TERMINAL_TYPE = "xterm-256color"
# The organization's pool, which the run writes itself for someone who may
# not write it as themselves (the owner's choice of 2026-10-18): a free slot
# only, never one that holds a token, kept as the person's own.
POOL_SLOTS = tuple(str(n) for n in range(1, 33))
SLOT_PREFIX = "SYMPHONY_CLAUDE_"
ACCOUNTS_VARIABLE = "SYMPHONY_CLAUDE_ACCOUNTS"
SETTINGS_VARIABLE = "SYMPHONY_CLAUDE_SETTINGS"
ORG_SHAPE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
# What claude must never see: the run's tokens, which the child would inherit.
WITHHELD = ("GITHUB_TOKEN", "APP_TOKEN")
# The App's token is minted only after claude has gone, since a process can
# read its parent's environment however the child's is trimmed.
API = "https://api.github.com"


class RunError(Exception):
    """Why no token was sealed, in words the page shows; never a token."""


class GitHub:
    """The few issue calls the run makes, on the run's own GITHUB_TOKEN."""

    def __init__(self, repo, token, issue):
        self.repo, self.token, self.issue = repo, token, issue

    def call(self, method, path, body=None):
        request = urllib.request.Request(
            API + path, method=method, data=None if body is None else json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode()
        return json.loads(text) if text else None

    def comment(self, body):
        return self.call("POST", f"/repos/{self.repo}/issues/{self.issue}/comments", {"body": body})

    def comments(self):
        return self.call("GET", f"/repos/{self.repo}/issues/{self.issue}/comments?per_page=100") or []

    def delete_comment(self, comment_id):
        self.call("DELETE", f"/repos/{self.repo}/issues/comments/{comment_id}")


def code_from(comments, actor):
    """The code the person who started the run posted, with its comment's id."""
    for item in comments:
        login = (item.get("user") or {}).get("login", "")
        body = (item.get("body") or "").strip()
        if login.lower() != actor.lower() or not body.startswith(CODE_MARK):
            continue
        code = body[len(CODE_MARK):].strip()
        if CODE_SHAPE.match(code):
            return code, item["id"]
    return None, None


class Claude:
    """claude setup-token behind a pseudo-terminal, its output read through
    tokens.py's Masker, so a token is kept and never passed on."""

    def __init__(self, command=tokens.SETUP_TOKEN):
        import fcntl
        import pty
        import struct
        import termios
        self.pid, self.master = pty.fork()
        if self.pid == 0:
            for name in ("COLUMNS", "LINES") + WITHHELD:
                os.environ.pop(name, None)
            # GitHub's runners set no TERM, and claude then draws only the cells
            # that change, with cursor moves between, which no token pattern finds
            os.environ["TERM"] = os.environ.get("TERM") or TERMINAL_TYPE
            fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", *tokens.TERMINAL_SIZE, 0, 0))
            try:
                os.execvp(command[0], list(command))
            except OSError:
                os._exit(127)
        self.masker = tokens.Masker()
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self.seen = ""
        self.ended = False

    def read(self, seconds):
        """What claude printed within the time, masked; nothing once it ended."""
        if self.ended:
            return ""
        ready, _, _ = select.select([self.master], [], [], seconds)
        if not ready:
            return ""
        try:
            data = os.read(self.master, 4096)
        except OSError:
            data = b""
        if not data:
            self.ended = True
            return self.masker.feed(self.decoder.decode(b"", final=True), final=True)
        shown = self.masker.feed(self.decoder.decode(data))
        self.seen = (self.seen + shown)[-20000:]
        return shown

    def type(self, text):
        os.write(self.master, text.encode())

    def submit(self, code, clock=time.monotonic):
        """The code, then Enter on its own, as a person pastes and presses it."""
        self.type(code)
        settled = clock() + PASTE_SETTLE
        while clock() < settled and not self.ended:
            self.read(0.1)
        self.type("\r")

    def shows(self, words):
        """Whether the screen holds the words, terminal codes and line
        breaks between them folded to single spaces."""
        plain = " ".join(re.sub(tokens.CODE, " ", self.seen).split())
        return " ".join(words.split()) in plain

    def link(self):
        found = SIGN_IN_LINK.findall(self.seen)
        return found[0] if found else None

    def finish(self):
        """claude's exit status, waiting a moment and then stopping it."""
        for _ in range(20):
            done, status = os.waitpid(self.pid, os.WNOHANG)
            if done:
                return os.waitstatus_to_exitcode(status)
            time.sleep(0.1)
        os.kill(self.pid, 15)
        _, status = os.waitpid(self.pid, 0)
        return os.waitstatus_to_exitcode(status)


def wait_for_link(claude, clock=time.monotonic):
    deadline = clock() + WAIT_FOR_LINK
    while clock() < deadline and not claude.ended:
        claude.read(1)
        link = claude.link()
        if link:
            return link
    raise RunError("claude setup-token printed no sign-in link")


def wait_for_prompt(claude, clock=time.monotonic):
    deadline = clock() + WAIT_FOR_PROMPT
    while clock() < deadline and not claude.ended and not claude.shows(PROMPT):
        claude.read(0.5)


def wait_for_code(github, claude, actor, clock=time.monotonic, sleep=time.sleep):
    deadline = clock() + WAIT_FOR_CODE
    while clock() < deadline:
        if claude.ended:
            raise RunError("claude setup-token ended before the code came")
        code, comment_id = code_from(github.comments(), actor)
        if code:
            return code, comment_id
        claude.read(POLL_EVERY)
    raise RunError("no code came within ten minutes; press Add a Claude account again")


def claude_said(claude, code):
    """The last words claude printed, as a line for the page: terminal codes
    and blanks folded, the code taken out, and only what the mask let
    through, so never a token."""
    plain = re.sub(tokens.CODE, " ", claude.seen)
    if code:
        plain = plain.replace(code, "<code>")
    words = " ".join(plain.split())
    return words[-300:]


def wait_for_token(claude, clock=time.monotonic):
    deadline = clock() + WAIT_FOR_TOKEN
    while clock() < deadline and not claude.ended:
        claude.read(1)
        if claude.masker.tokens:
            break
    while not claude.ended and claude.read(0.5):
        pass
    found = claude.masker.tokens
    if len(found) != 1:
        raise RunError("claude printed no token after the code: the code may be wrong or used already; press Add a Claude account again")
    return tokens.whole_token(found[0])


class Pool:
    """The organization's slots, written with the App's installation token,
    which may write the organization's secrets and variables."""

    def __init__(self, org, token, repo_id, call=None):
        self.org, self.repo_id = org, repo_id
        self.base = f"/orgs/{org}/actions"
        self.api = call or GitHub("", token, "").call

    def read(self, path):
        try:
            return self.api("GET", path)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            raise

    def taken(self):
        names, page = set(), 1
        while True:
            got = (self.api("GET", f"{self.base}/secrets?per_page=100&page={page}") or {}).get("secrets") or []
            names.update(item.get("name", "") for item in got)
            if len(got) < 100 or page >= 50:
                return names
            page += 1

    def free_slot(self):
        taken = self.taken()
        for slot in POOL_SLOTS:
            if SLOT_PREFIX + slot not in taken:
                return slot
        raise RunError("all 32 slots of the organization's pool hold a token; an owner frees one with its X")

    def put_secret(self, slot, token):
        key = self.api("GET", f"{self.base}/secrets/public-key")
        sealed = base64.b64encode(sealbox.seal(token.encode(), sealbox.key_from_base64(key["key"]))).decode()
        self.api("PUT", f"{self.base}/secrets/{SLOT_PREFIX}{slot}", {
            "encrypted_value": sealed, "key_id": key["key_id"],
            "visibility": "selected", "selected_repository_ids": [self.repo_id]})

    def write_variable(self, name, change):
        have = self.read(f"{self.base}/variables/{name}")
        value = change(have["value"] if have else "")
        if not have:
            self.api("POST", f"{self.base}/variables", {"name": name, "value": value,
                     "visibility": "selected", "selected_repository_ids": [self.repo_id]})
            return
        if value != have["value"]:
            self.api("PATCH", f"{self.base}/variables/{name}", {"name": name, "value": value})
        if have.get("visibility") == "selected":
            self.api("PUT", f"{self.base}/variables/{name}/repositories/{self.repo_id}")

    def add_to_accounts(self, slot):
        # an owner's page may write the list at the same moment, so it is read
        # back and written once more where that write took the slot away
        for _ in range(3):
            self.write_variable(ACCOUNTS_VARIABLE, lambda text: with_slot(text, slot))
            have = self.read(f"{self.base}/variables/{ACCOUNTS_VARIABLE}") or {}
            if slot in re.split(r"[,\s]+", have.get("value", "")):
                return
        raise RunError(f"the token is in slot {slot}, but {ACCOUNTS_VARIABLE} would not keep it; an owner adds it")

    def store(self, token, actor):
        """The token in the first free slot, the slot on the accounts list and
        the person named as its owner; the slot's number back."""
        step = "read which slots are free"
        try:
            slot = self.free_slot()
            step = f"store the token in slot {slot}"
            # asked once more just before the write, so a slot another run took
            # since the list is never written over
            if self.read(f"{self.base}/secrets/{SLOT_PREFIX}{slot}") is not None:
                raise RunError(f"slot {slot} was taken while the run looked; press Add Token again")
            self.put_secret(slot, token)
            step = f"add slot {slot} to {ACCOUNTS_VARIABLE}"
            self.add_to_accounts(slot)
            step = f"mark slot {slot} as yours in {SETTINGS_VARIABLE}"
            self.write_variable(SETTINGS_VARIABLE, lambda text: with_owner(text, slot, actor))
        except urllib.error.HTTPError as error:
            # the page waits for a word from the run, so GitHub's refusal becomes one
            raise RunError(f"GitHub answered {error.code} when the run tried to {step} in {self.org}'s pool") from None
        return slot


def with_slot(text, slot):
    words = [w for w in re.split(r"[,\s]+", text or "") if w]
    return ",".join(words if slot in words else words + [slot])


def with_owner(text, slot, actor):
    # a variable that is not an object by slot is left for an owner to mend,
    # since writing over it would take every other slot's settings away
    try:
        data = json.loads(text) if (text or "").strip() else {}
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        raise RunError(f"the token is in slot {slot}, but {SETTINGS_VARIABLE} is not JSON by slot, so it is not marked as yours yet; an owner mends it")
    data[slot] = {"owner": actor, "id": os.urandom(4).hex()}
    return json.dumps(data, separators=(",", ":"))


def settings(environ, sealing=None):
    issue, key, key_id = environ.get("ISSUE", ""), environ.get("KEY", ""), environ.get("KEY_ID", "")
    actor, repo, token = environ.get("ACTOR", ""), environ.get("GITHUB_REPOSITORY", ""), environ.get("GITHUB_TOKEN", "")
    if not ISSUE_SHAPE.match(issue):
        raise RunError("the run was not given the page's issue")
    if not actor or not repo or not token:
        raise RunError("the run lacks its actor, repository or token")
    if sealing is None:
        sealing = not environ.get("STORE_ORG")
    if not sealing:
        return GitHub(repo, token, issue), None, "", actor
    if not KEY_ID_SHAPE.match(key_id):
        raise RunError("the run was not given the secrets key's id")
    return GitHub(repo, token, issue), sealbox.key_from_base64(key), key_id, actor


def pool_of(environ):
    org, app_token, repo_id = environ.get("STORE_ORG", ""), environ.get("APP_TOKEN", ""), environ.get("REPO_ID", "")
    if not ORG_SHAPE.match(org) or not app_token or not re.fullmatch(r"[1-9][0-9]{0,15}", repo_id):
        raise RunError("the run was not given the organization, the App's token or the repository's id to store the token with")
    return Pool(org, app_token, int(repo_id))


def held_file(environ):
    path = environ.get("TOKEN_FILE", "")
    if not path:
        raise RunError("the run was not given the file that holds the token between its steps")
    return path


def hold(token, path):
    """The token on the runner's disk between the sign-in and the store, readable
    by the runner's user alone, since the App's token is minted only once claude
    has gone and no process of claude's can read it."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as held:
        held.write(token)


def take_held(path):
    try:
        with open(path) as held:
            return held.read().strip()
    except OSError:
        raise RunError("the sign-in left no token for the store step") from None
    finally:
        if os.path.exists(path):
            os.remove(path)


def run(environ, start=Claude):
    github, key, key_id, actor = settings(environ)
    holding = held_file(environ) if environ.get("STORE_ORG") else ""
    claude = start()
    try:
        github.comment(f"{LINK_MARK}\n{wait_for_link(claude)}")
        print("Posted the sign-in link; waiting for the code.", flush=True)
        code, comment_id = wait_for_code(github, claude, actor)
        print(f"::add-mask::{code}", flush=True)
        github.delete_comment(comment_id)
        wait_for_prompt(claude)
        claude.submit(code)
        try:
            token = wait_for_token(claude)
        except RunError as error:
            said = claude_said(claude, code)
            print(f"claude's last words: {said}", flush=True)
            raise RunError(f"{error}. claude said: {said}") from None
        if holding:
            hold(token, holding)
            print("Held the token for the store step.", flush=True)
            return
        sealed = base64.b64encode(sealbox.seal(token.encode(), key)).decode()
        github.comment(f"{SEALED_MARK}\n{key_id}\n{sealed}")
        print("Posted the sealed token.", flush=True)
    finally:
        claude.finish()


def store(environ, pool=None):
    """The token the sign-in held, into the organization's pool with the App's token."""
    github, _, _, actor = settings(environ)
    pool = pool or pool_of(environ)
    token = take_held(held_file(environ))
    slot = pool.store(token, actor)
    github.comment(f"{STORED_MARK}\n{slot}")
    print(f"Stored the token in the organization's slot {slot}.", flush=True)


def fail(environ):
    """A word on the issue for a run that stopped before the script could say why,
    as when the App's token is refused or the job is skipped, so the page does not
    wait its fifteen minutes; none when the run said so already."""
    # the key is no matter here, and the step that failed may have been given none
    github, *_ = settings(environ, sealing=False)
    said = [c.get("body", "") for c in github.comments() if (c.get("user") or {}).get("login") == "github-actions[bot]"]
    if any(body.startswith(FAILED_MARK) for body in said):
        return
    github.comment(f"{FAILED_MARK}\n{environ.get('FAIL_WHY') or 'the run stopped before the token was saved; see its log under Actions, workflow Token'}")


STAGES = {"sign-in": run, "store": store, "fail": fail}


def main(argv=None):
    stage = (argv if argv is not None else sys.argv[1:] or ["sign-in"])[0]
    if stage not in STAGES:
        print(f"token_run: no stage {stage!r}; the stages are {', '.join(STAGES)}", file=sys.stderr)
        return 2
    try:
        STAGES[stage](os.environ)
    except Exception as error:
        # every failure reaches the page as a word, but only a RunError's own
        # words, which never hold a token; anything else by its kind alone
        known = isinstance(error, (RunError, sealbox.SealError, tokens.TokensError))
        why = str(error) if known else f"the run failed ({type(error).__name__}); see its log under Actions, workflow Token"
        print(f"token_run: {why}", file=sys.stderr)
        if stage != "fail":
            try:
                github, *_ = settings(os.environ, sealing=False)
                github.comment(f"{FAILED_MARK}\n{why}")
            except Exception:
                pass
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
