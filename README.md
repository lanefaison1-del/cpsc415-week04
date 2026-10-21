# Ask the course

CPSC 415, Week 4. A command-line program that answers a question about the course using only the course's own Markdown pages, cites the page and section each part of the answer came from, and replies "I can't find that in the course documents." when the pages don't contain the answer. It prints the chunks it retrieved and their similarity scores for every answer.

The artifacts, in the order they were approved: [`intent/ask-the-course.md`](intent/ask-the-course.md), [`spec.md`](spec.md), [`plan.md`](plan.md) (approved before the first code commit), then the code, [`questions.json`](questions.json) and [`CHECKS.md`](CHECKS.md).

## How it works

1. `indexer.py` reads `syllabus.md`, `assignments/` (except the Week 4 and Week 5 sheets) and `weeks/01` to `weeks/03` from my clone of the course repository, splits each page at its headings, labels every chunk `file › heading`, embeds the chunks with `openai/text-embedding-3-small`, and saves them to `index.json`.
2. `ask.py` embeds the question with the same model, scores every chunk by cosine similarity, prints the top 4 with their scores, and sends those 4 excerpts plus the question to the chat model with instructions to answer only from them, cite their labels, and refuse with the exact line when they don't contain the answer.
3. `eval.py` runs the five questions in `questions.json` with retrieval and without it.

## Build the index and ask a question

The course repository must be cloned beside this one (`../ai-integration-course`); set `COURSE_DIR` to point somewhere else.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

export OPENROUTER_API_KEY=...                      # your OpenRouter key
export CHAT_BASE_URL=https://openrouter.ai/api/v1  # optional; this is the default
export CHAT_MODEL=minimax/minimax-m3

.venv/bin/python indexer.py
.venv/bin/python ask.py "When is the Week 3 structured-output assignment due?"
.venv/bin/python ask.py --no-retrieval "When is the Week 3 structured-output assignment due?"
.venv/bin/python eval.py
```

| Variable | Used by | Purpose |
|---|---|---|
| `OPENROUTER_API_KEY` | all three | API key; never stored in the repository |
| `CHAT_MODEL` | `ask.py`, `eval.py` | Chat model slug |
| `CHAT_BASE_URL` | all three | API base URL (default `https://openrouter.ai/api/v1`); the embeddings call uses the same base |
| `COURSE_DIR` | `indexer.py` | Course repository folder (default `../ai-integration-course`) |

`index.json` is not committed: it is about 4 MB (136 chunks × 1,536 numbers, stored as text) and `.venv/bin/python indexer.py` rebuilds it for about $0.0005. Run the programs with `.venv/bin/python`; the Mac's built-in `python3` has no numpy.

## The five questions

| # | Question | What it is there to catch |
|---|---|---|
| 1 | When is the Week 2 chat client assignment due? | A due date stated in one place |
| 2 | What percentage of the final grade is the individual portfolio worth? | A grade weight; without retrieval the model is tempted to guess a plausible number |
| 3 | At Checkpoint B of the Week 1 setup, what branch should git report? | A lab step buried in the longest setup page |
| 4 | What tag do I push for the Week 3 submission, and how many late days do I get per semester? | An answer spread across two pages (the Week 3 assignment sheet and the syllabus), so both have to be retrieved |
| 5 | Who is the teaching assistant for CPSC 415? | Something the pages never say: the only right answer is the refusal line |

## Results

| | With retrieval | Without retrieval |
|---|---|---|
| Score | **4/5** | **0/5** |
| Failed | Question 4: the chunk with the Week 3 tag ranked 8th, outside the top 4; the model answered the late days and said the tag was not confirmed | All five: declined, or invented an answer (20% for the portfolio; the real weight is 25%) |

With retrieval the program answered every single-source question correctly and refused the unanswerable one exactly; without it the same model either declined or made up a plausible wrong number. One eval run scored question 4 as a pass because the model guessed the tag from the Week 1 and Week 2 pattern; I count it as a fail. Details in [`CHECKS.md`](CHECKS.md).

## The stale page

Asked "Which Xiaomi MiMo model does this course use as the fallback or second model?", the program retrieved both conflicting pages and reported both models as current: `xiaomi/mimo-v2.5` as the instructor fallback, cited to `weeks/01/setup.md › 1. Accounts and a small budget` (the page that was not updated after the September 28 change), and `xiaomi/mimo-v2.6-flash` as the second model, cited to `weeks/03/lab.md › 4. The second model (5 minutes)`. The Week 1 chunk misled it, and nothing in either chunk says which is newer. One way to prefer the current page: tag each chunk with the week of its page and tell the model the later week wins when excerpts disagree. File dates would not work in this repository: both pages show the same last-changed date, October 19.

## What I corrected

- The intent draft cited pages by file name only. I changed citations to file name plus section heading, because `syllabus.md` is too long to search by file name.
- The spec draft indexed every assignment sheet, including the Week 4 and Week 5 sheets posted after this lab. That contradicted my intent, which puts Week 4 onward out of scope, so I cut them.
- When I asked the plan "How big is one chunk, and why?", the answer turned up three sections that are only a heading and could still take a retrieval slot. I had the spec changed to skip them before any code existed.
- One eval run scored the two-page question as a pass, but the model had guessed the Week 3 tag from the Week 1 and Week 2 pattern. I recorded it as a fail.

## One line of code I can explain

From `retrieve()` in `ask.py`, where the chunks are ranked:

```python
scores = (matrix @ q) / (np.linalg.norm(matrix, axis=1) * np.linalg.norm(q))
```

Every chunk's embedding is one row of `matrix`, and `q` is the question's embedding. `matrix @ q` multiplies the question against every row at once. Dividing by the lengths turns that into cosine similarity, which measures whether two embeddings point the same direction, not how big they are. The four highest scores become the excerpts sent to the model. I checked this line against a plain four-line cosine function and it picked the same top 4; it is also where question 4 failed, because the chunk with the Week 3 tag scored 0.451 and landed 8th.
