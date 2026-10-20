"""The digest through GitHub alone: progress and the decisions waiting on
the owner, posted as a comment on one issue that mentions the owner, so
GitHub's own notification email carries it to the owner's inbox, and the
owner's reply to that email, which GitHub posts back as a comment, does
what it asks.

This is the native route the owner chose on 2026-10-20 in place of sending
from the Wayne State mailbox through Microsoft Graph: no Graph permission,
no mail server, no secret and no Claude, only GITHUB_TOKEN in
.github/workflows/digest.yml. What it gives up is the button: GitHub's
email carries no Outlook card, so an answer is a line of the reply, such as
"12 Accept", which tools/outlook_digest.py already reads. Everything else
the reply says opens an issue labelled from-email for Claude, as there.

  python3 tools/github_digest.py post --repo OWNER/NAME --to LOGIN
  python3 tools/github_digest.py answer --repo OWNER/NAME --to LOGIN --comment COMMENT.json

post finds or opens the digest issue (labelled digest, opened by the
workflow) and comments the digest on it, only when something was done
since the last digest or a decision is new since then. answer reads one
comment on the digest issue and, when its author is the digest's
recipient, makes the operations outlook_digest.plan gives: a comment on a
decision and its label off, a proposal closed, a project accepted by
starting drive-organize.yml's accept, a new issue for anything else.
Standard library and the gh command only.
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import outlook_digest as od  # noqa: E402

LABEL = "digest"
TITLE = "Symphony digest"
MARKER = re.compile(r"<!-- symphony-digest: (symphony-digest-[0-9]{12}) decisions=([0-9,]*) -->")
ISSUE_MARKER = "<!-- symphony-digest-issue -->"
BOT = "github-actions[bot]"
MAY_ANSWER = {"OWNER", "MEMBER", "COLLABORATOR"}
WHERE = "the digest email"


def gh(args, payload=None):
    done = subprocess.run(["gh"] + args, input=payload, capture_output=True, text=True)
    if done.returncode != 0:
        raise DigestError(f"gh {' '.join(args[:3])}: {done.stderr.strip()[:300]}")
    return done.stdout


class DigestError(Exception):
    pass


class GitHub:
    """The few calls the digest makes, on one repository."""

    def __init__(self, repo, run=gh):
        self.repo, self.run = repo, run

    def api(self, method, path, payload=None):
        args = ["api", "-X", method, f"repos/{self.repo}/{path}"]
        if payload is not None:
            args += ["--input", "-"]
        out = self.run(args, None if payload is None else json.dumps(payload))
        return json.loads(out) if out.strip() else {}

    def list(self, path):
        out = self.run(["api", "--paginate", "--slurp", f"repos/{self.repo}/{path}"])
        pages = json.loads(out) if out.strip() else []
        return [item for page in pages for item in page]


# Composing

def mention_safe(text):
    """A title in a code span, so an @name or #number in it pings and links nobody."""
    return "`" + od.plain(text).replace("\n", " ").strip() + "`"


def digest_issue(issues):
    """The open issue the workflow opened for the digest, or None."""
    for issue in issues:
        if issue.get("state") == "open" and (issue.get("user") or {}).get("login") == BOT \
                and LABEL in od.labels_of(issue) and ISSUE_MARKER in (issue.get("body") or ""):
            return issue
    return None


def last_digest(comments):
    """(when, decision numbers) of the latest digest comment, or (None, set())."""
    for comment in reversed(comments):
        found = MARKER.search(comment.get("body") or "")
        if found and (comment.get("user") or {}).get("login") == BOT:
            numbers = {int(n) for n in found.group(2).split(",") if n}
            return comment.get("created_at"), numbers
    return None, set()


def body(to, digest, decisions, done):
    """The digest comment, in Markdown, with the marker the next run reads."""
    numbers = ",".join(str(d.number) for d in decisions)
    lines = [f"<!-- symphony-digest: {digest} decisions={numbers} -->", f"@{to}, here is your Symphony digest.", ""]
    if done:
        lines.append("**Done since the last digest**")
        lines += [f"- #{i['number']} {mention_safe(i.get('title', ''))}" for i in done[:od.LIST_LINES]]
        if len(done) > od.LIST_LINES:
            lines.append(f"- and {len(done) - od.LIST_LINES} more")
        lines.append("")
    if decisions:
        lines.append("**Waiting on you**")
        for decision in decisions:
            lines.append(f"- #{decision.number} {mention_safe(decision.title)}")
            for name, consequence in decision.options:
                mark = " (recommended)" if name == decision.recommended else ""
                lines.append(f"  - **{name}**{mark}: {mention_safe(consequence)}")
        lines.append("")
    lines.append("Reply to this email, or comment here, with one line per answer, such as `12 Accept`. "
                 "Anything else you write becomes a new task for Claude.")
    return "\n".join(lines)


def worth_sending(decisions, done, previous):
    return bool(done) or not {d.number for d in decisions} <= previous


def closed_since(issues, since):
    return [i for i in od.done_in(issues) if not since or (i.get("closed_at") or "") > since]


def ensure_label(github):
    if LABEL not in {label.get("name") for label in github.list("labels?per_page=100")}:
        github.api("POST", "labels", {"name": LABEL, "color": "c5def5", "description": "The digest GitHub emails the owner"})


def post(github, to, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    issue = digest_issue(github.list(f"issues?state=open&labels={LABEL}&per_page=100"))
    comments = github.list(f"issues/{issue['number']}/comments?per_page=100") if issue else []
    since, previous = last_digest(comments)
    if since is None:
        since = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    open_ones = github.list("issues?state=open&labels=decision&per_page=100") + \
        github.list("issues?state=open&labels=proposed&per_page=100")
    decisions = od.decisions_in({i["number"]: i for i in open_ones}.values())
    done = closed_since(github.list(f"issues?state=closed&since={urllib.parse.quote(since)}&per_page=100"), since)
    if not worth_sending(decisions, done, previous):
        return "nothing new since the last digest; nothing posted"
    if issue is None:
        ensure_label(github)
        issue = github.api("POST", "issues", {"title": TITLE, "labels": [LABEL], "body": (
            f"{ISSUE_MARKER}\nThe digest of this repository's progress and the decisions waiting on @{to}, "
            "posted here as a comment so GitHub emails it. Reply to the email, or comment here, to answer.")})
    github.api("POST", f"issues/{issue['number']}/comments", {"body": body(to, od.digest_id(now), decisions, done)})
    return f"posted to #{issue['number']}: {len(done)} done, {len(decisions)} decisions"


# Answering

def read_answer(text, decisions):
    """(answers, prompt) from a reply: a line such as "12 Accept" per answer."""
    by_number = {d.number: d for d in decisions}
    answers, rest = [], []
    # Every line that reads as an answer goes to plan, which refuses one
    # whose issue waits on no decision or has no such option, so a stale or
    # misspelled answer is said back and never becomes a task for Claude.
    for line in od.strip_quote(text).split("\n"):
        command = od.COMMAND.match(line)
        if command:
            decision = by_number.get(int(command.group(1)))
            label = decision.option(command.group(2)) if decision else None
            answers.append((int(command.group(1)), label or command.group(2), ""))
        else:
            rest.append(line)
    return answers, "\n".join(rest).strip()


def may_answer(comment, to):
    author = (comment.get("user") or {}).get("login", "")
    return author.lower() == to.lower() and comment.get("author_association") in MAY_ANSWER


def apply(github, ops, digest_number, default_branch):
    """Make each operation; a refusal or a failure is said on the digest
    issue, and one failure stops none of the others."""
    said, failed = [], False
    for op in ops:
        try:
            done = apply_one(github, op, default_branch)
        except DigestError as problem:
            done, failed = f"failed: {op['op']} ({problem})", True
        if done:
            said.append(done)
    if said:
        github.api("POST", f"issues/{digest_number}/comments", {"body": "From your reply: " + "; ".join(said) + "."})
    if failed:
        raise DigestError("; ".join(said))
    return said


def apply_one(github, op, default_branch):
    kind = op["op"]
    if kind == "comment":
        github.api("POST", f"issues/{op['issue']}/comments", {"body": op["body"]})
        return f"commented on #{op['issue']}"
    if kind == "unlabel":
        try:
            github.api("DELETE", f"issues/{op['issue']}/labels/{urllib.parse.quote(op['label'], safe='')}")
        except DigestError as problem:
            if "404" not in str(problem) and "Not Found" not in str(problem):
                raise  # only a label already gone counts as taken off
        return ""
    if kind == "close":
        github.api("PATCH", f"issues/{op['issue']}", {"state": "closed", "state_reason": op["reason"]})
        return f"closed #{op['issue']}"
    if kind == "accept_project":
        github.api("POST", "actions/workflows/drive-organize.yml/dispatches",
                   {"ref": default_branch, "inputs": {"step": "accept", "epic": str(op["epic"])}})
        return f"started accepting #{op['epic']}"
    if kind == "open_issue":
        made = github.api("POST", "issues", {"title": op["title"][:250], "body": op["body"], "labels": op["labels"]})
        return f"opened #{made.get('number')} for Claude"
    if kind == "refuse":
        return "not done: " + op["why"]
    return ""


def answer(github, to, comment, default_branch):
    issues = github.list(f"issues?state=open&labels={LABEL}&per_page=100")
    issue = digest_issue(issues)
    if issue is None or not comment.get("issue_url", "").endswith(f"/issues/{issue['number']}"):
        return "not a comment on the digest issue; nothing done"
    to = to or addressed(github.list(f"issues/{issue['number']}/comments?per_page=100"))
    if not to or not may_answer(comment, to):
        return "the comment is not the digest recipient's; nothing done"
    open_ones = github.list("issues?state=open&labels=decision&per_page=100") + \
        github.list("issues?state=open&labels=proposed&per_page=100")
    decisions = od.decisions_in({i["number"]: i for i in open_ones}.values())
    answers, prompt = read_answer(comment.get("body") or "", decisions)
    ops = od.plan(answers, prompt, decisions, where=WHERE)
    return "; ".join(apply(github, ops, issue["number"], default_branch)) or "nothing to do"


LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})")
ADDRESSED = re.compile(r"^@(" + LOGIN.pattern + r"), here is your Symphony digest\.$", re.MULTILINE)


def recipient(codeowners, owner, owner_type, actor=""):
    """The login the digest goes to: CODEOWNERS' first user, else a user's
    repository's owner, else the person the run is for (who pressed Run, or
    for the schedule whoever last changed it), since an organization is no
    one to email and a template's CODEOWNERS is filled only in its copies."""
    for line in codeowners.splitlines():
        if line.strip().startswith("#"):
            continue
        for word in line.split()[1:]:
            if re.fullmatch(r"@[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", word):
                return word[1:]
    if owner_type == "User":
        return owner
    return actor if LOGIN.fullmatch(actor or "") else None


def addressed(comments):
    """The recipient the latest digest named, so an answer is checked
    against the person the digest went to, never against whoever answers."""
    for comment in reversed(comments):
        if (comment.get("user") or {}).get("login") == BOT and MARKER.search(comment.get("body") or ""):
            found = ADDRESSED.search(comment["body"])
            return found.group(1) if found else None
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("post", "answer"):
        step = sub.add_parser(name)
        step.add_argument("--repo", required=True)
        step.add_argument("--to", required=(name == "post"), help="answer: the latest digest's recipient when omitted")
        if name == "answer":
            step.add_argument("--comment", required=True, help="the issue_comment event's comment, as JSON")
            step.add_argument("--default-branch", default="main")
    found = sub.add_parser("recipient")
    found.add_argument("--owner-type", default="User")
    found.add_argument("--actor", default="")
    args = parser.parse_args(argv)
    try:
        if args.command == "recipient":
            return recipient_command(args)
        github = GitHub(args.repo)
        if args.command == "post":
            print(post(github, args.to))
        else:
            comment = json.loads(Path(args.comment).read_text(encoding="utf-8"))
            print(answer(github, args.to, comment, args.default_branch))
    except DigestError as problem:
        print(f"github_digest: {problem}", file=sys.stderr)
        return 1
    return 0


def recipient_command(args):
    path = Path(".github/CODEOWNERS")
    found = recipient(path.read_text(encoding="utf-8") if path.exists() else "",
                      os.environ.get("GITHUB_REPOSITORY_OWNER", ""), args.owner_type, args.actor)
    if not found:
        print("github_digest: no recipient; set the repository variable SYMPHONY_DIGEST_TO", file=sys.stderr)
        return 1
    print(found)
    return 0


if __name__ == "__main__":
    sys.exit(main())
