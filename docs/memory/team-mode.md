Team mode runs a lead and parallel members on one epic, CooperBench's best-scoring arm built on GitHub.

With the repository variable CLAUDE_TEAM set to member names and
CLAUDE_WORKER to true, labelling an
issue epic starts .github/workflows/claude-lead.yml: Claude returns a plan
as JSON and tools/team.py opens one sub-issue per member, labelled todo and
agent:<name>, and starts .github/workflows/claude-worker.yml, one leg per
member. Members stay in the files their task owns, look at each other's
claim branches, merge the default branch in when it moves, and land by
auto-merge on a green check; when the last task closes, the lead integrates.
The deterministic steps (routing, seeding, choosing a member's next move)
spend no Claude usage. Inside claude-code-action, Claude gets only the
action's GitHub tools unless --allowedTools grants more, so the workflows
grant git, gh, python3 and scripts/check.sh; in tag mode (@claude) the
action's own prompt also forbids rebasing and merging, which a custom
prompt (automation mode) does not. In that automation mode the action
also refuses a run whose actor is a bot unless allowed_bots names it, and
runs dispatched by GITHUB_TOKEN act as github-actions[bot], merges the
app turned on act as claude[bot]: the team's workflows name both. A
workflow-wide concurrency group drops waiting runs (GitHub keeps one
pending run per group), so the lead's groups sit on its jobs, per epic.
The evidence for the design is the
authors' later ablation, unreviewed: team 62%, shared remote 56%, solo 48%,
messaging-only 26%. docs/agents/TEAM.md has the protocol.

Source: cooperbench/CooperBench at 63b9d44 (team_harness/prompt.py,
runner/team.py) and anthropics/claude-code-action at 2dca132
(src/create-prompt/index.ts, src/entrypoints/run.ts, docs/faq.md), read
2026-10-09.
