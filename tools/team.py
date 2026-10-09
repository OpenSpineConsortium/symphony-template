"""Team mode's clerical work, done by code so no Claude usage goes to it.

Team mode (docs/agents/TEAM.md) runs CooperBench's best-scoring
configuration on GitHub: a lead turns an epic into a plan and pre-assigned
sub-issues, members work them in parallel on claim branches, and the lead
integrates at the end. Claude does the thinking; this tool does the rest,
three ways, each run by a workflow step with GITHUB_TOKEN:

  seed   read the lead's plan (the JSON claude-code-action returns under
         --json-schema), write it into the epic, open one sub-issue per
         task labelled todo and agent:<owner>, and link each under the epic.
  route  after an issue event, say what the lead does next:
         "plan <epic>", "integrate <epic>" or "none".
  next   for one member, say what it does next: "carry <issue>" (its own
         claimed task needs work), "take <issue>" (its pre-assigned task,
         else any unclaimed todo) or "none".

The answer is one line on stdout for the workflow to read; a failure is
one line on stderr and exit 1, and the workflow then does nothing.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from board import BoardError, GitHub  # noqa: E402

EPIC_LABEL = "epic"
TODO_LABEL = "todo"
BLOCKED_LABEL = "blocked"
AGENT_PREFIX = "agent:"
CLAIM_PREFIX = "claude/"
PLAN_MARKER = "<!-- team:plan -->"
TASKS_LINE = re.compile(r"<!-- team:tasks ([0-9 ]*) -->")
EPIC_LINE = re.compile(r"^Epic: #(\d+)\s*$", re.MULTILINE)
# A ready pull request with one of these states has fallen behind its
# base or conflicts with it; any other state waits on checks or a merge.
NEEDS_REBASE = {"behind", "dirty"}
FAILED = {"failure", "timed_out"}
AGENT_COLOUR = "c5def5"


class TeamError(Exception):
    """What this tool could not do; the message never holds the token."""


def label_names(issue):
    return {label["name"] for label in issue.get("labels", [])}


def agent_of(issue):
    """The member an issue is assigned to, by its agent:<name> label."""
    names = [n[len(AGENT_PREFIX):] for n in label_names(issue) if n.startswith(AGENT_PREFIX)]
    return names[0] if names else None


def epic_of(issue):
    """The epic a task belongs to, from the "Epic: #N" line seed writes."""
    found = EPIC_LINE.search(issue.get("body") or "")
    return int(found.group(1)) if found else None


def task_numbers(epic):
    """The task issues seed opened for an epic, from its machine line."""
    found = TASKS_LINE.search(epic.get("body") or "")
    return [int(n) for n in found.group(1).split()] if found else []


def open_issues(api):
    """Every open issue (pull requests, which the API mixes in, left out)."""
    found = api.get_all(f"/repos/{api.repo}/issues", {"state": "open"})
    return [issue for issue in found if "pull_request" not in issue]


def claim_branches(api):
    """The issue numbers that have a claude/<number> branch on the remote."""
    names = [b["name"] for b in api.get_all(f"/repos/{api.repo}/branches")]
    return {int(n[len(CLAIM_PREFIX):]) for n in names
            if n.startswith(CLAIM_PREFIX) and n[len(CLAIM_PREFIX):].isdigit()}


# --- route ------------------------------------------------------------------

def route(api, event, number, label=None):
    """What the lead does after an issue event: plan a newly labelled epic,
    integrate an epic whose last task just closed, or nothing."""
    issue = api.get(f"/repos/{api.repo}/issues/{number}")
    if event == "labeled":
        planned = PLAN_MARKER in (issue.get("body") or "")
        is_epic = label == EPIC_LABEL and issue.get("state") == "open"
        return f"plan {number}" if is_epic and not planned else "none"
    if event == "closed":
        return integration_due(api, epic_of(issue))
    return "none"


def integration_due(api, epic_number):
    """"integrate <epic>" when every task of an open epic is closed."""
    if epic_number is None:
        return "none"
    epic = api.get(f"/repos/{api.repo}/issues/{epic_number}")
    tasks = task_numbers(epic)
    if epic.get("state") != "open" or not tasks:
        return "none"
    states = [api.get(f"/repos/{api.repo}/issues/{n}").get("state") for n in tasks]
    return f"integrate {epic_number}" if all(s == "closed" for s in states) else "none"


# --- next -------------------------------------------------------------------

def claim_needs_work(api, number):
    """Whether a member's open claim has something for it to do: no pull
    request yet, a draft, a base it has fallen behind or conflicts with, or
    a failed check. One that is ready and only waiting for its checks or
    its merge needs nothing, and a run spent on it would be usage wasted."""
    owner = api.repo.split("/")[0]
    pulls = api.get(f"/repos/{api.repo}/pulls",
                    {"state": "open", "head": f"{owner}:{CLAIM_PREFIX}{number}"}) or []
    if not pulls:
        return True
    pull = api.get(f"/repos/{api.repo}/pulls/{pulls[0]['number']}")
    if pull.get("draft") or pull.get("mergeable_state") in NEEDS_REBASE:
        return True
    runs = api.get(f"/repos/{api.repo}/commits/{pull['head']['sha']}/check-runs") or {}
    return any(run.get("conclusion") in FAILED for run in runs.get("check_runs", []))


def next_for(api, agent):
    """The member's next move: its own claims first, then its pre-assigned
    tasks, then any unclaimed todo that no member was given."""
    issues = sorted(open_issues(api), key=lambda issue: issue["number"])
    claimed = claim_branches(api)
    mine = [i for i in issues if agent_of(i) == agent and BLOCKED_LABEL not in label_names(i)]
    for issue in mine:
        if issue["number"] in claimed and claim_needs_work(api, issue["number"]):
            return f"carry {issue['number']}"
    for pool in (mine, [i for i in issues if agent_of(i) is None]):
        for issue in pool:
            labels = label_names(issue)
            if TODO_LABEL in labels and EPIC_LABEL not in labels and issue["number"] not in claimed:
                return f"take {issue['number']}"
    return "none"


# --- seed -------------------------------------------------------------------

def owners_for(tasks, agents):
    """Each task's owner: the one the lead named when it is on the team,
    else the members in turn, so no task is left without one."""
    owners = []
    for index, task in enumerate(tasks):
        named = task.get("owner")
        owners.append(named if named in agents else agents[index % len(agents)])
    return owners


def task_body(epic_number, task):
    files = "\n".join(f"- {path}" for path in task.get("files", [])) or "- (the lead named none)"
    return (f"Epic: #{epic_number}\n\n{task.get('body', '').strip()}\n\n"
            f"## Files to touch\n\n{files}\n\n"
            "Stay inside these files; another member owns the rest of the epic "
            "(docs/agents/TEAM.md).\n")


def ensure_label(api, name):
    """Make an agent label; one that exists already answers 422, which is fine."""
    try:
        api.post(f"/repos/{api.repo}/labels", {"name": name, "color": AGENT_COLOUR})
    except BoardError as problem:
        if "HTTP 422" not in str(problem):
            raise


def open_task(api, epic_number, task, owner):
    """Open one task issue and hang it under the epic as a sub-issue; the
    link is a convenience for people, so its failure is not one."""
    label = AGENT_PREFIX + owner
    ensure_label(api, label)
    made = api.post(f"/repos/{api.repo}/issues", {
        "title": task["title"], "body": task_body(epic_number, task), "labels": [TODO_LABEL, label]})
    try:
        api.post(f"/repos/{api.repo}/issues/{epic_number}/sub_issues", {"sub_issue_id": made["id"]})
    except BoardError:
        pass
    return made["number"]


def plan_section(plan, made):
    """What seed appends to the epic: the lead's plan, the task list, and
    the machine line route reads."""
    lines = [f"- [ ] #{number} {title} (agent:{owner})" for number, title, owner in made]
    numbers = " ".join(str(number) for number, _, _ in made)
    return (f"\n\n{PLAN_MARKER}\n## Plan, by the lead\n\n{plan.strip()}\n\n"
            "## Tasks\n\n" + "\n".join(lines) + f"\n\n<!-- team:tasks {numbers} -->\n")


def seed(api, epic_number, plan, agents):
    """Open the epic's tasks and write the plan into it, once."""
    epic = api.get(f"/repos/{api.repo}/issues/{epic_number}")
    if PLAN_MARKER in (epic.get("body") or ""):
        return "already planned"
    tasks = plan.get("tasks") or []
    if not tasks or not agents:
        raise TeamError("the plan has no tasks, or the team has no members")
    made = []
    for task, owner in zip(tasks, owners_for(tasks, agents)):
        made.append((open_task(api, epic_number, task, owner), task["title"], owner))
    body = (epic.get("body") or "") + plan_section(plan.get("plan", ""), made)
    api.request("PATCH", api.url(f"/repos/{api.repo}/issues/{epic_number}"), body={"body": body})
    return "seeded " + " ".join(str(number) for number, _, _ in made)


# --- command line -------------------------------------------------------------

def team_members(text):
    """The members from the CLAUDE_TEAM variable's JSON list."""
    try:
        members = json.loads(text or "[]")
    except ValueError:
        raise TeamError("CLAUDE_TEAM is not a JSON list") from None
    if not isinstance(members, list) or not all(isinstance(m, str) and m for m in members):
        raise TeamError("CLAUDE_TEAM must be a JSON list of names, as in [\"w1\",\"w2\"]")
    return members


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Team mode's clerical steps (docs/agents/TEAM.md).")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    sub = parser.add_subparsers(dest="command", required=True)
    seeding = sub.add_parser("seed")
    seeding.add_argument("--epic", type=int, required=True)
    seeding.add_argument("--plan", required=True, help="the lead's plan as a JSON file")
    seeding.add_argument("--team", default=os.environ.get("CLAUDE_TEAM", ""))
    routing = sub.add_parser("route")
    routing.add_argument("--event", required=True)
    routing.add_argument("--issue", type=int, required=True)
    routing.add_argument("--label", default=None)
    nexting = sub.add_parser("next")
    nexting.add_argument("--agent", required=True)
    return parser.parse_args(argv)


def run(api, args):
    if args.command == "seed":
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        return seed(api, args.epic, plan, team_members(args.team))
    if args.command == "route":
        return route(api, args.event, args.issue, args.label)
    return next_for(api, args.agent)


def main(argv=None):
    args = parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token or not args.repo:
        print("GITHUB_TOKEN and --repo (or GITHUB_REPOSITORY) are needed", file=sys.stderr)
        return 1
    try:
        print(run(GitHub(token, args.repo), args))
    except (BoardError, TeamError, ValueError, KeyError) as problem:
        print(f"team: {problem}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
