"""flowbench: the workflow as a plug-in, on SWE-bench's issues.

The package holds the harness: tasks.py reads SWE-bench's task repository
and draws the pre-registered order, backlog.py is the shared list of
(instance, arm) items the lanes take, run.py provisions, runs and finishes
one (instance, arm) attempt with the arm's stages, score.py calls
SWE-bench's own harness, record.py writes the run's record and prices its
tokens, report.py sets the arms side by side, and fake_agent.py stands in
for an agent in a run that spends no usage. arms/ holds the flows. Python
3.12 or later with its standard library and git; Docker for a real run;
SWE-bench's harness in a virtualenv of its own for scoring.
"""
