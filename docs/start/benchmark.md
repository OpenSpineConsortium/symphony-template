# Benchmark coordination with coordbench

[OpenSpineConsortium/coordbench](https://github.com/OpenSpineConsortium/coordbench) keeps the task, the agents and the scoring fixed and swaps the way agents coordinate (an arm: solo, coop, coop-nocomm, coop-git, team, sdlc, sdlc-watch), so two ways can be compared on the same work: CooperBench's task pairs, scored by CooperBench's own evaluation. The agents are headless Claude Code on your own subscription, started in Docker inside one cloud session, which itself only drives shell scripts. You need Claude Pro or Max and nothing on GitHub; the repository is public.

## Steps

1. **Make a subscription token, on your own computer,** signed in to the account whose usage the runs should spend. It prints a token good for about a year and saves it nowhere. Bash or PowerShell:

   ```
   claude setup-token
   ```

2. **Put it in a cloud environment of your own.** At https://claude.ai/code, select the cloud icon in the row above the message box, then Cloud, Add cloud environment:

   | Field | Value | Why |
   | --- | --- | --- |
   | Name | `coordbench` | the link in step 3 chooses it by name |
   | Network access | Trusted | 42 of the 50 flash pairs grade with it |
   | Environment variables | the line below | the agents the session starts need the token itself |
   | Setup script | empty | bench/cooperbench/setup.sh does the setup inside the session |

   ```
   COORDBENCH_CLAUDE_TOKEN=<paste the token from claude setup-token here>
   ```

   Press "Create environment". Put it under Environment variables, not Network secrets: a network secret is never attached to requests for api.anthropic.com, which is where the agents send it. Not as CLAUDE_CODE_OAUTH_TOKEN either: the environment withholds that name from the session, since it runs the session's own Claude Code, and run.py copies the alias to it for the agents. Leave ANTHROPIC_API_KEY unset: CooperBench's adapter prefers it, and it bills the API. Keep the environment personal, never shared: anyone who uses an environment reads its variables. The seven pairs of three tasks that do not grade need openaipublic.blob.core.windows.net, huggingface.co and pypi.nvidia.com (Custom network access, with the default package managers kept), and then their downloads baked into the task images (coordbench's bench/cooperbench/README.md).

3. **Start a new session on coordbench in that environment,** since a session reads the variables when it starts: https://claude.ai/code?repositories=OpenSpineConsortium/coordbench&environment=coordbench (or your fork, step 7). Paste the smoke-test prompt from [prompts.md](prompts.md), or run steps 4 and 5 yourself.

4. **Set up and prepare one task,** in the session:

   ```bash
   bash bench/cooperbench/setup.sh
   bash bench/cooperbench/prepare_task.sh pallets_click_task 2068
   ```

   setup.sh starts Docker, clones CooperBench at its pinned commit with the one patch, and starts Redis and the git server; you should see `ready: CooperBench at 63b9d44 in /root/cooperbench`. prepare_task.sh pulls the task's image from mirror.gcr.io, since Docker Hub rate-limits the cloud host, and checks that its features grade.

5. **The smoke run: one pair, one arm, one agent.**

   ```bash
   env -u ANTHROPIC_API_KEY python3 coordbench/run.py run --arm solo --repo pallets_click_task --task 2068 --features 1,6 --driver claude-cli --name smoke-solo
   python3 bench/cooperbench/report.py --run solo=smoke-solo
   ```

   You should see a last line beginning `timings:` and then the report, with the pair under ~/cooperbench/logs/smoke-solo/solo/pallets_click_task/2068/f1_f6/ (result.json, eval.json, the agent's trajectory). For the protocol itself, the same pair under the sdlc arm: `--arm sdlc --name smoke-sdlc`, two agents.

6. **The pilot: six arms on one task.** solo, coop, coop-nocomm, coop-git, team and sdlc over the task's flash pairs, then the report and the free heuristics judge:

   ```bash
   bash bench/cooperbench/pilot.sh pallets_click_task 2068 pilot
   ```

   The report lands at ~/cooperbench/logs/pilot-report.md. A session's background command stops after two hours, and the pilot can take longer; run the same command again and it carries on, since finished pairs are kept. When you are done with a task, free the disk for the next: `docker rmi akhatua/cooperbench-pallets-click:task2068`.

7. **Read the results.** None of these calls a model:

   ```bash
   python3 bench/cooperbench/report.py --run solo=pilot-solo --run coop=pilot-coop --run sdlc=pilot-sdlc
   python3 coordbench/compare.py ~/cooperbench/logs/smoke-solo/solo/pallets_click_task/2068/f1_f6 -o smoke.html
   python3 coordbench/judge.py heuristics ~/cooperbench/logs/pilot-sdlc
   ```

   report.py sets the arms side by side with CooperBench's own rates and intervals. compare.py writes one HTML page with the runs embedded, which opens from disk with no server and no network; to look at it, the page has to leave the VM: have the session commit it to a branch of its own (never main) and push, then download it from the file's page on GitHub and open it in a browser. That push needs Write on the repository the session runs on, so without Write on coordbench run the session on your own fork (https://github.com/OpenSpineConsortium/coordbench/fork). `python3 coordbench/export.py <pair dir> --site OUT` lays runs out for CooperBench's own viewer instead (coordbench/viewer/README.md). judge.py's other sections (commerrors, symptoms, speechacts, emergent) do call a model, on your subscription through the same token; run them only on purpose, with `--dry-run` first to see what would be sent.

## What it costs

On a subscription these are usage drawn from your plan's limits, not a bill; the dollar figures are API prices, for planning, from coordbench's bench/cooperbench/README.md, which takes the CooperBench authors' own Claude Code run: about $0.43 per agent session, with Sonnet 4.5.

| Run | Agent sessions | At API prices | Time |
| --- | --- | --- | --- |
| setup.sh, prepare_task.sh, report.py, compare.py, judge.py heuristics | 0 | nothing | minutes |
| Smoke run, solo, one pair | 1 | about $0.43 | 5 to 20 minutes |
| Smoke run, sdlc or coop, one pair | 2 | about $0.86 | 5 to 20 minutes |
| pilot.sh on pallets_click 2068 (6 pairs, six arms) | 66 | about $28 | hours |
| Four arms over the 42 flash pairs that grade | 294 | about $125 | several usage windows |

The owner's first two six-arm pilots, on pallets_click 2068 and pallets_jinja 1559 on 2026-10-10, came to about $8 at API prices together, well under that planning figure. A pair whose agents stop at a usage limit is marked Error, and running the same command after the reset runs it again. The session itself spends almost nothing: it only drives the scripts. The session has about 4 CPUs, 16 GB of memory and 30 GB of disk, which holds about one large task image at a time, so the steps go one task at a time.
