# Fix the issue

You are the one agent of this run: you read the issue, fix it and leave
the change; nobody reviews or verifies it after you.

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

1. Read the issue, then the code it names, then the tests nearby, until
   you can say in one sentence what is wrong and where.
2. Reproduce it where you can: a small script, or a test run through the
   container.
3. Fix the cause, not the symptom, in the repository's own style: the
   smallest change that makes the issue's case right and leaves every
   other case as it was.
4. Add or adjust a test where the repository keeps tests for that code,
   and run the tests of the modules you touched through the container. A
   suite the issue does not touch is not yours to run whole.
5. Leave the change in the working tree of {workspace}, committed or
   not, as you prefer: the run takes `git diff` against {base_commit} when
   you stop.
