# Ashley's Add Token run on spine-program, 2026-10-21

Source: the thread "Ashley's token pool add" in the symphony_2 Project, 2026-10-22, from the owner's report that Ashley Schehr (aschehr) could not add her token, with GitHub's notification email of the Token workflow's run 8 on OpenSpineConsortium/spine-program (https://github.com/OpenSpineConsortium/spine-program/actions/runs/39692381334). Read from that run's jobs and log, from runs 2 and 4 of 2026-10-20, and from issue 222's comments.

## What happened

Run 8 succeeded. Its job store logged "Stored the token in the organization's slot 1." and posted the stored marker with slot 1 on issue 222, which the control panel then closed as completed. `TokenStore.store` writes the owner mark in SYMPHONY_CLAUDE_SETTINGS, the secret SYMPHONY_CLAUDE_1 and the accounts list in that order, and raises before printing that line if any of the three fails, so slot 1 holds her token, marked as hers and lent to spine-program. A cloud session cannot read the organization's secrets or variables to confirm it directly (the proxy refuses those paths).

## Why it looked like a failure

GitHub's notification email lists every step of the job by name and leaves out whether each ran. The step "Say that the run stopped" runs only on failure() and was skipped in run 8; "Remove the held token" runs always(), deleting the token file from the runner. Read as a list, the two names say the run stopped and the token was removed, beside the run's own message that the token was saved. The email's success message was true.

Ashley's two runs of 2026-10-20 (runs 2 and 4, issues 217 and 218) did fail, at the store step: GitHub answered 404 when the run tried to mark slot 1 as hers in SYMPHONY_CLAUDE_SETTINGS, the fault spine-program-token-404.md explains. Those, not run 8, are the attempts that left no token.

## What changed

The steps are renamed in .github/workflows/token.yml so the email's bare list reads true whatever happened: "If a step failed, say why (skipped when all went well)" and "Delete the held token from the runner (runs every time)". The sync carries the file to adopted repositories.
