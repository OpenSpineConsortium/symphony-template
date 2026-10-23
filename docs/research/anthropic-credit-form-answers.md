# Anthropic credit form answers and handoff

Source: the thread "Anthropic research credit applications", 2026-10-23, answering the AI for
Science application form the owner pasted that day, built from the AIDaS seed proposal
(spine-program, 01_carm_level_detection/grants/aidas_2027/). The same text is in the Claude Doc
"Anthropic research credit applications" (https://claude.ai/artifact/Ct2s8QCmApGuX3tUJ5nHki);
this copy keeps it in the repository. The programs themselves are in
anthropic-research-credits.md. Anthropic treats the form as non-confidential, so these answers
carry no preliminary accuracy figure or method detail; keep it that way.

## Handoff: where it stands

Nothing is submitted. The owner submits; no session can.

1. Wait until the provisional patent is filed (due 2026-10-30): the form is a public disclosure.
2. Tell Dr. Zhizhong Han that Anthropic will email h312h@wayne.edu to approve the project.
3. Copy the Organization ID: https://claude.ai, your name, Settings, Account.
4. Fill the bracketed items below (exact title, Google Scholar links) and check the 25,000 USD
   estimate against the owner's own 2026 usage.
5. Submit the form by Sunday 2026-11-01 for the 2026-11-02 review (else 2026-12-07); a declined
   application gets no reply.
6. In parallel, Dr. Han verifies the Team plan for scientists at
   https://claude.ai/labs-verification/attestation with the text under "Team plan" below; if
   credits are approved, email aiforscience@anthropic.com to ask whether they can move to the
   lab's Team organization.

## Form answers, field by field

- Name of primary contact: Gregory John Schwing
- Organization: Wayne State University
- Position or title: Clinical collaborator and lead, Open Spine Consortium (MD, PhD; General
  Surgery, Wayne State University School of Medicine / Detroit Medical Center). [Confirm.]
- PI's email: h312h@wayne.edu (Dr. Zhizhong Han)
- Website: https://github.com/OpenSpineConsortium
- Where heard: Anthropic's announcement "Expanding support for scientists" (August 2026)
- Project title: Framework-bound AI research agents on a university GPU cluster: measuring their
  reliability and cost, with spine surgery level checking as the case example
- Scientific fields: Medicine/Healthcare; Other: Computer science (agentic AI systems,
  high-performance computing)
- Organization ID: the owner's own Pro/Max organization for now (see the handoff)
- Account type: Pro/Max
- Key team members using Claude: Gregory Schwing (agents and frameworks); a part-time research
  assistant (checks Aim 1's runs); eight medical students and residents in two waves (from
  month 4); Dr. Han and Dr. Schwiebert (review).
- Profiles: [Google Scholar links for Dr. Han, Dr. Schwiebert and the owner]
- Biosecurity: None of the above

### Research team (under 100 words)

Zhizhong Han, PhD (PI), Assistant Professor of Computer Science and founding director of Wayne State's Machine Perception Lab, publishes on 3D Gaussian splatting and neural implicit surfaces (CVPR 2025 and 2026, NeurIPS 2024). Loren Schwiebert, PhD (Co-PI), Professor of Computer Science, accelerates scientific codes on GPUs and high-performance clusters. Gregory Schwing, MD, PhD (clinical collaborator, General Surgery, WSU School of Medicine and Detroit Medical Center) leads the Open Spine Consortium, which built the spine imaging platform, a labeled CT benchmark (NeurIPS 2026) and open-source tooling for running Claude Code agents on the university's GPU cluster.

### Research proposal (under 500 words)

Question. Can an AI agent do real scientific iteration, running experiments on a shared GPU cluster, with strict frameworks rather than the model deciding which results count? And can that workflow, measured and held to sealed tests, build a clinically useful tool in months? Our test case is wrong-level spine surgery, a never event that persists because surgeons confirm the level by counting vertebrae on an intraoperative C-arm X-ray, and the count fails on anatomy such as an extra lumbar segment.

Approach. This six-month project is the agentic core of our 2026-2027 Wayne State AIDaS seed proposal. Claude Code agents run on the Wayne State HPC grid through our open frameworks: Beethoven (the grid's job rules and a Claude Code worker as a Slurm job), beethoven-qa (a code gate with contract checking), REFORMS reporting rules, and Symphony (MIT-licensed coordination of many agents on one GitHub repository). A person sets each task's question and a pass/fail gate, sealed by hash before any run; the agent iterates hypothesis, jobs and analysis until the gate passes; a person merges the result.

Aim 1a: 20 sealed research tasks, each with a clean copy and a copy with a planted fault (data leakage, wrong labels, test-set tuning), run with and without automated checks (80 runs), counting wrong but plausible results submitted.
Aim 1b: a profiler logs every token and tool call; the agent tests four economies (context compression, fewer tool calls, indexed code retrieval, profiled prompts) as sealed tasks.
Aim 1c: Symphony's claim protocol against worktree and framework orchestrators on CooperBench and SWE-bench, scoring pass rate, tokens, dollars, conflicts and duplicated work.
Aim 3 (case example): agents close the gap between synthetic and real C-arm images (physics renders, public radiotherapy cone-beam projections) for a vertebra detector and level model, and build the first release of a locally hosted spine retrieval-augmented model that answers with verbatim, cited quotations. Patient data never reaches Claude; all imaging is public and de-identified.

Expected outcomes. A measured answer to how much enforced checks cut wrong results (hypothesis: from over half to under 20 percent of faulted runs); token and dollar cost per passing task for each economy and each orchestrator; open benchmark suites and run records (MIT); a C-arm level model tested on held-out devices; and the RAG-LLM's first release on public data with a graded question set.

Timeline. Months 1-2: tasks and gates sealed, faults planted, profiler in place. Months 2-5: Aim 1a runs, 1b economies, 1c suites, Aim 3 agent runs. Month 6: analysis, report, data and code release, and the NSF CAREER and NIH R21 proposals these results feed.

### How Claude will be used (200 words max)

Claude Code is the research agent itself, not an assistant beside it. On the grid it writes and runs the training and evaluation code, submits Slurm GPU jobs, reads their logs, revises hypotheses and keeps the reporting record, iterating until a sealed test passes; several agents work in parallel, each holding one task through Symphony's claim on GitHub. A person sets the question and merges the result. Today one researcher runs perhaps two experiments a day with Claude as a coding assistant; with agents running unattended across four GPU nodes, a task set of dozens of experiments runs in days, and every run is recorded for measurement. Claude also reads and summarises dataset licences and papers to map which data may train a commercial or a non-commercial model, and, through the Beethoven extension, gives medical trainees with no coding background the same agent. The study of the agents is itself the science of Aim 1: the reliability and cost of Claude-based research agents under enforced checks, measured run by run.

### Scientific impact (200 words max)

If it works, Aim 1 gives the field a measured answer to a question every lab using AI agents now faces: which results from an autonomous agent can be trusted, and what enforced checks (sealed tests, code gates, split and rerun checks) buy over written rules alone. The planted-fault design counts the leakage, label and tuning errors agents inherit from a lab's data, which current benchmarks of code edits and paper writing do not. Aim 1b and 1c add the first paired cost comparison of a claim protocol against orchestrators for coordinating many agents, with tokens, dollars and conflicts per passing task. All tasks, records and suites are open, so others can rerun them. In medical imaging, a level model that works on C-arm images from devices it never saw, without a preoperative CT, would remove the main barrier to automated level checks, and the work shows on one concrete case what a small academic team with agents can build in a year.

### Practical applications (200 words max)

Yes. Wrong-level spine surgery is a reportable never event that Medicare does not pay for; paid US malpractice claims for surgical never events reached 1.3 billion dollars over 1990-2010. The intended product is an advisory level label on each C-arm image, which the surgeon confirms, with two FDA-precedented routes (an app on the C-arm maker's platform, or an external unit reading the C-arm's video output); an FDA Pre-Submission and an NIH R21 follow in 2027. The spine RAG-LLM is customizable: any lab swaps in its own literature, detectors and records, hosted locally so no patient record leaves the institution. The agent frameworks (Symphony, Beethoven, beethoven-qa) are open source and let any university run gated Claude Code research on its own cluster; our trainee program extends this to medical students and residents with no coding background, and an NSF CyberTraining proposal will scale it.

### Measures of success (100 words max)

1. Wrong results submitted on faulted tasks: under 20 percent with checks versus over half without, with no fewer passes on clean tasks.
2. Every accepted number reruns within its sealed tolerance.
3. The four economies pass the same gates at under half the tokens.
4. Symphony's cost per passing task at or under each orchestrator's, pass rates within paired intervals.
5. Detector finds 97 percent of vertebrae on held-out C-arm devices.
6. RAG-LLM graded correct as often as a commercial evidence service, with no unsupported quotation.

### Credits requested

We request $25,000 in extra usage credits for six months (estimates at list price, from our 2026 runs; we will report actual use).
- Aim 1a, 80 multi-hour research runs (about $60 each): $4,800.
- Aim 1b, four economies, 20 tasks each, baseline and treatment (160 runs at about $30): $4,800.
- Aim 1c, CooperBench pairs for three coordination systems (about 2,000 runs at $2.50) and SWE-bench instances (about 1,500 runs at $1): $6,500.
- Aim 3, agent runs on detector transfer and the RAG-LLM's first release: $4,000.
- Medical trainees' agent work and licence and literature review: $3,000.
- Reruns required by the reproducibility gates (about 8 percent): $1,900.
Why it matters: our measurements need agents to run unattended and to completion. Subscription limits stop a run partway, which breaks the paired comparisons and forces reruns; credits let every arm of every task finish under the same conditions, so the reliability and cost results are clean.

### Additional information

This project is the agentic core of our 2026-2027 Wayne State AIDaS Seed Grant proposal (PI Han, Co-PI Schwiebert), submitted October 2026; Anthropic credits would let its Aim 1 measurements start before that award year and run at full scale. The lab is setting up Claude's Team plan for scientists for its members. No patient data or protected health information is sent to Claude; patient records stay on the university's grid. Our frameworks are public: github.com/OpenSpineConsortium (Symphony, coordbench, the Claude Code plugin). We will share run records and findings on agent reliability and cost with Anthropic and publicly.

## Team plan for scientists (Dr. Han verifies)

Affiliation: Department of Computer Science, College of Engineering, Wayne State University,
Detroit, Michigan.

Research description: Our lab works on 3D deep learning and medical imaging AI. A current project
builds a model that names vertebral levels on intraoperative spine X-ray, to help prevent
wrong-level surgery, trained on public CT and radiograph datasets on the university's HPC
cluster. A second line studies how teams of AI coding agents can carry out scientific software
work reliably, using an open-source coordination protocol and a public benchmark. Claude Code and
Claude would be used by [N] lab members for coding, analysis and literature review.

Seats: [N]; Premium (15 USD a month, 5x usage) for those running agents daily, Standard (free)
for the rest; the AIDaS budget's line C1 buys six Premium seats.
