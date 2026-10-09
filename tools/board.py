"""Render the board and nudge the pull requests that wait.

The board is the file STATE.md on the branch "board": what GitHub knows
about the repository's open work, rewritten by .github/workflows/board.yml
so every Claude session and every account reads the same page instead of
asking the API. The file holds no wall-clock value and its rows are sorted,
so the same repository state renders the same bytes and the workflow writes
the branch only when something moved. docs/agents/STATE.md on the default
branch only describes the layout rendered here.

Comments are the board's one side effect. After a push to the default
branch, a pull request behind it or in conflict with it hears so once per
commit of the default branch; a pull request nobody touched for a day is
asked once whether it is parked. Each comment starts with an HTML marker and
is posted only when no comment on that pull request carries the marker.

Everything comes from GitHub's REST API through urllib with GITHUB_TOKEN;
--dry-run FIXTURE renders a JSON snapshot instead, with no network and no
token, and --render-only writes the file without commenting.
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API = "https://api.github.com"
API_VERSION = "2022-11-28"
USER_AGENT = "sdlc-board"
TIMEOUT = 60
PER_PAGE = 100
# GitHub computes mergeability after the first ask; one more ask after a
# pause is enough, and "unknown" is the honest word when it still has not.
MERGEABLE_RETRY_SECONDS = 3
IDLE_AFTER = timedelta(hours=24)
RECENT_MERGED = 5
# The workflow writes the board to the branch "board", so the default is a
# file in the current directory, not a path inside the checkout.
STATE_PATH = Path("STATE.md")
CLAIM_BRANCH_PREFIX = "claude/"
CLAIM_DIR = "docs/agents/claims"
NO_CLAIM_FILE = "no claim file yet"
# A claim branch that outlived its issue: the row stays, and says what to do.
ISSUE_CLOSED = "issue closed"
DELETE_BRANCH = "delete the branch"
ACCOUNT_LABEL_PREFIX = "account:"

MAIN_MOVED_MARKER = "<!-- sdlc-board: main-moved {sha} -->"
IDLE_MARKER = "<!-- sdlc-board: idle -->"
IDLE_TEXT = (
    "idle: no change for more than a day; if this work is parked, say so "
    "here, or the coordinator may release the claim."
)

CLAIM_HEADING = "## Claims (open claude/<issue> branches and docs/agents/claims/<issue>.md)"
CLAIM_COLUMNS = ("Issue", "Branch", "Account", "PR", "Files it touches")
PULL_HEADING = "## Open pull requests"
PULL_COLUMNS = ("PR", "Title", "Branch", "State (clean, behind, conflicting, blocked, unknown)", "Last update")
QUEUE_HEADING = "## Queue (open issues labelled todo, unclaimed)"
ISSUE_COLUMNS = ("Issue", "Title", "Labels")
BLOCKER_HEADING = "## Blockers (open issues labelled blocker)"
MERGED_HEADING = f"## Recently merged (the last {RECENT_MERGED})"
MERGED_COLUMNS = ("PR", "Title", "Branch", "Merged")

ACCOUNT_LINE = re.compile(r"^\W*account\W*:\s*(.+?)\s*$", re.IGNORECASE)
# A note in parentheses after the account, like the claim template's
# "(label account:main)", is for the reader, not the board.
TRAILING_NOTE = re.compile(r"\s*\(.*\)\s*$")
FILES_HEADING = re.compile(r"^#+\s*files to touch\s*$", re.IGNORECASE)
LIST_ITEM = re.compile(r"^\s*[-*]\s+(.+?)\s*$")


class BoardError(Exception):
    """A call that failed; the message names the status and the path, never
    the token."""


def parse_time(value):
    """An ISO 8601 time as GitHub or git writes it, as an aware datetime."""
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    moment = datetime.fromisoformat(text)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


def next_link(headers):
    """The URL of the next page named by a Link header, or None."""
    link = (headers.get("Link") if headers is not None else None) or ""
    for part in link.split(","):
        pieces = part.split(";")
        if len(pieces) >= 2 and pieces[1].strip() == 'rel="next"':
            return pieces[0].strip().strip("<>")
    return None


class GitHub:
    """The few REST calls the board makes, through urllib.

    The opener and the sleep are arguments so a test can hand in fakes; the
    token travels once per call, in the Authorization header.
    """

    def __init__(self, token, repo, opener=None, sleep=time.sleep):
        self.token = token
        self.repo = repo
        self.opener = opener or urllib.request.build_opener()
        self.sleep = sleep

    def headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": USER_AGENT,
        }

    def url(self, path, params=None):
        return API + path + ("?" + urllib.parse.urlencode(params) if params else "")

    def request(self, method, url, body=None, missing_ok=False):
        """One call; the decoded JSON and the answer's headers."""
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = self.headers()
        if data is not None:
            headers["Content-Type"] = "application/json"
        call = urllib.request.Request(url, data=data, method=method, headers=headers)
        where = f"{method} {urllib.parse.urlsplit(url).path}"
        try:
            with self.opener.open(call, timeout=TIMEOUT) as answer:
                raw = answer.read()
                return (json.loads(raw) if raw else None), answer.headers
        except urllib.error.HTTPError as problem:
            if problem.code == 404 and missing_ok:
                return None, problem.headers
            raise BoardError(f"{where}: HTTP {problem.code}") from None
        except OSError as problem:
            raise BoardError(f"{where}: {getattr(problem, 'reason', problem)}") from None
        except ValueError:
            raise BoardError(f"{where}: the answer was not JSON") from None

    def get(self, path, params=None, missing_ok=False):
        data, _ = self.request("GET", self.url(path, params), missing_ok=missing_ok)
        return data

    def pages(self, path, params=None):
        """A list endpoint page by page, following the Link header, so a
        caller that has seen enough can stop asking."""
        params = dict(params or {})
        params["per_page"] = PER_PAGE
        url = self.url(path, params)
        while url:
            data, headers = self.request("GET", url)
            yield data or []
            url = next_link(headers)

    def get_all(self, path, params=None):
        """Every item of a list endpoint."""
        return [item for page in self.pages(path, params) for item in page]

    def post(self, path, body):
        data, _ = self.request("POST", self.url(path), body=body)
        return data


def branch_name(branch):
    """A branch as a name, whether the API's object or a fixture's string."""
    return branch if isinstance(branch, str) else branch["name"]


def claim_branches(branches):
    return [branch_name(b) for b in branches if branch_name(b).startswith(CLAIM_BRANCH_PREFIX)]


def claim_key(branch):
    """What follows claude/ in a claim branch: the issue number by protocol."""
    return branch_name(branch)[len(CLAIM_BRANCH_PREFIX):]


def label_names(issue):
    return sorted(l if isinstance(l, str) else l["name"] for l in issue.get("labels") or [])


def pull_with_detail(api, number):
    """One pull request with its mergeable_state settled and its file paths."""
    path = f"/repos/{api.repo}/pulls/{number}"
    detail = api.get(path)
    if detail.get("mergeable") is None:
        api.sleep(MERGEABLE_RETRY_SECONDS)
        detail = api.get(path)
    if detail.get("mergeable") is None:
        detail["mergeable_state"] = "unknown"
    detail["files"] = [f["filename"] for f in api.get_all(path + "/files")]
    return detail


def claim_text(api, branch):
    """The claim file on a claude/<issue> branch, or None when there is none yet."""
    found = api.get(
        f"/repos/{api.repo}/contents/{CLAIM_DIR}/{claim_key(branch)}.md",
        {"ref": branch_name(branch)}, missing_ok=True,
    )
    if found is None:
        return None
    return base64.b64decode(found.get("content") or "").decode("utf-8", "replace")


def recent_merged(api):
    """The pull requests merged last, newest first, at most RECENT_MERGED, from
    the first page of closed pull requests by last update (a hundred). The
    list depends on the repository alone, so two runs in a row render the
    same one. It used to be the merges since the previous board's commit, and
    a merge fires two runs (the pull request closing and the push to the
    default branch): the second measured from the first's commit and lost
    the merge it had just reported."""
    for page in api.pages(f"/repos/{api.repo}/pulls", {"state": "closed", "sort": "updated", "direction": "desc"}):
        merged = [p for p in page if p.get("merged_at")]
        merged.sort(key=lambda p: p["merged_at"], reverse=True)
        return merged[:RECENT_MERGED]
    return []


def claim_issues(api, branches, open_issues):
    """The issue behind each claim branch, by number: the state and the label
    names. An open issue comes from the list already read; any other takes one
    call, so the board can say that a branch outlived its issue. A branch
    whose name is not a number has none."""
    by_number = {str(i["number"]): i for i in open_issues}
    found = {}
    for branch in claim_branches(branches):
        key = claim_key(branch)
        if not key.isdigit():
            continue
        issue = by_number.get(key) or api.get(f"/repos/{api.repo}/issues/{key}", missing_ok=True)
        if issue is not None:
            found[key] = {"state": issue.get("state", ""), "labels": label_names(issue)}
    return found


def collect(api, sha, default_branch):
    """Everything the board renders, in the shape a --dry-run fixture has."""
    repo = api.repo
    issues = [i for i in api.get_all(f"/repos/{repo}/issues", {"state": "open"}) if "pull_request" not in i]
    pulls = [pull_with_detail(api, p["number"]) for p in api.get_all(f"/repos/{repo}/pulls", {"state": "open"})]
    branches = claim_branches(api.get_all(f"/repos/{repo}/branches"))
    claims = {claim_key(b): claim_text(api, b) for b in branches}
    return {
        "sha": sha,
        "default_branch": default_branch,
        "issues": issues,
        "pulls": pulls,
        "branches": branches,
        "claims": claims,
        "claim_issues": claim_issues(api, branches, issues),
        "merged": recent_merged(api),
    }


def load_fixture(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def short_sha(sha):
    return (sha or "")[:7] or "unknown"


def pr_state(pull):
    """One of the five words the board uses for a pull request. GitHub's
    has_hooks and unstable are mergeable states (the checks are what they
    are), so they read as clean; blocked is a computed state of its own;
    unknown is kept for a state GitHub has not computed yet."""
    state = pull.get("mergeable_state")
    if state in ("clean", "behind"):
        return state
    if state in ("has_hooks", "unstable"):
        return "clean"
    if state == "dirty":
        return "conflicting"
    if state == "blocked":
        return "blocked"
    return "unknown"


def claim_account(text):
    """The account a claim file names, from a line like "Account: main" in
    any of the Markdown spellings a hand might give it, without a note in
    parentheses after it."""
    for line in text.splitlines():
        match = ACCOUNT_LINE.match(line)
        if match:
            return TRAILING_NOTE.sub("", match.group(1)).strip("`*_ ")
    return "unnamed"


def claim_files(text):
    """The paths a claim file lists under its "Files to touch" heading, one
    list line each, up to the next heading: what the board shows for a claim
    whose pull request does not exist yet."""
    files = []
    inside = False
    for line in text.splitlines():
        if FILES_HEADING.match(line):
            inside = True
            continue
        if inside and line.startswith("#"):
            break
        match = LIST_ITEM.match(line) if inside else None
        if match:
            files.append(match.group(1).strip("`"))
    return sorted(files)


def by_number(value):
    """A sort key that puts numbers in order and anything else after them."""
    text = str(value)
    return (0, int(text), "") if text.isdigit() else (1, 0, text)


def issue_ref(key):
    return f"#{key}" if key.isdigit() else key


def cell(value):
    """A table cell: one line, ASCII, pipes escaped, so the board stays a
    valid table and passes the repository's own ASCII check."""
    text = str(value).replace("\r", " ").replace("\n", " ").replace("|", "\\|")
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().strip()


def table(columns, rows):
    """A Markdown table; an empty one keeps its header and says (none), so
    the layout is the same whatever the repository holds."""
    lines = ["| " + " | ".join(columns) + " |", "|" + " --- |" * len(columns)]
    for row in rows or [["(none)"] + [""] * (len(columns) - 1)]:
        lines.append("| " + " | ".join(cell(c) for c in row) + " |")
    return lines


def account_label(issue):
    """The account an issue's label names (account:main gives main), or None."""
    for name in label_names(issue or {}):
        if name.startswith(ACCOUNT_LABEL_PREFIX):
            return name[len(ACCOUNT_LABEL_PREFIX):]
    return None


def claim_row(key, branch, text, pull, issue):
    """One claim as the board shows it. The account is the claim file's, or
    the issue's label once the finishing pull request has deleted the file.
    A branch whose issue is closed is a leftover: the row says so in place of
    the pull request and asks for the branch to go in place of the files."""
    closed = bool(issue) and issue.get("state") == "closed"
    if pull:
        files = sorted(pull.get("files") or [])
    else:
        files = claim_files(text) if text else []
    if pull:
        pull_cell = f"#{pull['number']}"
    elif closed:
        pull_cell = ISSUE_CLOSED
    else:
        pull_cell = "(no pull request yet)"
    if files:
        files_cell = ", ".join(files)
    elif closed and not pull:
        files_cell = DELETE_BRANCH
    else:
        files_cell = "-"
    account = claim_account(text) if text else (account_label(issue) or NO_CLAIM_FILE)
    return [issue_ref(key), branch, account, pull_cell, files_cell]


def claim_rows(snap):
    pulls_by_branch = {p["head"]["ref"]: p for p in snap["pulls"]}
    issues = snap.get("claim_issues") or {}
    rows = []
    for branch in sorted(claim_branches(snap["branches"]), key=lambda b: by_number(claim_key(b))):
        key = claim_key(branch)
        text = (snap.get("claims") or {}).get(key)
        rows.append(claim_row(key, branch, text, pulls_by_branch.get(branch), issues.get(key)))
    return rows


def pull_rows(snap):
    return [
        [f"#{p['number']}", p.get("title", ""), p["head"]["ref"], pr_state(p), p.get("updated_at", "")]
        for p in sorted(snap["pulls"], key=lambda p: p["number"])
    ]


def claimed_numbers(branches):
    return {int(claim_key(b)) for b in claim_branches(branches) if claim_key(b).isdigit()}


def issue_rows(snap, label, unclaimed_only):
    claimed = claimed_numbers(snap["branches"])
    rows = []
    for issue in sorted(snap["issues"], key=lambda i: i["number"]):
        labels = label_names(issue)
        if label not in labels:
            continue
        if unclaimed_only and ("claimed" in labels or issue["number"] in claimed):
            continue
        rows.append([f"#{issue['number']}", issue.get("title", ""), ", ".join(labels)])
    return rows


def merged_rows(snap):
    return [
        [f"#{p['number']}", p.get("title", ""), p["head"]["ref"], p.get("merged_at", "")]
        for p in sorted(snap.get("merged") or [], key=lambda p: p.get("merged_at") or "", reverse=True)
    ]


def render(snap):
    """STATE.md for a snapshot: the layout docs/agents/STATE.md describes."""
    branch = cell(snap.get("default_branch") or "main")
    lines = [
        "# Board",
        "",
        f"As of commit {cell(short_sha(snap.get('sha')))} on {branch}. "
        "Rewritten by .github/workflows/board.yml; do not edit by hand.",
    ]
    sections = (
        (CLAIM_HEADING, CLAIM_COLUMNS, claim_rows(snap)),
        (PULL_HEADING, PULL_COLUMNS, pull_rows(snap)),
        (QUEUE_HEADING, ISSUE_COLUMNS, issue_rows(snap, "todo", True)),
        (BLOCKER_HEADING, ISSUE_COLUMNS, issue_rows(snap, "blocker", False)),
        (MERGED_HEADING, MERGED_COLUMNS, merged_rows(snap)),
    )
    for heading, columns, rows in sections:
        lines += ["", heading, ""] + table(columns, rows)
    return "\n".join(lines) + "\n"


def write_if_changed(path, text):
    """Write the board only when its bytes differ, so a caller comparing
    files sees no change when nothing moved."""
    data = text.encode("ascii")
    if path.is_file() and path.read_bytes() == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return True


def pulls_behind_main(pulls):
    """The pull requests the main-moved rule speaks to: behind or conflicting,
    and only those."""
    return [p for p in pulls if pr_state(p) in ("behind", "conflicting")]


def idle_pulls(pulls, now):
    return [p for p in pulls if now - parse_time(p["updated_at"]) > IDLE_AFTER]


def main_moved_text(state, default_branch, sha7):
    how = "behind" if state == "behind" else "conflicting with"
    return (
        f"main moved: this branch is {how} {default_branch} at {sha7}; "
        f"rebase or merge {default_branch} before the next push."
    )


def comment_once(api, number, marker, text):
    """Post the comment unless one on the pull request carries the marker."""
    comments = api.get_all(f"/repos/{api.repo}/issues/{number}/comments")
    if any(marker in (c.get("body") or "") for c in comments):
        return False
    api.post(f"/repos/{api.repo}/issues/{number}/comments", {"body": marker + "\n" + text})
    return True


def post_comments(api, snap, event_name, ref_name, now):
    """The comments this run posted, one line each."""
    posted = []
    default_branch = snap["default_branch"]
    if event_name == "push" and ref_name == default_branch:
        sha7 = short_sha(snap.get("sha"))
        marker = MAIN_MOVED_MARKER.format(sha=sha7)
        for pull in pulls_behind_main(snap["pulls"]):
            text = main_moved_text(pr_state(pull), default_branch, sha7)
            if comment_once(api, pull["number"], marker, text):
                posted.append(f"PR #{pull['number']}: main-moved comment posted")
    for pull in idle_pulls(snap["pulls"], now):
        if comment_once(api, pull["number"], IDLE_MARKER, IDLE_TEXT):
            posted.append(f"PR #{pull['number']}: idle comment posted")
    return posted


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Render the board (STATE.md) and comment on waiting pull requests.")
    parser.add_argument("--dry-run", metavar="FIXTURE", help="render this JSON snapshot instead of asking GitHub")
    parser.add_argument("--render-only", action="store_true", help="write the board and post no comment")
    parser.add_argument("--out", help=f"where to write the board (default: {STATE_PATH} in the current directory; stdout with --dry-run)")
    parser.add_argument("--default-branch", default="main", help="the default branch's name (default: main)")
    parser.add_argument("--sha", help="the default branch's commit the board describes (default: GITHUB_SHA)")
    return parser.parse_args(argv)


def run_dry(args):
    text = render(load_fixture(args.dry_run))
    if args.out:
        write_if_changed(Path(args.out), text)
    else:
        sys.stdout.write(text)
    return 0


def run_live(args):
    env = os.environ
    token = env.get("GITHUB_TOKEN")
    repo = env.get("GITHUB_REPOSITORY")
    if not token or not repo:
        raise BoardError("GITHUB_TOKEN and GITHUB_REPOSITORY must be set")
    event = env.get("GITHUB_EVENT_NAME", "")
    ref_name = env.get("GITHUB_REF_NAME", "")
    api = GitHub(token, repo)
    snap = collect(api, args.sha or env.get("GITHUB_SHA", ""), args.default_branch)
    out = Path(args.out) if args.out else STATE_PATH
    changed = write_if_changed(out, render(snap))
    print(f"{out.as_posix()}: {'rewritten' if changed else 'unchanged'}")
    if not args.render_only:
        for line in post_comments(api, snap, event, ref_name, datetime.now(timezone.utc)):
            print(line)
    return 0


def main(argv=None):
    args = parse_args(argv)
    try:
        return run_dry(args) if args.dry_run else run_live(args)
    except BoardError as problem:
        print(f"board: {problem}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
