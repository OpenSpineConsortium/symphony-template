# The token wizard: research notes

Notes of the thread that built scripts/tokens.py (symphony-template, the
token wizard thread of 2026-10-16), kept here so they accumulate in the
repository, as the owner asked on 2026-10-16. No line here holds a token
or a credential; a token's shape is written in pieces where it has to be
named. docs/setup/claude-tokens.md is the page for a person who wants to
use the wizard; this file is why it is built the way it is.

## The ask

The owner's handoff message of 2026-10-15 23:35 UTC, item 11: make the
Claude token authentication of Symphony seamless; set up all of the
owner's Claude accounts' long-lived tokens as saved secrets; "a wizard or
something". The standing rule binds hardest here: no API key and no
Claude credential anywhere, so a session never handles a token, and the
wizard runs on the owner's own computer.

## How Claude tokens were taken before (read 2026-10-16)

- One token per account: `claude setup-token`, a browser sign-in in an
  interactive terminal UI, prints a long-lived (about one year)
  subscription token and saves it nowhere (docs/setup/claude-action.md;
  the Claude Code documentation on authentication).
- CLAUDE_CODE_OAUTH_TOKEN, a repository secret, is read by
  .github/workflows/claude.yml, workers.yml and coordinator.yml; every
  Claude run in Actions draws on that one account's plan
  (docs/agents/WORKERS.md, What it costs). It was stored by
  `/install-github-app` (one OAuth flow) or by `bash
  scripts/setup-repo.sh --token`, which runs `gh secret set` at gh's
  hidden prompt after the person ran `claude setup-token` in another
  terminal and copied the token through the clipboard.
- The pool: OpenSpineConsortium/coordbench's .github/workflows/bench.yml
  takes, for a real run, one organization secret SYMPHONY_CLAUDE_<slot>
  per account, slots 1 to 8, named one by one in a chain of fixed names
  (a secret looked up by a computed name would hand the runner every
  secret, which CodeQL flags), runs one job per account at a time in the
  concurrency group of its slot, and reads the slots in use from the
  variable SYMPHONY_CLAUDE_ACCOUNTS, numbers between commas or blanks
  (bench/cooperbench/actions/plan.py, chosen_accounts). The owner's
  to-do list of 2026-10-15b, item 3, had the owner make each of those
  secrets by hand on the organization's secrets page with "Selected
  repositories" and coordbench ticked.
- The cloud route is retired: COORDBENCH_CLAUDE_TOKEN in a claude.ai
  cloud environment served one cloud session's bench agents; the
  handoff of 2026-10-15b says not to add it to a new account, and the
  coordination experiment now runs its agents as subagents with no token
  anywhere.
- The terms question is the owner's and settled: the owner decided on
  2026-10-13 to run their own several accounts as one pool, knowing the
  terms-of-service question, and that does not change the rule for
  contributors' credentials (CLAUDE.md, Durable decisions). A crowd
  repository holds no Claude token at all (docs/setup/crowdsourcing.md).

## What `claude setup-token` does (Claude Code 2.1.301, read 2026-10-16)

- Its help text has one option, --help: no quiet or raw output, so
  nothing documented prints the token alone, and `claude setup-token |
  gh secret set NAME` would feed gh the whole screen.
- The binary's strings give the screens: "This will guide you through
  long-lived (1-year) auth token setup for your Claude account.",
  "Browser didn't open? Use the url below to sign in", "Paste code here
  if prompted >", "Long-lived authentication token created
  successfully!", "Your OAuth token (valid for", the token on a line of
  its own, "Store this token securely. You won't be able to see it
  again." and "Use this token by setting: export
  CLAUDE_CODE_OAUTH_TOKEN=<token>", so the token appears twice. The
  token's head is sk-, ant-, oat, two digits and a dash, then letters,
  digits, underscores and dashes.
- Run behind a pseudo-terminal in the session's container, with nobody
  signing in and the process stopped after eight seconds, so that no
  token existed: the UI renders (the Claude Code banner, the guide
  line, the sign-in link as an OSC 8 hyperlink with the plain URL beside
  it, "Hold Shift while selecting to use your terminal's native copy",
  "Paste code here if prompted >"). Claude Code 2.1's renderer places
  each word by its column (CSI n G before every word) and ends a line
  with two carriage returns and a newline; a token is one word, so it
  comes whole between a column code and a line end. The sign-in link
  carried code=true with platform.claude.com's code callback, the flow
  where the page shows a code to paste. The renderer also turns on
  bracketed paste, focus events and keyboard-protocol queries, which the
  person's terminal answers on standard input: the wizard forwards the
  keyboard raw for that reason. On Linux claude opens the link with
  xdg-open and prints it when that fails.

## What gh does (gh 2.89.0's help text, read 2026-10-16)

- `gh secret set NAME` with no --body reads the value from standard
  input when none is a terminal (the help: "reads from standard input
  if not specified"), encrypts it locally and sends the sealed value; so
  the value need never be on a command line.
- An organization secret's visibility defaults to "private": a write
  with no --visibility would quietly set that on an existing secret, and
  --repos replaces the list rather than adding to it; so the wizard
  always sends the visibility, keeping an existing secret's own, and
  sends the union of the existing list and the one named. The lists
  come from orgs/{org}/actions/secrets/{name}/repositories and
  .../variables/{name}/repositories.
- `gh secret list --json` gives name, numSelectedRepos,
  selectedReposURL, updatedAt and visibility; `gh variable list --json`
  those plus createdAt and value; GitHub never gives a secret's value
  back, so the check after a store is by name and by GitHub's own date,
  before and after.
- Organization secrets need gh's token to carry admin:org, which `gh auth
  login` does not grant by default; `gh auth status` lists an OAuth
  token's scopes quoted, and the wizard looks there before any sign-in
  is spent.
- `gh auth status` could not be read in the session's container (its
  token is the proxy's), so the scopes line's form is from gh's source
  and the fixture in tests/test_tokens.py, not from a live run.

## Design: why a pseudo-terminal, and why these names

- The seamless route is the one with no clipboard: run `claude
  setup-token` for the person, take the token out of its output, hand it
  to gh. The output is an interactive UI that needs a terminal, so the
  wizard forks it behind a pseudo-terminal of its own (Python's pty and
  termios, standard library), sets the child's window to 400 columns so
  the token is never wrapped, forwards the keyboard raw, and runs every
  chunk of output through a masker before it reaches the screen. The
  masker keeps a tail that may be a token's start until the rest comes
  and keeps the last characters shown for matching, so a token cut at any
  byte, one character at a time included, is still caught whole; the
  tests cut a frame at every size from 1 to 47 and a few larger.
  util-linux's script(1) was considered and dropped: it copies the
  session to the terminal itself, so the token would show, and macOS's
  differs in syntax.
- gh's hidden prompt stays as the fallback (--paste), for a Windows
  shell, which has no pseudo-terminal, and for a machine with gh but no
  claude; a pasted export line is accepted and an API key refused.
- The names are the consumers' names, unchanged: CLAUDE_CODE_OAUTH_TOKEN
  and SYMPHONY_CLAUDE_1 to 8 with SYMPHONY_CLAUDE_ACCOUNTS. One new
  convention, optional: SYMPHONY_CLAUDE_<slot>_LABEL, a variable holding
  a word of the owner's own, since GitHub shows nothing of a secret but
  its name and date and the owner has several accounts to tell apart at
  renewal time; a variable is readable by anyone who reads the
  repository's workflows, so the page says never an e-mail address.
- Organization secrets, not GitHub "environment" secrets: bench.yml's
  run-real jobs do not run inside its environment bench (only the
  approve job waits there), so an environment secret would reach none of
  them; the owner's "environment secrets" of the ask are read as the
  Actions secrets the workflows name.
- The variable SYMPHONY_CLAUDE_ACCOUNTS is kept equal to the slots whose
  secret exists, since a slot named there with no secret makes
  plan.py refuse a real run, and a secret not named there is idle.
- Crowd mode is refused the way scripts/setup-repo.sh refuses it: the
  clone's mode line in docs/project.md, then each named repository's
  variable CLAUDE_CROWD, read before any write; a read that fails for a
  reason other than 404 stops the wizard rather than guessing.

## Checks

- tests/test_tokens.py: the masker at every chunk size, in Ink's form and
  in the 2.1 renderer's placed-words form; the mint with a fake claude
  behind the real pseudo-terminal (the fake reports it saw a terminal of
  400 columns and the code typed); the store through the fake gh, in the
  process and as a command, with the token on gh's standard input and on
  no command line; the paste path; the API-key refusal; the crowd
  refusals; status, remove, the place options before and after the
  command, the origin's reading, the scope check, and that neither the
  script nor the test file holds a secret's shape.
- `bash scripts/check.sh` passes, the filled copies included: a crowd
  copy runs these tests with its own mode line saying on, so the tests
  read a project file of their own.

## Open items

- tools/crowd_check.py's SECRET_NAMES does not name SYMPHONY_CLAUDE_1 to
  8, so an organization pool secret that reaches a crowd repository would
  pass the crowd check; the wizard refuses to put one there, the by-hand
  path does not. A pull request of its own, with ci.yml's values job
  naming the eight.
- Nothing warns a year later: `status` says "renew soon" and "renew now",
  and only when run. A scheduled workflow could list the secrets' dates
  on GITHUB_TOKEN and open an issue; not built.
- Revoking a token from the account's side was not verified against a
  page of claude.ai; the page says only that a revoked token's secret
  stays listed until replaced.
- The real sign-in through the wizard has not been run end to end, since
  no session may hold a credential: the owner's first run is the test,
  and a token claude prints in a form the masker does not know would
  reach the screen as claude prints it, which the page says.
