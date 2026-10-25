# The textbook's search graph in the control panel

Source: the thread "Explore textbook RAG in control panel", 2026-10-25; the site's pull request OpenSpineConsortium/openspineconsortium.github.io#144.

The owner asked for the status of the RAG over SchwingNet's textbook and for a way to explore it visually on the control panel's Explore tab, beside the task dependencies.

## Status of the RAG

It is built and merged in SchwingNet (issue #250): "Ask the book", a BM25 search over the textbook's sections chosen as named blocks (src/schwingnet/rag.py, tools/rag.py). It is retrieval, not a trained model: nothing is learnt, and the index is rebuilt from the chapters on every site build and never committed. SchwingNet's own memory, docs/memory/the-textbook-rag.md, holds the parts, the evaluation (recall at 5 0.877, MRR 0.764 for version 1 on 54 written questions) and where it runs: the members-only docs site and the claude.ai textbook reader, where the viewer's own Claude answers from the passages.

## What the panel shows, and why that way

Explore has a switch: Task dependencies, the view as it was, and Textbook search graph. The graph draws each chapter as a circle sized by its sections, a solid line where one chapter cites another, a dashed line to each chapter's two most alike by tf-idf cosine with the shared words on hover, and a search box that ranks sections as version 1 does and lights the chapters holding the best eight.

The book is confidential until the provisional is filed and the site is public, so the panel holds none of it: it reads the chapters from the private repository through GitHub's API as the signed-in person, only when the view opens, and keeps them in the page's memory alone. An account that cannot read SchwingNet sees a sentence and no graph. The alternatives were refused: embedding the built index in the site would publish the book, and reading the members-only Pages site from openspineconsortium.com is cross-origin and carries no GitHub sign-in.

The panel's search differs from the book's in detail (no 300-word cut of long sections, no stem block), so scores are not identical; the ranking rule is the same.

## Why retrieval and not a trained model

The owner asked, the same day, what it means that the search is BM25 and not a trained model, and why not train one. Only the search is untrained: in the reader the viewer's own Claude writes the answer from the passages the search picks.

- BM25 matches words, not meaning, so a question in other words than the book's ("how fast is it" for "latency") can miss; that is its real weakness. In return it is exact on names and numbers, instant, runs in the reader's browser with nothing sent anywhere, and needs no retraining when the book changes. In the reader Claude calls the search as a tool and can search again in other words, which closes much of the gap.
- The evaluation's 54 questions were written from the chapters and likely reuse their wording, which probably flatters a lexical search; no reworded set has been scored yet. This is an inference, not a measurement.
- Fine-tuning is not open to a Claude subscription, and a fine-tuned model cannot cite where a fact came from and goes stale with each edition, which is why retrieval suits a book that changes.
- The realistic upgrade is a trained embedding model beside BM25, in the embed slot rag.py already keeps (none today). It stays empty because the project keeps no API key, a subscription token makes no embeddings, and a local model is a new dependency, which needs an issue and the owner's word, and a large download for the in-browser search.
- The suggested order: score about 20 reworded questions first, and add an embedding block only if recall falls.

## Embeddings and the Console credits

The owner then asked whether about 250 API Console credits a month would pay for an embedding search to feed idea generation in Sakana's AI Scientist (the handoff of 2026-10-25, section 9).

- Anthropic offers no embedding model: its Embeddings page (platform.claude.com/docs/en/build-with-claude/embeddings, read 2026-10-25) points to Voyage AI by MongoDB, whose keys come from MongoDB Atlas and bill there, so Console credits cannot buy embeddings. The cloud proxy refuses mongodb.com, so Voyage's prices were not read.
- None is needed to start: the book is about 275,000 words in 876 sections, so the existing BM25 search costs nothing, and a small open embedding model on the owner's machine or the grid embeds it in minutes at no cost, keeping the confidential text away from a new third party before the filing.
- The credits fit AI Scientist's own model calls instead, roughly 20 cents an idea on Sonnet 5.5 by an estimate of about 60,000 tokens read and 6,000 written per idea with its self-review rounds; using them needs an API key, which the project's rule forbids unless the owner decides otherwise (asked on a decision card in the thread).
- AI Scientist's novelty check searches Semantic Scholar by default, which sends words about each idea to an outside service; it is off or reviewed until the filing.

## The key or the subscription, and Elsevier's search

Asked next for the pros and cons of the two ways, and whether AI Scientist could use the owner's ScienceDirect and Scopus institutional tokens.

- One Console key, paid from the credits: it spares the subscription's weekly window, near its limit; AI Scientist runs as Sakana built it, which is less work and a fairer comparison with its published results; the API's prompts are not used for training by default, which suits the confidential book and Elsevier's text; and the spend stops at the credits. Against it: a live key can leak and be spent by whoever holds it, full experiment-and-paper runs may use the month's credits up, and it breaks the no-key rule.
- The subscription only: no new credential, and it works as the research loop does, inside the claim protocol and the required check. Against it: it shares the five-hour and weekly windows with every other thread, each stage must be rewired to run through Claude Code, which is work and moves away from Sakana's method, and on a personal plan whether sessions may train a model depends on the privacy setting.
- Elsevier: Scopus can stand in for Semantic Scholar as AI Scientist's literature search, and ScienceDirect can give full text by DOI, through the owner's API key with the institutional token (Elsevier's APIs take the token only beside a key). The library and Elsevier cleared Claude reading Elsevier's text on 2026-10-19 so long as the token and the text are never public (notebooks.md), so the search then stays with a provider already cleared, and the field's journals include Elsevier's (The Spine Journal, World Neurosurgery, Medical Image Analysis). The cloud proxy refuses api.elsevier.com, dev.elsevier.com and www.elsevier.com (2026-10-25), so it runs on the grid or the owner's computer; the key and token stay out of git, logs and URLs; and it stays on Claude, since Elsevier's word names Claude and no other AI service.
