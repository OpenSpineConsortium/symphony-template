"""Run one (instance, arm) attempt: provision the instance's image as a
container with the repository on the host, run the arm's stages, take
the patch, score it and write the record.

The agents run on the host, in the workspace, a copy of the image's
/testbed (the repository at the instance's base commit, under the one
commit the image's build adds on top of it, which is where the harness
applies a patch; the prompts' {base_commit} is that start commit, and
the record keeps both), and the
container runs the same workspace bind-mounted at /testbed, as the place
where the repository's tests run in the image's own Python environment:
an agent runs a test there with the line every prompt gives it as
{test_shell}, `docker exec <container> bash -lc 'source
/opt/miniconda3/bin/activate testbed && cd /testbed && <command>'`. The
task repository's checkout, which holds the gold patch and the hidden
tests, is never mounted, copied or named to an agent: run.py reads the
instance from it and passes on the problem statement alone, as a file
beside the workspace.

An arm is a folder under arms/ with stages.json and its prompts
(arms/README.md). A stage runs one or more agents, each a headless Claude
Code (`claude -p`) on the host's own login, never an API key, or in fake
mode fake_agent.py, which spends nothing and walks the same path. Each
agent's stream-json output is kept beside the run as
agents/<agent>.stream.jsonl, and the record reads its tokens, cost and
end from it (record.stream_summary). A failure of the flow itself (an
agent that ended in error, a stage that left no output for the next) is
the arm's result, counted as an orchestration failure and scored with
whatever patch there is; a failure of the harness (no image, no docker,
a usage limit) is a harness error, and the audit names it so the report
leaves the run out.

    python3 flowbench/run.py run --logs LOGS --tag TAG --arm script --instance ID --task-repo CHECKOUT [--model M] [--fake]
    python3 flowbench/run.py lane --backlog B --lane L --logs LOGS --task-repo CHECKOUT [--fake]
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
DEFAULT_AGENT_MINUTES = 45
DEFAULT_RUN_MINUTES = 120
DEFAULT_MAX_TURNS = 200
DEFAULT_PARALLEL = 3
# Claude Code tools the agents may not use: the comparison is of local
# tools only (PLAN.md), so the web is off for every arm alike.
LOCAL_ONLY_DISALLOWED = ("WebFetch", "WebSearch")
# What the patch leaves out: the caches a test run leaves in the
# workspace, which git would otherwise add as new binary files that the
# harness's git apply refuses.
EXCLUDED_FROM_PATCH = ("__pycache__/", "*.pyc", ".pytest_cache/", ".mypy_cache/", "*.egg-info/", ".flowbench/")
STAGE_KINDS = ("work", "stack", "review", "verify", "fix", "answer")
AGENT_COUNT_WORDS = ("builders", "per_finding")
PLACEHOLDERS = ("instance_id", "repo", "base_commit", "workspace", "container", "test_shell", "problem_file",
                "run_dir", "flow_dir", "stage", "agent", "lens", "lens_text", "findings_file", "verdict_file",
                "finding", "finding_id", "findings", "confirmed_findings", "builders", "branch", "run_token", "options")
PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")
# What a usage limit looks like in Claude Code's result text: an agent
# that ends on one is the harness's failure, not the arm's.
LIMIT_TEXT = re.compile(r"usage limit|rate limit|out of (?:extra )?usage|credit balance", re.IGNORECASE)


class RunError(RuntimeError):
    """A failure of the harness, not of the arm: the run is left out."""


class Docker:
    """The docker commands the runner uses, one method each, so a test runs
    with a fake that records them instead."""

    def __init__(self, executable="docker"):
        self.executable = executable

    def command(self, *args, check=True, timeout=600):
        done = subprocess.run([self.executable, *args], capture_output=True, text=True, timeout=timeout, check=False)
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


def git(workspace, *args, check=True):
    done = subprocess.run(["git", "-c", "safe.directory=*", "-C", str(workspace), *args],
                          capture_output=True, text=True, check=False)
    if check and done.returncode != 0:
        raise RunError(f"git {' '.join(args)} in {workspace} failed ({done.returncode}): {done.stderr.strip()[-2000:]}")
    return done.stdout


def run_directory(logs, tag, arm, instance, attempt):
    return Path(logs) / tag / arm / instance / f"attempt-{attempt}"


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
        if not isinstance(name, str) or not name or name in seen:
            raise RunError(f"{config_path}: every stage has a name of its own ({name!r})")
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


def test_shell(container):
    if not container:
        return "bash -lc '<command>' (the fake run has no container; run the tests on the host)"
    return f"docker exec {container} bash -lc '{ACTIVATE} && cd {CONTAINER_WORKSPACE} && <command>'"


def exclude_from_patch(workspace):
    exclude = Path(workspace) / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a", encoding="utf-8") as out:
        out.write("".join(f"{pattern}\n" for pattern in EXCLUDED_FROM_PATCH))


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
                       ("gc.autoDetach", "false"), ("maintenance.auto", "false"), ("commit.gpgsign", "false")):
        git(workspace, "config", key, value)


def make_worktrees(workspace, run_dir, count):
    """One worktree and branch per builder beyond the first, builder-1 to
    builder-K, each from the base; the stack stage merges them."""
    builders = []
    for k in range(1, count + 1):
        path = Path(run_dir) / f"worktree-{k}"
        git(workspace, "worktree", "add", "-b", f"builder-{k}", str(path), "HEAD")
        builders.append({"k": k, "branch": f"builder-{k}", "workspace": str(path), "container": None})
    return builders


def prepare(logs, tag, arm, task, attempt=None, model=DEFAULT_MODEL, options=None, fake=False, docker=None,
            fake_agents=False):
    """The run directory, the workspace (and its container), plan.json."""
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
    run_id = score.run_id_for(tag, arm["name"], task.instance_id, attempt)
    containers = []
    image_id = None
    if fake:
        base_commit = start_commit = fake_workspace(workspace, task.instance_id)
        image = "fake"
    else:
        docker = docker or Docker()
        image = task.image
        name = container_name(tag, arm["name"], task.instance_id, attempt)
        docker.remove(name)
        docker.create(image, name)
        docker.copy_out(name, CONTAINER_WORKSPACE, workspace)
        docker.remove(name)
        configure_git(workspace)
        base_commit = task.base_commit
        start_commit = git(workspace, "rev-parse", "HEAD").strip()
        descends = subprocess.run(["git", "-c", "safe.directory=*", "-C", str(workspace), "merge-base", "--is-ancestor",
                                   base_commit, start_commit], capture_output=True, text=True, check=False)
        if descends.returncode != 0:
            raise RunError(f"{task.instance_id}: the image's /testbed is at {start_commit}, which does not descend from "
                           f"the base {base_commit}")
        docker.start_workspace(image, name, workspace, f"flowbench.run={run_id}")
        containers.append(name)
        image_id = docker.image_id(image)
    exclude_from_patch(workspace)
    count = int(options.get("builders", 1) or 1)
    builders = make_worktrees(workspace, run_dir, count) if count > 1 else []
    for builder in builders:
        if not fake:
            name = container_name(tag, arm["name"], task.instance_id, attempt, builder["k"])
            docker.remove(name)
            docker.start_workspace(image, name, builder["workspace"], f"flowbench.run={run_id}")
            builder["container"] = name
            containers.append(name)
    plan = {"tag": tag, "arm": arm["name"], "arm_dir": arm["dir"], "instance": task.instance_id, "repo": task.repo,
            "attempt": attempt, "run_dir": str(run_dir), "workspace": str(workspace), "base_commit": base_commit,
            "start_commit": start_commit,
            "container": containers[0] if containers else None, "containers": containers, "image": image,
            "image_id": image_id, "model": model, "options": options, "builders": builders, "fake": fake,
            "fake_agents": bool(fake or fake_agents),
            "run_token": f"flowbench-{secrets.token_hex(8)}", "run_id": run_id,
            "stages": [stage["name"] for stage in arm["stages"]], "started": round(time.time(), 3)}
    record.write_json(run_dir / "plan.json", plan)
    events.emit("prepared", instance=task.instance_id, arm=arm["name"], attempt=attempt, image=image, fake=fake)
    return plan


def read_findings(flow_dir):
    """Every finding the review stage raised, in file order, each with its
    lens; a file that is not a findings table is left out and named."""
    findings, problems = [], []
    for path in sorted(Path(flow_dir).glob("findings-*.json")):
        data = record.read_json(path)
        if not isinstance(data, dict) or not isinstance(data.get("findings"), list):
            problems.append(f"{path.name}: not a findings table")
            continue
        for finding in data["findings"]:
            if isinstance(finding, dict) and isinstance(finding.get("id"), str):
                findings.append({**finding, "lens": data.get("lens") or path.stem[len("findings-"):]})
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
                   "test_shell": test_shell(plan["container"]), "problem_file": str(run_dir / "problem.md"),
                   "run_dir": str(run_dir), "flow_dir": str(run_dir / "flow"), "stage": stage["name"], "agent": agent,
                   "builders": json.dumps(plan["builders"], sort_keys=True), "run_token": plan["run_token"],
                   "options": json.dumps(plan["options"], sort_keys=True)})
    fields.update(extra)
    return fields


def jobs_for_stage(plan, stage):
    """The stage's agents, each with its prompt fields: one per lens, one
    per builder (in its worktree, with its container), one per finding
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
    if stage.get("lenses"):
        for lens, text in stage["lenses"].items():
            agent = f"{stage['name']}-{lens}"
            jobs.append(job_fields(plan, stage, agent, lens=lens, lens_text=text,
                                   findings_file=str(flow_dir / f"findings-{lens}.json")))
    elif stage.get("agents", 1) == "builders":
        builders = plan["builders"] or [{"k": 1, "branch": "", "workspace": plan["workspace"], "container": plan["container"]}]
        for builder in builders:
            agent = f"{stage['name']}-{builder['k']}" if plan["builders"] else stage["name"]
            jobs.append(job_fields(plan, stage, agent, workspace=builder["workspace"], container=builder["container"] or "",
                                   test_shell=test_shell(builder["container"]), branch=builder["branch"]))
    elif stage.get("agents", 1) == "per_finding":
        for finding in raised:
            agent = f"{stage['name']}-{safe_file_name(finding['id'])}"
            jobs.append(job_fields(plan, stage, agent, finding=json.dumps(finding, indent=2, sort_keys=True),
                                   finding_id=finding["id"], lens=finding.get("lens", ""),
                                   verdict_file=str(flow_dir / f"verdict-{safe_file_name(finding['id'])}.json")))
    else:
        count = int(stage.get("agents", 1))
        for i in range(1, count + 1):
            agent = f"{stage['name']}-{i}" if count > 1 else stage["name"]
            jobs.append(job_fields(plan, stage, agent, findings=raised_text, confirmed_findings=confirmed_text))
    return jobs


def claude_command(model, max_turns, disallowed):
    return ["claude", "--print", "--verbose", "--output-format=stream-json", "--permission-mode=bypassPermissions",
            "--model", model, "--max-turns", str(int(max_turns)), "--disallowedTools", ",".join(disallowed)]


def agent_environment():
    """The host's environment, less any API key: the agents run on the
    login's subscription, and a key present would bill it instead."""
    environment = {key: value for key, value in os.environ.items() if key != "ANTHROPIC_API_KEY"}
    environment.setdefault("GIT_TERMINAL_PROMPT", "0")
    return environment


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
        command = claude_command(plan["model"], limits["max_turns"], limits["disallowed"])
    events.emit("agent_started", stage=stage["name"], agent=agent, fake=fake)
    started = time.monotonic()
    status, exit_code = "success", None
    with stream_path.open("w", encoding="utf-8") as out, stderr_path.open("w", encoding="utf-8") as err:
        try:
            done = subprocess.run(command, input=prompt, stdout=out, stderr=err, cwd=fields["workspace"], text=True,
                                  timeout=limits["agent_seconds"], env=agent_environment(), check=False)
            exit_code = done.returncode
        except subprocess.TimeoutExpired:
            status = "timeout"
        except FileNotFoundError as error:
            raise RunError(f"{command[0]} is not there: {error}") from error
    elapsed_ms = int((time.monotonic() - started) * 1000)
    summary = record.stream_summary(stream_path) or {}
    if status == "success" and (exit_code != 0 or summary.get("is_error")):
        status = "error"
    text = summary.get("result_text") or ""
    harness_error = bool(status == "error" and LIMIT_TEXT.search(text))
    agent_record = {"agent": agent, "stage": stage["name"], "lens": fields.get("lens") or None, "status": status,
                    "end": summary.get("end"), "exit_code": exit_code, "duration_ms": elapsed_ms,
                    "turns": summary.get("turns"), "tokens": summary.get("tokens"), "cost_usd": summary.get("cost_usd"),
                    "cost_source": summary.get("cost_source"), "model": summary.get("model"),
                    "harness_error": harness_error, "result_text": text[:500] or None}
    events.emit("agent_ended", stage=stage["name"], agent=agent, status=status, duration_ms=elapsed_ms)
    return agent_record


def run_stage(plan, arm, stage, limits, fake, events):
    """The stage's agents, in parallel where it says so, then a look at
    what it was to leave: a missing output is the flow's failure."""
    template = (Path(arm["dir"]) / stage["prompt"]).read_text(encoding="utf-8")
    jobs = jobs_for_stage(plan, stage)
    started = time.monotonic()
    stage_record = {"name": stage["name"], "kind": stage["kind"], "agents": [], "missing": [], "skipped": not jobs}
    if not jobs:
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
    included, as the harness's git apply takes it on the image."""
    git(workspace, "add", "-A")
    return git(workspace, "diff", "--cached", start_commit)


def flow_metrics(plan, stage_records):
    flow_dir = Path(plan["run_dir"]) / "flow"
    findings, problems = read_findings(flow_dir)
    verdicts = read_verdicts(flow_dir)
    fixed = record.read_json(flow_dir / "fixed.json")
    answers = record.read_json(flow_dir / "answers.json")
    stack = record.read_json(flow_dir / "stack.json")
    reasons = list(problems)
    for stage in stage_records:
        for agent in stage["agents"]:
            if agent["status"] != "success" and not agent["harness_error"]:
                reasons.append(f"{agent['agent']}: {agent['status']} ({agent['end']})")
        for missing in stage["missing"]:
            reasons.append(f"{stage['name']}: left no {Path(missing).name}")
    fixed_ids = fixed.get("fixed") if isinstance(fixed, dict) and isinstance(fixed.get("fixed"), list) else []
    if isinstance(answers, dict) and isinstance(answers.get("answers"), list):
        fixed_ids = fixed_ids + [a.get("id") for a in answers["answers"] if isinstance(a, dict) and a.get("changed")]
    return {"orchestration_failure": bool(reasons), "orchestration_reasons": reasons,
            "findings_raised": len(findings), "findings_by_lens": count_by(f["lens"] for f in findings),
            "findings_confirmed": sum(1 for f in findings if verdicts.get(f["id"])),
            "findings_fixed": len(fixed_ids),
            "merges": stack if isinstance(stack, dict) else None, "review_rounds": 1 if answers else 0}


def count_by(names):
    counts = {}
    for name in names:
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


def cost_of(agents, model):
    """The run's cost: Claude Code's own figure summed when every agent
    has one, else the list-price estimate from the tokens."""
    costs = [agent.get("cost_usd") for agent in agents]
    if costs and all(cost is not None for cost in costs):
        return round(sum(costs), 4), "claude code"
    tokens = record.sum_tokens([agent.get("tokens") for agent in agents])
    estimate = record.price(tokens, model)
    if estimate is not None:
        return estimate, "estimated from tokens"
    return record.price_lower_bound(tokens, model), "lower bound from tokens"


def finish(plan, stage_records, task_repo=None, swebench=None, score_timeout=score.DEFAULT_TIMEOUT, keep=False,
           docker=None, events=None, harness_errors=None):
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
        scoring = score.score(run_dir, plan["tag"], plan["arm"], plan["instance"], plan["attempt"], task_repo, swebench,
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
            harness_errors.append(f"{agent['agent']}: {agent['result_text']}")
    cost, cost_source = cost_of(agents, plan["model"])
    agents_ms = sum(agent["duration_ms"] for agent in agents)
    result = {"instance": plan["instance"], "repo": plan["repo"], "arm": plan["arm"], "tag": plan["tag"],
              "attempt": plan["attempt"], "model": plan["model"],
              "driver": "fake" if plan.get("fake_agents") else "claude-cli",
              "route": plan["options"].get("route", "host"), "fake": fake, "options": plan["options"],
              "scoring": scoring, "patch_bytes": len(patch.encode("utf-8")),
              "tokens": record.sum_tokens([agent.get("tokens") for agent in agents]), "cost_usd": cost,
              "cost_source": cost_source, "agents": agents,
              "stages": [{key: stage[key] for key in ("name", "kind", "duration_ms", "missing", "skipped")} for stage in stage_records],
              "timings": {"agents_seconds": round(agents_ms / 1000, 3), "wall_seconds": round(time.time() - plan["started"], 3)},
              "flow": flow_metrics(plan, stage_records), "harness_error": bool(harness_errors),
              "provenance": {"image": plan["image"], "image_id": plan["image_id"], "base_commit": plan["base_commit"],
                             "start_commit": plan["start_commit"], "run_token": None,
                             "scorer": scoring["harness"] if scoring else None}}
    record.write_json(run_dir / "result.json", result)
    record.write_json(run_dir / "audit.json", {"harness_error": bool(harness_errors), "reasons": harness_errors,
                                               "orchestration_failure": result["flow"]["orchestration_failure"],
                                               "orchestration_reasons": result["flow"]["orchestration_reasons"]})
    if not keep and not fake:
        docker = docker or Docker()
        for name in plan["containers"]:
            docker.remove(name)
    events.emit("finished", resolved=bool(scoring and scoring["resolved"]), harness_error=bool(harness_errors))
    return result


def limits_from(args):
    return {"agent_seconds": int(args.agent_minutes * 60), "run_seconds": int(args.run_minutes * 60),
            "max_turns": args.max_turns, "parallel": args.parallel, "disallowed": LOCAL_ONLY_DISALLOWED}


def run_one(logs, tag, arm, task, attempt, model, options, limits, fake, task_repo, swebench, score_timeout, keep,
            docker=None, fake_agents=False):
    """prepare, every stage in order while the run's time holds, finish;
    a harness error before the stages leaves a result that says so."""
    arm = load_arm(arm)
    fake_agents = fake or fake_agents
    plan = prepare(logs, tag, arm, task, attempt, model, options, fake, docker, fake_agents)
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
    return finish(plan, stage_records, task_repo, swebench, score_timeout, keep, docker, events, harness_errors)


def read_task(task_repo, instance):
    directory = Path(task_repo) / "tasks" / instance
    if not directory.is_dir():
        raise RunError(f"{instance}: not in {task_repo} (tasks/{instance} is missing)")
    return tasks.read_task(directory)


def command_run(args):
    task = read_task(args.task_repo, args.instance)
    options = backlog.parse_options(args.option or [])
    result = run_one(args.logs, args.tag, args.arm, task, args.attempt, args.model, options, limits_from(args), args.fake,
                     args.task_repo, args.swebench, args.score_timeout, args.keep, fake_agents=args.fake_agents)
    print(json.dumps({key: result[key] for key in ("instance", "arm", "attempt", "harness_error", "cost_usd")}
                     | {"resolved": bool(result["scoring"] and result["scoring"]["resolved"]),
                        "reason": result["scoring"]["reason"] if result["scoring"] else None,
                        "orchestration_failure": result["flow"]["orchestration_failure"],
                        "run_dir": str(run_directory(args.logs, args.tag, result["arm"], result["instance"], result["attempt"]))},
                     sort_keys=True))
    return 0 if not result["harness_error"] else 2


def command_lane(args):
    """Take backlog items until none is pending, run each and report it
    to the backlog; the item's attempt number names the run directory
    unless that directory is there already, from a run that died."""
    limits = limits_from(args)
    ran = 0
    while True:
        item = backlog.take(args.backlog, args.lane)
        if item is None:
            break
        task = read_task(args.task_repo, item["instance"])
        attempt = item["attempt"]
        if run_directory(args.logs, item["tag"], item["arm"], item["instance"], attempt).exists():
            attempt = next_attempt(args.logs, item["tag"], item["arm"], item["instance"])
        options = {**(item.get("options") or {})}
        try:
            result = run_one(args.logs, item["tag"], item["arm"], task, attempt, args.model, options, limits, args.fake,
                             args.task_repo, args.swebench, args.score_timeout, args.keep, fake_agents=args.fake_agents)
        except RunError as error:
            backlog.finish(args.backlog, item["instance"], item["arm"], item["attempt"], "error", None, True)
            print(f"{item['instance']} {item['arm']}: harness error: {error}", file=sys.stderr)
            continue
        verdict = "error" if result["harness_error"] else ("resolved" if result["scoring"]["resolved"] else "failed")
        backlog.finish(args.backlog, item["instance"], item["arm"], item["attempt"], verdict,
                       str(run_directory(args.logs, item["tag"], item["arm"], item["instance"], attempt)),
                       result["harness_error"])
        ran += 1
        print(f"{item['instance']} {item['arm']}: {verdict}")
    print(f"{ran} run(s)")
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
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--fake", action="store_true", help="the whole path faked: no image, the fake agent, a fake score")
    parser.add_argument("--fake-agents", action="store_true",
                        help="the real image and the real scorer with the fake agent: a rehearsal that spends nothing")
    parser.add_argument("--swebench", help="the harness's executable (default FLOWBENCH_SWEBENCH, then swebench)")
    parser.add_argument("--score-timeout", type=int, default=score.DEFAULT_TIMEOUT)
    parser.add_argument("--agent-minutes", type=float, default=DEFAULT_AGENT_MINUTES)
    parser.add_argument("--run-minutes", type=float, default=DEFAULT_RUN_MINUTES)
    parser.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
    parser.add_argument("--parallel", type=int, default=DEFAULT_PARALLEL, help="agents at once in a parallel stage")
    parser.add_argument("--keep", action="store_true", help="leave the containers for a look")


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
    arm = commands.add_parser("arm", help="check an arm's stages.json and prompts")
    arm.add_argument("arm")
    args = parser.parse_args(argv)
    try:
        return {"run": command_run, "lane": command_lane, "arm": command_arm}[args.command](args)
    except (RunError, tasks.TaskError, backlog.BacklogError, OSError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
