# Claude Code handoff, 2026-10-20: the session on Greg's laptop (workspace CTSpinoPelvic1K-1)

Source: the Claude Code session in VS Code on Greg's Windows laptop, written on the owner's ask of 2026-10-20 to
checkpoint it here as the claude.ai Project threads do, so its knowledge is kept where every account can read it.
Revised at 02:00 UTC on 2026-10-21 (the same evening in Detroit) with the work that followed and the CI errors of the
evening explained: part 8. The memory beside this file was exported again at the revision.

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
  - #221 (issue #220): every statement that VinDr-SpineXR was outside determination 2026-269, or that its determination
    was pending or not recorded, now names WSU IRB HPR 2026-330 of 29 September 2026: 168 lines in 65 files, and the data
    platform copy under 10_data_platform_grid takes the same lines from its source. The copy now differs from
    spinesurg-ct-nnunet's data_platform at bf1432f only by the program's redactions (laptop paths, the C&IT account, the
    Balgrist address).

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

### 3.5 SchwingNet's dataset registry and its reproduction kit

OpenSpineConsortium/SchwingNet. PR #27 (issue #26, merged by automerge on 2026-10-20) corrected two records of #24's
registry and made the rest consistent, as Greg asked:
- **AASCE:** 609 labelled films and 98 challenge-test films, in two Ceph copies.
- **VinDr:** held, covered by WSU IRB HPR 2026-330 of 29 September 2026.
- **Closing prose:** every count read from a record.
- **ASCII rule:** `data/sources/` sits under `tools/check_docs.py`.

PR #32 (issue #31) is the reproduction kit Greg asked for the same evening ("all the manifest and direct links and code
that could reproduce this dataset and all the links they came from"):
- `data/reproduce/`: the manifest of 211 sources and the fetch code, byte-for-byte copies of spinesurg-ct-nnunet's
  `data_platform/` at bf1432f, with their SHA-256 in `SHA256SUMS`; `map.json`, the 60 registry records mapped to the
  manifest records that hold them (4 have none and say why); `README.md`, what was checked and how to run it.
- `tools/reproduce_table.py` renders `docs/research/datasets-reproduce.md`: per registry record, the manifest records
  with acquisition date and method, origin links, fetch command, checks, grid path and licence; the 144 sources of the
  anomaly harvest; what no script reproduces. Its check, in `scripts/check.sh`, fails when the page, the map and the
  copies disagree.
- Verified in the source repository on 2026-10-20, no network: `reacquire.py --list` (211 sources), the dry run of
  every source (2,171 lines, exit 0), `test_reacquire.py` (28 tests OK).

Another session landed the frame catalog (#30: `data/registry/`, `data/splits/`, `tools/catalog.py`) the same evening;
#32 carries it merged in. Part 8 has the state of #32 at the revision.

Never run `bash scripts/check.sh` or `tools/living_docs.py test` in a clone you commit from. The lessons run in the
working copy: on this laptop they blanked the local git identity, switched to `claude/7` and left files at the root
(topic memory `living-docs-test-mutates-the-clone.md`; SchwingNet memory `run-the-checks-in-a-throwaway-copy.md`).

### 3.6 Clones and scratch on the laptop

- Clones on the Desktop: `spine-program`, `SchwingNet` and `symphony-template`.
- Claim worktrees go under `C:\Users\grego\spc\<N>` and are removed after each merge.
- The session's scratchpad is temporary. That includes a Python venv with pydantic, beartype, icontract, typeguard,
  hypothesis and pytest, used to run SchwingNet's record renderer and tests.
- The CTSpinoPelvic1K working tree carries uncommitted NeurIPS camera-ready edits (`CAMERA_READY_NEURIPS/`) from
  before this session. This session did not touch them.

## 4. Open pull requests at the handoff (as of the revision, 02:00 UTC on 2026-10-21)

- OpenSpineConsortium/SchwingNet #32: this session's reproduction kit, auto-merge armed at the revision; it merged at
  02:03 UTC (part 8).
- OpenSpineConsortium/SchwingNet #34: another session's, the catalog as read-only versions and the data layout.
- OpenSpineConsortium/SchwingNet #2 and #3: dependabot action bumps.
- OpenSpineConsortium/spine-program #216: symphony/sync, the board's files brought up to date. Greg merges there.
- OpenSpineConsortium/spine-program #89: claude/25, folder 05 (CT-2, the anterior pelvic plane), an older claim.
- OpenSpineConsortium/symphony-template #322: this revision (issue #320); #318, #319 and #321 are other threads'.

Merged earlier in the session: SchwingNet #27; symphony-template #311 (the first writing of this checkpoint);
spine-program #117, #212 and #221.

## 5. Waiting on greg, numbered

1. Before the first student session, the steps in spine-program #72: the Claude GitHub App, the Setup App, the
   invitations, the labels and the Python environment.
   https://github.com/OpenSpineConsortium/spine-program/issues/72
2. Withhold the other datasets' patient header values still quoted on spine-program main (#81).
   https://github.com/OpenSpineConsortium/spine-program/issues/81
3. Merge spine-program #216 (symphony/sync): open
   https://github.com/OpenSpineConsortium/spine-program/pull/216, read the files and press Merge pull request.
4. Done on 2026-10-21 (Greg said yes): the stale VinDr lines in spine-program are corrected, PR #221 (issue #220).
   What remains is the manuscript's own token: `\PENDING{G0}` in spinesurg-ct-nnunet `SchwingNet/main.tex` line 137
   takes "HPR 2026-330, 29 September 2026" at the next build of the paper.
5. Say whether the WSU invention disclosure package of 2026-09-25 was sent, so `provisional_patent/README.md` can
   record it.
6. Decide whether AASCE is a training corpus or the thoracic test set. The data audit leaves the two uses in
   conflict, and the 128 labelled BoostNet test films have never reached a render bank.
7. Send the fluoroscopy request letters you want. They are drafted in spine-program `data_mining/CATALOG.md`, under
   Requests, and none has been sent.
8. spinesurg-ct-nnunet `HANDOFF/DATASET_USAGE.md` still says VinDr's determination is pending; it is the one copy of
   that handoff not corrected on 2026-10-21, because that repository was not in the ask. Say whether to fix it.

## 8. Revision of 2026-10-21, 02:00 UTC: the evening's work, and the CI errors you saw

What landed after the first writing of this file, on Greg's word of the evening ("yes fix them and also make sure we have
all the manifest and direct links and code that could reproduce this dataset and all the links they came from, and then
add it to the repo, handoff, and then stop"; then "get this bulletproof and unambiguously transparent and correct"):

- spinesurg-ct-nnunet bf1432f (branch L6_Class, pushed): the two VinDr README cards of the data platform carry HPR
  2026-330, as its sources.json had since 65fb454 of 2026-10-10.
- spine-program #221, merged: part 3.1 above. Every changed line is in its diff; the search for the stale phrases
  afterwards found nothing outside the dated history left as written.
- SchwingNet #32: part 3.5 above. Its state at this revision is in the line below, written when it was known.
- The memory beside this file, exported again, now 175 fact files.

The standard applied to all of it: a claim in a document names its source (the IRB notice, a commit, a listing taken on a
named date); a number comes from a record or a listing; what is not known is written as not known.

**The CI errors of the evening, in plain words.** Three kinds of red appeared on pull requests in SchwingNet and
symphony-template between 22:00 and 23:30 UTC on 2026-10-20, none of them caused by the content that landed:

1. A test in the template (`tests/test_pool.py`) pinned a reset time that passed at 22:00 UTC. From then on it failed
   the required check on every pull request in both repositories, whatever the change. The template fixed it on main
   at 22:16 UTC (commit 944743b, "The pool test stands on the real clock, since its frozen date rotted"); SchwingNet's
   main carried the same fix from 22:20 UTC (commit 628bfd2, landed by its #29 at 22:24 UTC). Each pull request opened
   before the fix went red once, then green after main was merged into it.
2. The template holds every page under docs/ to a rule: every push command must name the remote and the branch it
   pushes. One memory file copied here said "git push/pull" and failed the check in three jobs (the two filled-copy
   tests rerun the same rule). The file was reworded, here and on the laptop.
3. "Cancelled" runs beside the failed ones were superseded runs: each new push cancels the run of the previous commit.
   They are not failures.

Final state of each pull request of this session: spine-program #117 (2026-10-17 21:57 UTC), #212 (2026-10-20 04:15
UTC) and #221 (2026-10-21 01:44 UTC) merged by the owner's account after a file-list check; SchwingNet #27 merged by
automerge at 22:32 UTC once its check was green with main merged in; symphony-template #311 merged by auto-merge at
22:43 UTC after the two fixes above; SchwingNet #32 and symphony-template #322 as the line below says.

State line: SchwingNet #32 merged by automerge at 02:03 UTC on 2026-10-21 (merge commit 9fe369e; issue #31 closed);
symphony-template #322 is this revision.
