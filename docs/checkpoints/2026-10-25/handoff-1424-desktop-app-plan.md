# Handoff of 2026-10-25 at 14:24 UTC, thread "Plan Symphony desktop app and LLM-agnostic design"

Source: the thread "Plan Symphony desktop app and LLM-agnostic design" in the claude.ai project "symphony3", written at the owner's checkpoint of 14:23 UTC into the Project's files and copied here by the thread "Write project handoff for new account", since another account cannot read those files.

State: done. Nothing unpushed, no open pull request.

- The plan is merged as symphony-template#470. It is docs/research/desktop-app-and-llm-agnostic.md, with its line in docs/research/README.md.
- Recorded in it: the owner stated on 2026-10-25 at 11:36 UTC that an Anthropic representative gave them written permission to offer a claude.ai sign-in in their third-party apps. No session has seen that writing. The owner should keep a copy private, outside git.

Waiting on the owner before phase 1 can start:
1. Electron (recommended) or Tauri.
2. Code signing: an Apple Developer membership and a Windows code-signing certificate, both paid yearly.
3. The first local model: Ollama on the desktop (recommended) or vLLM on the grid.
4. Creating a new repository for the desktop app. Only the owner can do this; sessions cannot create repositories.

To continue from another account: open a thread on symphony-template and read the note above. Phase 1 is in the note's Phases section: an Electron shell around the site's control-panel console, the GitHub sign-in kept in the OS keychain, opening a project, and starting the local Claude Code. Phase 1 starts in the new repository once the owner has made the choices above.
