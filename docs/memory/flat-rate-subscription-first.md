Flat-rate subscriptions come first (the owner, 2026-10-25): every feature runs entirely on subscription accounts, an allowed Claude API key is used only when a setting puts it first, and no key is ever pasted.

The owner's words of 2026-10-25, 13:00 UTC, answering decision 4 of the
AI Scientist Pro plan: "Prioritizes Flat-Rate Subscription over API Key
(Default), with supported priority customization. Entirely supported by
Flat-Rate Subscription Accounts." At 13:18 UTC the owner added "i want
one-click oauth type secret key creation to completely avoid pasting",
recalling Anthropic's written permission for the owner's apps to handle
the claude.ai login (docs/research/desktop-app-and-llm-agnostic.md,
Decisions for the owner, 1).

- A feature that can use a key works without one, on a subscription
  sign-in, and the subscription is the default wherever both exist.
- A credential that a service can make at sign-in is made by a one-click
  sign-in that the owner's own app completes. Claude Code's sign-in
  returns by itself where the browser is on the same computer; elsewhere
  the extension picks the code up from Anthropic's return page,
  https://platform.claude.com/oauth/code/callback, and hands it to the
  machine that asked. `claude auth login --console` makes the Console key
  the same way, with Claude Code creating the key itself.
- A value no sign-in can make, such as the Elsevier key and token
  (ELSEVIER_API_KEY and ELSEVIER_INSTTOKEN, named by the owner on
  2026-10-25 and sent as Elsevier's headers X-ELS-APIKey and X-ELS-Insttoken),
  is an encrypted GitHub secret under secret scanning and push protection,
  carried to the grid by the key route
  (docs/research/service-keys-to-the-grid.md); never in git, an issue, a
  log, a URL or browser code.
- Claude Code prefers ANTHROPIC_API_KEY over any sign-in and then loads
  no claude.ai connectors, so nothing sets that variable where the
  subscription should be used.

The rule's wording for the Project's instructions and both CLAUDE.md
files, and where the old wording still stands, are in
docs/research/ai-scientist-pro-plan.md.
