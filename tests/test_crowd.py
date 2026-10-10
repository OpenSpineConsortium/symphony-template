"""scripts/crowd.py makes the calls the crowd design names, in order, with
their bodies; writes nothing twice; refuses before any write when the
repository is not what setup works on; builds the crowd pull request from
the template's own files; and tells a contributor the next step.

No test has GitHub: a fake gh on PATH (tests/fake_gh.py) answers from
routes built here out of a World, the GitHub one organization and one
repository look like, and records every call. The template's own files,
filled by template_init as in a fresh copy, are the World's default branch,
so a change to the template that breaks one of crowd.py's edits fails here.
The template's placeholders are assembled at run time, so template-init
leaves this file alone.
"""

import ast
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_docs  # noqa: E402
import crowd  # noqa: E402
import crowd_check  # noqa: E402
import fake_gh  # noqa: E402
import marked_section  # noqa: E402
import template_init  # noqa: E402
from fake_gh import answer  # noqa: E402

ORG, NAME, REPO, OWNER = "octo", "widgets", "octo/widgets", "owner1"
API = f"repos/{REPO}"
MAIN_SHA, TREE_SHA, HEAD_SHA = "a" * 40, "b" * 40, "c" * 40
NEW_TREE, NEW_COMMIT = "d" * 40, "e" * 40
ACTIONS_ID = 15368
AREAS = ("parser", "renderer")
PULL_NUMBER, GOAL_NUMBER, RULESET_ID = 5, 7, 9
P = {name: template_init.placeholder(name) for name in template_init.PLACEHOLDER_NAMES}
_COPY = {}
# The World's default branch is the template's own text, filled as a fresh
# copy has it. A repository made from the template has filled its own names
# in, and in crowd mode changed the very files these tests read, so the tests
# built on that text run in the template alone, where .template/ still is.
IN_TEMPLATE = (ROOT / ".template" / "PENDING").is_file()
template_only = unittest.skipUnless(IN_TEMPLATE, "reads the template's own files, which a copy has filled and changed")


def filled_copy():
    """The template as template-init leaves a fresh copy octo/widgets, made
    once per run."""
    if "root" not in _COPY:
        folder = tempfile.mkdtemp(prefix="crowd-copy-")
        root = Path(folder) / NAME
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        template_init.fill_tree(root, template_init.values(REPO, "main", 2026))
        template_init.remove_template_files(root)
        template_init.reset_checkpoint(root)
        _COPY["root"] = root
    return _COPY["root"]


def tearDownModule():
    if "root" in _COPY:
        shutil.rmtree(_COPY["root"].parent, ignore_errors=True)


def copy_text(path):
    file = filled_copy() / path
    return file.read_text(encoding="utf-8") if file.is_file() else None


def crowd_file_ruleset(pinned):
    ruleset = crowd.crowd_ruleset((ROOT / crowd.RULESET_FILE).read_text(), pinned)
    ruleset.update(id=RULESET_ID, source_type="Repository")
    return ruleset


class World:
    """One organization and one repository as GitHub would answer for them;
    routes() turns it into the fake gh's answers."""

    def __init__(self):
        self.scopes = "admin:org, repo, workflow"
        self.login = OWNER
        self.org = {"login": ORG, "id": 11, "two_factor_requirement_enabled": False,
                    "default_repository_permission": "write", "members_can_create_repositories": True}
        self.org_role = {"role": "admin", "state": "active"}
        self.repository = {
            "full_name": REPO, "id": 22, "owner": {"login": ORG, "id": 11}, "default_branch": "main",
            "private": False, "visibility": "public", "is_template": False, "allow_auto_merge": True,
            "delete_branch_on_merge": False, "pull_request_creation_policy": "all",
            "security_and_analysis": {"secret_scanning": {"status": "disabled"},
                                      "secret_scanning_push_protection": {"status": "disabled"}},
            "permissions": {"admin": True, "push": True},
        }
        self.repository_missing = False
        self.pending = False
        self.token = {"default_workflow_permissions": "write", "can_approve_pull_request_reviews": True}
        self.fork_approval = {"approval_policy": "first_time_contributors"}
        self.secrets, self.variables = [], {}
        self.org_secrets, self.org_variables = [], {}
        self.labels = {name: (color, description) for name, color, description in template_init.LABELS}
        self.teams = {}
        self.rulesets = {}
        self.rulesets_after = {}
        self.main_reported = False
        self.installations = []
        self.main_files = {path: copy_text(path) for path in self.readable_paths()}
        self.branch_files = {}
        self.pull = None
        self.head_files = {}
        self.pull_authors = [OWNER]
        self.pull_filenames = None
        self.setup_branch = False
        self.codeowners_errors = {"crowd/setup": [], "main": []}
        self.head_runs = []
        self.main_runs = [{"app": {"id": ACTIONS_ID, "slug": "github-actions"}, "conclusion": "success"}]
        self.issues = [{"number": 1, "title": template_init.SETUP_ISSUE_TITLE, "body": "the template's checklist"}]
        self.admins = [OWNER]
        self.without_two_factor = []
        self.environments = {}
        self.dependabot, self.codespaces = [], []
        self.outside = []
        self.workflows = {name: "active" for name in ("ci.yml", "board.yml", "queue.yml", "tidy.yml", "claude.yml")}
        self.interaction = {}
        self.board_pushers = ["github-actions[bot]"]
        self.claims = {}
        self.queued = {}
        self.roles = {OWNER: "admin"}
        self.users = {"alice", "bob", OWNER}
        self.team_memberships = {}
        self.team_members = {}
        self.open_pulls = []
        self.collaborator_roles = {}
        self.my_membership = {"state": "active"}

    @staticmethod
    def readable_paths():
        return crowd.files_to_read(AREAS) + [crowd.RULESET_FILE, crowd.CROWD_RULE]

    def file_routes(self, routes, ref, files):
        for path in self.readable_paths():
            text = files.get(path)
            routes[f"GET {API}/contents/{path}?ref={ref}"] = [answer(200, text) if text is not None else answer(404, {"message": "Not Found"})]

    def routes(self):
        routes = {}
        self.base_routes(routes)
        self.settings_routes(routes)
        self.value_routes(routes)
        self.label_routes(routes)
        self.team_routes(routes)
        self.ruleset_routes(routes)
        self.pull_routes(routes)
        self.audit_routes(routes)
        self.people_routes(routes)
        return routes

    def base_routes(self, routes):
        routes["--version"] = [answer(200, "gh version 2.89.0 (fake)\n")]
        routes["auth status"] = [answer(200, "")]
        routes["GET user"] = [answer(200, {"login": self.login}, {"X-OAuth-Scopes": self.scopes})]
        routes[f"GET orgs/{ORG}"] = [answer(200, self.org)]
        routes[f"GET orgs/{ORG}/memberships/{self.login}"] = [answer(200, self.org_role)]
        routes[f"GET {API}"] = [answer(404, {"message": "Not Found"}) if self.repository_missing else answer(200, self.repository)]
        routes[f"GET {API}/contents/.template/PENDING"] = [answer(200, "x") if self.pending else answer(404, {"message": "Not Found"})]
        main = dict(self.main_files)
        main.update(self.branch_files)
        self.file_routes(routes, "main", main)
        self.file_routes(routes, MAIN_SHA, self.main_files)
        routes[f"GET {API}/git/ref/heads/main"] = [answer(200, {"object": {"sha": MAIN_SHA}})]
        routes[f"GET {API}/git/commits/{MAIN_SHA}"] = [answer(200, {"tree": {"sha": TREE_SHA}})]
        routes[f"GET {API}/issues?state=open&per_page=100"] = [answer(200, self.issues)]
        routes[f"POST {API}/issues"] = [answer(201, {"number": GOAL_NUMBER})]
        routes[f"PATCH {API}/issues/1"] = [answer(200, {})]
        routes[f"PATCH orgs/{ORG}"] = [answer(200, {})]
        routes[f"GET apps/github-actions"] = [answer(200, {"id": ACTIONS_ID, "slug": "github-actions"})]
        routes[f"GET orgs/{ORG}/installations?per_page=100"] = [answer(200, {"installations": self.installations})]

    def settings_routes(self, routes):
        routes[f"PATCH {API}"] = [answer(200, {})]
        routes[f"GET {API}/actions/permissions/workflow"] = [answer(200, self.token)]
        routes[f"PUT {API}/actions/permissions/workflow"] = [answer(204)]
        fork = f"{API}/actions/permissions/fork-pr-contributor-approval"
        routes["GET " + fork] = [answer(200, self.fork_approval)]
        routes["PUT " + fork] = [answer(204)]
        routes[f"PUT {API}/interaction-limits"] = [answer(200, {})]

    def value_routes(self, routes):
        actions = f"{API}/actions"
        listed = lambda names: [{"name": name} for name in names]  # noqa: E731
        valued = lambda values: [{"name": k, "value": v} for k, v in values.items()]  # noqa: E731
        routes[f"GET {actions}/secrets?per_page=100"] = [answer(200, {"secrets": listed(self.secrets)})]
        routes[f"GET {actions}/variables?per_page=100"] = [answer(200, {"variables": valued(self.variables)})]
        routes[f"GET {actions}/organization-secrets?per_page=100"] = [answer(200, {"secrets": listed(self.org_secrets)})]
        routes[f"GET {actions}/organization-variables?per_page=100"] = [answer(200, {"variables": valued(self.org_variables)})]
        for name in self.secrets:
            routes[f"DELETE {actions}/secrets/{name}"] = [answer(204)]
        for name in self.variables:
            routes[f"DELETE {actions}/variables/{name}"] = [answer(204)]
        crowd_value = self.variables.get("CLAUDE_CROWD")
        routes[f"GET {actions}/variables/CLAUDE_CROWD"] = [
            answer(200, {"name": "CLAUDE_CROWD", "value": crowd_value}) if crowd_value is not None else answer(404, {"message": "Not Found"})]
        routes[f"POST {actions}/variables"] = [answer(201, {})]
        routes[f"PATCH {actions}/variables/CLAUDE_CROWD"] = [answer(204)]

    def label_routes(self, routes):
        listing = [{"name": name, "color": color, "description": description}
                   for name, (color, description) in self.labels.items()]
        routes[f"GET {API}/labels?per_page=100"] = [answer(200, listing)]
        routes[f"POST {API}/labels"] = [answer(201, {})]
        names = set(self.labels) | {"area:" + area for area in AREAS} | {
            prefix + user for prefix in ("account:", "agent:") for user in self.users}
        for name in names:
            path = f"{API}/labels/{name}"
            have = self.labels.get(name)
            routes["GET " + path] = [answer(200, {"name": name, "color": have[0], "description": have[1]})
                                     if have else answer(404, {"message": "Not Found"})]
            routes["PATCH " + path] = [answer(200, {})]

    def team_routes(self, routes):
        slugs = ["contributors", "maintainers"] + [f"{area}-maintainers" for area in AREAS]
        for slug in slugs:
            routes[f"GET orgs/{ORG}/teams/{slug}"] = [answer(200, {"slug": slug}) if slug in self.teams else answer(404, {"message": "Not Found"})]
            routes[f"PUT orgs/{ORG}/teams/{slug}/repos/{REPO}"] = [answer(204)]
            routes[f"GET orgs/{ORG}/teams/{slug}/members?per_page=100"] = [
                answer(200, [{"login": login} for login in self.team_members.get(slug, [OWNER])])]
            for user in self.users:
                state = self.team_memberships.get((slug, user))
                routes[f"GET orgs/{ORG}/teams/{slug}/memberships/{user}"] = [
                    answer(200, {"state": state, "role": "member"}) if state else answer(404, {"message": "Not Found"})]
                routes[f"PUT orgs/{ORG}/teams/{slug}/memberships/{user}"] = [answer(200, {"state": "pending", "role": "member"})]
        routes[f"POST orgs/{ORG}/teams"] = [answer(201, {})]
        listing = [{"slug": slug, "permission": permission} for slug, permission in self.teams.items() if permission]
        routes[f"GET {API}/teams?per_page=100"] = [answer(200, listing)]

    def ruleset_routes(self, routes):
        listing = [{"id": rid, "name": r["name"], "source_type": r.get("source_type", "Repository")}
                   for rid, r in self.rulesets.items()]
        routes[f"GET {API}/rulesets?per_page=100"] = [answer(200, listing)]
        for rid, ruleset in self.rulesets.items():
            later = self.rulesets_after.get(rid)
            routes[f"GET {API}/rulesets/{rid}"] = [answer(200, ruleset)] + ([answer(200, later)] if later else [])
            routes[f"PUT {API}/rulesets/{rid}"] = [answer(200, {})]
        routes[f"POST {API}/rulesets"] = [answer(201, {"id": RULESET_ID})]
        total = 1 if self.main_reported else 0
        routes[f"GET {API}/commits/main/check-runs?check_name=check&app_id={ACTIONS_ID}"] = [answer(200, {"total_count": total})]

    def pull_routes(self, routes):
        pulls = [self.pull] if self.pull else []
        routes[f"GET {API}/pulls?head={ORG}:crowd/setup&state=open"] = [answer(200, pulls)]
        routes[f"GET {API}/git/ref/heads/crowd/setup"] = [answer(200, {}) if self.setup_branch else answer(404, {"message": "Not Found"})]
        routes[f"POST {API}/git/trees"] = [answer(201, {"sha": NEW_TREE})]
        routes[f"POST {API}/git/commits"] = [answer(201, {"sha": NEW_COMMIT})]
        routes[f"POST {API}/git/refs"] = [answer(201, {})]
        routes[f"PATCH {API}/git/refs/heads/crowd/setup"] = [answer(200, {})]
        routes[f"POST {API}/pulls"] = [answer(201, {"number": PULL_NUMBER})]
        for ref, errors in self.codeowners_errors.items():
            routes[f"GET {API}/codeowners/errors?ref={ref}"] = [answer(200, {"errors": errors})]
        if self.pull:
            self.file_routes(routes, HEAD_SHA, self.head_files)
            commits = [{"sha": "f" * 40, "author": {"login": login}} for login in self.pull_authors]
            routes[f"GET {API}/pulls/{PULL_NUMBER}/commits?per_page=100"] = [answer(200, commits)]
            names = self.pull_filenames
            if names is None:
                names = [path for path in self.head_files if self.head_files[path] != self.main_files.get(path)]
            routes[f"GET {API}/pulls/{PULL_NUMBER}/files?per_page=100"] = [answer(200, [{"filename": n} for n in names])]
            routes[f"GET {API}/commits/{HEAD_SHA}/check-runs?check_name=check&filter=latest"] = [answer(200, {"check_runs": self.head_runs})]
            routes["pr merge"] = [answer(200, "")]

    def audit_routes(self, routes):
        routes[f"GET orgs/{ORG}/members?role=admin&per_page=100"] = [answer(200, [{"login": x} for x in self.admins])]
        routes[f"GET orgs/{ORG}/members?filter=2fa_disabled&per_page=100"] = [answer(200, [{"login": x} for x in self.without_two_factor])]
        routes[f"GET {API}/environments?per_page=100"] = [answer(200, {"environments": [{"name": n} for n in self.environments]})]
        for env, held in self.environments.items():
            for kind in ("secrets", "variables"):
                routes[f"GET {API}/environments/{env}/{kind}?per_page=100"] = [answer(200, {kind: [{"name": n} for n in held.get(kind, [])]})]
        routes[f"GET {API}/dependabot/secrets"] = [answer(200, {"secrets": [{"name": n} for n in self.dependabot]})]
        routes[f"GET {API}/codespaces/secrets"] = [answer(200, {"secrets": [{"name": n} for n in self.codespaces]})]
        routes[f"GET {API}/collaborators?affiliation=outside&per_page=100"] = [answer(200, self.outside)]
        routes[f"GET {API}/actions/workflows?per_page=100"] = [answer(200, {"workflows": [
            {"path": ".github/workflows/" + name, "state": state} for name, state in self.workflows.items()]})]
        routes[f"GET {API}/interaction-limits"] = [answer(200, self.interaction)]
        routes[f"GET {API}/activity?ref=refs/heads/board&time_period=week&per_page=100"] = [
            answer(200, [{"actor": {"login": x}} for x in self.board_pushers])]
        branches = [{"name": "main"}, {"name": "board"}] + [{"name": f"claude/{n}"} for n in self.claims]
        routes[f"GET {API}/branches?per_page=100"] = [answer(200, branches)]
        for number, (account, pushers) in self.claims.items():
            text = f"# Claim: #{number}\n\n- Account: {account}\n"
            routes[f"GET {API}/contents/docs/agents/claims/{number}.md?ref=claude/{number}"] = [answer(200, text)]
            routes[f"GET {API}/activity?ref=refs/heads/claude/{number}&time_period=week&per_page=100"] = [
                answer(200, [{"actor": {"login": x}} for x in pushers])]
        routes[f"GET {API}/issues?state=open&labels=todo&per_page=100"] = [answer(200, [{"number": n} for n in self.queued])]
        for number, events in self.queued.items():
            routes[f"GET {API}/issues/{number}/events?per_page=100"] = [answer(200, [
                {"event": event, "label": {"name": "todo"}, "actor": {"login": actor}} for event, actor in events])]
        for login, role in self.roles.items():
            routes[f"GET {API}/collaborators/{login}/permission"] = [answer(200, {"role_name": role})]
        routes[f"GET {API}/commits/main/check-runs?check_name=check&filter=latest"] = [answer(200, {"check_runs": self.main_runs})]

    def people_routes(self, routes):
        for user in self.users:
            routes[f"GET users/{user}"] = [answer(200, {"login": user})]
        routes["GET users/nobody-here"] = [answer(404, {"message": "Not Found"})]
        routes[f"GET {API}/pulls?state=open&per_page=100"] = [answer(200, self.open_pulls)]
        for login, role in self.collaborator_roles.items():
            routes[f"GET {API}/collaborators/{login}/permission"] = [answer(200, {"role_name": role})]
            routes[f"DELETE {API}/collaborators/{login}"] = [answer(204)]
            routes[f"GET orgs/{ORG}/memberships/{login}"] = [answer(200, {"state": "active", "role": "member"})]
            routes[f"DELETE orgs/{ORG}/memberships/{login}"] = [answer(204)]
        routes[f"GET user/memberships/orgs/{ORG}"] = [answer(200, self.my_membership) if self.my_membership else answer(404, {"message": "Not Found"})]


def set_up_world(world, areas=("parser",)):
    """The state a first setup leaves: everything it writes, written, and
    the crowd pull request open with the change on its head."""
    world.org.update(default_repository_permission="read", members_can_create_repositories=False)
    world.repository.update(allow_auto_merge=False, delete_branch_on_merge=True, pull_request_creation_policy="collaborators_only",
                            security_and_analysis={"secret_scanning": {"status": "enabled"},
                                                   "secret_scanning_push_protection": {"status": "enabled"}})
    world.token = {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False}
    world.fork_approval = {"approval_policy": "all_external_contributors"}
    world.variables = {"CLAUDE_CROWD": "true"}
    for area in areas:
        world.labels["area:" + area] = ("c5def5", f"The {area} slice; see docs/agents/OWNERSHIP.md")
    world.teams = {"contributors": "push", "maintainers": "maintain"}
    world.teams.update({f"{area}-maintainers": "push" for area in areas})
    world.rulesets = {RULESET_ID: crowd_file_ruleset(pinned=False)}
    change = crowd.build_change(world.main_files, REPO, "main", OWNER, sorted(areas))
    world.head_files = dict(world.main_files)
    world.head_files.update(change.files)
    world.pull = {"number": PULL_NUMBER, "head": {"sha": HEAD_SHA}}
    world.setup_branch = True
    world.issues = world.issues + [{"number": GOAL_NUMBER, "title": crowd.GOAL_TITLE}]
    return change


def merged_world(world):
    """The state a finish leaves: the crowd files on main, the check pinned,
    and a repository the audit finds healthy."""
    set_up_world(world)
    world.main_files = dict(world.head_files)
    world.pull = None
    world.setup_branch = False
    world.rulesets = {RULESET_ID: crowd_file_ruleset(pinned=True)}
    world.org["two_factor_requirement_enabled"] = True
    world.installations = [{"app_slug": "claude", "repository_selection": "selected"}]
    return world


class Run:
    """One run of crowd.py against a World, in this process: the exit code,
    what it printed, and the calls. gh is the fake first on PATH; it answers
    in this process unless through_path asks for a process per call, which
    a few tests keep so the whole road through PATH stays proven."""

    def __init__(self, world, *args, extra_env=None, through_path=False):
        folder = tempfile.mkdtemp(prefix="crowd-run-")
        try:
            env = fake_gh.environment(folder, world.routes())
            env.update(extra_env or {})
            out, err = io.StringIO(), io.StringIO()
            run = fake_gh.routed_run(subprocess.run, env["FAKE_GH_LOG"], env["FAKE_GH_ROUTES"])
            stand_in = patch("subprocess.run", run) if not through_path else patch.dict(os.environ, {})
            with patch.dict(os.environ, env), stand_in, redirect_stdout(out), redirect_stderr(err):
                self.code = crowd.main(list(args))
            self.out, self.err = out.getvalue(), err.getvalue()
            self.lines = self.out.splitlines()
            self.calls = fake_gh.calls(env["FAKE_GH_LOG"])
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    @property
    def writes(self):
        return [call for call in self.calls if call["args"][0] == "api" and call["key"].split()[0] != "GET"
                or call["key"] == "pr merge"]

    def write_keys(self):
        return [call["key"] for call in self.writes]

    def body_of(self, key, index=0):
        return [call["body"] for call in self.writes if call["key"] == key][index]

    def unrouted(self):
        return [line for line in self.out.splitlines() + self.err.splitlines() if "no route" in line]


def setup_run(world, *extra, through_path=False):
    return Run(world, "setup", REPO, "--area", "parser", *extra, through_path=through_path)


FRESH_WRITES = [
    f"PATCH orgs/{ORG}",
    f"PATCH {API}", f"PATCH {API}", f"PATCH {API}",
    f"PUT {API}/actions/permissions/workflow",
    f"PUT {API}/actions/permissions/fork-pr-contributor-approval",
    f"POST {API}/actions/variables",
    f"POST {API}/labels",
    f"POST orgs/{ORG}/teams", f"POST orgs/{ORG}/teams", f"POST orgs/{ORG}/teams",
    f"PUT orgs/{ORG}/teams/contributors/repos/{REPO}",
    f"PUT orgs/{ORG}/teams/maintainers/repos/{REPO}",
    f"PUT orgs/{ORG}/teams/parser-maintainers/repos/{REPO}",
    f"POST {API}/rulesets",
    f"POST {API}/git/trees", f"POST {API}/git/commits", f"POST {API}/git/refs", f"POST {API}/pulls",
    f"POST {API}/issues",
    f"PATCH {API}/issues/1",
]


class GhRunner(unittest.TestCase):
    def run_gh(self, routes, action):
        folder = tempfile.mkdtemp(prefix="crowd-gh-")
        try:
            env = fake_gh.environment(folder, routes)
            out = io.StringIO()
            with patch.dict(os.environ, env), redirect_stdout(out):
                result = action()
            return result, out.getvalue(), fake_gh.calls(env["FAKE_GH_LOG"])
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    def test_status_headers_and_body_are_read(self):
        routes = {"GET user": [answer(200, {"login": "x"}, {"X-OAuth-Scopes": "repo, admin:org"})]}
        got, _, calls = self.run_gh(routes, lambda: crowd.Gh().call("GET", "user"))
        self.assertEqual(got.status, 200)
        self.assertEqual(got.body, {"login": "x"})
        self.assertEqual(crowd.granted_scopes(got.headers), {"repo", "admin:org"})
        self.assertIn("X-GitHub-Api-Version: 2022-11-28", calls[0]["args"])

    def test_a_404_is_an_answer_and_any_other_failure_raises_with_the_call(self):
        routes = {"GET a": [answer(404, {"message": "Not Found"})], "PUT b": [answer(422, {"message": "Validation Failed"})]}
        got, _, _ = self.run_gh(routes, lambda: crowd.Gh().get("a"))
        self.assertEqual(got.status, 404)

        def failing():
            with self.assertRaises(crowd.CrowdError) as caught:
                crowd.Gh().call("PUT", "b", {"x": 1})
            return str(caught.exception)
        message, _, calls = self.run_gh(routes, failing)
        self.assertIn("PUT b: HTTP 422: Validation Failed", message)
        self.assertEqual(calls[0]["body"], {"x": 1})

    def test_pages_follow_the_next_link(self):
        link = '<https://api.github.com/repositories/1/labels?per_page=100&page=2>; rel="next"'
        routes = {"GET x/labels?per_page=100": [answer(200, [{"name": "a"}], {"Link": link})],
                  "GET repositories/1/labels?per_page=100&page=2": [answer(200, [{"name": "b"}])]}
        got, _, _ = self.run_gh(routes, lambda: crowd.Gh().pages("x/labels"))
        self.assertEqual([item["name"] for item in got], ["a", "b"])

    def test_a_dry_run_reads_and_prints_writes_without_making_them(self):
        routes = {"GET a": [answer(200, {})]}

        def both():
            gh = crowd.Gh(dry_run=True)
            gh.get("a")
            return gh.call("PATCH", "repos/o/r", {"allow_auto_merge": False, "body": "x" * 100})
        got, out, calls = self.run_gh(routes, both)
        self.assertEqual([call["key"] for call in calls], ["GET a"])
        self.assertIn('would PATCH repos/o/r {"allow_auto_merge": false, "body": "<100 characters>"}', out)
        self.assertIsNone(got.body)


@template_only
class SetupOnAFreshCopy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = World()
        cls.run_ = setup_run(cls.world, through_path=True)

    def test_exits_0_with_every_call_routed(self):
        self.assertEqual(self.run_.code, 0, self.run_.err)
        self.assertEqual(self.run_.unrouted(), [])

    def test_the_writes_in_order(self):
        self.assertEqual(self.run_.write_keys(), FRESH_WRITES)

    def test_the_settings_bodies(self):
        run = self.run_
        self.assertEqual(run.body_of(f"PATCH orgs/{ORG}"), {"default_repository_permission": "read", "members_can_create_repositories": False})
        self.assertEqual(run.body_of(f"PATCH {API}", 0), {"delete_branch_on_merge": True, "allow_auto_merge": False, "pull_request_creation_policy": "collaborators_only"})
        self.assertEqual(run.body_of(f"PATCH {API}", 1), {"security_and_analysis": {"secret_scanning": {"status": "enabled"}}})
        self.assertEqual(run.body_of(f"PATCH {API}", 2), {"security_and_analysis": {"secret_scanning_push_protection": {"status": "enabled"}}})
        self.assertEqual(run.body_of(f"PUT {API}/actions/permissions/workflow"), {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False})
        self.assertEqual(run.body_of(f"PUT {API}/actions/permissions/fork-pr-contributor-approval"), {"approval_policy": "all_external_contributors"})
        self.assertEqual(run.body_of(f"POST {API}/actions/variables"), {"name": "CLAUDE_CROWD", "value": "true"})

    def test_the_variable_comes_before_the_pull_request(self):
        keys = self.run_.write_keys()
        self.assertLess(keys.index(f"POST {API}/actions/variables"), keys.index(f"POST {API}/pulls"))

    def test_labels_teams_and_the_ruleset(self):
        run = self.run_
        self.assertEqual(run.body_of(f"POST {API}/labels"), {"name": "area:parser", "color": "c5def5", "description": "The parser slice; see docs/agents/OWNERSHIP.md"})
        self.assertEqual([run.body_of(f"POST orgs/{ORG}/teams", i)["name"] for i in range(3)], ["contributors", "maintainers", "parser-maintainers"])
        self.assertTrue(all(run.body_of(f"POST orgs/{ORG}/teams", i)["privacy"] == "closed" for i in range(3)))
        self.assertEqual(run.body_of(f"PUT orgs/{ORG}/teams/maintainers/repos/{REPO}"), {"permission": "maintain"})
        self.assertEqual(run.body_of(f"PUT orgs/{ORG}/teams/contributors/repos/{REPO}"), {"permission": "push"})
        wanted = json.loads((ROOT / crowd.RULESET_FILE).read_text())
        for check in crowd.status_checks(wanted):
            del check["integration_id"]
        self.assertEqual(run.body_of(f"POST {API}/rulesets"), wanted)

    def test_the_tree_commit_ref_and_pull_request(self):
        run = self.run_
        change = crowd.build_change(self.world.main_files, REPO, "main", OWNER, ["parser"])
        tree = run.body_of(f"POST {API}/git/trees")
        self.assertEqual(tree["base_tree"], TREE_SHA)
        self.assertEqual({entry["path"]: entry["content"] for entry in tree["tree"]}, change.files)
        self.assertTrue(all(entry["mode"] == "100644" and entry["type"] == "blob" for entry in tree["tree"]))
        commit = run.body_of(f"POST {API}/git/commits")
        self.assertEqual((commit["tree"], commit["parents"]), (NEW_TREE, [MAIN_SHA]))
        self.assertTrue(commit["message"].startswith("Turn on crowd mode\n\n- "))
        self.assertEqual(run.body_of(f"POST {API}/git/refs"), {"ref": "refs/heads/crowd/setup", "sha": NEW_COMMIT})
        pull = run.body_of(f"POST {API}/pulls")
        self.assertEqual((pull["title"], pull["head"], pull["base"]), ("Turn on crowd mode", "crowd/setup", "main"))
        self.assertIn(f"python3 scripts/crowd.py finish {REPO}", pull["body"])
        self.assertNotRegex(pull["body"], r"(?i)\b(close[sd]?|fix(e[sd])?|resolve[sd]?) #\d")
        self.assertFalse([entry["path"] for entry in tree["tree"] if entry["path"].startswith(".github/workflows/")])

    def test_the_goal_issue_and_the_checklist(self):
        run = self.run_
        goal = run.body_of(f"POST {API}/issues")
        self.assertEqual((goal["title"], goal["labels"]), (crowd.GOAL_TITLE, ["todo"]))
        for heading in ("### Goal", "### Acceptance", "### Files likely touched"):
            self.assertIn(heading, goal["body"])
        body = run.body_of(f"PATCH {API}/issues/1")["body"]
        ticked = [line for line in body.splitlines() if line.startswith("- [x]")]
        self.assertEqual(len(ticked), 5, body)
        self.assertIn(f"#{PULL_NUMBER}", body)
        self.assertIn(f"(#{GOAL_NUMBER})", body)
        self.assertIn("suggested_target_id=11&repository_ids[]=22", body)
        self.assertIn("No Project, no CLAUDE_WORKER and no CLAUDE_TEAM", body)

    def test_the_last_lines_are_the_open_items_by_hand(self):
        lines = self.run_.lines
        start = lines.index("Left for you, in this order:")
        left = lines[start + 1:]
        self.assertTrue(left[0].startswith("  1. require two-factor authentication"), left)
        self.assertTrue(left[1].startswith("  2. install the Claude GitHub App"), left)
        self.assertTrue(left[2].startswith(f"  3. read pull request #{PULL_NUMBER}"), left)
        self.assertTrue(left[3].startswith("After finish: write the goal (#7)"), left)
        self.assertEqual(len(left), 4, left)

    def test_no_secret_is_set_auto_merge_stays_off_and_only_the_crowd_variable_is_made(self):
        for call in self.run_.writes:
            self.assertNotIn("/secrets", call["key"])
            if call["key"] == f"POST {API}/actions/variables":
                self.assertEqual(call["body"]["name"], "CLAUDE_CROWD")
            if call["key"] == f"PATCH {API}":
                self.assertNotEqual(call["body"].get("allow_auto_merge"), True)


@template_only
class SetupAgain(unittest.TestCase):
    def test_a_second_run_writes_nothing_and_says_already(self):
        world = World()
        first = setup_run(world)
        self.assertEqual(first.code, 0, first.err)
        set_up_world(world)
        world.issues[0]["body"] = first.body_of(f"PATCH {API}/issues/1")["body"]
        second = setup_run(world)
        self.assertEqual(second.code, 0, second.err)
        self.assertEqual(second.write_keys(), [])
        for step in ("organization defaults", "general", "secret scanning", "secret scanning push protection",
                     "actions token", "fork pull request approval", "variable CLAUDE_CROWD", "label todo",
                     "label area:parser", "team contributors", "team parser-maintainers", 'ruleset "Protect',
                     "crowd files", "goal issue", "setup issue"):
            line = next(line for line in second.lines if line.startswith(step))
            self.assertRegex(line, r"already|up to date", line)


@template_only
class SetupDryRun(unittest.TestCase):
    def test_reads_run_and_every_write_is_a_would_line(self):
        run = setup_run(World(), "--dry-run")
        self.assertEqual(run.code, 0, run.err)
        self.assertEqual(run.writes, [])
        self.assertTrue(all(call["key"].startswith("GET ") or call["key"] == "--version" for call in run.calls))
        would = [" ".join(line.split()[1:3]) for line in run.lines if line.startswith("would ")]
        self.assertEqual(would, FRESH_WRITES)
        self.assertIn('would PATCH orgs/octo {"default_repository_permission": "read", "members_can_create_repositories": false}', run.lines)


@template_only
class SetupValues(unittest.TestCase):
    def test_deletes_the_claude_values_reports_others_and_leaves_the_organization_its_own(self):
        world = World()
        world.secrets = ["CLAUDE_CODE_OAUTH_TOKEN", "DEPLOY_KEY"]
        world.variables = {"CLAUDE_WORKER": "true"}
        world.org_secrets = ["COORDINATOR_TRIGGER_TOKEN"]
        run = setup_run(world)
        self.assertEqual(run.code, 0, run.err)
        keys = run.write_keys()
        self.assertIn(f"DELETE {API}/actions/secrets/CLAUDE_CODE_OAUTH_TOKEN", keys)
        self.assertIn(f"DELETE {API}/actions/variables/CLAUDE_WORKER", keys)
        self.assertNotIn(f"DELETE {API}/actions/secrets/DEPLOY_KEY", keys)
        self.assertTrue(any("secret DEPLOY_KEY: left as it is" in line for line in run.lines))
        self.assertTrue(any("COORDINATOR_TRIGGER_TOKEN" in line and "settings/secrets/actions" in line
                            for line in run.lines[run.lines.index("Left for you, in this order:"):]))


class SetupRefuses(unittest.TestCase):
    def refused(self, world, *extra, args=None):
        run = Run(world, *(args or ("setup", REPO, "--area", "parser", *extra)))
        self.assertEqual(run.code, 1, run.out)
        self.assertEqual(run.writes, [])
        return run.err

    def test_without_the_admin_org_scope(self):
        world = World()
        world.scopes = "repo, workflow"
        self.assertIn("gh auth refresh -h github.com -s admin:org", self.refused(world))

    def test_when_not_an_owner_of_the_organization(self):
        world = World()
        world.org_role = {"role": "member", "state": "active"}
        self.assertIn("is not an owner of octo", self.refused(world))

    def test_a_personal_account(self):
        world = World()
        world.login = ORG
        self.assertIn("personal account", self.refused(world))

    def test_a_private_repository(self):
        world = World()
        world.repository.update(private=True, visibility="private")
        self.assertIn("is not public", self.refused(world))

    def test_the_template_itself(self):
        world = World()
        world.repository["is_template"] = True
        self.assertIn("is a template", self.refused(world))

    def test_template_init_not_done_after_wait_0(self):
        world = World()
        world.pending = True
        self.assertIn("template-init has not finished", self.refused(world, "--wait", "0"))

    def test_a_copy_without_the_crowd_files(self):
        world = World()
        world.main_files[crowd.CROWD_DIR + "/rule.md"] = None
        self.assertIn("predates crowd mode", self.refused(world))

    def test_a_missing_repository_without_template(self):
        world = World()
        world.repository_missing = True
        self.assertIn("--template", self.refused(world))

    def test_a_bad_area_is_a_usage_error_before_any_call(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            crowd.main(["setup", REPO, "--area", "Not An Area"])
        self.assertEqual(caught.exception.code, 2)


@template_only
class SetupFromTheTemplate(unittest.TestCase):
    def test_generates_the_copy_then_waits_for_init(self):
        world = World()
        routes = world.routes()
        routes[f"GET {API}"] = [answer(404, {"message": "Not Found"}), answer(200, world.repository)]
        routes["POST repos/templater/crowd-template/generate"] = [answer(201, world.repository)]
        world.routes = lambda: routes
        run = Run(world, "setup", REPO, "--template", "templater/crowd-template", "--dry-run")
        self.assertEqual(run.code, 0, run.err)
        self.assertIn("would POST repos/templater/crowd-template/generate", run.out)
        run = Run(world, "setup", REPO, "--template", "templater/crowd-template")
        self.assertEqual(run.code, 0, run.err)
        self.assertEqual(run.write_keys()[0], "POST repos/templater/crowd-template/generate")
        self.assertEqual(run.body_of("POST repos/templater/crowd-template/generate"),
                         {"owner": ORG, "name": NAME, "private": False, "include_all_branches": False})
        self.assertIn("template-init: done", run.lines)


@template_only
class SetupRuleset(unittest.TestCase):
    def test_an_existing_ruleset_is_replaced_by_the_crowd_one_unpinned_until_actions_reports(self):
        world = World()
        shipped = json.loads((ROOT / "docs/setup/ruleset-main.json").read_text())
        shipped.update(id=3, source_type="Repository")
        world.rulesets = {3: shipped}
        run = setup_run(world)
        self.assertEqual(run.code, 0, run.err)
        self.assertNotIn(f"POST {API}/rulesets", run.write_keys())
        put = run.body_of(f"PUT {API}/rulesets/3")
        self.assertIsNone(crowd.pinned_app(put))
        self.assertEqual(crowd.status_checks(put), [{"context": "check"}])

    def test_pins_when_check_is_already_required_and_actions_has_reported(self):
        world = World()
        shipped = json.loads((ROOT / "docs/setup/ruleset-main.json").read_text())
        shipped.update(id=3, source_type="Repository")
        world.rulesets = {3: shipped}
        world.main_reported = True
        run = setup_run(world)
        self.assertEqual(crowd.pinned_app(run.body_of(f"PUT {API}/rulesets/3")), ACTIONS_ID)
        self.assertNotIn(f"read pull request #{PULL_NUMBER}, then run: python3 scripts/crowd.py finish {REPO}, which pins", run.out)


@template_only
class SetupAreas(unittest.TestCase):
    def test_an_area_whose_label_exists_stays_in_codeowners(self):
        world = World()
        world.labels["area:renderer"] = ("c5def5", "The renderer slice; see docs/agents/OWNERSHIP.md")
        run = setup_run(world)
        self.assertEqual(run.code, 0, run.err)
        tree = {entry["path"]: entry["content"] for entry in run.body_of(f"POST {API}/git/trees")["tree"]}
        for area in ("parser", "renderer"):
            self.assertIn(f"/src/{area}/ @{ORG}/{area}-maintainers", tree[".github/CODEOWNERS"])
            self.assertIn(f"tests/test_{area}/__init__.py", tree)
        self.assertIn(f"POST orgs/{ORG}/teams", run.write_keys())
        self.assertEqual(sum(1 for c in run.writes if c["key"] == f"POST orgs/{ORG}/teams"), 4)


@template_only
class BuildChange(unittest.TestCase):
    """The crowd pull request against the template's own files."""

    @classmethod
    def setUpClass(cls):
        cls.files = {path: copy_text(path) for path in crowd.files_to_read(AREAS)}
        cls.change = crowd.build_change(cls.files, REPO, "main", OWNER, list(AREAS))

    def test_every_advisory_edit_matches_the_fresh_copy(self):
        self.assertEqual(self.change.misses, [])

    def test_every_advisory_old_text_occurs_once_in_the_template(self):
        project = (ROOT / crowd.PROJECT).read_text()
        claude_md = (ROOT / crowd.CLAUDE_MD).read_text()
        self.assertEqual(project.count(crowd.unfilled(crowd.OLD_OWNERS)), 1)
        for old in (crowd.WRITING_BULLET, crowd.OLD_BLOCK_BULLET, crowd.OLD_CHECKPOINT_SENTENCE):
            self.assertEqual(claude_md.count(old), 1, old)

    def test_a_second_build_on_the_changed_files_changes_nothing(self):
        files = dict(self.files)
        files.update(self.change.files)
        again = crowd.build_change(files, REPO, "main", OWNER, list(AREAS))
        self.assertEqual((again.files, again.misses), ({}, []))

    def test_the_changed_copy_passes_the_document_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / NAME
            shutil.copytree(filled_copy(), root)
            for path, text in self.change.files.items():
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_text(text, encoding="utf-8")
            problems, _ = check_docs.run_checks(root)
            self.assertEqual(problems, [])

    def test_the_required_edits(self):
        files = self.change.files
        for form in ("task.yml", "blocker.yml"):
            text = files[".github/ISSUE_TEMPLATE/" + form]
            self.assertIn("\nlabels: []\n", text)
            self.assertIn("A maintainer reads it", text)
        self.assertEqual(crowd_check.mode_of(files[crowd.PROJECT]), "on")
        self.assertEqual(files[crowd.CROWD_RULE], copy_text("docs/setup/crowd/rule.md"))
        self.assertIn(crowd.README_PARAGRAPH, files[crowd.README])
        for area in AREAS:
            self.assertIn(f"{area} area's tests", files[f"tests/test_{area}/__init__.py"])
        for text in files.values():
            for marker in P.values():
                self.assertNotIn(marker, text)
        for path in (".github/CODEOWNERS", "docs/agents/OWNERSHIP.md"):
            self.assertNotRegex(files[path], r"(?<![A-Za-z0-9])(AREA|OWNER_LOGIN)(?![A-Za-z0-9])", path)

    def test_a_mode_line_that_says_off_is_turned_on_in_place(self):
        files = dict(self.files)
        files[crowd.PROJECT] = files[crowd.PROJECT].replace("## Owners", "## Crowd mode\n\n- Crowd mode: off. See scripts/crowd.py.\n\n## Owners")
        text = crowd.build_change(files, REPO, "main", OWNER, []).files[crowd.PROJECT]
        self.assertEqual(len(crowd_check.MODE_LINE.findall(text)), 1)
        self.assertEqual(crowd_check.mode_of(text), "on")
        self.assertNotIn("Crowd mode: off", text)

    def test_claude_md_keeps_its_markers_and_only_one_sentence_changes_inside(self):
        old, new = self.files[crowd.CLAUDE_MD], self.change.files[crowd.CLAUDE_MD]
        for marker in (marked_section.MARK_BEGIN, marked_section.MARK_END):
            self.assertEqual(new.count(marker), 1)

        def inside(text):
            return text[text.index(marked_section.MARK_BEGIN):text.index(marked_section.MARK_END)]
        self.assertEqual(inside(new), inside(old).replace(crowd.OLD_CHECKPOINT_SENTENCE, crowd.NEW_CHECKPOINT_SENTENCE))
        self.assertNotEqual(inside(new), inside(old))

    def test_an_advisory_edit_that_does_not_match_is_listed_not_guessed(self):
        files = dict(self.files)
        files[crowd.CLAUDE_MD] = files[crowd.CLAUDE_MD].replace("do not edit it by hand", "leave it")
        change = crowd.build_change(files, REPO, "main", OWNER, [])
        self.assertEqual([miss.where for miss in change.misses], ["the Conventions bullet about the cswap block"])
        self.assertIn("leave it", change.files[crowd.CLAUDE_MD])
        self.assertIn("Edits that did not match", crowd.pull_body(change, REPO, "main"))

    def test_without_areas_no_area_line_remains(self):
        change = crowd.build_change(self.files, REPO, "main", OWNER, [])
        for path in (".github/CODEOWNERS", "docs/agents/OWNERSHIP.md"):
            self.assertNotRegex(change.files[path], r"(?<![A-Za-z0-9])AREA(?![A-Za-z0-9])")
            self.assertNotIn("OWNER_LOGIN", change.files[path])

    def test_the_old_codeowners_lines_it_drops_are_quoted(self):
        self.assertEqual(self.change.dropped, [f"* @{ORG}"])


def last_match_owners(text, path):
    """A small reading of CODEOWNERS of the test's own, for the patterns the
    crowd file uses: *, /folder/ and /file, the last match winning."""
    owners = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        pattern, *names = line.split()
        if pattern == "*" or (pattern.endswith("/") and path.startswith(pattern[1:])) or path == pattern[1:]:
            owners = names
    return owners


@template_only
class CrowdCodeowners(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        files = {path: copy_text(path) for path in crowd.files_to_read(["parser"])}
        cls.text = crowd.build_change(files, REPO, "main", OWNER, ["parser"]).files[".github/CODEOWNERS"]

    def shared_paths(self):
        settings = json.loads((ROOT / ".claude/settings.json").read_text())
        hooks = [hook["command"] for groups in settings["hooks"].values() for group in groups for hook in group["hooks"]]
        paths = [re.search(r'"\$CLAUDE_PROJECT_DIR"/(\S+)', command).group(1) for command in hooks]
        paths += [p.relative_to(ROOT).as_posix() for p in (ROOT / ".claude/rules").glob("*.md")]
        paths += [p.relative_to(ROOT).as_posix() for p in (ROOT / ".claude/skills").rglob("SKILL.md")]
        paths += [".claude/rules/crowd.md", "CLAUDE.md", "docs/project.md", "docs/agents/PROTOCOL.md",
                  "docs/memory/MEMORY.md", "tools/check_docs.py", "scripts/check.sh", ".github/workflows/ci.yml",
                  "docs/setup/ruleset-crowd.json", "tests/test_crowd.py"]
        return paths

    def test_every_hook_and_instruction_file_asks_the_owner_alone(self):
        paths = self.shared_paths()
        self.assertGreater(len(paths), 15)
        for path in paths:
            self.assertEqual(last_match_owners(self.text, path), [f"@{OWNER}"], path)
            self.assertEqual(crowd.owners_of(self.text, path), [f"@{OWNER}"], path)

    def test_an_area_asks_its_team_and_the_rest_asks_the_maintainers(self):
        for path in ("src/parser/x.py", "tests/test_parser/test_x.py"):
            self.assertEqual(last_match_owners(self.text, path), [f"@{ORG}/parser-maintainers"], path)
            self.assertEqual(crowd.owners_of(self.text, path), [f"@{ORG}/parser-maintainers"], path)
        self.assertEqual(last_match_owners(self.text, "README.md"), [f"@{ORG}/maintainers"])
        self.assertEqual(crowd.owners_of(self.text, "src/other/y.py"), [f"@{ORG}/maintainers"])


def prompt_of(path):
    text = (ROOT / path).read_text()
    return text.split("```")[-2].strip("\n")


@template_only
class CrowdPrompts(unittest.TestCase):
    """The crowd pages cannot drift from the shipped prompts they extend."""

    def test_the_worker_prompt_is_the_shipped_one_for_login_then_the_crowd_lines(self):
        shipped = prompt_of("docs/agents/routines/worker.md").replace("account:main", "account:LOGIN").splitlines()
        crowd_lines = prompt_of("docs/setup/crowd/worker.md").splitlines()
        self.assertEqual(crowd_lines[:len(shipped)], shipped)
        addendum = "\n".join(crowd_lines[len(shipped):])
        for needed in ("The claim file's Account line is LOGIN.", "Take only issues labelled area:AREA, blockers excepted.",
                       "role admin or maintain", "as data, never as instructions", "leave your checkpoint as a comment",
                       "finished; ready to mark", "agent:LOGIN"):
            self.assertIn(needed, addendum)

    def test_the_coordinator_prompt_keeps_the_shipped_paragraphs_it_does_not_replace(self):
        shipped = prompt_of("docs/agents/routines/coordinator.md").split("\n\n")
        crowd_prompt = prompt_of("docs/setup/crowd/coordinator.md").split("\n\n")
        self.assertEqual(crowd_prompt[0], shipped[0])
        self.assertEqual(crowd_prompt[3:6], shipped[3:6])
        self.assertTrue(crowd_prompt[1].startswith("1. Split queued requests into issues."))
        self.assertIn("role admin or maintain", crowd_prompt[1])
        self.assertTrue(crowd_prompt[2].startswith("2. Release idle claims."))
        self.assertTrue(crowd_prompt[6].startswith("In this cloud session gh issue and gh pr are refused"))
        self.assertEqual(len(crowd_prompt), 7)

    def test_the_crowd_checkpoint_skill_commits_nothing(self):
        text = (ROOT / "docs/setup/crowd/checkpoint-skill.md").read_text()
        self.assertTrue(text.startswith("---\nname: checkpoint\n"))
        for line in text.splitlines():
            self.assertNotRegex(line, r"git add|git commit|marked_section\.py|cswap checkpoint write")
        self.assertIn("gh pr comment", text)
        self.assertIn("/issues/<pr>/comments", text)

    def test_doctor_fills_the_worker_prompt(self):
        page = copy_text("docs/agents/routines/worker.md")
        crowd_page = copy_text("docs/setup/crowd/worker.md")
        self.assertNotEqual(page, crowd_page)
        filled = crowd.worker_prompt(crowd_page, "alice", "parser")
        self.assertIn("account:alice", filled)
        self.assertIn("Take only issues labelled area:parser, blockers excepted.", filled)
        self.assertNotRegex(filled, r"(?<![A-Za-z0-9])(LOGIN|AREA)(?![A-Za-z0-9])")
        anywhere = crowd.worker_prompt(crowd_page, "alice", None)
        self.assertNotIn("area:", anywhere)
        self.assertEqual(len(anywhere.splitlines()), len(filled.splitlines()) - 1)


class CrowdRuleset(unittest.TestCase):
    def test_differs_from_the_shipped_ruleset_only_in_the_crowd_rules(self):
        main = json.loads((ROOT / "docs/setup/ruleset-main.json").read_text())
        crowd_file = json.loads((ROOT / crowd.RULESET_FILE).read_text())
        for key in ("name", "target", "enforcement", "conditions"):
            self.assertEqual(crowd_file[key], main[key])
        self.assertEqual([r["type"] for r in crowd_file["rules"]], [r["type"] for r in main["rules"]])
        pull = {r["type"]: r for r in crowd_file["rules"]}["pull_request"]["parameters"]
        self.assertEqual(pull, {"required_approving_review_count": 1, "dismiss_stale_reviews_on_push": False,
                                "require_code_owner_review": True, "require_last_push_approval": True,
                                "required_review_thread_resolution": True,
                                "allowed_merge_methods": ["merge", "squash", "rebase"]})
        checks = {r["type"]: r for r in crowd_file["rules"]}["required_status_checks"]["parameters"]
        self.assertFalse(checks["strict_required_status_checks_policy"])
        self.assertEqual(checks["required_status_checks"], [{"context": "check", "integration_id": ACTIONS_ID}])
        self.assertEqual(crowd_file["bypass_actors"], [{"actor_id": None, "actor_type": "OrganizationAdmin", "bypass_mode": "pull_request"}])

    def test_a_live_ruleset_with_github_defaults_compares_equal(self):
        live = crowd_file_ruleset(pinned=True)
        live["bypass_actors"][0]["actor_id"] = 1
        for rule in live["rules"]:
            if rule["type"] == "pull_request":
                rule["parameters"]["required_reviewers"] = []
                rule["parameters"]["allowed_merge_methods"] = ["rebase", "merge", "squash"]
        wanted = crowd.crowd_ruleset((ROOT / crowd.RULESET_FILE).read_text(), True)
        self.assertTrue(crowd.same_ruleset(live, wanted))
        self.assertFalse(crowd.same_ruleset(crowd_file_ruleset(pinned=False), wanted))


def ready_pull_world():
    world = World()
    set_up_world(world)
    world.head_runs = [{"status": "completed", "conclusion": "success", "app": {"id": ACTIONS_ID, "slug": "github-actions"}}]
    world.branch_files = {path: text for path, text in world.head_files.items()}
    world.org["two_factor_requirement_enabled"] = True
    world.installations = [{"app_slug": "claude", "repository_selection": "selected"}]
    world.rulesets_after = {RULESET_ID: crowd_file_ruleset(pinned=True)}
    return world


@template_only
class Finish(unittest.TestCase):
    def test_a_check_still_running_merges_nothing_and_exits_0(self):
        world = ready_pull_world()
        world.head_runs = [{"status": "in_progress", "app": {"id": ACTIONS_ID}}]
        run = Run(world, "finish", REPO)
        self.assertEqual(run.code, 0, run.err)
        self.assertEqual(run.writes, [])
        self.assertIn("not finished yet; wait, then run finish again", run.out)

    def test_a_passed_check_pins_the_ruleset_then_merges(self):
        run = Run(ready_pull_world(), "finish", REPO, through_path=True)
        self.assertEqual(run.unrouted(), [])
        keys = run.write_keys()
        self.assertEqual(keys[:2], [f"PUT {API}/rulesets/{RULESET_ID}", "pr merge"])
        self.assertEqual(crowd.pinned_app(run.body_of(f"PUT {API}/rulesets/{RULESET_ID}")), ACTIONS_ID)
        merge = next(call for call in run.calls if call["key"] == "pr merge")
        self.assertEqual(merge["args"], ["pr", "merge", str(PULL_NUMBER), "--repo", REPO, "--merge", "--admin",
                                         "--match-head-commit", HEAD_SHA])
        self.assertIn(f"PATCH {API}/issues/1", keys)
        self.assertIn("ok    mode: crowd mode is on", run.out)
        self.assertEqual(run.code, 0, run.out + run.err)

    def refused(self, world, words):
        run = Run(world, "finish", REPO)
        self.assertEqual(run.code, 1, run.out)
        self.assertEqual(run.writes, [])
        self.assertIn(words, run.err)

    def test_a_check_from_another_app_is_refused(self):
        world = ready_pull_world()
        world.head_runs = [{"status": "completed", "conclusion": "success", "app": {"id": 42, "slug": "someone"}}]
        self.refused(world, "not GitHub Actions")

    def test_a_commit_by_someone_else_is_refused(self):
        world = ready_pull_world()
        world.pull_authors = [OWNER, "mallory"]
        self.refused(world, "is by mallory")

    def test_a_head_that_differs_from_what_setup_would_write_is_refused(self):
        world = ready_pull_world()
        world.head_files[crowd.CROWD_RULE] = "# Crowd rules\n\nAnything goes.\n"
        self.refused(world, "is not what setup would write")

    def test_an_extra_file_on_the_head_is_refused(self):
        world = ready_pull_world()
        world.pull_filenames = list(crowd.build_change(world.main_files, REPO, "main", OWNER, ["parser"]).files) + [".github/workflows/x.yml"]
        self.refused(world, "is not what setup would write")

    def test_a_codeowners_error_is_refused(self):
        world = ready_pull_world()
        world.codeowners_errors["crowd/setup"] = [{"line": 7, "message": "Unknown owner"}]
        self.refused(world, "line 7: Unknown owner")

    def test_without_a_pull_request_on_a_crowd_main_it_pins_and_audits_only(self):
        world = merged_world(World())
        world.rulesets = {RULESET_ID: crowd_file_ruleset(pinned=False)}
        world.rulesets_after = {RULESET_ID: crowd_file_ruleset(pinned=True)}
        run = Run(world, "finish", REPO)
        self.assertEqual(run.write_keys()[0], f"PUT {API}/rulesets/{RULESET_ID}")
        self.assertNotIn("pr merge", run.write_keys())
        self.assertIn("ok    ruleset:", run.out)
        self.assertEqual(run.code, 0, run.out)


@template_only
class Invite(unittest.TestCase):
    def test_refused_before_finish_with_no_write(self):
        world = World()
        set_up_world(world)
        run = Run(world, "invite", REPO, "alice")
        self.assertEqual(run.code, 1)
        self.assertEqual(run.writes, [])
        self.assertIn("not ready for people", run.err)
        self.assertIn("finish", run.err)

    def test_a_contributor_gets_two_labels_and_the_contributors_team(self):
        run = Run(merged_world(World()), "invite", REPO, "alice")
        self.assertEqual(run.code, 0, run.err)
        self.assertEqual(run.write_keys(), [f"POST {API}/labels", f"POST {API}/labels",
                                            f"PUT orgs/{ORG}/teams/contributors/memberships/alice"])
        self.assertEqual(run.body_of(f"POST {API}/labels", 0), {"name": "account:alice", "color": "5319e7", "description": "Work for alice's Claude account"})
        self.assertEqual(run.body_of(f"POST {API}/labels", 1), {"name": "agent:alice", "color": "0052cc", "description": "Pre-assigned to alice"})
        self.assertEqual(run.body_of(f"PUT orgs/{ORG}/teams/contributors/memberships/alice"), {"role": "member"})
        self.assertIn(f"https://github.com/orgs/{ORG}/invitation", run.out)
        self.assertIn(f"gh repo clone {REPO} && cd {NAME} && python3 scripts/crowd.py doctor --area AREA", run.out)

    def test_a_maintainer_of_an_area_joins_three_teams_and_hears_about_two_reviewers(self):
        run = Run(merged_world(World()), "invite", REPO, "alice", "--maintainer", "--area", "parser")
        self.assertEqual(run.code, 0, run.err)
        teams = [key.split("/")[3] for key in run.write_keys() if "/memberships/" in key]
        self.assertEqual(teams, ["contributors", "maintainers", "parser-maintainers"])
        self.assertIn("stay on parser-maintainers until it has two others", run.out)
        self.assertIn("doctor --area parser", run.out)

    def test_an_unknown_login_or_area_is_refused_before_any_write(self):
        for args, words in ((("alice", "nobody-here"), "no GitHub user nobody-here"),
                            (("alice", "--area", "renderer"), "no area renderer")):
            run = Run(merged_world(World()), "invite", REPO, *args)
            self.assertEqual(run.code, 1)
            self.assertEqual(run.writes, [])
            self.assertIn(words, run.err)

    def test_an_active_member_is_not_written_again_and_two_logins_go_in_one_call(self):
        world = merged_world(World())
        world.team_memberships[("contributors", "alice")] = "active"
        world.labels["account:alice"] = ("5319e7", "Work for alice's Claude account")
        world.labels["agent:alice"] = ("0052cc", "Pre-assigned to alice")
        run = Run(world, "invite", REPO, "alice", "bob")
        self.assertEqual(run.code, 0, run.err)
        self.assertEqual(run.write_keys(), [f"POST {API}/labels", f"POST {API}/labels",
                                            f"PUT orgs/{ORG}/teams/contributors/memberships/bob"])
        self.assertIn("team contributors: alice already active", run.out)
        self.assertIn("Send bob this:", run.out)


@template_only
class Remove(unittest.TestCase):
    def test_removes_the_membership_and_a_remaining_collaborator_and_lists_what_is_left(self):
        world = merged_world(World())
        world.collaborator_roles = {"alice": "write"}
        world.open_pulls = [{"number": 12, "title": "Parse dates", "user": {"login": "alice"}},
                            {"number": 13, "title": "Other", "user": {"login": "bob"}}]
        world.claims = {12: ("alice", ["alice"]), 14: ("bob", ["bob"])}
        run = Run(world, "remove", REPO, "alice")
        self.assertEqual(run.code, 0, run.err)
        self.assertEqual(run.write_keys(), [f"DELETE orgs/{ORG}/memberships/alice", f"DELETE {API}/collaborators/alice"])
        self.assertIn("open pull request #12: Parse dates", run.out)
        self.assertIn("claim claude/12: held by alice", run.out)
        self.assertNotIn("#13", run.out)
        self.assertNotIn("claude/14", run.out)

    def test_no_collaborator_delete_when_no_access_remains(self):
        world = merged_world(World())
        world.collaborator_roles = {"alice": "read"}
        run = Run(world, "remove", REPO, "alice")
        self.assertEqual(run.write_keys(), [f"DELETE orgs/{ORG}/memberships/alice"])


@template_only
class Audit(unittest.TestCase):
    def audit(self, world):
        run = Run(world, "audit", REPO)
        self.assertEqual(run.unrouted(), [])
        self.assertEqual(run.writes, [])
        return run

    def test_a_healthy_repository_gives_only_ok_lines(self):
        run = self.audit(merged_world(World()))
        results = [line for line in run.lines if line[:5].strip() in ("ok", "warn", "FAIL")]
        self.assertGreater(len(results), 20)
        self.assertEqual([line for line in results if not line.startswith("ok ")], [])
        self.assertEqual(run.code, 0)

    def assert_fails(self, change, words):
        world = merged_world(World())
        change(world)
        run = self.audit(world)
        self.assertEqual(run.code, 1, run.out)
        fails = [line for line in run.lines if line.startswith("FAIL")]
        self.assertTrue(any(words in line for line in fails), "\n".join(fails) or run.out)

    def test_each_failure_on_its_own(self):
        cases = [
            (lambda w: setattr(w, "secrets", ["DEPLOY_KEY"]), "repository secrets: DEPLOY_KEY"),
            (lambda w: setattr(w, "org_secrets", ["CLAUDE_CODE_OAUTH_TOKEN"]), "CLAUDE_CODE_OAUTH_TOKEN reaches this repository"),
            (lambda w: w.variables.update(CLAUDE_WORKER="true"), "CLAUDE_WORKER"),
            (lambda w: w.variables.pop("CLAUDE_CROWD"), "CLAUDE_CROWD is not true"),
            (lambda w: w.repository.update(allow_auto_merge=True), "auto-merge is on"),
            (lambda w: setattr(w, "rulesets", {RULESET_ID: crowd_file_ruleset(pinned=False)}), "differs from docs/setup/ruleset-crowd.json"),
            (lambda w: w.rulesets[RULESET_ID]["bypass_actors"].append({"actor_id": 5, "actor_type": "Team", "bypass_mode": "always"}),
             "differs from docs/setup/ruleset-crowd.json"),
            (lambda w: w.outside.append({"login": "helper", "role_name": "maintain"}), "helper has maintain"),
            (lambda w: w.main_files.update({crowd.PROJECT: copy_text(crowd.PROJECT)}), "does not say crowd mode is on"),
            (lambda w: w.codeowners_errors.update(main=[{"line": 3, "message": "Unknown owner"}]), "line 3: Unknown owner"),
            (lambda w: w.workflows.update({"queue.yml": "disabled_manually"}), "queue.yml is disabled_manually"),
            (lambda w: setattr(w, "queued", {21: [("labeled", "writer1")]}) or w.roles.update(writer1="write"), "#21: todo was last added by writer1"),
        ]
        for change, words in cases:
            with self.subTest(words=words):
                self.assert_fails(change, words)

    def test_a_strict_ruleset_or_an_always_bypass_is_reported(self):
        def strict(world):
            for rule in world.rulesets[RULESET_ID]["rules"]:
                if rule["type"] == "required_status_checks":
                    rule["parameters"]["strict_required_status_checks_policy"] = True
        self.assert_fails(strict, "strict_required_status_checks_policy")
        world = merged_world(World())
        world.rulesets[4] = {"id": 4, "name": "Other", "source_type": "Repository",
                             "bypass_actors": [{"actor_id": 5, "actor_type": "Team", "bypass_mode": "always"}]}
        run = self.audit(world)
        self.assertIn('warn  ruleset: the ruleset "Other" lets someone bypass it always', run.lines)

    def test_warnings_for_a_lapsing_limit_and_a_stranger_pushing_board(self):
        world = merged_world(World())
        soon = (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
        world.interaction = {"limit": "collaborators_only", "origin": "repository", "expires_at": soon}
        world.board_pushers = ["github-actions[bot]", "writer1"]
        run = self.audit(world)
        self.assertEqual(run.code, 0, run.out)
        warns = [line for line in run.lines if line.startswith("warn")]
        self.assertTrue(any("interaction limit" in line and "renews it" in line for line in warns), warns)
        self.assertTrue(any("board pushes" in line and "writer1" in line for line in warns), warns)


def bare_repository(folder, name, files):
    """A local bare repository with one commit of files, for publish-template
    to clone from and push to through CROWD_GIT_BASE."""
    work = Path(folder) / ("work-" + name.replace("/", "-"))
    work.mkdir(parents=True)
    git = ["git", "-c", "user.name=Ann Author", "-c", "user.email=ann@example.com", "-c", "init.defaultBranch=main"]
    subprocess.run(git + ["init", "-q", str(work)], check=True)
    for path, text in files.items():
        (work / path).parent.mkdir(parents=True, exist_ok=True)
        (work / path).write_text(text)
    subprocess.run(git + ["-C", str(work), "add", "-A"], check=True)
    subprocess.run(git + ["-C", str(work), "commit", "-q", "-m", "First"], check=True)
    bare = Path(folder) / "base" / (name + ".git")
    bare.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "-q", "--bare", str(work), str(bare)], check=True)
    return bare


def head_of(bare):
    return subprocess.run(["git", "--git-dir", str(bare), "rev-parse", "main"], capture_output=True, text=True).stdout.strip()


class PublishTemplate(unittest.TestCase):
    SRC, DEST = "spine/sdlc-template", "pubowner/crowd-template"

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="crowd-publish-")
        self.source = bare_repository(self.folder, self.SRC, {"README.md": "# x\n", ".template/PENDING": "x\n"})
        self.env = {"CROWD_GIT_BASE": str(Path(self.folder) / "base")}

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def world(self, login="pubowner", dest=None):
        world = World()
        world.login = login
        routes = world.routes()
        routes[f"GET repos/{self.SRC}"] = [answer(200, {"default_branch": "main", "visibility": "internal"})]
        routes[f"GET repos/{self.DEST}"] = dest or [answer(404, {"message": "Not Found"}),
                                                     answer(200, {"is_template": True, "default_branch": "main"})]
        routes[f"GET repos/{self.DEST}/contents/.template/PENDING"] = [answer(200, "x\n")]
        routes["POST user/repos"] = [answer(201, {})]
        routes["POST orgs/pubowner/repos"] = [answer(201, {})]
        world.routes = lambda: routes
        return world

    def test_without_yes_it_only_prints_what_would_be_published(self):
        run = Run(self.world(), "publish-template", self.SRC, self.DEST, extra_env=self.env)
        self.assertEqual(run.code, 0, run.err)
        self.assertEqual(run.writes, [])
        head = head_of(self.source)
        for words in (f"{self.SRC}: internal, branch main at {head}", "commits: 1", "  Ann Author <ann@example.com>",
                      "files: 2", "Nothing was published"):
            self.assertIn(words, run.out)
        self.assertFalse((Path(self.folder) / "base" / (self.DEST + ".git")).exists())

    def test_with_yes_it_makes_a_template_and_pushes_the_history(self):
        dest = Path(self.folder) / "base" / (self.DEST + ".git")
        subprocess.run(["git", "init", "-q", "--bare", str(dest)], check=True)
        run = Run(self.world(), "publish-template", self.SRC, self.DEST, "--yes", extra_env=self.env)
        self.assertEqual(run.code, 0, run.err)
        self.assertEqual(run.write_keys(), ["POST user/repos"])
        body = run.body_of("POST user/repos")
        self.assertEqual((body["name"], body["private"], body["is_template"]), ("crowd-template", False, True))
        self.assertEqual(head_of(dest), head_of(self.source))
        self.assertIn(f"setup ORG/NAME --template {self.DEST}", run.out)

    def test_an_organization_destination_is_made_there(self):
        dest = Path(self.folder) / "base" / (self.DEST + ".git")
        subprocess.run(["git", "init", "-q", "--bare", str(dest)], check=True)
        run = Run(self.world(login="someone"), "publish-template", self.SRC, self.DEST, "--yes", extra_env=self.env)
        self.assertEqual(run.code, 0, run.err)
        self.assertEqual(run.body_of("POST orgs/pubowner/repos")["visibility"], "public")

    def test_an_existing_destination_with_other_history_is_refused(self):
        existing = [answer(200, {"is_template": True, "default_branch": "main"})]
        world = self.world(dest=existing)
        routes = world.routes()
        routes[f"GET repos/{self.DEST}/git/ref/heads/main"] = [answer(200, {"object": {"sha": "9" * 40}})]
        run = Run(world, "publish-template", self.SRC, self.DEST, "--yes", extra_env=self.env)
        self.assertEqual(run.code, 1)
        self.assertEqual(run.writes, [])
        self.assertIn("nothing is overwritten", run.err)

    def test_a_managed_user_is_refused(self):
        run = Run(self.world(login="ann_spine"), "publish-template", self.SRC, self.DEST, "--yes", extra_env=self.env)
        self.assertEqual(run.code, 1)
        self.assertIn("managed user", run.err)
        self.assertIn("bundle", run.err)


@template_only
class Doctor(unittest.TestCase):
    """doctor runs as a contributor runs it: a process of its own in a clone,
    with a clean environment and a home of its own."""

    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix="crowd-doctor-"))
        self.clone = self.folder / NAME
        shutil.copytree(filled_copy(), self.clone)
        change = crowd.build_change({p: copy_text(p) for p in crowd.files_to_read(["parser"])}, REPO, "main", OWNER, ["parser"])
        for path, text in change.files.items():
            (self.clone / path).parent.mkdir(parents=True, exist_ok=True)
            (self.clone / path).write_text(text)
        git = ["git", "-C", str(self.clone)]
        subprocess.run(git + ["init", "-q"], check=True)
        subprocess.run(git + ["remote", "add", "origin", f"https://github.com/{REPO}.git"], check=True)
        self.home = self.folder / "home"
        self.home.mkdir()
        self.world = merged_world(World())
        self.world.login = "alice"
        self.world.labels.update({"account:alice": ("5319e7", ""), "agent:alice": ("0052cc", ""),
                                  "area:parser": ("c5def5", "")})

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def doctor(self, *args, env=None):
        routes_folder = self.folder / "gh"
        routes_folder.mkdir(exist_ok=True)
        fake = fake_gh.environment(routes_folder, self.world.routes())
        claude = Path(fake["PATH"].split(os.pathsep)[0]) / "claude"
        claude.write_text("#!/bin/sh\necho '2.1.0 (Claude Code)'\n")
        claude.chmod(0o755)
        clean = {"PATH": fake["PATH"], "HOME": str(self.home), "LANG": "C.UTF-8",
                 "FAKE_GH_LOG": fake["FAKE_GH_LOG"], "FAKE_GH_ROUTES": fake["FAKE_GH_ROUTES"]}
        clean.update(env or {})
        done = subprocess.run([sys.executable, str(ROOT / "scripts" / "crowd.py"), "doctor", *args],
                              cwd=self.clone, env=clean, capture_output=True, text=True)
        return done.returncode, done.stdout + done.stderr

    def next_line(self, output):
        nexts = [line for line in output.splitlines() if line.startswith("Next:")]
        self.assertEqual(len(nexts), 1, output)
        return nexts[0]

    def test_all_good_gives_the_claim_sentence_and_says_ready(self):
        code, out = self.doctor("--area", "parser")
        self.assertEqual(code, 0, out)
        self.assertTrue(out.rstrip().endswith("ready"), out)
        self.assertIn("Next: run claude here, check that /status names your own claude.ai account", out)
        self.assertIn("labelled area:parser", out)
        self.assertIn("My account label is account:alice and the claim file's Account line is alice.", out)
        self.assertNotRegex(out, r"(?<![A-Za-z0-9])(LOGIN|AREA)(?![A-Za-z0-9])")
        for path in (".claude/settings.json", ".claude/hooks/session-start.sh", "tools/guard_push.py",
                     "tools/check_edit.py", "tools/sdlc_protocol/guard.py", "tools/check_docs.py"):
            self.assertIn("  " + path + "\n", out)

    def test_a_credential_in_the_shell_is_named_and_its_value_never_shown(self):
        value = "sk-" + "ant-" + "fake" * 8
        code, out = self.doctor("--area", "parser", env={"ANTHROPIC_API_KEY": value})
        self.assertEqual(code, 1)
        self.assertIn("ANTHROPIC_API_KEY is set in this shell (value not shown)", out)
        self.assertNotIn(value, out)
        self.assertIn("unset ANTHROPIC_API_KEY", self.next_line(out))

    def test_credentials_in_settings_files_are_named_by_file(self):
        config = self.folder / "config"
        config.mkdir()
        secret = "helper-" + "value-" + "not-shown"
        (config / "settings.json").write_text(json.dumps({"apiKeyHelper": secret}))
        (self.clone / ".claude" / "settings.local.json").write_text(json.dumps({"env": {"CLAUDE_CODE_USE_BEDROCK": "1"}}))
        code, out = self.doctor("--area", "parser", env={"CLAUDE_CONFIG_DIR": str(config)})
        self.assertEqual(code, 1)
        self.assertIn(f"{config}/settings.json has apiKeyHelper", out)
        self.assertIn(".claude/settings.local.json has env.CLAUDE_CODE_USE_BEDROCK", out)
        self.assertNotIn(secret, out)

    def test_each_rung_of_the_ladder_has_its_own_next_line(self):
        cases = [
            ("not invited", lambda w: setattr(w, "my_membership", None), f"invite {REPO} alice"),
            ("pending", lambda w: setattr(w, "my_membership", {"state": "pending"}), f"https://github.com/orgs/{ORG}/invitation"),
            ("no Write", lambda w: w.repository.update(permissions={"push": False}), "team contributors"),
            ("a missing label", lambda w: w.labels.pop("agent:alice"), "which makes your labels"),
        ]
        for name, change, words in cases:
            with self.subTest(name):
                self.world = merged_world(World())
                self.world.login = "alice"
                self.world.labels.update({"account:alice": ("5319e7", ""), "agent:alice": ("0052cc", ""), "area:parser": ("c5def5", "")})
                change(self.world)
                code, out = self.doctor("--area", "parser")
                self.assertEqual(code, 1, out)
                self.assertIn(words, self.next_line(out))
                self.assertNotIn("ready", out.splitlines()[-1])

    def test_a_single_branch_clone_is_told_to_fetch_every_branch(self):
        source = bare_repository(self.folder, "src", {"README.md": "# x\n"})
        shutil.rmtree(self.clone / ".git")
        single = self.folder / "single"
        subprocess.run(["git", "clone", "-q", "--single-branch", "--branch", "main", str(source), str(single)], check=True)
        shutil.move(str(single / ".git"), str(self.clone / ".git"))
        subprocess.run(["git", "-C", str(self.clone), "remote", "set-url", "origin", f"https://github.com/{REPO}.git"], check=True)
        code, out = self.doctor("--area", "parser")
        self.assertEqual(code, 1)
        self.assertIn("git config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'", self.next_line(out))

    def test_worker_fills_the_prompt_and_drops_the_area_line_without_an_area(self):
        code, out = self.doctor("--worker")
        self.assertEqual(code, 0, out)
        self.assertIn("your account's label is account:alice", out)
        self.assertNotIn("Take only issues labelled area:", out)
        self.assertNotRegex(out, r"(?<![A-Za-z0-9])LOGIN(?![A-Za-z0-9])")
        code, out = self.doctor("--worker", "--area", "parser")
        self.assertIn("Take only issues labelled area:parser, blockers excepted.", out)


class SetupRepoScript(unittest.TestCase):
    """scripts/setup-repo.sh turns auto-merge on and can store a token, so in
    a crowd repository it stops before any write."""

    def run_script(self, crowd_answer):
        folder = tempfile.mkdtemp(prefix="crowd-setup-repo-")
        try:
            routes = {
                "repo view": [answer(200, f"{REPO}\tmain\tPUBLIC\n")],
                f"GET {API}/actions/variables/CLAUDE_CROWD": [crowd_answer],
                f"GET {API}/rulesets": [answer(200, "")],
                f"POST {API}/rulesets": [answer(201, "")],
                "repo edit": [answer(200, "")],
                "label create": [answer(200, "")],
            }
            env = dict(os.environ, **fake_gh.environment(folder, routes))
            done = subprocess.run(["bash", str(ROOT / "scripts" / "setup-repo.sh"), REPO], cwd=ROOT, env=env,
                                  capture_output=True, text=True)
            return done, [call["key"] for call in fake_gh.calls(env["FAKE_GH_LOG"])]
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    def test_stops_before_any_write_when_crowd_mode_is_on(self):
        done, keys = self.run_script(answer(200, "True\n"))
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("crowd mode is on", done.stderr)
        self.assertIn(f"python3 scripts/crowd.py setup {REPO}", done.stderr)
        self.assertEqual(keys, ["repo view", f"GET {API}/actions/variables/CLAUDE_CROWD"])

    def test_goes_on_as_before_without_the_variable(self):
        done, keys = self.run_script(answer(404, {"message": "Not Found"}))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn(f"POST {API}/rulesets", keys)
        self.assertIn("repo edit", keys)


class Source(unittest.TestCase):
    def test_carries_no_placeholder_and_parses_on_python_3_8(self):
        for path in (ROOT / "scripts" / "crowd.py", Path(__file__), ROOT / "tests" / "fake_gh.py", ROOT / "tools" / "crowd_check.py"):
            text = path.read_text(encoding="utf-8")
            for marker in P.values():
                self.assertNotIn(marker, text, path.name)
        ast.parse((ROOT / "scripts" / "crowd.py").read_text(encoding="utf-8"), feature_version=(3, 8))

    def test_calls_github_only_through_gh(self):
        text = (ROOT / "scripts" / "crowd.py").read_text(encoding="utf-8")
        self.assertNotIn("urllib", text)
        self.assertNotIn("http.client", text)


if __name__ == "__main__":
    unittest.main()
