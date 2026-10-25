# Handoff of 2026-10-25 at 14:30 UTC, thread "Fix worker launch in control panel"

Source: the thread "Fix worker launch in control panel" in the claude.ai project "symphony3", written because the owner asked every thread at 14:23 UTC to checkpoint, push everything that could be needed, update the handoff, say how to continue on another account, and stop. A session that picks this thread up reads this page, then the board. No secret, token or e-mail is written here.

## Where this thread stands

Everything the thread made is merged, and nothing of it lives only in its container: at 14:30 UTC every clone it used was clean, and each of its branches `claude/project-thread-35q4f7` was on origin or squash-merged. Its research is docs/research/control-panel-worker-launch.md (symphony-template#468 and #474), and the memory it corrected is docs/memory/protocol-changes-come-from-symphony-protocol.md (#474).

What the owner asked, and where each landed:

1. Run the workers now did nothing. .github/workflows/workers.yml runs only the registry's workers that say `"runs": "actions"`, and SchwingNet registers none, so its run ended green having done nothing. The control panel now reads the registry first and says why, launches a task or a worker in Actions directly, and shows each repository as a tab, with All first (openspineconsortium.github.io#142).
2. The order of the work: the owner chose priority labels. symphony-protocol#63 takes the work of each of Pick's places labelled p1 first, then p2, then p3, then the rest, blockers still before the queue; the panel's arrows on a task put the labels on (openspineconsortium.github.io#145).
3. Release 0.7.0, on the owner's card of 12:50 UTC: symphony-protocol#64 raised the version, and its merge published v0.7.0 at 13:33 UTC. It is on main in symphony-template (#472), coordbench (#36), symphony-marketplace (#20, the plugin at 0.1.16), symphony-app (#91) and SchwingNet (#313, merged at 14:22 UTC once the owner had approved its runs and the pull request); each copy's record names sdlc-protocol 0.7.0 at 9f94c4d.
4. A grid worker's Open the session opened claude.ai on the wrong account: the Grid tab asks which grid account this Chrome profile is signed in to, and points a worker on another account to Chrome's own Open link as (openspineconsortium.github.io#143).
5. Beethoven: 24.2.0 keeps its grid sign-in sheet on screen while the grid is out of reach (beethoven-extension#26), and 25.0.0 adds Open in Beethoven to the right-click menu of a worker's link, or a greyed line naming the account for a worker on another one (#27, the permission contextMenus). The site was rebuilt for Beethoven's privacy statement version 20 (openspineconsortium.github.io#146).
6. The panel under the tabs that says who is signed in takes its height from a grip on its top edge, dragged or moved with the arrow keys (openspineconsortium.github.io#145).
7. The Chrome Web Store refused 25.0.0's upload while 24.2.0 was in review. The release kit now withdraws an older review so the newer build is submitted in its place (chrome-store-release-kit#1). On the rerun, 25.0.0.125 became the store's draft, but its submit was refused until the new permission's justification is pasted on the dashboard, which is the owner's step below.

## Open work

1. Beethoven 25.0.0 waits for its first submit, the owner's step below. Its record is the section "The store release of 25.0.0" of docs/research/control-panel-worker-launch.md and beethoven-extension's Release run 18. Nothing follows it: each later merge to beethoven-extension's main submits its own build, since CWS_ON_PUSH is publish.
2. SchwingNet registers no worker in Actions, so the panel's Run the workers now starts nothing there. A worker in Actions is a Claude run, which SchwingNet's rules leave to the owner's word: it is added with the panel's + Add worker (Where it runs: actions) and its pull request, with the secret CLAUDE_CODE_OAUTH_TOKEN set. Not started.
3. Any other repository made from the template takes 0.7.0 from its own .github/workflows/protocol.yml at the next weekly run, Monday 26 October at 06:17 UTC, or when it is run by hand. Where that repository's ruleset requires more than the check, as SchwingNet's does, its pull request waits for the owner to approve its runs and its review, as #313 did.
4. SchwingNet's own docs/memory/protocol-changes-come-from-symphony-protocol.md still says the template vendors 0.5.0 and that the sync of 0.4.1 is a downgrade to close; the template's copy was corrected in #474. Carry the correction into SchwingNet with the next SchwingNet pull request that touches the protocol, since memory never travels alone there either.

## Waiting on the owner

1. Submit Beethoven 25.0.0, if it is not done yet:
   1. Open the Chrome Web Store Developer Dashboard, https://chrome.google.com/webstore/devconsole, and click the item Beethoven.
   2. Open the tab Privacy practices. In the justification field for contextMenus, paste the text under "contextMenus (new in 25.0.0)" in https://github.com/OpenSpineConsortium/beethoven-extension/blob/main/docs/store/PASTE.md.
   3. Click Save draft, then Submit for review.
2. Nothing else.

## Resume on another account

1. On the next account, make its own Project as docs/setup/claude-project.md says, linking OpenSpineConsortium/symphony-template and OpenSpineConsortium/SchwingNet as this project does, and copy this project's instructions into it, since they carry the owner's standing rules for every thread. The account needs GitHub connected (https://claude.ai/connect-github); the Claude GitHub App is already on every repository of the organization.
2. Start a thread there; read this page and docs/research/control-panel-worker-launch.md, then fetch and read the board.
3. Add the other repositories this thread used, with add_repo, only when the work needs them: symphony-protocol, coordbench, symphony-marketplace, symphony-app, beethoven-extension, chrome-store-release-kit and openspineconsortium.github.io.
4. Nothing of this thread's is claimed or half done. Take the open work above in its order: items 1 and 2 are the owner's, item 3 runs by itself and may wait for the owner's approval, and item 4 needs no word. A further release of symphony-protocol needs the owner's own words, as 0.7.0 had.
