"""The agent of a fake run: spends nothing and walks every stage's path.

run.py gives it the job as a JSON file (the stage, its kind, the agent's
name, the prompt's fields and the run's options) and the prompt on
stdin, which it reads and ignores. It does what the stage is to leave
behind, by the stage's kind: a work stage edits the workspace (and
commits on its branch when it is a builder, and makes the claim branch
claude/1 and commits on it when it is a worker that opens a pull
request), a stack stage merges the
builders' branches and writes stack.json, a review stage writes its
findings file with one finding, a verify stage its verdict (real for the
correctness lens, not real for the others), a fix stage edits once more
and writes fixed.json, an answer stage writes answers.json. Then it
writes a stream-json file shaped as Claude Code's, with an init event, an
assistant message and a result event, so the record reads it as it reads
a real agent's.

The options steer the rehearsal: fake_fail=<stage or agent> ends that
agent in error, fake_limit=<stage or agent> ends it on a usage limit (a
harness error), fake_findings=0 leaves the review empty, fake_tokens=N
reports N input tokens per agent, fake_conflict=1 makes the builders'
changes collide so the stack stage sees a conflict.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

REHEARSAL_LINE = "# flowbench rehearsal: {agent}\n"


def git(workspace, *args, check=True):
    done = subprocess.run(["git", "-c", "safe.directory=*", "-C", str(workspace), *args],
                          capture_output=True, text=True, check=False)
    if check and done.returncode != 0:
        raise SystemExit(f"fake agent: git {' '.join(args)} failed: {done.stderr.strip()}")
    return done


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def target_file(workspace):
    """The file a rehearsal edits: the fake workspace's pkg/core.py, else
    the first Python file at the repository's root, else a new file."""
    workspace = Path(workspace)
    core = workspace / "pkg" / "core.py"
    if core.is_file():
        return core
    for path in sorted(workspace.glob("*.py")):
        return path
    return workspace / "flowbench-rehearsal.txt"


def edit(workspace, agent, conflict=False):
    """The fix when the workspace is the fake one (add returns a - b), a
    harmless line otherwise; with conflict, every builder rewrites the
    same line differently so a merge cannot take both."""
    path = target_file(workspace)
    if path.name == "core.py" and "return a - b" in path.read_text(encoding="utf-8"):
        text = path.read_text(encoding="utf-8").replace("return a - b", "return a + b")
        if conflict:
            text = text.replace("def add(a, b):", f"def add(a, b):  # {agent}")
        path.write_text(text, encoding="utf-8")
        return str(path.relative_to(workspace))
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    line = REHEARSAL_LINE.format(agent=agent)
    if conflict:
        path.write_text(line + existing, encoding="utf-8")
    else:
        path.write_text(existing + ("" if existing.endswith("\n") or not existing else "\n") + line, encoding="utf-8")
    return str(path.relative_to(workspace))


def work(job):
    fields = job["fields"]
    claims = job.get("writes", "").endswith(".md")
    if claims:
        git(fields["workspace"], "switch", "-c", "claude/1", "--no-track")
    changed = edit(fields["workspace"], job["agent"], conflict=str(job["options"].get("fake_conflict", "")) == "1")
    if fields.get("branch") or claims:
        git(fields["workspace"], "add", "-A")
        git(fields["workspace"], "commit", "-q", "-m", f"{job['agent']}: the rehearsal's change")
    if claims:
        Path(job["writes"]).parent.mkdir(parents=True, exist_ok=True)
        Path(job["writes"]).write_text(f"# Fix for {fields['instance_id']}\n\nChanged {changed}.\n", encoding="utf-8")
    return f"edited {changed}"


def stack(job):
    fields = job["fields"]
    builders = json.loads(fields["builders"] or "[]")
    merged, conflicts = [], []
    for builder in builders:
        done = git(fields["workspace"], "merge", "--no-edit", builder["branch"], check=False)
        if done.returncode == 0:
            merged.append(builder["branch"])
        else:
            conflicts.append(builder["branch"])
            git(fields["workspace"], "merge", "--abort", check=False)
    write_json(Path(fields["flow_dir"]) / "stack.json", {"merged": merged, "conflicts": conflicts, "tests": "not run"})
    return f"merged {len(merged)}, {len(conflicts)} conflict(s)"


def review(job):
    fields = job["fields"]
    findings = []
    if str(job["options"].get("fake_findings", "1")) != "0":
        findings.append({"id": f"{fields['lens']}-1", "file": "pkg/core.py", "line": 2,
                         "claim": f"a {fields['lens']} finding of the rehearsal", "evidence": "none; this is a rehearsal",
                         "severity": "medium"})
    write_json(fields["findings_file"], {"lens": fields["lens"], "findings": findings})
    return f"{len(findings)} finding(s)"


def verify(job):
    fields = job["fields"]
    real = fields["finding_id"].startswith("correctness")
    write_json(fields["verdict_file"], {"id": fields["finding_id"], "real": real,
                                        "why": "the rehearsal confirms the correctness lens and refutes the rest"})
    return "real" if real else "not real"


def fix(job):
    fields = job["fields"]
    confirmed = json.loads(fields["confirmed_findings"] or "[]")
    for _ in confirmed:
        edit(fields["workspace"], job["agent"])
    write_json(Path(fields["flow_dir"]) / "fixed.json", {"fixed": [f["id"] for f in confirmed], "not_fixed": []})
    return f"fixed {len(confirmed)}"


def answer(job):
    fields = job["fields"]
    raised = json.loads(fields["findings"] or "[]")
    answers = []
    for finding in raised:
        changed = finding["id"].startswith("correctness")
        if changed:
            edit(fields["workspace"], job["agent"])
        answers.append({"id": finding["id"], "answer": "changed" if changed else "not a change: the rehearsal disagrees",
                        "changed": changed})
    if fields.get("branch") or git(fields["workspace"], "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() != "HEAD":
        git(fields["workspace"], "add", "-A")
        git(fields["workspace"], "commit", "-q", "--allow-empty", "-m", f"{job['agent']}: the answers")
    write_json(Path(fields["flow_dir"]) / "answers.json", {"answers": answers})
    return f"answered {len(answers)}"


DEEDS = {"work": work, "stack": stack, "review": review, "verify": verify, "fix": fix, "answer": answer}


def names_this(option, job):
    return str(job["options"].get(option, "")) in (job["stage"], job["agent"])


def stream(job, text, is_error, tokens):
    usage = {"input_tokens": tokens, "output_tokens": tokens // 10, "cache_read_input_tokens": 0,
             "cache_creation_input_tokens": 0}
    session_id = f"fake-{job['agent']}"
    lines = [{"type": "system", "subtype": "init", "model": job["model"], "session_id": session_id, "cwd": job["fields"]["workspace"]},
             {"type": "assistant", "message": {"id": f"msg_{job['agent']}", "role": "assistant", "usage": usage,
                                               "stop_reason": "end_turn", "content": [{"type": "text", "text": text}]}},
             {"type": "result", "subtype": "error_during_execution" if is_error else "success", "is_error": is_error,
              "num_turns": 1, "duration_ms": 1, "usage": usage, "session_id": session_id, "result": text}]
    Path(job["stream"]).write_text("".join(json.dumps(line, sort_keys=True) + "\n" for line in lines), encoding="utf-8")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: fake_agent.py JOB.json (the prompt on stdin)", file=sys.stderr)
        return 2
    job = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    sys.stdin.read()
    tokens = int(job["options"].get("fake_tokens", 1000) or 0)
    time.sleep(0.01)
    if names_this("fake_limit", job):
        stream(job, "You've hit your usage limit. Try again later.", True, tokens)
        return 1
    if names_this("fake_fail", job):
        stream(job, "the rehearsal fails here on purpose", True, tokens)
        return 1
    deed = DEEDS[job["kind"]]
    text = f"{job['fields']['run_token']}\n{deed(job)}"
    stream(job, text, False, tokens)
    return 0


if __name__ == "__main__":
    sys.exit(main())
