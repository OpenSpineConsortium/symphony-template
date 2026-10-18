Agents are Claude Code subagent files under .claude/agents/, registered in .github/symphony/agents.json, imported by pull request with tools/agents.py, and taken as they are by coordbench and flowbench.

- The format and the rules are docs/agents/AGENTS.md; the research and the options left to the owner are docs/research/importable-agents.md.
- The template brings reviewer, developer and tester, all runs: manual, so none spends a token until someone switches one on.
- .github/workflows/agents.yml runs an agent with `claude --agent NAME` on the default branch's copy (never a pull request's), with only the tools the agent lists, on pull requests where its runs is pull_request or by Run workflow, and imports one with its "import" input; workers.yml runs a worker under the agent whose workers list names it.
- An agent's token is its name's line in .github/symphony/accounts.json (tools/pool.py, the Tokens thread's), so an agent may not share a name with a worker.
- An imported agent lists its tools and carries no hooks, no MCP servers and no bypassPermissions, and the check holds it to the sha256 it came with; `tools/agents.py own NAME` keeps a hand edit.
- coordbench `run.py run --agent-file FILE` and a flowbench stage's "agent" run the file under the run's own model and denied tools; no run without the owner's word and number.
