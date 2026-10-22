# Several grid workers, one per project

Oct 21, 2026

## What was asked

greg, 2026-10-21 20:06 UTC: switch between and update projects using several Claude workers on the grid, because the laptop cannot keep several Claude desktops signed in at once. He wants to remote into several workers and switch between them in the browser through the Beethoven extension.

Short answer: yes, and most of the grid side already exists. Since framework 22 the grid runs several named workers at once, each one a Remote Control environment. What is missing is on the Beethoven side. Today Beethoven knows one worker name and one project address. The plan below gives it a list of projects, each tied to its own worker, with a switcher.

## What exists today

- **Grid (hpcworker framework 22-23).** `hpcworker accounts start N NAME` starts a worker of its own on Claude account slot N. Each worker is a separate Slurm job, has a separate Remote Control link, and keeps its own status.json and connection.json. `accounts stop NAME` stops it. `worker status --name NAME --json` reports on one worker.
- **Control panel (Grid tab).** The tab lists every grid worker and has Start, Stop, Log and Sign in another for each. The Workers tab's "Running now" box shows the grid workers and the cloud workers together.
- **Beethoven (23.x).** It has one `worker_name` and one `project_url`. *Open my project* opens that single project page, and the home screen follows that single worker.
- **The constraint behind it all.** A claude.ai project reaches a worker only when the project asks for it through *Work locally* and someone allows the folder on the card. A worker started on its own never appears inside a project, so each project must be paired with its own worker by hand once.

## The design

1. **Projects list in Beethoven.** Settings gets a list in place of the single project address. Each row holds a short name, a claude.ai project address, the grid worker's name, and which Claude account slot it runs on. The existing single address becomes the first row, so nothing breaks.
2. **Switcher on the home screen.** A row of project chips sits at the top. Pressing one makes it the active project: the home screen then shows that worker's state, and *Open my project* opens that project's page in its own tab. Each project keeps its own tab record, so going back to a project brings its tab forward instead of opening a second one.
3. **Start on press.** When the chosen project's worker is not running, Beethoven starts it with `accounts start N NAME` through the portal shell. This is the same one-sbatch press it already makes, and it never starts a second worker of the same name.
4. **Update.** *Update* on a project row pulls that worker's workspace to its repository's main by fast-forward only, the same rule as the gate's `update`. It asks first if the worker is busy.
5. **Same list in the control panel.** The Grid tab shows the same pairing, so a session can start or stop a project's worker through the gate without greg. The list is stored on the grid (accounts.json gets a `project` field per worker), so Beethoven and the panel read one record.

## Build order and open questions

Build order, one pull request each:

1. hpcworker: the `project` field on a worker, plus an `accounts list` that returns it (the contract export moves up one version).
2. Beethoven: the projects list, the switcher and start on press, read through the new contract. This needs a store release.
3. Control panel: the project column, and Start and Stop per project.
4. The workspace *Update* press, on both sides.

Open questions, not yet measured:

- **Shared accounts.** Can two workers on the same Claude account each stay registered as a separate environment? Framework 22 keeps each worker to an account of its own, and the environment id is stable per machine id. If not, the number of projects running at once is the number of Claude accounts signed in on the grid. Today that is the Wayne State Max account only. Adding the gmail account (Grid tab, Sign in another) makes it two.
- **Resume after a wall-time restart.** Does a project's *Work locally* pairing survive when the worker's successor job resumes with `--continue`? If not, Beethoven should say so and offer to pair again.
