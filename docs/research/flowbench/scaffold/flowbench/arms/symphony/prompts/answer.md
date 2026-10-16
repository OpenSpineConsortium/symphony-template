# Answer the review

You are the worker again, back on your pull request (the branch claude/1
in {workspace}, against {base_commit}) with the reviewer's findings.

## Where you are

The repository {repo} is checked out at {workspace}, your working
directory, at the commit {base_commit}. The issue to fix is the file
{problem_file}; read it first. The repository's own tests run in a
container whose Python environment is the repository's, through the
script {test_shell}, with your command after it:

    {test_shell} pytest -x path/to/test_x.py
    {test_shell} bash -c 'python -c "import pkg; print(pkg.thing())"'

The container sees the same files as {workspace}. Nothing else is yours
to read or change: stay inside {workspace}, write under {flow_dir} only
the file this prompt asks for and notes of your own, never read another
agent's files there, use no web, and do not look for the issue's fix,
its tests or anyone's patch outside the repository: the benchmark keeps
them out of reach, and a run whose transcript shows it went looking is
thrown out. The repository holds only the change when you stop: remove
any scratch file you made inside it. When you are done, your last message
begins with the line

{run_token}

followed by what you did, in a few sentences.

## The findings

{findings}

## What to do

Answer each finding as the protocol asks: change the code where the
finding is right, as a commit on claude/1 with a test where the
repository keeps tests for that code and the tests of the modules you
touched run through the container; or say why not where it is wrong, with
the input or the trace that shows it. A finding is never left silent.

Write {flow_dir}/answers-{stage}.json:

    {"answers": [{"id": "...", "answer": "what you changed, or why not",
                  "changed": true | false}]}

Leave claude/1 checked out when you stop.
