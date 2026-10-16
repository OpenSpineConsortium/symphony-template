# Review the change through the {lens} lens

You are one reviewer of several, each reading the same change through a
lens of its own. Yours is {lens}:

{lens_text}

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

## What to do

The change under review is `git diff {base_commit}` in {workspace}: the
working tree and any commits since the base. Read the issue, then the
change, then the code around it. Raise a finding only where you can point
to a file and a line and say what goes wrong for which input or case; a
doubt without a path is not a finding, and an empty list is a good answer
when the change is right under your lens. Change nothing in the
repository.

Write {findings_file}:

    {"lens": "{lens}",
     "findings": [{"id": "{lens}-1", "file": "path/in/the/repository.py", "line": 12,
                   "claim": "what is wrong, in one sentence",
                   "evidence": "the input or case that shows it, and what happens",
                   "severity": "high" | "medium" | "low"}]}

Number the ids {lens}-1, {lens}-2 and so on.
