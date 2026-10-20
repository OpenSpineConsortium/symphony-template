# Claude Code handoff, 2026-10-20: the session on Greg's laptop (workspace CTSpinoPelvic1K-1)

Source: the Claude Code session in VS Code on Greg's Windows laptop, written on the owner's ask of 2026-10-20 to
checkpoint it here as the claude.ai Project threads do, so its knowledge is kept where every account can read it.

The session differs from those threads in two ways:
- It is not a Project thread. It runs in the workspace `C:\Users\grego\OneDrive\Desktop\CTSpinoPelvic1K-1`, with these
  extra folders:
  - spinesurg-ct-nnunet
  - NextPaper\spinopelvic-seg
  - NextPaper\AR
  - openspineconsortium.github.io
  - OpenSpineToolkit
  - ERAS_2026
- Its memory is files, not a Project memory: 175 files under
  `C:\Users\grego\.claude\projects\c--Users-grego-OneDrive-Desktop-CTSpinoPelvic1K-1\memory\`.

Beside this file:
- `memory.md` is that folder's MEMORY.md index.
- `topic-memories/` holds every one of its fact files.

Three changes make them fit docs/ here:
- Typographic characters are spelt in ASCII.
- One file name that carried the root CLAUDE.md's banned word is renamed (`splits-origin-and-v3-resplit.md`).
- Students' GitHub usernames are replaced by `[student N]`, because a repository made from this template may have
  students on it. The laptop keeps the originals.

Everything under docs/checkpoints/ is copied into every repository made from this template. As of 2026-10-20 no
public repository was made from it. These files carry unpublished SchwingNet results and the grid's layout, so delete
docs/checkpoints/ from any copy before it goes public.

## 1. Restore the memory in another Claude Code install

Claude Code keeps a project's memory in `~/.claude/projects/<slug>/memory/`, where `<slug>` is the workspace path with
every `:`, `\` and `/` turned into `-` (on this laptop `c--Users-grego-OneDrive-Desktop-CTSpinoPelvic1K-1`).

1. Open the workspace once in the new install, so the folder exists.
2. Copy `topic-memories/*.md` into it.
3. Copy `memory.md` into it as `MEMORY.md`, then remove the `topic-memories/` prefix from its links:
   `sed -i 's#](topic-memories/#](#g' MEMORY.md`.

The project's own instructions travel with the repositories, so they need no copy. The CTSpinoPelvic1K root CLAUDE.md
is the working context, and spine-program and SchwingNet each have their own CLAUDE.md.

## 2. First message for a new session

Paste into Claude Code in the CTSpinoPelvic1K-1 workspace, after restoring the memory:

```
Pick up where the laptop session stopped on 2026-10-20. Read docs/checkpoints/2026-10-20-claude-code/handoff.md in
OpenSpineConsortium/symphony-template first, then MEMORY.md. spine-program changes go by issue, claim and pull request
only (the symphony plugin's claim skill), and I merge there; SchwingNet lands by automerge when its checks pass;
network goes through WSL; nothing runs on the grid's login node. Start nothing that spends without my word and the
number of jobs. Tell me what in part 5 still waits on me before you start anything else.
```

## 3. Workstreams, with their state

### 3.1 spine-program on the Symphony protocol

OpenSpineConsortium/spine-program is internal: Greg and one outside collaborator, a student, can read it.
- **Readiness:** the 13 numbered project folders are ready for students, with start-here issues #4 to #16 and
  follow-on tasks #17 to #42, plus the AIDaS map (13_aidas_program, #183). On 2026-10-20 there were 90 open issues
  labelled todo.
- **Claims:** the symphony plugin's claim skill; scripts for headless claims are in `_ops/headless/`.
- **Who merges:** Greg does. A session merged only on his word, through `_ops/headless/wsl_merge_pr.sh`.
- **Traps:**
  - `wsl_merge_pr.sh` splits its allowed list on spaces, so a path with a space never matches.
  - `gh pr edit` fails on this token (scopes repo and workflow, no read:org); set a body with `gh api -X PATCH`.
  - spine-program has no `scripts/check.sh`.
- **Merged in this session:**
  - #117: `data_mining/`, the Fluoroscopy Data Atlas.
  - #212: `provisional_patent/`.

### 3.2 Grid data platform and student access

- The Ceph migration is complete, and HOME is at about 520 GB.
- The visibility script in spinesurg-ct-nnunet (branch L6_Class, 0ab783f) leaves everything readable by approved
  students except `build_archive_private`, which holds the annotator map. This follows Greg's word of 2026-10-12,
  "anyone can read anything".
- Large outputs go under `/rs/rs_grp_oschome/go2432/`.
- Access is by `ssh wsu-grid` from Windows, or through WSL. Nothing runs on the login node.

### 3.3 Fluoroscopy Data Atlas

spine-program `data_mining/`:
- 217 datasets and 16 request letters;
- `CATALOG.md` reads on GitHub;
- the page `fluoroscopy_data_atlas.html`;
- the rebuild is `python data_mining/scripts/merge_atlas.py`.

None of the 16 letters has been sent. The Radiopaedia steps are manual by its terms.

### 3.4 Provisional patent (SchwingNet)

spine-program `provisional_patent/`:
- The current packet is `provisional/`, of 2026-09-18.
- Beside it are the invention disclosure, the counsel memorandum and the WSU disclosure package of 2026-09-25.

Greg chose on 2026-10-20 to keep the confidential parts in that internal repository. Whether the WSU package was sent
is recorded nowhere. Another thread added the inventor's answers to counsel's 60 questions for WSU 26-1902 (#215).

### 3.5 SchwingNet's dataset registry

OpenSpineConsortium/SchwingNet: PR #27 (issue #26) corrects two records of #24's registry and makes the rest
consistent, as Greg asked on 2026-10-20.
- **AASCE:** 609 labelled films and 98 challenge-test films, in two Ceph copies.
- **VinDr:** held, covered by WSU IRB HPR 2026-330 of 29 September 2026.
- **Closing prose:** every count read from a record.
- **ASCII rule:** `data/sources/` now sits under `tools/check_docs.py`.

It lands by automerge once CI's required "check" is green. Never run `bash scripts/check.sh` or
`tools/living_docs.py test` in a real clone on Windows. The lessons run in the working copy: they blank the local git
identity, switch to `claude/7` and leave files at the root (topic memory `living-docs-test-mutates-the-clone.md`).

### 3.6 Clones and scratch on the laptop

- Clones on the Desktop: `spine-program`, `SchwingNet` and `symphony-template`.
- Claim worktrees go under `C:\Users\grego\spc\<N>` and are removed after each merge.
- The session's scratchpad is temporary. That includes a Python venv with pydantic, beartype, icontract, typeguard,
  hypothesis and pytest, used to run SchwingNet's record renderer and tests.
- The CTSpinoPelvic1K working tree carries uncommitted NeurIPS camera-ready edits (`CAMERA_READY_NEURIPS/`) from
  before this session. This session did not touch them.

## 4. Open pull requests at the handoff

- OpenSpineConsortium/SchwingNet #27: this session's registry fix, with auto-merge armed.
- OpenSpineConsortium/SchwingNet #2 and #3: dependabot action bumps.
- OpenSpineConsortium/spine-program #216: symphony/sync, the board's files brought up to date. Greg merges there.
- OpenSpineConsortium/spine-program #89: claude/25, folder 05 (CT-2, the anterior pelvic plane), an older claim.
- OpenSpineConsortium/symphony-template, the pull request that adds this checkpoint (#311, issue #310).

## 5. Waiting on greg, numbered

1. Before the first student session, the steps in spine-program #72: the Claude GitHub App, the Setup App, the
   invitations, the labels and the Python environment.
   https://github.com/OpenSpineConsortium/spine-program/issues/72
2. Withhold the other datasets' patient header values still quoted on spine-program main (#81).
   https://github.com/OpenSpineConsortium/spine-program/issues/81
3. Merge spine-program #216 (symphony/sync): open
   https://github.com/OpenSpineConsortium/spine-program/pull/216, read the files and press Merge pull request.
4. Say whether the stale VinDr lines in spine-program should be corrected. They still call its determination
   pending, though HPR 2026-330 covers it:
   - `01_carm_level_detection/docs/handoff/DATASET_USAGE.md`, lines 30, 204 and 223;
   - its twin under `02_transitional_naming_truth`;
   - `01_carm_level_detection/CLAUDE.md`, line 144.

   A yes is one issue and one pull request.
5. Say whether the WSU invention disclosure package of 2026-09-25 was sent, so `provisional_patent/README.md` can
   record it.
6. Decide whether AASCE is a training corpus or the thoracic test set. The data audit leaves the two uses in
   conflict, and the 128 labelled BoostNet test films have never reached a render bank.
7. Send the fluoroscopy request letters you want. They are drafted in spine-program `data_mining/CATALOG.md`, under
   Requests, and none has been sent.
