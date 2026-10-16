# Research

This folder holds the project's running research programmes: for each, the question, the instrument that measures it, the measurements taken with it and what they found, kept beside each other so that a reader can go from a claim to the record it rests on and to the command that reproduces it. One folder per programme, with a README that says where the programme stands. docs/history/ is for what a piece of work found and settled; a programme lives here while its questions are open, and a settled finding goes to docs/history/ or, when every session should know it, to docs/memory/.

Three rules hold in every programme, taken from OpenSpineConsortium/coordbench, where the project measured coordination first:

- A measurement is taken by code, deterministic and tested, from records the work leaves behind; a model judges only when the owner runs it on purpose, and never on an API key.
- A run that spends tokens or money waits for the owner's word and the number: how many runs, of what, at about what cost. Nothing here starts a run by itself; a schedule, where one exists, is a fallback and never the only trigger.
- A record carries counts, bytes, seconds and tokens, with tool names and model names, and never a path, a command, a prompt, a title or any text of a conversation, so it can be committed and shared. Transcripts and logs stay where they were written.

Programmes:

- [beyond-cooperation](beyond-cooperation/README.md): what one agent spends, context, tool calls, reading and time, and how to spend less, measured with tools/profile.py.
