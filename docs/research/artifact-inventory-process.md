# Inventorying an account's artifact gallery as files

The thread "Artifact Textbook", 2026-10-22. The owner asked for one reference book synthesised from every artifact his accounts had made, read as the files that artifacts/ holds here and in a private repository, never from memory. This note keeps the process alone, what was done to read 69 exported artifacts into one inventory in an afternoon and what failed, so the next export of a gallery is inventoried the same way; the inventory itself, the book and everything the private repository's artifacts hold stay there.

## What was done

1. The two artifacts/README.md indexes were read as the one list: a row per artifact with its folder, link and owning account, and the rows marked not copied (three: court filings and a letter with its mailing list) were skipped and never sought elsewhere.
2. Each folder was reduced to plain text by a script: the page's HTML stripped to its text, a Design-type artifact's page taken from the JSON its script tag embeds (the folder's index.html alone reads as nearly empty), and a page's data files summarised. Before any reader saw a text, e-mail addresses and phone numbers were replaced by a marker, since two flyers and an outreach page print them; people appear by role. The replacement also mangled one commit hash that looked like a phone number, which did no harm.
3. Readers worked three artifacts at a time, each writing one record from the text and the folder's own files: kind, date and its evidence, the question answered, claims with the evidence the artifact gives for each, every number with its unit, n and interval, datasets, tools and models, decisions with date, owner and reason, open questions, unsourced assertions, stale markers, cited sources, cross-references, confidentiality, related artifacts and people by role. The records were merged into one JSON in the indexes' order and rendered to a Markdown table by a script, so the table and the record never disagree.
4. Three readers clustered the records by different lenses (the question answered, the stage of the work, the reader and the decision) and a fourth settled one clustering with a canonical artifact per question and the superseded and duplicate versions collapsed onto it. A script checked that every id was placed exactly once.
5. Two readers went over the numbers table, one half each, for every quantity two artifacts give with different values; one reader per cluster went over the records for disagreements, revised figures, stale statements and shared unsourced claims. A script then looked for each candidate's quotes and values in the extracted text and, failing that, in the page's own files, and the rendered file carries that status beside each candidate.
6. The proposed table of contents was drafted from the clusters, with every artifact mapped to the chapters that use it, and posted on the pull request for the owner before any chapter.

## What failed and what it cost

- A reader's quote is not a source. Of 247 number collisions, 2 quotes were not found anywhere; of 189 cluster disagreements, 35 had a paraphrase where a quote should be, 33 of them from one reader. The script's check is cheap and should run before any candidate is shown to a person.
- Numbers that live in a page's script or data block are not in the extracted text: 39 of the 247 collisions had a quote found only in the page's own files. An extractor should keep the text of script-embedded data, or the verifier should read the raw folder as this one did.
- The account's usage limit stopped the work for two hours in the middle of the verification pass: the readers that verify, one per pair of artifacts, were the most numerous and the first to be cut off, and the first draft of the table of contents was lost with them. The verification by script above replaced most of what they would have done; the per-cluster reading continues in the next phase, cluster by cluster rather than all at once.
- A workflow handed a placeholder where its arguments belonged fails at its first step; a workflow's saved output is a file whose result sits under one key beside its logs. Both cost a relaunch.

## What to keep

The one list is the index, the one record is the JSON, every Markdown file is rendered, every count is checked by script, every quote is matched to its source by script, and no address of any kind leaves the folder it was printed in. The scripts that did this are not in this repository; they belong with the inventory they render, and the private repository takes them with its next phase.
