# Handoff of 2026-10-25 at 14:25 UTC, AI Scientist Pro plan thread

Source: the thread "Plan AI Scientist Pro integration" (first named "Explore textbook RAG in control panel"), written because the owner asked every thread at 14:23 UTC to checkpoint, push everything, write a handoff for another account and stop. A session on another account that resumes this work reads this page first, then the research note it names. No secret, token or e-mail is written here.

## Where this thread stands

- The plan is the Claude Doc "AI Scientist integration plan", https://claude.ai/artifact/AzcxFaDBdXVDkKDSZWjBv5, on the owner's account. It holds the roadmap drawing and the owner's answers. Its record in this repository is docs/research/ai-scientist-pro-plan.md, which says the same, and a session that cannot open the doc works from the note alone.
- Merged on 2026-10-25: #469 (the textbook's search graph, embeddings and AI Scientist's routes, docs/research/textbook-search-graph-in-the-panel.md, with the owner's one-key decision), #471 (the plan) and #473 (the owner's six decisions, no key pasted, the work in GitHub Actions). The site's pull request #144 in OpenSpineConsortium/openspineconsortium.github.io, the Explore graph of the textbook in the control panel, was this thread's earlier work.
- The memories every session loads: docs/memory/one-api-key-for-ai-scientist.md, docs/memory/flat-rate-subscription-first.md and docs/memory/polished-papers-over-a-hidden-raw-layer.md.
- This page's own pull request also carries the Elsevier secret names into the note and into flat-rate-subscription-first.md, and into the Claude Doc (already edited, revision 46). It merges once its check is green. No other pull request of this thread is open, and the branch claude/project-thread-necwvx holds nothing else.
- Nothing of this thread runs on the grid, and no grid job, fetch or training was started.

## The owner's decisions of 2026-10-25

The note's last section has them word for word. In short:

1. The base is Sakana's v3, The Agentic Scientist (SakanaAI/AI-Scientist-v3), run through Claude Code. If it cannot run that way, its stages become Claude Code agents, never v2's direct model calls.
2. Every literature service and web search is open from the start, with no word list (the owner's card at 13:16 UTC).
3. No key is ever pasted. Claude's credentials come from one-click sign-ins that the owner's own extension completes (Claude Code's sign-in code is picked up from Anthropic's return page), on Anthropic's written permission for the owner's apps to handle the claude.ai sign-in. Only the Elsevier key and token, which no sign-in can make, are GitHub secrets.
4. The subscription comes first. The one Console key allowed for AI Scientist Pro is made by `claude auth login --console` and used only when a setting puts it first. Nothing sets ANTHROPIC_API_KEY.
5. No dollar cap.
6. The textbook is embedded by an open model on the grid.

At 13:28 UTC, in another thread, the owner asked that the research loop run entirely in GitHub Actions. The plan puts long jobs on the grid's self-hosted runner while the budget for extra Actions minutes is $0, and keeps every job that touches the corpora on the grid. At 14:17 UTC the owner named the Elsevier secrets ELSEVIER_API_KEY and ELSEVIER_INSTTOKEN. Code maps them to Elsevier's headers X-ELS-APIKey and X-ELS-Insttoken, since a secret's name cannot hold a hyphen.

## Open work

1. AI Scientist Pro, phase 0. It waits for the owner's word to start. Record: docs/research/ai-scientist-pro-plan.md, section "The plan". Next steps, once the owner says go:
   1. Read v3's code and pin one commit. Map each stage to the claim protocol and the size rule. Find how it calls Claude Code, what it sandboxes and where it searches the literature.
   2. Write the plan into a SchwingNet issue: credentials, containment, confidentiality and the measure. The owner approves it there, and that is phase 0's gate.
   3. Phase 1 then follows the note: the one-click sign-in for the grid; the jobs on the grid's runner; the Elsevier server tools/elsevier_mcp.py and the setup step grid/literature-setup.sh in SchwingNet, tested on faked answers; and the order setting that puts the subscription first. Every grid job and every spend waits for the owner's word and the count.

2. The key rule's new wording. Record: the note's section "Relaxing the rule against API keys", whose blockquote is the wording. Next steps:
   1. The owner replaces the Project's instruction (below).
   2. Then one pull request in each repository adds docs/setup/keys.md, which lists each allowed key with its purpose, its owner and where it lives. In the same pull request, SchwingNet's docs/project.md says that "usage credits" means a subscription's extra usage.
   3. At the next checkpoint that rewrites the block at the end of CLAUDE.md, add the line "Flat-rate subscriptions come first; no key is ever pasted (the owner, 2026-10-25): every feature runs on subscription accounts alone, an allowed key is used only when a setting puts it first, a credential a service makes at sign-in comes from a one-click sign-in the owner's own app completes, and only a value no sign-in can make, such as ELSEVIER_API_KEY and ELSEVIER_INSTTOKEN, is an encrypted GitHub secret." This thread did not touch that block, because several threads were checkpointing at once.

3. The Elsevier secrets. Record: the note's setup step, items 3 and 4, and decision 3. The names are known. Where they are saved is not: no session can list secrets, since the proxy refuses that API. The plan recommends organization secrets shared with SchwingNet and symphony-template. With one copy of each, the key route can reach them, since .github/workflows/grid-accounts.yml runs in symphony-template's environment grid and a job reads its organization's secrets too. SchwingNet's jobs on GitHub's runners can reach the same copy. Next steps for phase 1:
   1. Ask the owner where the two secrets are saved, unless they are already saved as organization secrets, as recommended below.
   2. Teach the action key of grid-accounts.yml the name elsevier for both secrets, as physionet takes two. Teach hpcworker's gate word key the file they are written to. Then add a row to the "Service keys" table of docs/setup/grid.md.
   3. Phase 1 tests whether the grid needs the institutional token at all, since Elsevier may recognise Wayne State's network. GitHub's runners need it.

## Waiting on the owner

1. Turn on secret scanning's extra checks in SchwingNet. Open https://github.com/OpenSpineConsortium/SchwingNet/settings/security_analysis and, under Secret Protection, click Enable next to Generic patterns, then next to Scan for AI-detected secrets, then next to Validity checks.
2. Do the same at https://github.com/OpenSpineConsortium/symphony-template/settings/security_analysis.
3. In the claude.ai Project's settings, under Instructions, replace "No API key or Claude credential anywhere." with the blockquote in docs/research/ai-scientist-pro-plan.md, section "Relaxing the rule against API keys".
4. Skip this step if the Elsevier key and token are already saved. Otherwise open https://github.com/organizations/OpenSpineConsortium/settings/secrets/actions/new and type ELSEVIER_API_KEY as the Name. Put the key in Value. Under Repository access, choose Selected repositories and pick SchwingNet and symphony-template, then click Add secret. Do the same for ELSEVIER_INSTTOKEN with the institutional token. If they are saved somewhere else, say where.
5. Say go for phase 0 when you want it started.

## Resume

1. Open a session on this repository with the next account: a Project of its own on claude.ai, or a cloud session.
2. Read this page and docs/research/ai-scientist-pro-plan.md, then fetch and read the board.
3. Take the open work above in its order. Nothing of it is claimed, and phase 0 starts only on the owner's word.
