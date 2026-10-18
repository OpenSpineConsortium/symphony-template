"""tools/token_run.py mints one token on an Actions runner for the
Tokens page: the sign-in link out on the issue, the person's code in, the
token out only sealed. claude here is a stand-in script that prints the
link as claude setup-token does, an OSC 8 hyperlink, waits for the code
and prints a token of the subscription token's shape, built from pieces
so this file never looks like a secret; GitHub is a list of comments."""

import base64
import os
import stat
import sys
import tempfile
import unittest
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
        folder = tempfile.mkdtemp()
        self.claude = Path(folder) / "claude"
        self.claude.write_text(STAND_IN)
        self.claude.chmod(self.claude.stat().st_mode | stat.S_IEXEC)
        self.environ = {"ISSUE": "7", "KEY": base64.b64encode(sealbox.public_key(SECRET)).decode(), "KEY_ID": "k1",
                        "ACTOR": "Greg", "GITHUB_REPOSITORY": "o/r", "GITHUB_TOKEN": "t"}
        token_run.WAIT_FOR_CODE = 5
        token_run.POLL_EVERY = 0.2

    def run_with(self, github):
        original = token_run.settings
        token_run.settings = lambda environ: (github, *original(environ)[1:])
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

    def test_a_code_from_anyone_else_is_never_typed(self):
        github = FakeGitHub(CODE, poster="someone-else")
        with self.assertRaisesRegex(token_run.RunError, "no code came"):
            self.run_with(github)
        self.assertEqual(len(github.posted), 1)

    def test_a_wrong_code_seals_nothing(self):
        github = FakeGitHub("wrong-code-1")
        with self.assertRaises(token_run.RunError):
            self.run_with(github)
        self.assertEqual(len(github.posted), 1)

    def test_settings_refuse_what_the_page_would_not_send(self):
        for name, value in (("ISSUE", "07"), ("KEY_ID", "a b"), ("KEY", "short")):
            with self.assertRaises((token_run.RunError, sealbox.SealError)):
                token_run.settings({**self.environ, name: value})


if __name__ == "__main__":
    unittest.main()
