# Plan

Implements [`spec.md`](spec.md). No code is written until this plan is approved.

## Files to create or change

| File | Purpose |
|---|---|
| `requirements.txt` | The one dependency, `numpy`, installed into `.venv` with pip. |
| `rag_common.py` | Shared helpers: read and check the environment variables, POST JSON with `urllib`, `embed(texts)`, `chat(messages)`, and the HTTP and timeout error messages. |
| `indexer.py` | Find the course pages, split them into labeled chunks (skipping heading-only sections), embed them in batches, write `index.json`, print counts, chunk sizes and cost. |
| `ask.py` | Load `index.json`, embed the question, rank chunks by cosine similarity with numpy, print the top 4 with scores, build the prompt, print the answer and usage. `--no-retrieval` skips the excerpts. |
| `questions.json` | The five eval questions and their expected phrases, written by me. |
| `eval.py` | Run the five questions with and without retrieval, print pass/fail tables and the chunk labels for failures. |
| `CHECKS.md` | Eval results for both runs, and the stale-page finding. |
| `README.md` | How to build and ask, environment variables, the questions, results, the stale-page finding, one line of code I can explain. |
| `.gitignore` | Add `index.json`; it is several megabytes and is rebuilt with one command. |

## Order of work

1. Create `.venv`, install from `requirements.txt`.
2. Write `rag_common.py`.
3. Write `indexer.py` and build the index.
4. Write `ask.py` and ask one question with a known answer and one with no answer.
5. Write `questions.json`, then `eval.py`, and run the eval with and without retrieval.
6. Ask the stale-page question and record the result.
7. Write `CHECKS.md` and `README.md`.

## Risks

- **Wrong folder.** If `COURSE_DIR` points somewhere else, the index is tiny and every answer is a refusal. Assumption: the course clone sits beside this repo. Blast radius: every answer.
- **Embedding model mismatch.** If the index is built with one model and the question is embedded with another, the scores are meaningless. Behavior 5 guards it.
- **Refusal wording drift.** The model may paraphrase the refusal ("I couldn't find..."), which the eval would mark as a fail. The prompt gives the exact line.
- **Top 4 misses part of a spread answer.** The late-day policy may sit in sections that don't both rank in the top 4. The printed chunks will show it.
- **Stale pages.** Two pages that disagree can both be retrieved; there is no rule for which wins (intent decision). Observed in step 6, not fixed.
- **Heading-only sections.** Three sections in the documents are a heading with nothing under it (`syllabus.md › Trinity College`, `syllabus.md › Department of Computer Science`, `weeks/01/setup.md › 2. Install Git and Claude Code`). As chunks they would carry no answer but could still take a retrieval slot. The indexer skips them (spec behavior 2). A size cutoff would be wrong: three other short sections hold real answers, such as the Finals Week dates.
- **Running outside the `.venv`.** The Mac's built-in `python3` has no numpy. `ask.py` catches the import error and prints "Run with .venv/bin/python (see README)" instead of a traceback.
- **Python 3.9.** No `match` and no `X | Y` hints; checked before every run.

## Proof

| Step | Proof |
|---|---|
| 1 | `.venv/bin/python -c "import numpy; print(numpy.__version__)"` prints a version. |
| 2 | One embedding call returns 1,536 numbers; with the key unset, the program names the missing variable and makes no request. |
| 3 | The indexer prints 15 files and about 135 chunks, with the smallest, median and largest chunk size (expected median about 580 characters, no chunk that is only a heading); `index.json` exists; one label spot-checked by hand. |
| 4 | A due-date question prints 4 chunks with scores and an answer that cites a label; a question about something the course never covers prints exactly "I can't find that in the course documents." One question is also ranked with a plain-Python four-line cosine, and its top 4 must match numpy's. |
| 5 | **The five-question eval**, run with retrieval and without it; both tables recorded in `CHECKS.md`. |
| 6 | The answer to the MiMo question and the chunks it cited, recorded in `CHECKS.md`. |
| 7 | README lists every graded item. |

## Questions I asked before approving

1. **"How big is one chunk, and why that size?"** About 580 characters at the median (about 135 chunks from the 15 files), because splitting at headings keeps one topic per chunk and gives each chunk its citation; the 2,000-character cap affects only 4 long sections (three in the syllabus, one in the Week 1 setup page), whose single embedding would blur several topics. The answer exposed three heading-only sections. Corrected: the spec now skips them, step 3's proof prints chunk sizes, and the risk is listed above.
2. **"Why this library, and what does it do that we'd otherwise write ourselves?"** numpy stacks all chunk embeddings into one matrix and scores every chunk against the question in one line; by hand it is a four-line cosine function in a loop. Speed is not the reason at 138 chunks; readability of the ranking step and the setup's package-manager requirement are. The cost is an install and a `.venv`. Corrected: a risk for running outside the `.venv`, and a step 4 proof that numpy and the hand-written cosine pick the same top 4.

## Subagents and parallel work

None. The program is small and each step depends on the one before it.

**Approved by:** Lane Faison, October 21, 2026
