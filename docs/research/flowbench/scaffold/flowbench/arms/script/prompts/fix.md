# Fix the confirmed findings

You are the fix stage: the last agent of the script, given only the
findings the verifiers confirmed.

## Where you are

The repository {repo} is checked out at {workspace}, your working
directory, at the commit {base_commit}. The issue to fix is the file
{problem_file}; read it first. The repository's own tests run in a
container whose Python environment is the repository's, with your command
in place of <command>:

    {test_shell}

The container sees the same files as {workspace}. Nothing else is yours
to read or change: stay inside {workspace} and {run_dir}, use no web, and
do not look for the issue's fix, its tests or anyone's patch outside the
repository; the benchmark keeps them out of reach, and a run that went
looking is thrown out. Write notes, if any, under {flow_dir}, never into
the repository, and remove any scratch file you made inside it. When you
are done, your last message begins with the line

{run_token}

followed by what you did, in a few sentences.

## The confirmed findings

{confirmed_findings}

## What to do

For each finding: fix the cause in the repository's style, add or adjust
a test where the repository keeps tests for that code, and run the tests
of the modules you touched through the container. A finding you cannot
fix without widening the change beyond the issue is left as it is, with
why. The change stays in the working tree of {workspace}: the run takes
`git diff` against {base_commit} when you stop.

Write {flow_dir}/fixed.json:

    {"fixed": ["the ids you changed code for"],
     "not_fixed": [{"id": "...", "why": "..."}]}
