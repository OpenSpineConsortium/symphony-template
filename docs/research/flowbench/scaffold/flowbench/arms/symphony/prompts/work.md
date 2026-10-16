# Claim the issue and open the pull request

You are the worker of this run under the claim protocol (the arm's
README says how it is kept here): the issue is #1 of this repository,
your claim is the branch claude/1, and your pull request is that branch's
diff against {base_commit}, which a reviewer reads next through three
lenses and asks you to answer.

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

1. Make the claim branch from the checkout: `git switch -c claude/1 --no-track`.
2. Read the issue, then the code it names, then the tests nearby, until
   you can say in one sentence what is wrong and where; reproduce it where
   you can, through the container.
3. Fix the cause, not the symptom, in the repository's own style, with a
   test where the repository keeps tests for that code, and run the tests
   of the modules you touched through the container.
4. Commit on claude/1 with a message that says why, in the repository's
   style; several commits are fine.
5. Write the pull request's description to {flow_dir}/pull-request.md:
   what a reader sees before and after the change, then how it is done,
   in plain prose. It is what the reviewer reads first.

Leave claude/1 checked out when you stop.
