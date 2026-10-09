// The research run behind docs/history/experiment-research/README.md, as
// it was launched with Claude Code's Workflow tool on 2026-10-09. Kept so
// the unfinished verification can be finished; see the README's Resuming.

export const meta = {
  name: 'experiment-research',
  description: 'Verify CooperBench and the GitHub/Claude mechanics a PR-gated vs shared-workspace agent experiment needs',
  phases: [
    { title: 'Research', detail: 'four researchers, primary sources' },
    { title: 'Verify', detail: 'three skeptics on each load-bearing claim' },
    { title: 'Critic', detail: 'what is still missing for the experiment' },
  ],
}

const CLAIMS = {
  type: 'object',
  properties: {
    claims: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          claim: { type: 'string' },
          source_url: { type: 'string' },
          quote: { type: 'string' },
          load_bearing: { type: 'boolean' },
        },
        required: ['claim', 'source_url', 'quote', 'load_bearing'],
      },
    },
    notes: { type: 'string' },
  },
  required: ['claims', 'notes'],
}

const VERDICT = {
  type: 'object',
  properties: { refuted: { type: 'boolean' }, correction: { type: 'string' } },
  required: ['refuted', 'correction'],
}

const RULES = `Use primary sources only (the paper itself on arXiv or the venue, the benchmark's own repository or site, official GitHub docs, official Anthropic docs, the anthropics/claude-code-action repository). Open every page you cite and quote it exactly; a search snippet is not a source. Mark a claim load_bearing when an experiment design would change if it were false. Today is 2026-10-09.`

const TOPICS = [
  {
    key: 'cooperbench',
    prompt: `${RULES}\n\nThe user cites "Cooper bench" results as showing that too much collaboration between coding agents hurts progress. Find this benchmark (likely CooperBench or similar; check spelling variants) and establish exactly: full title, authors, date, arXiv id or venue, and repository; the task design (what a task is, how many, which languages/repos, how features are split between agents, whether agents share one workspace or have separate ones, how and when work is merged, the communication channel between agents and its limits); the conditions compared (solo agent doing all features vs agents cooperating, any other arms); the metrics (success rate definition, how merge conflicts count, cost/tokens if measured); the headline numbers per condition and per model; the failure modes the authors identify (e.g. communication failures, broken commitments, conflicting edits); and the authors' own stated conclusion and limitations. If you find no such benchmark, say so plainly and report the nearest real work instead.`,
  },
  {
    key: 'related-evidence',
    prompt: `${RULES}\n\nFind other published evidence (2024-2026) on whether multi-agent coordination helps or hurts LLM coding agents' productivity: e.g. parallel agents on separate git worktrees or branches vs shared workspaces, multi-agent SWE frameworks compared with single agents on SWE-bench-style tasks, studies of communication overhead between agents, and any Anthropic engineering writing on running multiple Claude Code agents in parallel (worktrees, subagents, agent teams). For each: what was compared, the measured effect with numbers, and the setting. Also note the classic human-software-engineering evidence the user's thesis echoes (Brooks's law; studies of pull-request-based development and merge conflicts) only where a primary or well-established source states it.`,
  },
  {
    key: 'actions-mechanics',
    prompt: `${RULES}\n\nEstablish the GitHub mechanics an autonomous multi-agent experiment in one repository depends on, from docs.github.com: (1) can a workflow run started by GITHUB_TOKEN dispatch another run of a workflow via workflow_dispatch or repository_dispatch (the documented exception to the no-recursion rule), and any limits; (2) how a job matrix can be built from a repository variable with fromJSON(vars.X), and per-leg concurrency groups; (3) auto-merge: the repository setting "Allow auto-merge", which plans/visibilities have it, that it needs branch protection or a ruleset with required checks, and enabling it per pull request via gh pr merge --auto; (4) whether a merge or push made by GITHUB_TOKEN versus by a GitHub App installation token triggers further workflows; (5) the REST endpoints and permissions to list a pull request's timeline events (including head_ref_force_pushed), its check runs, and to list and download workflow run artifacts as zip; (6) setting repository variables and secrets through the REST API and the permission each needs; (7) the concurrency limits on jobs for GitHub Free and Team.`,
  },
  {
    key: 'claude-mechanics',
    prompt: `${RULES}\n\nEstablish the Claude-side mechanics, from code.claude.com docs, support.claude.com, and the anthropics/claude-code-action repository (README, action.yml, docs/): (1) the outputs of claude-code-action, especially execution_file, and the exact shape of what it contains (does it carry token usage, num_turns, total_cost_usd, duration); (2) automation mode with the prompt input versus @claude mention mode, and which token the action uses for git pushes and pull request creation (GitHub App installation token or GITHUB_TOKEN) and how to make it use one or the other; (3) how many Claude Code sessions can run concurrently on one Pro or Max subscription token, and how rate limiting behaves when several Actions jobs share one CLAUDE_CODE_OAUTH_TOKEN (five-hour window, weekly limit, 429 behaviour); (4) --max-turns, --model and other claude_args relevant to holding conditions equal across experiment arms; (5) whether Claude Code supports agent teams or shared-context multi-agent features natively (e.g. an agent teams feature, subagents) that a 'shared project' arm could use as its native form.`,
  },
]

phase('Research')
const found = await parallel(TOPICS.map(t => () =>
  agent(t.prompt, { label: `research:${t.key}`, phase: 'Research', schema: CLAIMS })
))

const loadBearing = []
found.forEach((r, i) => {
  if (!r) return
  r.claims.filter(c => c.load_bearing).forEach(c => loadBearing.push({ ...c, topic: TOPICS.at(i).key }))
})
log(`${loadBearing.length} load-bearing claims to verify`)

phase('Verify')
const verified = await parallel(loadBearing.map(c => () =>
  parallel([1, 2, 3].map(n => () => agent(
    `${RULES}\n\nSkeptic ${n} of 3. Open the source and try to REFUTE this claim; if it is partly wrong, refute it and give the correct statement in correction.\nTopic: ${c.topic}\nClaim: ${c.claim}\nSource: ${c.source_url}\nQuoted: ${c.quote}\n\nDefault to refuted=true if the source does not say it.`,
    { label: `verify:${c.topic}`, phase: 'Verify', schema: VERDICT }
  ))).then(votes => {
    const live = votes.filter(Boolean)
    const refutes = live.filter(v => v.refuted)
    return { ...c, confirmed: live.length > 0 && refutes.length < 2, corrections: refutes.map(v => v.correction) }
  })
))

phase('Critic')
const critic = await agent(
  `${RULES}\n\nYou review research gathered to build a GitHub template that runs an experiment: the same task suite done by Claude Code agents under (a) a PR-gated workflow (one issue, one branch, one pull request each, CI-gated merges) and (b) a shared high-collaboration workspace, and probably (c) a single solo agent, to test whether coordination overhead lowers productivity, as the user believes CooperBench showed. Here are the verified claims:\n${JSON.stringify(verified.filter(Boolean).map(v => ({ topic: v.topic, claim: v.claim, confirmed: v.confirmed, corrections: v.corrections })), null, 1)}\n\nAnd the researchers' notes:\n${found.filter(Boolean).map(r => r.notes).join('\n---\n')}\n\nList what is still missing or unverified that the experiment's design or the template's automation depends on, and any fact above that undermines the user's framing (for example, if CooperBench measured something different from what the user believes). Be specific and short.`,
  { label: 'critic', phase: 'Critic' }
)

return {
  verified: verified.filter(Boolean),
  notes: found.filter(Boolean).map((r, i) => ({ topic: TOPICS.at(i).key, notes: r.notes })),
  critic,
}