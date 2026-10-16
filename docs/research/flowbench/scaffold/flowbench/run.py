"""Run one (instance, arm) attempt: provision the instance's image as a
container with the repository on the host, run the arm's stages, take
the patch, score it and write the record.

The agents run on the host, in the workspace, a copy of the image's
/testbed (the repository at the instance's base commit, under the one
commit the image's build adds on top of it, which is where the harness
applies a patch; the prompts' {base_commit} is that start commit, and
the record keeps both), and the container runs the same workspace
bind-mounted at /testbed, as the place where the repository's tests run
in the image's own Python environment: every prompt gives the agent a
wrapper script, {test_shell}, that runs a command there. The task
repository's checkout, which holds the gold patch and the hidden tests,
is never mounted, copied or named to an agent: run.py reads the instance
from it and passes on the problem statement alone, as a file beside the
workspace; an audit of each agent's stream names a run that went looking
anyway, and the report leaves it out.

An arm is a folder under arms/ with stages.json and its prompts
(arms/README.md). A stage runs one or more agents, each a headless Claude
Code (`claude -p`) on the host's own login, never an API key, with the
login's settings, MCP servers and subagents off, or in fake mode
fake_agent.py, which spends nothing and walks the same path. Each
agent's stream-json output is kept beside the run as
agents/<agent>.stream.jsonl, and the record reads its tokens, cost and
end from it (record.stream_summary). A failure of the flow itself (an
agent that ended in error, a stage that left no output for the next, a
builder whose work was never committed) is the arm's result, counted as
an orchestration failure and scored with whatever patch there is; an
agent that ran out of time or turns is counted apart; a failure of the
harness (no image, no docker, the scorer failing, a usage limit) is a
harness error, and the audit names it so the report leaves the run out.

    python3 flowbench/run.py run --logs LOGS --tag TAG --arm script --instance ID --task-repo CHECKOUT --dataset DIR [--fake]
    python3 flowbench/run.py lane --backlog B --lane L --logs LOGS --task-repo CHECKOUT --dataset DIR [--fake]
    python3 flowbench/run.py pull --task-repo CHECKOUT --instances a,b | @FILE
    python3 flowbench/run.py arm script

--fake is the whole path faked: no image, a small repository for a
workspace, the fake agent, a fake score. --fake-agents is the real path
with only the agents faked: the image, the container, the fake agent's
edit and SWE-bench's own harness on the result, which is how the plumbing
is rehearsed on a real instance without spending a token.
"""

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from flowbench import backlog  # noqa: E402
from flowbench import record, score, tasks  # noqa: E402

HERE = Path(__file__).resolve().parent
ARMS_DIR = HERE / "arms"
CONTAINER_WORKSPACE = "/testbed"
ACTIVATE = "source /opt/miniconda3/bin/activate testbed"
DEFAULT_MODEL = "claude-sonnet-5-5"
DEFAULT_EFFORT = "medium"
DEFAULT_AGENT_MINUTES = 45
DEFAULT_RUN_MINUTES = 120
# No turn cap unless asked (PLAN.md): 0 is none.
DEFAULT_MAX_TURNS = 0
DEFAULT_PARALLEL = 3
DEFAULT_MIRROR = "mirror.gcr.io"
# Claude Code tools the agents may not use: the comparison is of local
# tools only (PLAN.md), so the web is off for every arm alike, and one
# agent is one Claude Code process, so subagents are off too (Task is the
# older name of the Agent tool).
DISALLOWED_TOOLS = ("WebFetch", "WebSearch", "Task", "Agent")
# Variables that would make claude bill something other than the login.
BILLING_VARIABLES = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "CLAUDE_CODE_USE_BEDROCK",
                     "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY")
# What the patch leaves out beyond the repository's own .gitignore: the
# caches and leavings a test run or a merge puts in the workspace, which
# git would otherwise add as new files that the harness's git apply
# refuses; the files the image already held untracked are excluded at
# prepare (exclude_from_patch).
EXCLUDED_FROM_PATCH = ("__pycache__/", "*.pyc", ".pytest_cache/", ".mypy_cache/", "*.egg-info/", ".hypothesis/",
                       ".tox/", ".coverage", ".coverage.*", "*.orig", "*.rej")
STAGE_KINDS = ("work", "stack", "review", "verify", "fix", "answer")
AGENT_COUNT_WORDS = ("builders", "per_finding")
PLACEHOLDERS = ("instance_id", "repo", "base_commit", "workspace", "container", "test_shell", "problem_file",
                "run_dir", "flow_dir", "stage", "agent", "lens", "lens_text", "findings_file", "verdict_file",
                "finding", "finding_id", "findings", "confirmed_findings", "builders", "branch", "run_token", "options")
PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")
# What a usage limit looks like in Claude Code's result text: an agent
# that ends on one is the harness's failure, not the arm's.
LIMIT_TEXT = re.compile(r"usage limit|hit your limit|rate limit|out of (?:extra )?usage|credit balance|limit reached",
                        re.IGNORECASE)
# What a failed login looks like there: the harness's failure too.
AUTH_TEXT = re.compile(r"invalid api key|run /login|not logged in|authentication_error|authentication failed|"
                       r"oauth token has expired", re.IGNORECASE)
# How an agent can end that is the harness's failure, not the arm's.
HARNESS_STATUSES = ("usage_limit", "auth_error")
# Commands in an agent's Bash calls that reach the network; recorded in
# the audit, since the comparison is of local tools.
NETWORK_COMMAND = re.compile(r"\b(?:curl|wget|pip3? install|pip3? download|git (?:fetch|pull|clone)|apt(?:-get)? install)\b")
# What in an agent's stream excludes the run: the task repository's path
# or name, or the answer's file names. A hidden test's name is recorded
# beside them and excludes nothing, since an agent may write a test of
# the same name on its own.
EXCLUDING_KINDS = ("task_repo", "task_repo_name", "gold_patch", "test_patch")
WRAPPER_CONTAINER = """#!/bin/sh
# Runs a command in the instance's container, in the repository's own
# Python environment, from /testbed, which holds the same files as the
# workspace: `{wrapper} pytest -x path/to/test_x.py`, or a shell line as
# `{wrapper} bash -c '...'`.
exec docker exec -i {container} bash -lc '{activate} && cd {workspace} && exec "$@"' -- "$@"
"""
WRAPPER_HOST = """#!/bin/sh
# A fake run has no container: the command runs on the host, in the
# workspace, as `{wrapper} pytest -x path/to/test_x.py`.
cd {workspace} && exec "$@"
"""


class RunError(RuntimeError):
    """A failure of the harness, not of the arm: the run is left out."""


class Docker:
    """The docker commands the runner uses, one method each, so a test runs
    with a fake that records them instead."""

    def __init__(self, executable="docker"):
        self.executable = executable

    def command(self, *args, check=True, timeout=600):
        try:
            done = subprocess.run([self.executable, *args], capture_output=True, text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as error:
            raise RunError(f"docker {' '.join(args[:2])} ran past {timeout} s") from error
        except FileNotFoundError as error:
            raise RunError(f"{self.executable} is not there: {error}") from error
        if check and done.returncode != 0:
            raise RunError(f"docker {' '.join(args[:2])} failed ({done.returncode}): {done.stderr.strip()[-2000:]}")
        return done

    def create(self, image, name):
        self.command("create", "--name", name, image, "sleep", "infinity")

    def copy_out(self, container, source, target):
        self.command("cp", f"{container}:{source}", str(target), timeout=1800)

    def remove(self, name):
        self.command("rm", "-f", name, check=False)

    def start_workspace(self, image, name, workspace, label):
        self.command("run", "-d", "--name", name, "--label", label, "-v", f"{workspace}:{CONTAINER_WORKSPACE}",
                     "-w", CONTAINER_WORKSPACE, image, "sleep", "infinity")

    def image_id(self, image):
        return self.command("image", "inspect", "--format", "{{.Id}}", image).stdout.strip()

    def pull(self, image, mirror):
        """The image through the mirror, tagged under its own name, which
        is the name the task names and the harness looks up."""
        source = f"{mirror}/{image}" if mirror else image
        self.command("pull", source, timeout=3600)
        if source != image:
            self.command("tag", source, image)

    def has_image(self, image):
        return self.command("image", "inspect", "--format", "{{.Id}}", image, check=False).returncode == 0

    def ensure_image(self, image, mirror):
        """The image pulled through the mirror unless it is here already."""
        if not self.has_image(image):
            self.pull(image, mirror)

    def remove_image(self, image, mirror=None):
        """Both of the image's names, its own and the mirror's, or the
        layers stay on the disk under the other."""
        self.command("rmi", image, check=False)
        if mirror:
            self.command("rmi", f"{mirror}/{image}", check=False)


def git(workspace, *args, check=True):
    done = subprocess.run(["git", "-c", "safe.directory=*", "-c", "core.fileMode=false", "-C", str(workspace), *args],
                          capture_output=True, text=True, check=False)
    if check and done.returncode != 0:
        raise RunError(f"git {' '.join(args)} in {workspace} failed ({done.returncode}): {done.stderr.strip()[-2000:]}")
    return done.stdout


def command_output(command, cwd=None):
    """The first line a command prints, or None when it cannot run."""
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False, cwd=cwd)
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (done.stdout or "").strip() or (done.stderr or "").strip()
    return text.splitlines()[0] if done.returncode == 0 and text else None


def run_directory(logs, tag, arm, instance, attempt):
    """Absolute, since the workspace in it is bind-mounted into a
    container and named to the agents, and a relative path is neither."""
    return Path(logs).resolve() / tag / arm / instance / f"attempt-{attempt}"


def next_attempt(logs, tag, arm, instance):
    """The first attempt number whose directory is not there yet."""
    parent = Path(logs) / tag / arm / instance
    attempt = 1
    while (parent / f"attempt-{attempt}").exists():
        attempt += 1
    return attempt


def container_name(tag, arm, instance, attempt, k=None):
    raw = f"flowbench-{tag}-{arm}-{instance}-a{attempt}" + (f"-b{k}" if k else "")
    return re.sub(r"[^A-Za-z0-9_.-]", "-", raw)[:120]


def load_arm(arm):
    """The arm's stages.json, checked: a name, stages with unique names, a
    kind each from STAGE_KINDS, a prompt file that exists, an agent count
    that is a positive integer or one of AGENT_COUNT_WORDS, and lenses as
    a name-to-text table. The arm is a folder, or the name of one under
    arms/."""
    arm_dir = Path(arm)
    if not arm_dir.is_dir():
        arm_dir = ARMS_DIR / str(arm)
    config_path = arm_dir / "stages.json"
    if not config_path.is_file():
        raise RunError(f"{arm}: no arm there ({config_path} is missing)")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config.get("name"), str) or not isinstance(config.get("stages"), list) or not config["stages"]:
        raise RunError(f"{config_path}: an arm has a name and a list of stages")
    seen = set()
    for stage in config["stages"]:
        name = stage.get("name")
        if not isinstance(name, str) or not name or name in seen or "-" in name:
            raise RunError(f"{config_path}: every stage has a name of its own, without a dash ({name!r})")
        seen.add(name)
        if stage.get("kind") not in STAGE_KINDS:
            raise RunError(f"{config_path}: stage {name}: kind is one of {', '.join(STAGE_KINDS)}")
        prompt = arm_dir / str(stage.get("prompt", ""))
        if not stage.get("prompt") or not prompt.is_file():
            raise RunError(f"{config_path}: stage {name}: prompt {stage.get('prompt')!r} is not a file")
        agents = stage.get("agents", 1)
        if not ((isinstance(agents, int) and agents >= 1) or agents in AGENT_COUNT_WORDS):
            raise RunError(f"{config_path}: stage {name}: agents is a count or one of {', '.join(AGENT_COUNT_WORDS)}")
        lenses = stage.get("lenses")
        if lenses is not None and not (isinstance(lenses, dict) and lenses
                                       and all(isinstance(v, str) for v in lenses.values())):
            raise RunError(f"{config_path}: stage {name}: lenses is a table of name to text")
        if "parallel" in stage and not isinstance(stage["parallel"], bool):
            raise RunError(f"{config_path}: stage {name}: parallel is true or false")
        if "needs" in stage and stage["needs"] not in ("raised", "confirmed"):
            raise RunError(f"{config_path}: stage {name}: needs is raised or confirmed")
        if "writes" in stage and not isinstance(stage["writes"], str):
            raise RunError(f"{config_path}: stage {name}: writes is a file name")
    config["dir"] = str(arm_dir)
    return config


def render(template, fields):
    """The prompt with its placeholders filled; every placeholder in
    PLACEHOLDERS is given, so a brace that is not one, as in a JSON
    example, stays as it is."""
    text = template
    for key in PLACEHOLDERS:
        text = text.replace("{" + key + "}", str(fields.get(key, "")))
    return text


def unknown_placeholders(template):
    """The {names} in a prompt that are not placeholders of the runner's,
    for a check of the arms; a JSON example's braces hold spaces or
    quotes and do not match."""
    return sorted({name for name in PLACEHOLDER.findall(template) if name not in PLACEHOLDERS})


def write_wrapper(path, container, workspace):
    """The script an agent runs the repository's tests through."""
    path = Path(path)
    if container:
        text = WRAPPER_CONTAINER.format(wrapper=path, container=container, activate=ACTIVATE, workspace=CONTAINER_WORKSPACE)
    else:
        text = WRAPPER_HOST.format(wrapper=path, workspace=workspace)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)
    return str(path)


def exclude_from_patch(workspace):
    """The patterns above, and every file the image already held untracked
    and not ignored (a build product, a generated file), which would
    otherwise come out as a new file the harness's git apply refuses,
    since it is there already."""
    exclude = Path(workspace) / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    untracked = [line for line in git(workspace, "ls-files", "--others", "--exclude-standard").splitlines() if line]
    with exclude.open("a", encoding="utf-8") as out:
        out.write("".join(f"{pattern}\n" for pattern in EXCLUDED_FROM_PATCH))
        out.write("".join(f"/{name}\n" for name in untracked))
    return untracked


def fake_workspace(workspace, instance):
    """A small repository in place of the image's: a package with one
    function and a test, committed once; the commit is the base."""
    workspace = Path(workspace)
    (workspace / "pkg").mkdir(parents=True)
    (workspace / "tests").mkdir()
    (workspace / "README.md").write_text(f"# {instance}\n\nA fake workspace for a rehearsal.\n", encoding="utf-8")
    (workspace / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (workspace / "pkg" / "core.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (workspace / "tests" / "test_core.py").write_text(
        "from pkg.core import add\n\n\ndef test_add():\n    assert add(2, 2) == 4\n", encoding="utf-8")
    git(workspace, "init", "-q")
    configure_git(workspace)
    git(workspace, "add", "-A")
    git(workspace, "commit", "-q", "-m", "The base")
    return git(workspace, "rev-parse", "HEAD").strip()


def configure_git(workspace):
    """An identity for the commits an arm makes, and no background
    maintenance, which races a teardown."""
    for key, value in (("user.name", "flowbench"), ("user.email", "flowbench@localhost"), ("gc.auto", "0"),
                       ("gc.autoDetach", "false"), ("maintenance.auto", "false"), ("commit.gpgsign", "false"),
                       ("core.fileMode", "false")):
        git(workspace, "config", key, value)


def make_builder_copies(workspace, run_dir, count):
    """One copy of the workspace per builder, builder-1 to builder-K, each
    on a branch of that name from the start commit: a copy and not a
    worktree, since a worktree has none of the image's untracked build
    products and its .git file names a host path no container sees. The
    stack stage gets each branch fetched into the workspace."""
    builders = []
    for k in range(1, count + 1):
        path = Path(run_dir) / f"builder-{k}"
        shutil.copytree(workspace, path, symlinks=True)
        git(path, "switch", "-q", "-c", f"builder-{k}")
        builders.append({"k": k, "branch": f"builder-{k}", "workspace": str(path), "container": None, "test_shell": None})
    return builders


def provenance_of(task_repo, swebench):
    """What scored the run, pinned by version and commit where it can be
    read; None where it cannot."""
    return {"swebench": score.harness_version(swebench) if swebench is not False else None,
            "task_repo_commit": command_output(["git", "-c", "safe.directory=*", "rev-parse", "HEAD"], cwd=task_repo)
            if task_repo else None,
            "flowbench_commit": command_output(["git", "-c", "safe.directory=*", "rev-parse", "HEAD"], cwd=HERE)}


def prepare(logs, tag, arm, task, attempt=None, model=DEFAULT_MODEL, options=None, fake=False, docker=None,
            fake_agents=False, effort=DEFAULT_EFFORT, task_repo=None, swebench=None):
    """The run directory, the workspace (and its container), plan.json;
    what was started is removed again when a later step fails."""
    arm = load_arm(arm) if not isinstance(arm, dict) else arm
    options = dict(options or {})
    attempt = attempt or next_attempt(logs, tag, arm["name"], task.instance_id)
    run_dir = run_directory(logs, tag, arm["name"], task.instance_id, attempt)
    if run_dir.exists():
        raise RunError(f"{run_dir} exists; every attempt has a directory of its own")
    run_dir.mkdir(parents=True)
    events = record.Events(run_dir / "events.jsonl")
    workspace = run_dir / "workspace"
    (run_dir / "problem.md").write_text(task.problem_statement, encoding="utf-8")
    (run_dir / "flow").mkdir()
    (run_dir / "mcp.json").write_text('{"mcpServers": {}}\n', encoding="utf-8")
    run_id = score.run_id_for(tag, arm["name"], task.instance_id, attempt)
    containers = []
    docker = docker or (Docker() if not fake else None)
    try:
        image_id = None
        if fake:
            base_commit = start_commit = fake_workspace(workspace, task.instance_id)
            image = "fake"
        else:
            image = task.image
            name = container_name(tag, arm["name"], task.instance_id, attempt)
            docker.remove(name)
            docker.create(image, name)
            containers.append(name)
            docker.copy_out(name, CONTAINER_WORKSPACE, workspace)
            docker.remove(name)
            containers.remove(name)
            configure_git(workspace)
            base_commit = task.base_commit
            start_commit = git(workspace, "rev-parse", "HEAD").strip()
            descends = subprocess.run(["git", "-c", "safe.directory=*", "-C", str(workspace), "merge-base",
                                       "--is-ancestor", base_commit, start_commit],
                                      capture_output=True, text=True, check=False)
            if descends.returncode != 0:
                raise RunError(f"{task.instance_id}: the image's /testbed is at {start_commit}, which does not descend "
                               f"from the base {base_commit}")
            docker.start_workspace(image, name, workspace, f"flowbench.run={run_id}")
            containers.append(name)
            image_id = docker.image_id(image)
        untracked = exclude_from_patch(workspace)
        count = int(options.get("builders", 1) or 1)
        builders = make_builder_copies(workspace, run_dir, count) if count > 1 else []
        for builder in builders:
            if not fake:
                name = container_name(tag, arm["name"], task.instance_id, attempt, builder["k"])
                docker.remove(name)
                docker.start_workspace(image, name, builder["workspace"], f"flowbench.run={run_id}")
                builder["container"] = name
                containers.append(name)
            builder["test_shell"] = write_wrapper(run_dir / f"test-{builder['k']}", builder["container"], builder["workspace"])
    except (RunError, OSError, shutil.Error) as error:
        if docker:
            for name in containers:
                docker.remove(name)
        raise RunError(str(error)) from error
    plan = {"tag": tag, "arm": arm["name"], "arm_dir": arm["dir"], "instance": task.instance_id, "repo": task.repo,
            "attempt": attempt, "run_dir": str(run_dir), "workspace": str(workspace), "base_commit": base_commit,
            "start_commit": start_commit, "untracked_in_image": len(untracked),
            "container": containers[0] if containers else None, "containers": containers, "image": image,
            "image_id": image_id, "model": model, "effort": effort, "options": options, "builders": builders,
            "fake": fake, "fake_agents": bool(fake or fake_agents),
            "test_shell": write_wrapper(run_dir / "test", containers[0] if containers else None, workspace),
            "run_token": f"flowbench-{secrets.token_hex(8)}", "run_id": run_id,
            "stages": [stage["name"] for stage in arm["stages"]], "started": round(time.time(), 3),
            "provenance": provenance_of(task_repo, False if fake else swebench)}
    record.write_json(run_dir / "plan.json", plan)
    events.emit("prepared", instance=task.instance_id, arm=arm["name"], attempt=attempt, image=image, fake=fake)
    return plan


def read_findings(flow_dir):
    """Every finding the review stages raised, in file order, each with its
    lens and its stage; a file that is not a findings table is left out
    and named."""
    findings, problems = [], []
    for path in sorted(Path(flow_dir).glob("findings-*.json")):
        data = record.read_json(path)
        if not isinstance(data, dict) or not isinstance(data.get("findings"), list):
            problems.append(f"{path.name}: not a findings table")
            continue
        stage_and_lens = path.stem[len("findings-"):]
        stage = stage_and_lens.split("-", 1)[0]
        lens = data.get("lens") or stage_and_lens.split("-", 1)[-1]
        for finding in data["findings"]:
            if isinstance(finding, dict) and isinstance(finding.get("id"), str):
                findings.append({**finding, "lens": lens, "stage": stage})
            else:
                problems.append(f"{path.name}: a finding without an id")
    return findings, problems


def read_verdicts(flow_dir):
    verdicts = {}
    for path in sorted(Path(flow_dir).glob("verdict-*.json")):
        data = record.read_json(path)
        if isinstance(data, dict) and isinstance(data.get("id"), str):
            verdicts[data["id"]] = bool(data.get("real"))
    return verdicts


def confirmed_findings(flow_dir):
    findings, _ = read_findings(flow_dir)
    verdicts = read_verdicts(flow_dir)
    return [finding for finding in findings if verdicts.get(finding["id"])]


def safe_file_name(text):
    return re.sub(r"[^A-Za-z0-9_.-]", "-", text)[:80]


def job_fields(plan, stage, agent, **extra):
    run_dir = Path(plan["run_dir"])
    fields = {key: "" for key in PLACEHOLDERS}
    fields.update({"instance_id": plan["instance"], "repo": plan["repo"], "base_commit": plan["start_commit"],
                   "workspace": plan["workspace"], "container": plan["container"] or "",
                   "test_shell": plan["test_shell"], "problem_file": str(run_dir / "problem.md"),
                   "run_dir": str(run_dir), "flow_dir": str(run_dir / "flow"), "stage": stage["name"], "agent": agent,
                   "builders": json.dumps([{k: b[k] for k in ("k", "branch")} for b in plan["builders"]], sort_keys=True),
                   "run_token": plan["run_token"], "options": json.dumps(plan["options"], sort_keys=True)})
    fields.update(extra)
    return fields


def jobs_for_stage(plan, stage):
    """The stage's agents, each with its prompt fields: one per lens, one
    per builder (in its own copy, with its container), one per finding
    raised, or a count; a stage that needs findings (raised, or confirmed
    by the verdicts) has no agents and is skipped when there are none."""
    flow_dir = Path(plan["run_dir"]) / "flow"
    jobs = []
    raised, _ = read_findings(flow_dir)
    confirmed = confirmed_findings(flow_dir)
    if stage.get("needs") == "raised" and not raised:
        return jobs
    if stage.get("needs") == "confirmed" and not confirmed:
        return jobs
    raised_text = json.dumps(raised, indent=2, sort_keys=True)
    confirmed_text = json.dumps(confirmed, indent=2, sort_keys=True)
    name = stage["name"]
    if stage.get("lenses"):
        for lens, text in stage["lenses"].items():
            jobs.append(job_fields(plan, stage, f"{name}-{lens}", lens=lens, lens_text=text,
                                   findings_file=str(flow_dir / f"findings-{name}-{lens}.json")))
    elif stage.get("agents", 1) == "builders":
        if plan["builders"]:
            for builder in plan["builders"]:
                jobs.append(job_fields(plan, stage, f"{name}-{builder['k']}", workspace=builder["workspace"],
                                       container=builder["container"] or "", test_shell=builder["test_shell"],
                                       branch=builder["branch"]))
        else:
            jobs.append(job_fields(plan, stage, name))
    elif stage.get("agents", 1) == "per_finding":
        for finding in raised:
            jobs.append(job_fields(plan, stage, f"{name}-{safe_file_name(finding['id'])}",
                                   finding=json.dumps(finding, indent=2, sort_keys=True), finding_id=finding["id"],
                                   lens=finding.get("lens", ""),
                                   verdict_file=str(flow_dir / f"verdict-{name}-{safe_file_name(finding['id'])}.json")))
    else:
        count = int(stage.get("agents", 1))
        for i in range(1, count + 1):
            jobs.append(job_fields(plan, stage, f"{name}-{i}" if count > 1 else name, findings=raised_text,
                                   confirmed_findings=confirmed_text))
    return jobs


def claude_command(model, effort, max_turns, disallowed, mcp_config):
    """Headless Claude Code on the login, with the login's own settings,
    MCP servers and subagents left out, so every agent of every arm has
    the same tools: the built-in ones less the web and the Agent tool."""
    command = ["claude", "--print", "--verbose", "--output-format=stream-json", "--permission-mode=bypassPermissions",
               "--model", model, "--effort", effort, "--setting-sources", "project", "--strict-mcp-config",
               "--mcp-config", str(mcp_config), "--disallowedTools", ",".join(disallowed)]
    if max_turns:
        command += ["--max-turns", str(int(max_turns))]
    return command


def agent_environment():
    """The host's environment, less any key or provider setting that
    would bill something other than the login."""
    environment = {key: value for key, value in os.environ.items() if key not in BILLING_VARIABLES}
    environment.setdefault("GIT_TERMINAL_PROMPT", "0")
    return environment


def status_of(exit_code, summary, timed_out, stderr_text=""):
    """How an agent ended, from its exit, its result event and its stderr:
    success, timeout, turn_limit, usage_limit or auth_error (both the
    harness's), or error."""
    if timed_out:
        return "timeout"
    end = str(summary.get("end") or "")
    text = (summary.get("result_text") or "") + "\n" + (stderr_text or "")
    if exit_code == 0 and not summary.get("is_error"):
        return "success"
    if end == "error_max_turns":
        return "turn_limit"
    if AUTH_TEXT.search(text):
        return "auth_error"
    if LIMIT_TEXT.search(text) or "limit" in end:
        return "usage_limit"
    return "error"


def login_problem_of(status):
    """Why claude's login (`claude auth status --json`) is not one flowbench
    runs on, or None: it must be logged in, with Anthropic itself, and not
    by an API key."""
    method = str(status.get("authMethod") or "")
    if not status.get("loggedIn"):
        return "claude is not logged in: run `claude auth login` with the subscription's account"
    if status.get("apiProvider") not in (None, "firstParty") or re.search(r"api.?key", method, re.IGNORECASE):
        return (f"claude is logged in by {method or status.get('apiProvider')}, not on a subscription: "
                "flowbench never runs on an API key")
    return None


def login_problem():
    """login_problem_of what claude says of its own login, in the agents'
    environment; reading it spends nothing."""
    try:
        done = subprocess.run(["claude", "auth", "status", "--json"], capture_output=True, text=True, timeout=60,
                              env=agent_environment(), check=False)
        status = json.loads(done.stdout or "{}")
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        return f"claude's login could not be read: {error}"
    return login_problem_of(status if isinstance(status, dict) else {})


def strip_token(text, token):
    """The result text without the run token line, which is the host's
    alone: the record keeps the rest for a reader."""
    lines = [line for line in (text or "").splitlines() if token not in line]
    return "\n".join(lines).strip()[:500] or None


def run_job(plan, stage, fields, template, limits, fake, events):
    """One agent: its prompt rendered and written, claude (or the fake
    agent) run in its workspace with the prompt on stdin and the stream
    kept, then the record of how it went."""
    run_dir = Path(plan["run_dir"])
    agents_dir = run_dir / "agents"
    agents_dir.mkdir(exist_ok=True)
    agent = fields["agent"]
    prompt = render(template, fields)
    prompt_path = agents_dir / f"{agent}.prompt.md"
    stream_path = agents_dir / f"{agent}.stream.jsonl"
    stderr_path = agents_dir / f"{agent}.stderr.log"
    prompt_path.write_text(prompt, encoding="utf-8")
    if fake:
        job_path = agents_dir / f"{agent}.job.json"
        record.write_json(job_path, {"stage": stage["name"], "kind": stage["kind"], "agent": agent, "fields": fields,
                                     "options": plan["options"], "model": plan["model"], "stream": str(stream_path),
                                     "writes": render(stage["writes"], fields) if stage.get("writes") else ""})
        command = [sys.executable, "-I", str(HERE / "fake_agent.py"), str(job_path)]
    else:
        command = claude_command(plan["model"], plan["effort"], limits["max_turns"], limits["disallowed"], run_dir / "mcp.json")
    events.emit("agent_started", stage=stage["name"], agent=agent, fake=fake)
    started = time.monotonic()
    timed_out, exit_code = False, None
    with stream_path.open("w", encoding="utf-8") as out, stderr_path.open("w", encoding="utf-8") as err:
        try:
            done = subprocess.run(command, input=prompt, stdout=out, stderr=err, cwd=fields["workspace"], text=True,
                                  timeout=limits["agent_seconds"], env=agent_environment(), check=False)
            exit_code = done.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
        except FileNotFoundError as error:
            raise RunError(f"{command[0]} is not there: {error}") from error
    elapsed_ms = int((time.monotonic() - started) * 1000)
    summary = record.stream_summary(stream_path) or {}
    status = status_of(exit_code, summary, timed_out, stderr_path.read_text(encoding="utf-8", errors="replace")[-4000:])
    agent_record = {"agent": agent, "stage": stage["name"], "lens": fields.get("lens") or None, "status": status,
                    "end": summary.get("end"), "exit_code": exit_code, "duration_ms": elapsed_ms,
                    "turns": summary.get("turns"), "tokens": summary.get("tokens"), "cost_usd": summary.get("cost_usd"),
                    "cost_source": summary.get("cost_source"), "model": summary.get("model"),
                    "tools": summary.get("tools"), "mcp_servers": summary.get("mcp_servers"),
                    "harness_error": status in HARNESS_STATUSES,
                    "result_text": strip_token(summary.get("result_text"), plan["run_token"])}
    events.emit("agent_ended", stage=stage["name"], agent=agent, status=status, duration_ms=elapsed_ms)
    return agent_record


def collect_builders(plan, stage_record):
    """Before the stack stage: each builder's branch fetched from its copy
    into the workspace; a builder that left its work uncommitted, or no
    branch to fetch, is named as the flow's failure."""
    for builder in plan["builders"]:
        left = git(builder["workspace"], "status", "--porcelain", check=False).strip()
        if left:
            stage_record["missing"].append(f"{builder['branch']}: uncommitted changes left in the builder's copy")
        done = subprocess.run(["git", "-c", "safe.directory=*", "-C", plan["workspace"], "fetch", "-q",
                               builder["workspace"], f"{builder['branch']}:{builder['branch']}"],
                              capture_output=True, text=True, check=False)
        if done.returncode != 0:
            stage_record["missing"].append(f"{builder['branch']}: not fetched ({done.stderr.strip()[-200:]})")


def run_stage(plan, arm, stage, limits, fake, events):
    """The stage's agents, in parallel where it says so, then a look at
    what it was to leave: a missing output is the flow's failure."""
    template = (Path(arm["dir"]) / stage["prompt"]).read_text(encoding="utf-8")
    started = time.monotonic()
    stage_record = {"name": stage["name"], "kind": stage["kind"], "agents": [], "missing": [], "skipped": False}
    if stage["kind"] == "stack" and plan["builders"]:
        collect_builders(plan, stage_record)
    jobs = jobs_for_stage(plan, stage)
    if not jobs:
        stage_record["skipped"] = True
        events.emit("stage_skipped", stage=stage["name"])
        stage_record["duration_ms"] = 0
        return stage_record
    events.emit("stage_started", stage=stage["name"], agents=[job["agent"] for job in jobs])
    workers = min(len(jobs), limits["parallel"]) if stage.get("parallel") else 1
    with ThreadPoolExecutor(max_workers=workers) as pool:
        stage_record["agents"] = list(pool.map(lambda fields: run_job(plan, stage, fields, template, limits, fake, events), jobs))
    for job in jobs:
        expected = render(stage["writes"], job) if stage.get("writes") else ""
        if expected and not Path(expected).is_file():
            stage_record["missing"].append(expected)
    stage_record["duration_ms"] = int((time.monotonic() - started) * 1000)
    events.emit("stage_ended", stage=stage["name"], duration_ms=stage_record["duration_ms"], missing=stage_record["missing"])
    return stage_record


def take_patch(workspace, start_commit):
    """The workspace's change against the commit it started at, new files
    included, as the harness's git apply takes it on the image; modes
    left out, as the harness's own diff leaves them."""
    git(workspace, "add", "-A")
    return git(workspace, "diff", "--cached", start_commit)


def count_by(names):
    counts = {}
    for name in names:
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def flow_metrics(plan, stage_records):
    flow_dir = Path(plan["run_dir"]) / "flow"
    findings, problems = read_findings(flow_dir)
    verdicts = read_verdicts(flow_dir)
    stack = record.read_json(flow_dir / "stack.json")
    reasons = list(problems)
    timeouts = turn_limits = 0
    for stage in stage_records:
        for agent in stage["agents"]:
            if agent["status"] == "timeout":
                timeouts += 1
            elif agent["status"] == "turn_limit":
                turn_limits += 1
            elif agent["status"] == "error":
                reasons.append(f"{agent['agent']}: error ({agent['end']})")
        for missing in stage["missing"]:
            reasons.append(f"{stage['name']}: left no {Path(missing).name}" if os.sep in missing else f"{stage['name']}: {missing}")
    fixed_ids = []
    for path in sorted(flow_dir.glob("fixed-*.json")):
        fixed = record.read_json(path)
        if isinstance(fixed, dict) and isinstance(fixed.get("fixed"), list):
            fixed_ids += fixed["fixed"]
    answered = 0
    for path in sorted(flow_dir.glob("answers-*.json")):
        answers = record.read_json(path)
        if isinstance(answers, dict) and isinstance(answers.get("answers"), list):
            answered += 1
            fixed_ids += [a.get("id") for a in answers["answers"] if isinstance(a, dict) and a.get("changed")]
    review_rounds = sum(1 for stage in stage_records if stage["kind"] == "review" and not stage["skipped"])
    return {"orchestration_failure": bool(reasons), "orchestration_reasons": reasons, "timeouts": timeouts,
            "turn_limits": turn_limits, "findings_raised": len(findings),
            "findings_by_lens": count_by(f["lens"] for f in findings),
            "findings_confirmed": sum(1 for f in findings if verdicts.get(f["id"])), "findings_fixed": len(fixed_ids),
            "merges": stack if isinstance(stack, dict) else None, "review_rounds": review_rounds, "answers": answered}


def cost_of(agents, model):
    """The run's cost: Claude Code's own figure summed when every agent
    has one, else the list-price estimate from the tokens, else a lower
    bound; None with no agent at all."""
    if not agents:
        return None, None
    costs = [agent.get("cost_usd") for agent in agents]
    if all(cost is not None for cost in costs):
        return round(sum(costs), 4), "claude code"
    tokens = record.sum_tokens([agent.get("tokens") for agent in agents])
    estimate = record.price(tokens, model)
    if estimate is not None:
        return estimate, "estimated from tokens"
    bound = record.price_lower_bound(tokens, model)
    return bound, "lower bound from tokens" if bound is not None else None


def audit_streams(plan, stage_records, forbidden):
    """What the agents' streams say about where they looked: a hit on the
    task repository's path or name or on the answer's file names (the
    EXCLUDING_KINDS) names the run as excluded, since it went looking; a
    hit on a hidden test's name is recorded for a reader; a network
    command is recorded and the run stays in."""
    agents_dir = Path(plan["run_dir"]) / "agents"
    hits, network = [], []
    for stage in stage_records:
        for agent in stage["agents"]:
            path = agents_dir / f"{agent['agent']}.stream.jsonl"
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for kind, pattern in forbidden:
                if pattern.search(text):
                    hits.append({"agent": agent["agent"], "kind": kind, "found": pattern.pattern[:120]})
            for found in NETWORK_COMMAND.findall(text):
                network.append({"agent": agent["agent"], "command": found})
    return hits, network


def finish(plan, stage_records, dataset=None, swebench=None, score_timeout=score.DEFAULT_TIMEOUT, keep=False,
           docker=None, events=None, harness_errors=None, forbidden=()):
    """The patch, its score, the record and the teardown."""
    run_dir = Path(plan["run_dir"])
    events = events or record.Events(run_dir / "events.jsonl")
    fake = plan["fake"]
    harness_errors = list(harness_errors or [])
    scoring = None
    patch = ""
    try:
        patch = take_patch(plan["workspace"], plan["start_commit"])
        (run_dir / "model.patch").write_text(patch, encoding="utf-8")
        score.write_prediction(run_dir, plan["instance"], plan["arm"], plan["model"], patch)
        events.emit("patch_taken", bytes=len(patch.encode("utf-8")))
        scoring = score.score(run_dir, plan["tag"], plan["arm"], plan["instance"], plan["attempt"], dataset, swebench,
                              score_timeout, fake)
        events.emit("scored", resolved=scoring["resolved"], reason=scoring["reason"])
        if scoring["reason"] in ("error", "infra_failure"):
            harness_errors.append(f"the scorer: {scoring.get('error') or scoring['reason']}")
    except (RunError, score.ScoreError) as error:
        harness_errors.append(str(error))
        events.emit("harness_error", error=str(error))
    agents = [agent for stage in stage_records for agent in stage["agents"]]
    for agent in agents:
        if agent["harness_error"]:
            harness_errors.append(f"{agent['agent']}: {agent['status']}: {agent['result_text']}")
    hits, network = audit_streams(plan, stage_records, forbidden)
    looked_outside = [hit for hit in hits if hit["kind"] in EXCLUDING_KINDS]
    hidden_seen = [hit for hit in hits if hit["kind"] not in EXCLUDING_KINDS]
    excluded = bool(looked_outside)
    cost, cost_source = cost_of(agents, plan["model"])
    agents_ms = sum(agent["duration_ms"] for agent in agents)
    flow = flow_metrics(plan, stage_records)
    result = {"instance": plan["instance"], "repo": plan["repo"], "arm": plan["arm"], "tag": plan["tag"],
              "attempt": plan["attempt"], "model": plan["model"], "effort": plan["effort"],
              "driver": "fake" if plan.get("fake_agents") else "claude-cli",
              "route": plan["options"].get("route", "host"), "fake": fake, "options": plan["options"],
              "scoring": scoring, "patch_bytes": len(patch.encode("utf-8")),
              "tokens": record.sum_tokens([agent.get("tokens") for agent in agents]), "cost_usd": cost,
              "cost_source": cost_source, "agents": agents,
              "stages": [{key: stage[key] for key in ("name", "kind", "duration_ms", "missing", "skipped")} for stage in stage_records],
              "timings": {"agents_seconds": round(agents_ms / 1000, 3), "wall_seconds": round(time.time() - plan["started"], 3)},
              "flow": flow, "harness_error": bool(harness_errors), "excluded": excluded,
              "provenance": {"image": plan["image"], "image_id": plan["image_id"], "base_commit": plan["base_commit"],
                             "start_commit": plan["start_commit"], "scorer": scoring["harness"] if scoring else None,
                             **(plan.get("provenance") or {})}}
    record.write_json(run_dir / "result.json", result)
    record.write_json(run_dir / "audit.json", {"harness_error": bool(harness_errors), "reasons": harness_errors,
                                               "excluded": excluded, "looked_outside": looked_outside,
                                               "hidden_tests_seen": hidden_seen, "network_commands": network,
                                               "orchestration_failure": flow["orchestration_failure"],
                                               "orchestration_reasons": flow["orchestration_reasons"]})
    if not keep:
        if not fake:
            docker = docker or Docker()
            for name in plan["containers"]:
                docker.remove(name)
        for path in [plan["workspace"]] + [b["workspace"] for b in plan["builders"]]:
            shutil.rmtree(path, ignore_errors=True)
    events.emit("finished", resolved=bool(scoring and scoring["resolved"]), harness_error=bool(harness_errors),
                excluded=excluded)
    return result


def bounded(name):
    """The name as a whole word, so latest.patch is no test.patch."""
    return re.compile(r"(?<![\w.-])" + re.escape(name) + r"(?![\w-])")


def forbidden_for(task, task_repo):
    """What the audit looks for in the agents' streams: the task
    repository's path and name and the answer's file names, which exclude
    the run, and every hidden test's name, which is recorded; kept in
    memory, never in a file an agent could read."""
    patterns = []
    if task_repo:
        patterns.append(("task_repo", re.compile(re.escape(str(Path(task_repo).resolve())))))
    patterns += [("task_repo_name", bounded("swe-bench-tasks")), ("gold_patch", bounded("gold.patch")),
                 ("test_patch", bounded("test.patch"))]
    for name in task.hidden_tests:
        patterns.append(("hidden_test", bounded(name)))
    return patterns


def write_failed_prepare(run_dir, task, arm_name, tag, attempt, error):
    """A record for a run the harness could not even start, so the report
    names it instead of skipping a directory with nothing in it."""
    record.write_json(Path(run_dir) / "result.json", {"instance": task.instance_id, "repo": task.repo, "arm": arm_name,
                                                      "tag": tag, "attempt": attempt, "scoring": None, "harness_error": True,
                                                      "excluded": False, "agents": [], "stages": [], "flow": None})
    record.write_json(Path(run_dir) / "audit.json", {"harness_error": True, "reasons": [str(error)], "excluded": False})


def preflight(args):
    """What a run needs before it spends anything, checked once for the
    run or the lane: a real score needs the compiled dataset, docker and
    the harness; real agents need claude, logged in on a subscription and
    not by an API key, and as root IS_SANDBOX=1,
    without which claude refuses --permission-mode=bypassPermissions and
    every agent would end in an error that reads as the arm's failure. A
    run that would spend usage and then fail to score is refused here,
    before its first agent."""
    problems = []
    if not args.fake:
        if not args.dataset:
            problems.append("a real score needs --dataset, the directory score.py build wrote")
        elif not (Path(args.dataset) / "test.parquet").is_file():
            problems.append(f"{args.dataset}: no test.parquet there; is it a directory score.py build wrote?")
        harness = score.harness_executable(args.swebench)
        if not shutil.which(harness):
            problems.append(f"the harness {harness} is not there; name it with --swebench or FLOWBENCH_SWEBENCH")
        try:
            Docker().command("version", "--format", "{{.Server.Version}}", timeout=60)
        except RunError as error:
            problems.append(f"docker cannot be reached: {error}")
    if not (args.fake or args.fake_agents):
        if not shutil.which("claude"):
            problems.append("claude is not on the PATH")
        else:
            login = login_problem()
            if login:
                problems.append(login)
        if hasattr(os, "geteuid") and os.geteuid() == 0 and os.environ.get("IS_SANDBOX") != "1":
            problems.append("claude refuses --permission-mode=bypassPermissions as root unless IS_SANDBOX=1 is set: "
                            "run as another user, or set it where the machine is a sandbox")
    if problems:
        raise RunError("; ".join(problems))


def limits_from(args):
    return {"agent_seconds": int(args.agent_minutes * 60), "run_seconds": int(args.run_minutes * 60),
            "max_turns": args.max_turns, "parallel": args.parallel, "disallowed": DISALLOWED_TOOLS}


def run_one(logs, tag, arm, task, attempt, model, options, limits, fake, task_repo, dataset, swebench, score_timeout,
            keep, docker=None, fake_agents=False, effort=DEFAULT_EFFORT):
    """prepare, every stage in order while the run's time holds, finish;
    a harness error anywhere leaves a result that says so."""
    arm = load_arm(arm)
    fake_agents = fake or fake_agents
    attempt = attempt or next_attempt(logs, tag, arm["name"], task.instance_id)
    try:
        plan = prepare(logs, tag, arm, task, attempt, model, options, fake, docker, fake_agents, effort, task_repo, swebench)
    except RunError as error:
        run_dir = run_directory(logs, tag, arm["name"], task.instance_id, attempt)
        if run_dir.is_dir():
            write_failed_prepare(run_dir, task, arm["name"], tag, attempt, error)
        raise
    run_dir = Path(plan["run_dir"])
    events = record.Events(run_dir / "events.jsonl")
    stage_records, harness_errors = [], []
    started = time.monotonic()
    try:
        for stage in arm["stages"]:
            if time.monotonic() - started > limits["run_seconds"]:
                events.emit("run_time_limit", stage=stage["name"])
                stage_records.append({"name": stage["name"], "kind": stage["kind"], "agents": [], "missing": [],
                                      "skipped": True, "duration_ms": 0, "time_limit": True})
                continue
            stage_records.append(run_stage(plan, arm, stage, limits, fake_agents, events))
            record.write_json(run_dir / "stages.json", stage_records)
    except RunError as error:
        harness_errors.append(str(error))
        events.emit("harness_error", error=str(error))
    return finish(plan, stage_records, dataset, swebench, score_timeout, keep, docker, events, harness_errors,
                  forbidden_for(task, task_repo))


def read_task(task_repo, instance):
    directory = Path(task_repo) / "tasks" / instance
    if not directory.is_dir():
        raise RunError(f"{instance}: not in {task_repo} (tasks/{instance} is missing)")
    return tasks.read_task(directory)


def summary_line(result, logs):
    scoring = result.get("scoring") or {}
    return json.dumps({"instance": result["instance"], "arm": result["arm"], "attempt": result["attempt"],
                       "resolved": bool(scoring.get("resolved")), "reason": scoring.get("reason"),
                       "harness_error": result["harness_error"], "excluded": result.get("excluded", False),
                       "orchestration_failure": bool((result.get("flow") or {}).get("orchestration_failure")),
                       "cost_usd": result.get("cost_usd"),
                       "run_dir": str(run_directory(logs, result["tag"], result["arm"], result["instance"], result["attempt"]))},
                      sort_keys=True)


def command_run(args):
    preflight(args)
    task = read_task(args.task_repo, args.instance)
    if not args.fake:
        Docker().ensure_image(task.image, args.mirror)
    options = backlog.parse_options(args.option or [])
    result = run_one(args.logs, args.tag, args.arm, task, args.attempt, args.model, options, limits_from(args), args.fake,
                     args.task_repo, args.dataset, args.swebench, args.score_timeout, args.keep,
                     fake_agents=args.fake_agents, effort=args.effort)
    print(summary_line(result, args.logs))
    return 0 if not result["harness_error"] else 2


def verdict_of(result):
    if result["harness_error"]:
        return "error"
    return "resolved" if (result.get("scoring") or {}).get("resolved") else "failed"


def command_lane(args):
    """Take backlog items until none is pending, run each and report it
    to the backlog; the item's attempt number names the run directory
    unless that directory is there already, from a run that died. Any
    failure of a run is the item's, marked as a harness error, and the
    lane goes on to the next."""
    preflight(args)
    limits = limits_from(args)
    ran = 0
    while True:
        item = backlog.take(args.backlog, args.lane)
        if item is None:
            break
        attempt = item["attempt"]
        if run_directory(args.logs, item["tag"], item["arm"], item["instance"], attempt).exists():
            attempt = next_attempt(args.logs, item["tag"], item["arm"], item["instance"])
        try:
            task = read_task(args.task_repo, item["instance"])
            if not args.fake:
                Docker().ensure_image(task.image, args.mirror)
            result = run_one(args.logs, item["tag"], item["arm"], task, attempt, args.model, dict(item.get("options") or {}),
                             limits, args.fake, args.task_repo, args.dataset, args.swebench, args.score_timeout, args.keep,
                             fake_agents=args.fake_agents, effort=args.effort)
        except Exception as error:  # noqa: BLE001 - a lane outlives any one run's failure
            backlog.finish(args.backlog, item["instance"], item["arm"], item["attempt"], "error", None, True)
            print(f"{item['instance']} {item['arm']}: harness error: {error}", file=sys.stderr)
            remove_image_when_done(args, item["instance"])
            continue
        verdict = verdict_of(result)
        backlog.finish(args.backlog, item["instance"], item["arm"], item["attempt"], verdict,
                       str(run_directory(args.logs, item["tag"], item["arm"], item["instance"], attempt)),
                       result["harness_error"])
        remove_image_when_done(args, item["instance"])
        ran += 1
        print(f"{item['instance']} {item['arm']}: {verdict}")
    print(f"{ran} run(s)")
    return 0


def remove_image_when_done(args, instance):
    """With --remove-image, the instance's image removed once no item of
    the backlog still needs it, so a lane holds one instance's image at a
    time and the instance's arms share one pull."""
    if not args.remove_image or args.fake or backlog.instance_open(args.backlog, instance):
        return
    try:
        Docker().remove_image(read_task(args.task_repo, instance).image, args.mirror)
    except (RunError, tasks.TaskError) as error:
        print(f"{instance}: the image was not removed: {error}", file=sys.stderr)


def command_pull(args):
    """Each instance's image through the mirror, tagged under its own
    name; one at a time, since a session's disk holds a few."""
    instances = backlog.split(args.instances)
    if len(instances) == 1 and instances[0].startswith("@"):
        instances = [line.strip() for line in Path(instances[0][1:]).read_text(encoding="utf-8").splitlines() if line.strip()]
    docker = Docker()
    for instance in instances:
        task = read_task(args.task_repo, instance)
        docker.pull(task.image, args.mirror)
        print(f"{instance}: {task.image}")
    return 0


def command_arm(args):
    arm = load_arm(args.arm)
    problems = []
    for stage in arm["stages"]:
        template = (Path(arm["dir"]) / stage["prompt"]).read_text(encoding="utf-8")
        for name in unknown_placeholders(template):
            problems.append(f"{stage['prompt']}: {{{name}}} is not a placeholder the runner fills")
    print(json.dumps({"name": arm["name"], "stages": [s["name"] for s in arm["stages"]], "problems": problems}, indent=2))
    return 1 if problems else 0


def add_run_arguments(parser):
    parser.add_argument("--logs", required=True)
    parser.add_argument("--task-repo", required=True, help="the checkout of SWE-bench/swe-bench-tasks")
    parser.add_argument("--dataset", help="the dataset compiled from it by score.py build (needed for a real score)")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--effort", default=DEFAULT_EFFORT, help="claude's effort level, the same for every agent")
    parser.add_argument("--fake", action="store_true", help="the whole path faked: no image, the fake agent, a fake score")
    parser.add_argument("--fake-agents", action="store_true",
                        help="the real image and the real scorer with the fake agent: a rehearsal that spends nothing")
    parser.add_argument("--swebench", help="the harness's executable (default FLOWBENCH_SWEBENCH, then swebench)")
    parser.add_argument("--score-timeout", type=int, default=score.DEFAULT_TIMEOUT)
    parser.add_argument("--agent-minutes", type=float, default=DEFAULT_AGENT_MINUTES)
    parser.add_argument("--run-minutes", type=float, default=DEFAULT_RUN_MINUTES)
    parser.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS, help="a turn cap per agent; 0 is none")
    parser.add_argument("--parallel", type=int, default=DEFAULT_PARALLEL, help="agents at once in a parallel stage")
    parser.add_argument("--keep", action="store_true", help="leave the containers and the workspace for a look")
    parser.add_argument("--mirror", default=DEFAULT_MIRROR,
                        help="the registry mirror an image missing here is pulled through; empty for Docker Hub itself")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run one (instance, arm) attempt, or a lane of the backlog.")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    add_run_arguments(run)
    run.add_argument("--tag", required=True)
    run.add_argument("--arm", required=True)
    run.add_argument("--instance", required=True)
    run.add_argument("--attempt", type=int)
    run.add_argument("--option", action="append", help="K=V for the arm (builders=3, route=session)")
    lane = commands.add_parser("lane")
    add_run_arguments(lane)
    lane.add_argument("--backlog", required=True, help="the backlog file (backlog.py)")
    lane.add_argument("--lane", required=True)
    lane.add_argument("--remove-image", action="store_true",
                      help="remove an instance's image once no item of the backlog still needs it")
    pull = commands.add_parser("pull", help="pull instances' images through the mirror, ahead of a run")
    pull.add_argument("--task-repo", required=True)
    pull.add_argument("--instances", required=True, help="comma separated, or @FILE with one per line")
    pull.add_argument("--mirror", default=DEFAULT_MIRROR, help="the registry mirror; empty for Docker Hub itself")
    arm = commands.add_parser("arm", help="check an arm's stages.json and prompts")
    arm.add_argument("arm")
    args = parser.parse_args(argv)
    try:
        return {"run": command_run, "lane": command_lane, "pull": command_pull, "arm": command_arm}[args.command](args)
    except (RunError, tasks.TaskError, backlog.BacklogError, OSError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
