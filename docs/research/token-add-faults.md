# Add Token faults of 2026-10-18

Source: the project thread "Add token faults" (greg's report of 2026-10-18, relayed by the coordinator), with the Control panel sign-in thread's diagnosis. Read from issue #222 and the logs of the Token workflow's runs 1 to 7 on this repository, and from `claude setup-token` 2.1.302 run in a cloud container behind tools/token_run.py's own pseudo-terminal with a made-up code, which no account can redeem.

## 1. A repository whose adoption is not merged

Ashley's repository, aschehr/OpenSpineToolbox-S1fix-2Dprojection, had its adoption pull request open, so its default branch had no .github/workflows/token.yml. The page opened an issue there, then the dispatch answered 404, and the page's hint told her to "pick symphony-template in the Repository box", which is the wrong advice for someone adding a token to her own repository.

The fix (site pull request "Tokens: say to merge the adoption first, and never strand Add Token"): the page reads `GET /repos/{repo}/actions/workflows/token.yml` before it opens the issue, so such a repository gets no stray issue, and on 404 says the workflow comes with the adoption and to merge the adoption pull request first, linking the open one from the branch symphony/adopt where there is one.

## 2. Add Token stuck after the dialog was closed

greg's press opened issue #222 and started run 39165163409, which posted the sign-in link at 20:51:01, 18 seconds after the run began. The page never showed the Sign in button, and Add Token did nothing afterwards. Three things in symphony-panel.js combined:

- GitHub answers an issue's comments with `Cache-Control: private, max-age=60`, so the browser served the page's first, empty read of the comments for up to a minute: the link could reach the page as much as a minute after the run posted it.
- Close only hid the dialog, and the poll went on for up to 15 minutes with the Add button disabled. Pressing Add Token opened the settings form, which cleared the dialog, so the sign-in view the poll drew into was no longer on the page; its Save and sign in then returned at once on the disabled button, and nothing showed.
- Nothing could stop the poll.

The same pull request reads the comments at an address of its own each time, so no cached answer is served; remembers the sign-in under way, so Add Token (or Renew) shows its dialog again instead of a dead form; and adds a Stop this sign-in button, which ends the poll, closes the issue as not planned and frees Add Token. The stop is hidden once the sealed token has arrived, so it never cuts the save of the secret short. An adversarial review of the change found that a stop which waited for the call on its way could wait for good, since the page leaves a call unanswered once it has signed out, so the stop frees Add Token at once and a sign-in begun before a sign-out is let go; the Add Token tile reads Sign-in waiting while one is under way; the dialog names the repository and says when another sign-in holds it; a 404 first asks whether SymphonyBoard reaches the repository at all; and a workflow Token that is turned off is said so, with its page, before any issue is opened.

## 3. Why runs 1 to 6 printed no token

Every run posted its sign-in link within about 15 seconds. Then:

| Run | Issue | What happened |
| --- | --- | --- |
| 1, 3, 4 | 187, 195, 196 | no code came within ten minutes |
| 2, 5, 6 | 189, 201, 202 | the code reached claude, which showed it as 92 asterisks, and printed nothing more within the 60 seconds the run waits |

Runs 1, 3 and 4 fit fault 2: the page drew its sign-in where nobody saw it, or a second press (runs 3 and 4 began 33 seconds apart) left one of them waiting.

Runs 2, 5 and 6 are not settled. What is known:

- The code's length, 92, is a 48-character code, the `#` and the 43-character state, so the page passed it whole.
- In the container, the same script's paste and Enter reach claude 2.1.302: a made-up code of that shape draws "OAuth error: Request failed with status code 400. Press Enter to retry." within seconds, with TERM set, with TERM unset, with TERM=dumb and with CI=true. A wrong or used code would have said so in the runs' last words; they show no error and no "Long-lived authentication token created successfully!" either. So claude neither refused the code nor finished within the minute, or it drew something the run did not keep.
- Inferred, not yet measured on a runner: GitHub's runners set no TERM, and with TERM unset claude draws only the cells that change, words separated by cursor moves (`\x1b[20G`) in place of the letters already on the screen. A token drawn over earlier text in that mode would reach tools/token_run.py in pieces that tokens.Masker's whole-token shape does not match, so it would be counted as no token and a piece of it could pass the mask. The runs show no sign this happened, since even the success line is missing, but it is a reason to give claude a TERM.

On the owner's word of 2026-10-18 ("just fix it so she and other collaborators can add their tokens"), tools/token_run.py now gives claude TERM=xterm-256color where the runner sets none; whether that was the cause is for the next real run to show. The rest stays proposed: in .github/workflows/token.yml set `TERM: xterm-256color` for the step, and on failure have tools/token_run.py report counts alone (bytes claude printed after the Enter, whether claude was still running, whether the mask holds a tail back), never text, so the owner's next run either works or says which of these it was.

## 4. A 403 writing a slot on a personal repository

Later on 2026-10-18 Ashley's Add Token answered 403 "Resource not accessible by integration" with the hint for an organization. On a personal account's repository the slots are the repository's own secrets and variables (slotPlace in symphony-panel.js), and Save and sign in writes the variable SYMPHONY_CLAUDE_SETTINGS before anything else. symphony-app's manifest.json grants the App the repository permission Secrets (write) and the organization's Secrets and Variables, but no repository Variables (actions_variables), so that write is refused on every personal repository, whoever presses. Inferred from the manifest, since no session can read the App's live settings. The site (pull request 68) now names the repository permissions in the hint for a personal repository; the App needs the repository permission Variables: read and write added in its settings, and each personal installation's owner accepts the new permissions.

## 5. The first token minted, and who may write the pool

Run 8 of the Token workflow (issue #228, started 22:00 UTC on 2026-10-18 by the owner, before the TERM change merged) posted its sign-in link, took the code and sealed the token, and the page saved it as slot 1. So runs 2, 5 and 6 did not fail for want of a terminal type alone, and the minting works as built; the TERM change stays as a guard.

Ashley's 403 has a cause no App setting removes: the Tokens page writes a slot as the person signed in, and GitHub lets only an organization's owners write its secrets and variables, and only a repository's administrators its own. She is neither an owner of OpenSpineConsortium nor a collaborator on symphony-template, which the page's old 404 hint told her to pick (inferred: the page's error does not name the repository). Site pull request 70 has the dialog say so before the press. Letting collaborators add tokens to an organization's pool would need the Token run to write the sealed token with the App's installation token; that choice is the owner's.

## 6. A collaborator's token into the organization's pool

The owner chose on 2026-10-18 ("Yes, free slots") to let someone who may write to an organization's repository, but is not an owner of the organization, add their own Claude token to its pool. Since GitHub refuses such a person every write of an organization secret or variable, the Token run does the writing itself: the page dispatches token.yml with `store: pool` and no key, and the workflow's job store, in the environment token-store, mints the SymphonyBoard App's installation token for the organization (organization secrets and variables, write) and runs tools/token_run.py with it. The script, once the token is minted, lists the organization's secrets and puts the token into the first slot of SYMPHONY_CLAUDE_1 to 32 that holds none, visible to the repository the run is in; adds the slot to SYMPHONY_CLAUDE_ACCOUNTS; marks it in SYMPHONY_CLAUDE_SETTINGS with the person as its owner and a new id; and posts only the slot's number on the issue. It never writes a slot that holds a token, and a settings variable that is not JSON by slot is left for an owner to mend rather than written over. Neither the run's GITHUB_TOKEN nor the App's token reaches claude's environment.

What holds it to that: the job's script is the default branch's only where the environment token-store allows the default branch alone, which an owner sets (Settings, Environments); otherwise anyone who may write could dispatch the workflow from a branch of their own with a script that does anything the App's token allows. Two collaborators storing within the same second could both see a slot free and the second would overwrite the first; the job holds no lock, since a concurrency group would hold the second person's sign-in until the first one's ended, and the window is the second between the list and the write. A collaborator can change or remove their own slot's settings from the page only as an owner can today, so the page shows them the slot as theirs and leaves its settings to an owner.
