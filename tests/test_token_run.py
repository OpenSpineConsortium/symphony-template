"""tools/token_run.py mints one token on an Actions runner for the
Tokens page: the sign-in link out on the issue, the person's code in, the
token out only sealed. claude here is a stand-in script that prints the
link as claude setup-token does, an OSC 8 hyperlink, waits for the code
and prints a token of the subscription token's shape, built from pieces
so this file never looks like a secret; GitHub is a list of comments."""

import base64
import io
import json
import os
import stat
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "scripts"))

import sealbox  # noqa: E402
import token_run  # noqa: E402
import tokens  # noqa: E402

SECRET = bytes(range(32))
TOKEN = tokens.TOKEN_HEAD + "01-" + "Ab3_" * 24
LINK = "https://claude.com/cai/oauth/authorize?code=true&client_id=x&response_type=code&state=abc123"
CODE = "a1b2c3d4e5#state-f6"
STAND_IN = f'''#!/usr/bin/env python3
import sys
link = {LINK!r}
sys.stdout.write("Browser didn't open? \\x1b]8;id=1;" + link + "\\x07" + link + "\\x1b]8;;\\x07\\r\\n")
sys.stdout.write("Paste code here if prompted > ")
sys.stdout.flush()
code = sys.stdin.readline().strip()
if code != {CODE!r}:
    print("Invalid code")
    sys.exit(1)
print("Your OAuth token (valid for 1 year):")
print({TOKEN!r})
'''

# claude's screen reads keys raw and takes a chunk holding more than one key
# as a paste, so an Enter that arrives with the code is part of the paste
# and sends nothing; only an Enter of its own sends the code.
SCREEN_STAND_IN = f'''#!/usr/bin/env python3
import os, sys, time, tty
link = {LINK!r}
sys.stdout.write("Browser didn't open? " + link + "\\r\\n")
sys.stdout.flush()
# The question comes a moment after the link, in raw mode, which throws
# away any key typed before it: the run has to wait for the question.
time.sleep(1)
tty.setraw(0)
sys.stdout.write("Paste code here if prompted > ")
sys.stdout.flush()
typed = ""
while True:
    chunk = os.read(0, 4096).decode()
    if chunk == "\\r":
        break
    typed += chunk
if typed != {CODE!r}:
    print("Invalid code")
    sys.exit(1)
sys.stdout.write("Your OAuth token (valid for 1 year):\\r\\n" + {TOKEN!r} + "\\r\\n")
'''


class FakeGitHub(token_run.GitHub):
    def __init__(self, actor_code=None, poster="greg"):
        super().__init__("o/r", "t", "7")
        self.posted, self.deleted = [], []
        self.waiting = [{"id": 99, "user": {"login": poster}, "body": f"{token_run.CODE_MARK}\n{actor_code}"}] if actor_code else []

    def comment(self, body):
        self.posted.append(body)

    def comments(self):
        # The code arrives only once the link is out, as the page posts it.
        return list(self.waiting) if self.posted else []

    def delete_comment(self, comment_id):
        self.deleted.append(comment_id)


class TokenRunTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.use_stand_in(STAND_IN)
        self.environ = {"ISSUE": "7", "KEY": base64.b64encode(sealbox.public_key(SECRET)).decode(), "KEY_ID": "k1",
                        "ACTOR": "Greg", "GITHUB_REPOSITORY": "o/r", "GITHUB_TOKEN": "t"}
        token_run.WAIT_FOR_CODE = 5
        token_run.POLL_EVERY = 0.2

    def use_stand_in(self, script):
        self.claude = Path(self.folder) / "claude"
        self.claude.write_text(script)
        self.claude.chmod(self.claude.stat().st_mode | stat.S_IEXEC)

    def run_with(self, github):
        original = token_run.settings
        token_run.settings = lambda environ, **how: (github, *original(environ, **how)[1:])
        try:
            token_run.run(self.environ, start=lambda: token_run.Claude(command=(str(self.claude),)))
        finally:
            token_run.settings = original

    def test_the_token_leaves_only_sealed_for_the_pages_key(self):
        github = FakeGitHub(CODE)
        self.run_with(github)
        self.assertEqual(github.posted[0], f"{token_run.LINK_MARK}\n{LINK}")
        mark, key_id, sealed = github.posted[1].split("\n")
        self.assertEqual((mark, key_id), (token_run.SEALED_MARK, "k1"))
        self.assertEqual(sealbox.open_sealed(base64.b64decode(sealed), SECRET).decode(), TOKEN)
        self.assertNotIn(TOKEN, "".join(github.posted))
        self.assertEqual(github.deleted, [99])

    def test_the_enter_that_sends_the_code_is_a_key_of_its_own(self):
        self.use_stand_in(SCREEN_STAND_IN)
        github = FakeGitHub(CODE)
        self.run_with(github)
        mark, _, sealed = github.posted[1].split("\n")
        self.assertEqual(mark, token_run.SEALED_MARK)
        self.assertEqual(sealbox.open_sealed(base64.b64decode(sealed), SECRET).decode(), TOKEN)

    def test_claude_gets_a_terminal_type_where_the_runner_sets_none(self):
        self.use_stand_in("#!/bin/sh\necho \"term=$TERM\"\n")
        saved = os.environ.pop("TERM", None)
        try:
            claude = token_run.Claude(command=(str(self.claude),))
            while not claude.ended:
                claude.read(1)
            claude.finish()
        finally:
            if saved is not None:
                os.environ["TERM"] = saved
        self.assertIn("term=" + token_run.TERMINAL_TYPE, claude.seen)

    def test_a_code_from_anyone_else_is_never_typed(self):
        github = FakeGitHub(CODE, poster="someone-else")
        with self.assertRaisesRegex(token_run.RunError, "no code came"):
            self.run_with(github)
        self.assertEqual(len(github.posted), 1)

    def test_a_wrong_code_seals_nothing(self):
        github = FakeGitHub("wrong-code-1")
        with self.assertRaisesRegex(token_run.RunError, "claude said: .*Invalid code"):
            self.run_with(github)
        self.assertEqual(len(github.posted), 1)

    def test_settings_refuse_what_the_page_would_not_send(self):
        for name, value in (("ISSUE", "07"), ("KEY_ID", "a b"), ("KEY", "short")):
            with self.assertRaises((token_run.RunError, sealbox.SealError)):
                token_run.settings({**self.environ, name: value})


class FakeOrg:
    """The organization's Actions secrets and variables as GitHub's API
    answers them, for the run's own store into the pool."""

    def __init__(self, secrets=(), variables=None, refuse=""):
        self.secrets = {name: None for name in secrets}
        self.variables = dict(variables or {})
        self.reached = {}
        self.refuse = refuse
        self.calls = []

    def call(self, method, path, body=None):
        self.calls.append((method, path))
        if self.refuse and self.refuse in path and method != "GET":
            raise urllib.error.HTTPError(path, 403, "Forbidden", {}, io.BytesIO())
        base = "/orgs/acme/actions"
        if path.startswith(base + "/secrets?"):
            return {"secrets": [{"name": n} for n in sorted(self.secrets)]}
        if path == base + "/secrets/public-key":
            return {"key": base64.b64encode(sealbox.public_key(SECRET)).decode(), "key_id": "org-key"}
        if path.startswith(base + "/secrets/") and method == "PUT":
            self.secrets[path.rsplit("/", 1)[1]] = body
            return None
        if path.startswith(base + "/secrets/") and method == "GET":
            if path.rsplit("/", 1)[1] not in self.secrets:
                raise urllib.error.HTTPError(path, 404, "Not Found", {}, io.BytesIO())
            return {"name": path.rsplit("/", 1)[1]}
        if path == base + "/variables" and method == "POST":
            self.variables[body["name"]] = body["value"]
            self.reached[body["name"]] = body["selected_repository_ids"]
            return None
        if "/repositories/" in path and method == "PUT":
            name = path.split("/variables/")[1].split("/")[0]
            self.reached.setdefault(name, []).append(int(path.rsplit("/", 1)[1]))
            return None
        if path.startswith(base + "/variables/"):
            name = path.rsplit("/", 1)[1]
            if method == "PATCH":
                self.variables[name] = body["value"]
                return None
            if name not in self.variables:
                raise urllib.error.HTTPError(path, 404, "Not Found", {}, io.BytesIO())
            return {"name": name, "value": self.variables[name], "visibility": "selected"}
        raise AssertionError(f"unexpected call {method} {path}")


class PoolStoreTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        claude = Path(self.folder) / "claude"
        claude.write_text(STAND_IN)
        claude.chmod(claude.stat().st_mode | stat.S_IEXEC)
        self.command = (str(claude),)
        self.environ = {"ISSUE": "7", "ACTOR": "ashley", "GITHUB_REPOSITORY": "acme/r", "GITHUB_TOKEN": "t",
                        "STORE_ORG": "acme", "APP_TOKEN": "app", "REPO_ID": "42",
                        "TOKEN_FILE": os.path.join(self.folder, "held")}
        token_run.WAIT_FOR_CODE = 5
        token_run.POLL_EVERY = 0.2

    def store(self, org, poster="ashley"):
        github = FakeGitHub(CODE, poster=poster)
        original = token_run.settings
        token_run.settings = lambda environ, **how: (github, *original(environ, **how)[1:])
        try:
            token_run.run(self.environ, start=lambda: token_run.Claude(command=self.command))
            self.assertEqual(oct(os.stat(self.environ["TOKEN_FILE"]).st_mode & 0o777), "0o600")
            token_run.store(self.environ, pool=token_run.Pool("acme", "app", 42, call=org.call))
        finally:
            token_run.settings = original
        return github

    def test_the_token_goes_into_the_first_free_slot_marked_as_the_persons(self):
        org = FakeOrg(secrets=["SYMPHONY_CLAUDE_1", "SYMPHONY_CLAUDE_2"],
                      variables={"SYMPHONY_CLAUDE_ACCOUNTS": "1,2",
                                 "SYMPHONY_CLAUDE_SETTINGS": json.dumps({"1": {"model": "claude-opus-5-5"}})})
        github = self.store(org)
        self.assertEqual(github.posted[1], f"{token_run.STORED_MARK}\n3")
        put = org.secrets["SYMPHONY_CLAUDE_3"]
        self.assertEqual((put["key_id"], put["visibility"], put["selected_repository_ids"]), ("org-key", "selected", [42]))
        self.assertEqual(sealbox.open_sealed(base64.b64decode(put["encrypted_value"]), SECRET).decode(), TOKEN)
        self.assertEqual(org.variables["SYMPHONY_CLAUDE_ACCOUNTS"], "1,2,3")
        settings = json.loads(org.variables["SYMPHONY_CLAUDE_SETTINGS"])
        self.assertEqual(settings["1"], {"model": "claude-opus-5-5"})
        self.assertEqual(settings["3"]["owner"], "ashley")
        self.assertRegex(settings["3"]["id"], r"^[0-9a-f]{8}$")
        self.assertNotIn(TOKEN, "".join(github.posted))
        self.assertFalse(os.path.exists(self.environ["TOKEN_FILE"]))

    def test_a_slot_taken_while_the_run_looked_is_never_written_over(self):
        org = FakeOrg()
        listed = org.call

        def another_run_takes_slot_1(method, path, body=None):
            got = listed(method, path, body)
            if path.startswith("/orgs/acme/actions/secrets?"):
                org.secrets["SYMPHONY_CLAUDE_1"] = "theirs"
            return got
        org.call = another_run_takes_slot_1
        with self.assertRaisesRegex(token_run.RunError, "slot 1 was taken"):
            self.store(org)
        self.assertEqual(org.secrets["SYMPHONY_CLAUDE_1"], "theirs")
        self.assertFalse(os.path.exists(self.environ["TOKEN_FILE"]))

    def test_no_slot_that_holds_a_token_is_ever_written(self):
        org = FakeOrg(secrets=[f"SYMPHONY_CLAUDE_{n}" for n in range(1, 33)])
        with self.assertRaisesRegex(token_run.RunError, "all 32 slots"):
            self.store(org)
        self.assertFalse([c for c in org.calls if c[0] != "GET"])

    def test_variables_made_new_reach_the_repository(self):
        org = FakeOrg()
        self.store(org)
        self.assertEqual(org.variables["SYMPHONY_CLAUDE_ACCOUNTS"], "1")
        self.assertEqual(org.reached["SYMPHONY_CLAUDE_SETTINGS"], [42])

    def test_settings_that_are_not_json_by_slot_are_left_for_an_owner(self):
        org = FakeOrg(variables={"SYMPHONY_CLAUDE_SETTINGS": "[1, 2]"})
        with self.assertRaisesRegex(token_run.RunError, "slot 1.*not JSON by slot"):
            self.store(org)
        self.assertEqual(org.variables["SYMPHONY_CLAUDE_SETTINGS"], "[1, 2]")

    def test_a_refusal_from_github_is_said_in_words_the_page_shows(self):
        org = FakeOrg(refuse="/secrets/SYMPHONY_CLAUDE_")
        with self.assertRaisesRegex(token_run.RunError, "403 when the run tried to store the token in slot 1"):
            self.store(org)

    def test_store_mode_needs_its_organization_token_and_repository(self):
        for name, value in (("STORE_ORG", "-bad"), ("APP_TOKEN", ""), ("REPO_ID", "042")):
            with self.assertRaises(token_run.RunError):
                token_run.pool_of({**self.environ, name: value})

    def test_a_run_that_stopped_early_tells_the_page_once(self):
        github = FakeGitHub()
        github.comments = lambda: [{"user": {"login": "github-actions[bot]"}, "body": c} for c in github.posted]
        original = token_run.settings
        token_run.settings = lambda environ, **how: (github, *original(environ, **how)[1:])
        try:
            token_run.fail({**self.environ, "FAIL_WHY": "crowd mode"})
            token_run.fail(self.environ)
        finally:
            token_run.settings = original
        self.assertEqual(github.posted, [f"{token_run.FAILED_MARK}\ncrowd mode"])

    def test_an_unforeseen_failure_reaches_the_page_by_its_kind_alone(self):
        github = FakeGitHub()
        original_settings, original_store = token_run.settings, token_run.STAGES["store"]
        token_run.settings = lambda environ, **how: (github, None, "", "ashley")

        def broken(environ):
            raise KeyError("sk-" + "x" * 10)
        token_run.STAGES["store"] = broken
        try:
            self.assertEqual(token_run.main(["store"]), 1)
        finally:
            token_run.settings, token_run.STAGES["store"] = original_settings, original_store
        self.assertEqual(len(github.posted), 1)
        self.assertIn("(KeyError)", github.posted[0])
        self.assertNotIn("sk-", github.posted[0])

    def test_claude_never_sees_the_runs_tokens(self):
        script = Path(self.folder) / "env"
        script.write_text("#!/bin/sh\necho \"gh=${GITHUB_TOKEN:-none} app=${APP_TOKEN:-none}\"\n")
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
        saved = {k: os.environ.get(k) for k in token_run.WITHHELD}
        os.environ.update({k: "visible" for k in token_run.WITHHELD})
        try:
            claude = token_run.Claude(command=(str(script),))
            while not claude.ended:
                claude.read(1)
            claude.finish()
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.assertIn("gh=none app=none", claude.seen)


if __name__ == "__main__":
    unittest.main()
