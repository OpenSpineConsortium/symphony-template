---
name: bootstrap
description: Use at the start of a thread of a claude.ai Project that links this repository, when the Project's instructions do not yet contain "Read CLAUDE.md first", to have the Project set up from the repository's files with one tap and no typing.
---

# Set the Project up from the repository

Linking this repository to a claude.ai Project is all a person does. claude.ai copies nothing from a linked repository by itself; what usually follows is that the Project's own Claude starts a first thread, and that thread, reading CLAUDE.md, finds this skill. The Project's own Claude never reads the repository: it knows the Project only from the Project's instructions, its chat and its memory, so without the instructions it cannot tell what "take the next issue from the board" means. The files decide what the Project gets; this thread composes it; the Project's own Claude offers it as one card in the project chat and applies it on the person's tap, because a Project's settings change only with the person's word. A claude.ai project has, of its own, a description, instructions, a memory of path-named entries, files and threads (cswap's export lists the same parts); the table says where each comes from here.

| The Project's own field | Comes from | How it lands |
| --- | --- | --- |
| Instructions | the pointer text in docs/setup/claude-project.md, followed by a "Goal:" line with the Goal paragraph of docs/project.md (no tool writes a Project's description, so the goal rides inside the instructions) | the card, on the tap |
| Memory | docs/memory/, one entry per file under the same path (`docs/memory/<file>`); it takes only when memory is on in the account's claude.ai settings | the card, on the tap |
| The worker routine | docs/agents/routines/worker.md, hourly, named `Worker: {{REPO}}`, each run a fresh thread of this Project; left out when docs/project.md says "Worker routine: none" | the card, on the tap |
| Files, the board, the rules, the skills | the repository | read inside every thread; nothing to place |

## When

At the start of a thread of a claude.ai Project, before the work the thread was started for, when the Project's instructions (shown to you at the start of the session) do not contain the sentence "Read CLAUDE.md first". A session in a terminal has no Project: do nothing. A Project whose instructions carry the sentence is set up: do nothing, and when asked say so in one line.

## Steps

1. Read the sources: the pointer text block in docs/setup/claude-project.md; the paragraph under "## Goal" in docs/project.md (when it still reads "Not yet written", use README.md's first paragraph); the prompt block in docs/agents/routines/worker.md; the files under docs/memory/; the "Worker routine:" line in docs/project.md.
2. Compose the request and send it to the Project's own Claude: get the Project's channel session (`get_channel_session_id`) and send it, with `send_message`, one message that says: the repository {{REPO}} was linked to this Project; its setup page, docs/setup/claude-project.md, asks that the Project be set up from its files; please offer the person one setup card in the project chat and apply it on their tap, with (a) the Project's instructions set to the text that follows, exactly; (b) the worker routine, hourly, named `Worker: {{REPO}}`, each run a fresh thread of this Project, with the prompt that follows; (c) when memory is on in the account's settings, one memory entry per file under docs/memory/ at the path `docs/memory/<file>`, with the contents that follow. Then the texts, each under its own heading, as they stand in the files. Do not make the routine yourself from the thread; a routine made that way may not belong to the Project, and the card's does.
3. When there is no channel session, say in your reply what the instructions should be and how the routine is made by hand (docs/agents/routines/worker.md), as the one thing a person then has to do.
4. Say in the thread, in plain words, that the setup card is on its way in the project chat and that one tap on Apply sets the instructions, the memory (when memory is on in the account's settings) and the worker routine, which then runs every hour and is paused or deleted on the Project's Routines tab; and that the next step is an issue with the Task form. Then carry on with what the thread was started for.

Never ask twice in one Project; never make the coordinator routine from here (docs/agents/routines/coordinator.md is made by hand when a second account joins); never place anything the table above does not name.
