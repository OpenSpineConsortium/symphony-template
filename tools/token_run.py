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

  python3 tools/token_run.py   with ISSUE, KEY, KEY_ID, ACTOR, GITHUB_REPOSITORY and GITHUB_TOKEN set
"""

import base64
import codecs
import json
import os
import re
import select
import sys
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sealbox  # noqa: E402
import tokens  # noqa: E402

LINK_MARK = "<!-- symphony-token: sign-in -->"
CODE_MARK = "<!-- symphony-token: code -->"
SEALED_MARK = "<!-- symphony-token: sealed -->"
FAILED_MARK = "<!-- symphony-token: failed -->"
SIGN_IN_LINK = re.compile(r"https://claude\.(?:ai|com)/[A-Za-z0-9/._-]*oauth/authorize\?[A-Za-z0-9%&=._~+-]+")
CODE_SHAPE = re.compile(r"^[A-Za-z0-9_.~#-]{8,512}$")
ISSUE_SHAPE = re.compile(r"^[1-9][0-9]{0,8}$")
KEY_ID_SHAPE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
WAIT_FOR_LINK = 90
WAIT_FOR_CODE = 600
WAIT_FOR_TOKEN = 60
POLL_EVERY = 3
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
            for name in ("COLUMNS", "LINES"):
                os.environ.pop(name, None)
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


def settings(environ):
    issue, key, key_id = environ.get("ISSUE", ""), environ.get("KEY", ""), environ.get("KEY_ID", "")
    actor, repo, token = environ.get("ACTOR", ""), environ.get("GITHUB_REPOSITORY", ""), environ.get("GITHUB_TOKEN", "")
    if not ISSUE_SHAPE.match(issue):
        raise RunError("the run was not given the page's issue")
    if not KEY_ID_SHAPE.match(key_id):
        raise RunError("the run was not given the secrets key's id")
    if not actor or not repo or not token:
        raise RunError("the run lacks its actor, repository or token")
    return GitHub(repo, token, issue), sealbox.key_from_base64(key), key_id, actor


def run(environ, start=Claude):
    github, key, key_id, actor = settings(environ)
    claude = start()
    try:
        github.comment(f"{LINK_MARK}\n{wait_for_link(claude)}")
        print("Posted the sign-in link; waiting for the code.", flush=True)
        code, comment_id = wait_for_code(github, claude, actor)
        print(f"::add-mask::{code}", flush=True)
        github.delete_comment(comment_id)
        claude.type(code + "\r")
        try:
            token = wait_for_token(claude)
        except RunError as error:
            said = claude_said(claude, code)
            print(f"claude's last words: {said}", flush=True)
            raise RunError(f"{error}. claude said: {said}") from None
        sealed = base64.b64encode(sealbox.seal(token.encode(), key)).decode()
        github.comment(f"{SEALED_MARK}\n{key_id}\n{sealed}")
        print("Posted the sealed token.", flush=True)
    finally:
        claude.finish()


def main():
    try:
        run(os.environ)
    except (RunError, sealbox.SealError, tokens.TokensError) as error:
        print(f"token_run: {error}", file=sys.stderr)
        try:
            github, *_ = settings(os.environ)
            github.comment(f"{FAILED_MARK}\n{error}")
        except Exception:
            pass
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
