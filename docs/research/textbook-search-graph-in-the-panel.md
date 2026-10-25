# The textbook's search graph in the control panel

Source: the thread "Explore textbook RAG in control panel", 2026-10-25; the site's pull request OpenSpineConsortium/openspineconsortium.github.io#144.

The owner asked for the status of the RAG over SchwingNet's textbook and for a way to explore it visually on the control panel's Explore tab, beside the task dependencies.

## Status of the RAG

It is built and merged in SchwingNet (issue #250): "Ask the book", a BM25 search over the textbook's sections chosen as named blocks (src/schwingnet/rag.py, tools/rag.py). It is retrieval, not a trained model: nothing is learnt, and the index is rebuilt from the chapters on every site build and never committed. SchwingNet's own memory, docs/memory/the-textbook-rag.md, holds the parts, the evaluation (recall at 5 0.877, MRR 0.764 for version 1 on 54 written questions) and where it runs: the members-only docs site and the claude.ai textbook reader, where the viewer's own Claude answers from the passages.

## What the panel shows, and why that way

Explore has a switch: Task dependencies, the view as it was, and Textbook search graph. The graph draws each chapter as a circle sized by its sections, a solid line where one chapter cites another, a dashed line to each chapter's two most alike by tf-idf cosine with the shared words on hover, and a search box that ranks sections as version 1 does and lights the chapters holding the best eight.

The book is confidential until the provisional is filed and the site is public, so the panel holds none of it: it reads the chapters from the private repository through GitHub's API as the signed-in person, only when the view opens, and keeps them in the page's memory alone. An account that cannot read SchwingNet sees a sentence and no graph. The alternatives were refused: embedding the built index in the site would publish the book, and reading the members-only Pages site from openspineconsortium.com is cross-origin and carries no GitHub sign-in.

The panel's search differs from the book's in detail (no 300-word cut of long sections, no stem block), so scores are not identical; the ranking rule is the same.
