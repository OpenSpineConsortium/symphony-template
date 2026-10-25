# The grid readout's limits

Source: the thread "Choose datasets for a powered normal-spine test", 2026-10-25, while reading SchwingNet's folder report through grid-accounts.yml.

tools/grid_accounts.py writes each gate job's output to logs/job-<job>.json on the branch `grid`, and it shapes that output in two ways a gate word's author has to plan for:

- It keeps only the last 400 lines (LOG_LINES), with each line cut to 300 characters. A report page longer than that loses its head. A gate word that deletes a page once printed, as SchwingNet's `folders` does, then loses it for good. On 2026-10-25 this cost page 1 of the folder report and one more approved grid job. SchwingNet #301 now cuts each page at 350 lines.
- It masks every run of 32 or more characters from `[A-Za-z0-9_+=-]` as `[hidden]` (LONG), so that a token cannot pass. A folder or file name that long is masked too. Two data-root folders came back as `[hidden]`. One was identified from the repository records that name it. The other is open as spine-datasets #368.

So a gate word that prints a report keeps each send under about 350 lines and deletes nothing before it has printed it whole. A long name is read from a record or a listing outside the readout, never from the readout itself.
