One Claude Console API key is allowed, for AI Scientist alone (the owner, 2026-10-25); every other no-key rule stands.

The owner chose on 2026-10-25, on a decision card in the thread "Explore
textbook RAG in control panel" (later "Plan AI Scientist Pro
integration"), to allow one Claude Console API key for Sakana's AI
Scientist alone, the owner's own build called AI Scientist Pro. It is
paid only from the owner's monthly Console credits, kept in a private
file where AI Scientist runs, and never in git, CI or logs. How it
reaches that file is decision 3 of the plan below.

Every other no-key rule stays: Claude Code sessions, the research loop
and `@claude` run on the subscription; scripts/tokens.py stores
subscription tokens only; tools/metrics.py's judge and
tools/crowd_check.py refuse ANTHROPIC_API_KEY; tools/check_docs.py fails
on a key's shape. "Usage credits are never used", in SchwingNet's
CLAUDE.md and docs/project.md, means a subscription's extra usage,
overage billed at API rates, not these Console credits.

Claude Code prefers ANTHROPIC_API_KEY over a subscription login and then
loads no claude.ai connectors, so the key is set only inside AI
Scientist Pro's own process, never in a shell profile.

The plan, a proposed rewording of the rule and six decisions waiting
for the owner are docs/research/ai-scientist-pro-plan.md.
