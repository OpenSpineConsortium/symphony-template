"""Turn a fresh copy of the template into its own repository.

"Use this template" copies the files with their placeholders still in them.
This script, run once by .github/workflows/template-init.yml on the first
push, fills the five placeholders in every text file outside
.github/workflows/, removes the marker folder .template/ and, with a token,
makes the labels the board uses and opens the "Set up this project" issue.
The workflows are never written: they carry no placeholder, and the
GITHUB_TOKEN the workflow runs with may not create, change or delete a file
under .github/workflows/, so the init workflow stays in the tree and ends
early on every later push. The script prints each path it changed or
removed. Running it twice changes nothing the second time: the placeholders
are gone, the folder is gone, a label that exists is fine and an open setup
issue is not opened again.
"""

import argparse
import json
import os
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

API = "https://api.github.com"
API_VERSION = "2022-11-28"
USER_AGENT = "sdlc-template-init"
TIMEOUT = 60
PLACEHOLDER_NAMES = ("PROJECT_NAME", "REPO", "OWNER", "DEFAULT_BRANCH", "YEAR")
REMOVED = (".template",)
WORKFLOWS = (".github", "workflows")
WORKFLOWS_NOTE = "(workflows are left as they are: GITHUB_TOKEN may not write them)"
SETUP_ISSUE_TITLE = "Set up this project"
# The labels GitHub Issues needs to be the queue: name, colour, description.
LABELS = (
    ("todo", "0e8a16", "In the queue, open for a claim"),
    ("claimed", "fbca04", "A claude/<issue> branch holds it"),
    ("in-review", "1d76db", "A pull request is open and waiting"),
    ("blocker", "b60205", "Stops everyone until it is settled"),
    ("account:main", "5319e7", "Work for the main Claude account"),
)


class InitError(Exception):
    """Something the script could not do; the message never holds the token."""


def placeholder(name):
    """The marker for one value, assembled so this file carries none of them
    and survives its own run."""
    return "{{" + name + "}}"


def values(repo, default_branch, year):
    """What each placeholder becomes."""
    owner, _, name = repo.partition("/")
    if not owner or not name or "/" in name:
        raise InitError(f"--repo must be OWNER/NAME, not {repo!r}")
    return {
        placeholder("PROJECT_NAME"): name,
        placeholder("REPO"): repo,
        placeholder("OWNER"): owner,
        placeholder("DEFAULT_BRANCH"): default_branch,
        placeholder("YEAR"): str(year),
    }


def is_removed(rel):
    """Whether a relative path is, or lies under, something the run deletes."""
    posix = rel.as_posix()
    return any(posix == gone or posix.startswith(gone + "/") for gone in REMOVED)


def is_workflow(rel):
    """Whether a relative path lies under .github/workflows/, which the run
    never writes."""
    return tuple(rel.parts[:2]) == WORKFLOWS


def candidate_files(root):
    """Every file under root that may carry a placeholder, in a fixed order:
    .git, the workflows and the paths about to be removed are left out."""
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if path.is_symlink() or not path.is_file():
            continue
        if rel.parts[0] == ".git" or is_workflow(rel) or is_removed(rel):
            continue
        yield path


def fill(path, mapping):
    """Replace the placeholders in one file; True when it changed. A file that
    is not UTF-8 is not text and is left alone, and the bytes are rewritten
    as they were, so line endings survive."""
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return False
    filled = text
    for marker, value in mapping.items():
        filled = filled.replace(marker, value)
    if filled == text:
        return False
    path.write_bytes(filled.encode("utf-8"))
    return True


def fill_tree(root, mapping):
    """The relative paths of the files that changed."""
    changed = []
    for path in candidate_files(root):
        if fill(path, mapping):
            changed.append(path.relative_to(root).as_posix())
    return changed


def remove_template_files(root):
    """Delete the marker folder; the paths removed."""
    removed = []
    for gone in REMOVED:
        path = root / gone
        if path.is_dir():
            shutil.rmtree(path)
            removed.append(gone + "/")
        elif path.exists():
            path.unlink()
            removed.append(gone)
    return removed


def request(token, method, path, body=None, params=None):
    """One call to GitHub's REST API; the answer's status and JSON. An error
    names the status and the path, never the token."""
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": USER_AGENT,
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    call = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(call, timeout=TIMEOUT) as answer:
            raw = answer.read()
            return answer.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as problem:
        raw = problem.read()
        try:
            detail = json.loads(raw) if raw else None
        except ValueError:
            detail = None
        return problem.code, detail
    except OSError as problem:
        raise InitError(f"{method} {path}: {getattr(problem, 'reason', problem)}") from None


def already_exists(detail):
    """Whether a 422 says the label is there, which is the fine kind."""
    errors = (detail or {}).get("errors") or []
    return any(e.get("code") == "already_exists" for e in errors if isinstance(e, dict))


def create_labels(token, repo):
    """Make the board's labels; one line per label saying what happened."""
    lines = []
    for name, color, description in LABELS:
        status, detail = request(
            token, "POST", f"/repos/{repo}/labels",
            {"name": name, "color": color, "description": description},
        )
        if status == 201:
            lines.append(f"label {name}: created")
        elif status == 422 and already_exists(detail):
            lines.append(f"label {name}: exists")
        else:
            raise InitError(f"POST /repos/{repo}/labels ({name}): HTTP {status}")
    return lines


def setup_issue_body(repo, default_branch):
    """The checklist the person works through after the template has landed;
    the links are absolute because an issue body is not in the tree."""
    base = f"https://github.com/{repo}/blob/{default_branch}"
    return "\n".join([
        "This repository was made from the SDLC template. Finish setting it up:",
        "",
        f"- [ ] Protect the default branch `{default_branch}` ([docs/setup/github.md]({base}/docs/setup/github.md)).",
        f"- [ ] Make a claude.ai Project per Claude account and link this repository as its only resource; the first thread sets the Project up ([docs/setup/claude-project.md]({base}/docs/setup/claude-project.md)).",
        f"- [ ] When a second account joins, make the coordinator routine on the main account ([docs/agents/routines/coordinator.md]({base}/docs/agents/routines/coordinator.md)).",
        f"- [ ] Fill in [docs/project.md]({base}/docs/project.md) and [docs/agents/OWNERSHIP.md]({base}/docs/agents/OWNERSHIP.md).",
        "- [ ] Run `bash scripts/check.sh` once locally.",
        "",
        "Close this issue when every box is ticked.",
    ])


def open_setup_issue(token, repo, default_branch):
    """Open the setup issue unless one with its title is already open."""
    status, found = request(token, "GET", f"/repos/{repo}/issues", params={"state": "open", "per_page": 100})
    if status != 200:
        raise InitError(f"GET /repos/{repo}/issues: HTTP {status}")
    for issue in found or []:
        if issue.get("title") == SETUP_ISSUE_TITLE and "pull_request" not in issue:
            return f"issue #{issue['number']}: exists"
    status, made = request(
        token, "POST", f"/repos/{repo}/issues",
        {"title": SETUP_ISSUE_TITLE, "body": setup_issue_body(repo, default_branch)},
    )
    if status != 201:
        raise InitError(f"POST /repos/{repo}/issues: HTTP {status}")
    return f"issue #{made['number']}: opened"


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Fill the template's placeholders and remove its marker folder.")
    parser.add_argument("--repo", required=True, help="OWNER/NAME of this repository")
    parser.add_argument("--default-branch", required=True, help="the default branch's name")
    parser.add_argument("--year", type=int, default=datetime.now().year, help="the LICENSE year (default: this year)")
    parser.add_argument("--root", default=".", help="the repository root (default: the current directory)")
    parser.add_argument("--create-labels", action="store_true", help="make the board's labels through the API (needs GITHUB_TOKEN)")
    parser.add_argument("--open-issue", action="store_true", help="open the setup issue through the API (needs GITHUB_TOKEN)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    root = Path(args.root).resolve()
    try:
        mapping = values(args.repo, args.default_branch, args.year)
        filled = fill_tree(root, mapping)
        for path in filled:
            print(f"{path}: filled")
        if filled:
            print(WORKFLOWS_NOTE)
        for path in remove_template_files(root):
            print(f"{path}: deleted")
        token = os.environ.get("GITHUB_TOKEN")
        if (args.create_labels or args.open_issue) and not token:
            raise InitError("GITHUB_TOKEN is not set; labels and the issue need it")
        if args.create_labels:
            for line in create_labels(token, args.repo):
                print(line)
        if args.open_issue:
            print(open_setup_issue(token, args.repo, args.default_branch))
    except InitError as problem:
        print(f"template_init: {problem}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
