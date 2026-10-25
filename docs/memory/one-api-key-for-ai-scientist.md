One Claude Console API key is allowed, for AI Scientist alone (the owner, 2026-10-25); Claude Code's own Console sign-in makes it, nobody pastes it, and it is used only when a setting puts it ahead of the subscription.

The owner chose on 2026-10-25, on a decision card in the thread "Explore
textbook RAG in control panel" (later "Plan AI Scientist Pro
integration"), to allow one Claude Console API key for Sakana's AI
Scientist alone, the owner's own build called AI Scientist Pro. It is
paid only from the owner's monthly Console credits, with no dollar cap
(decision 5 of the plan below).

The subscription comes first (flat-rate-subscription-first.md): AI
Scientist Pro runs on the owner's subscription by default and uses the
key only when an order setting puts it first. No key is pasted (the
owner, 13:18 UTC): `claude auth login --console`, Claude Code's own
Console sign-in, creates the key in the owner's Console and keeps it in
that sign-in's folder, and the owner's extension completes the sign-in
with one click. The folder lives on the grid, or is kept as an
encrypted secret for jobs on GitHub's runners.

Every other no-key rule stays: Claude Code sessions, the research loop
and `@claude` run on the subscription; scripts/tokens.py stores
subscription tokens only; tools/metrics.py's judge and
tools/crowd_check.py refuse ANTHROPIC_API_KEY; tools/check_docs.py fails
on a key's shape. "Usage credits are never used", in SchwingNet's
CLAUDE.md and docs/project.md, means a subscription's extra usage,
overage billed at API rates, not these Console credits.

Claude Code prefers ANTHROPIC_API_KEY over any sign-in and then loads no
claude.ai connectors, so nothing sets that variable: AI Scientist Pro's
launcher points Claude Code at the Console sign-in's folder instead.

The plan, the rule's new wording and the owner's six decisions are
docs/research/ai-scientist-pro-plan.md.
