---
name: bootstrap
description: Use at the start of a thread of a claude.ai Project that links this repository, when the Project's instructions do not yet contain "Read CLAUDE.md first", to place the Project's instructions, description and memory from the repository's files, without the person typing anything.
---

# Set the Project up from the repository

Linking this repository to a claude.ai Project is all a person does. claude.ai copies nothing from a linked repository by itself; what it does is start a thread, and that thread, reading CLAUDE.md, finds this skill. So the files decide what the Project gets, and this thread places them. A claude.ai project has, of its own, a description, instructions, a memory of path-named entries, files and threads (cswap's export lists the same parts); the repository carries the first three in known places, and the rest stays in the repository and is read inside every thread.

| The Project's own field | Comes from | Placed by |
| --- | --- | --- |
| Instructions | the pointer text in docs/setup/claude-project.md | the Project's own Claude, asked by this thread |
| Description | the Goal paragraph of docs/project.md, or README.md's first paragraph while the goal is not yet written | the same |
| Memory | docs/memory/, one entry per file under the same path (`docs/memory/<file>`), only when memory is on in the account's claude.ai settings | this thread, or the Project's own Claude |
| The worker routine | docs/agents/routines/worker.md, hourly, unless docs/project.md says "Worker routine: none" | this thread |

## When

At the start of a thread of a claude.ai Project, before the work the thread was started for, when the Project's instructions (shown to you at the start of the session) do not contain the sentence "Read CLAUDE.md first". A session in a terminal has no Project: do nothing. A Project whose instructions carry the sentence is set up: do nothing, and when asked say so in one line.

## Steps

1. Read the sources: the pointer text block in docs/setup/claude-project.md; the paragraph under "## Goal" in docs/project.md, or README.md's first paragraph when the goal still reads "Not yet written"; the files under docs/memory/.
2. The instructions and the description. Get the Project's channel session (`get_channel_session_id`) and send it, with `send_message`, one request: "The repository {{REPO}} was linked to this Project. Its setup page, docs/setup/claude-project.md, asks that the Project's instructions be set to the following text, exactly, and its description to the paragraph after it, with your project settings tool: <pointer text> <description>". When there is no channel session, say in your reply what the instructions and the description should be, as the one thing a person then has to paste.
3. The memory. When you have the project memory tools, write one entry per file under docs/memory/ at the path `docs/memory/<file>` with the file's content, and skip an entry that already exists with that content. When you do not have them, include the entries in the request of step 2. When the tool answers that memory is turned off in the account's settings, say so in your reply and go on; the shared memory in the repository is read in every thread regardless.
4. The worker routine. List the account's routines (`list_triggers`). When none is named `Worker: {{REPO}}`, and docs/project.md does not say "Worker routine: none", make it with `create_trigger`: the name `Worker: {{REPO}}`, the prompt from docs/agents/routines/worker.md as it stands, `cron_expression` `0 * * * *` (hourly, the shortest a routine allows), `create_new_session_on_fire` true, so every run is a fresh thread of this Project with the repository cloned, and `initiation` `human_request`, because the person linked the repository and README.md told them this is what linking does. When the result warns that the routine stores no connectors, repeat that warning and its remedy in your reply.
5. Say what was placed, in the thread, in plain words: the instructions and the description (asked for, or to be pasted), the memory (written, or off in the account's settings), the worker routine (made, runs every hour, paused or deleted on the Project's Routines tab), and that the next step is an issue with the Task form. Then carry on with what the thread was started for.

Never make a second worker routine; never make the coordinator routine from here (docs/agents/routines/coordinator.md is made by hand when a second account joins); never place anything the table above does not name.
