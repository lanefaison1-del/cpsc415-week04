# Checks: ask the course

All runs on October 21, 2026, with `CHAT_MODEL=minimax/minimax-m3`, `CHAT_BASE_URL=https://openrouter.ai/api/v1`, and the index built the same day from the course repository at commit `3db103e` (15 files, 136 chunks, embedded with `openai/text-embedding-3-small`: 22,533 tokens, $0.00045).

## Build checks

| Plan step | Check | Result |
|---|---|---|
| 1 | `.venv/bin/python -c "import numpy"` | Python 3.9.6, numpy 2.0.2 |
| 2 | One embedding call; then the same call with the key unset | 1,536 numbers, 11 tokens; with no key, exit 1 before any request |
| 3 | `indexer.py` | 15 files, 136 chunks; chunk size smallest 164, median 618, largest 1,955 characters; no heading-only chunks |
| 4 | "When is the Week 3 structured-output assignment due?" | Monday, October 5, 2026, 1:30 PM, cited `assignments/week03-structured-output.md › Week 3: Structured output with a five-case eval` |
| 4 | "Can I bring my dog to class?" | Exactly "I can't find that in the course documents." |
| 4 | Same question ranked with numpy and with a plain four-line cosine | Same top 4, same order |
| 4 | `ask.py` run with the Mac's built-in `python3` | "Run with .venv/bin/python (see README)", no traceback |

The first real run of step 4 cited excerpts by number (`[1 › Week 3: ...]`) instead of by `file › heading`. Fixed in the prompt before the eval; recorded under Common mistakes in `CLAUDE.md`.

## Five-question eval

`.venv/bin/python eval.py`, three runs. Runs 1 and 2 were started back to back by mistake and overlapped; both scored 4/5 with retrieval (question 4 failed) and 0/5 without. Run 3 (2:34 PM) is the run below.

| # | Question | Kind | With retrieval | Without retrieval |
|---|---|---|---|---|
| 1 | When is the Week 2 chat client assignment due? | single | PASS | FAIL: says it has no access to the course schedule |
| 2 | What percentage of the final grade is the individual portfolio worth? | single | PASS | FAIL: answers **20%** (the syllabus says 25%) |
| 3 | At Checkpoint B of the Week 1 setup, what branch should git report? | single | PASS | FAIL: guesses "`ai-integration` or a similarly named branch" (correct: `first-build`) |
| 4 | What tag do I push for the Week 3 submission, and how many late days do I get per semester? | spread | **FAIL** (scored PASS in run 3; a false pass, see below) | FAIL: says it has no access |
| 5 | Who is the teaching assistant for CPSC 415? | unanswerable | PASS: exact refusal line | FAIL: declines politely but not with the refusal line |
| | **Score** | | **4/5** | **0/5** |

Run 3 tokens: with retrieval, prompt 4,864 and completion 1,215; without, prompt 1,046 and completion 3,658. Without excerpts the model writes long "check your syllabus" answers, so it spends three times the output tokens to answer nothing.

### Question 4: a retrieval miss, and a false pass

Chunks retrieved for question 4 (the same in every run):

| Rank | Score | Chunk |
|---|---|---|
| 1 | 0.648 | `syllabus.md › Late Submission Policy` |
| 2 | 0.543 | `weeks/02/README.md › Due today at 1:30 PM` |
| 3 | 0.526 | `weeks/03/README.md › Due today at 1:30 PM` |
| 4 | 0.478 | `syllabus.md › Finals Week (December 17–23)` |
| 8 | 0.451 | `assignments/week03-structured-output.md › Week 3: Structured output with a five-case eval` (the only chunk that states `week03-submitted`) |

The late-days half of the question dominates the question's embedding, and the two "Due today" README sections, which name the Week 1 and Week 2 tags, outrank the Week 3 assignment sheet. Asked alone, "What tag do I push for the Week 3 submission?" still ranks that chunk only 6th.

The model handled the missing half honestly. Sent three more times outside the eval, it answered "3 late days" with the syllabus citation every time and said the Week 3 tag "is not explicitly stated", only that the Week 1 and Week 2 tags suggest a `week03-submitted` pattern "but this is not confirmed". Run 3 scored that as a PASS because the eval checks for phrases, and the guessed tag contains the phrase. I count it as a FAIL: the answer did not come from a retrieved chunk.

Two findings: top 4 is too few for a question with two unrelated halves, and a phrase-matching eval cannot tell a confirmed answer from a hedged guess. Neither the question nor the code was changed to make it pass.

### With retrieval versus without

Retrieval is the difference between right answers and confident wrong ones: with excerpts the model got every single-source fact right and refused the unanswerable question exactly; without them it either declined or invented a plausible number (20% for the portfolio).

Question 5 without retrieval is a fair-but-strict fail: the model did not invent a teaching assistant, but the baseline prompt never gives it the refusal line, so it cannot match.

## Stale page (lab step 4)

Question: "Which Xiaomi MiMo model does this course use as the fallback or second model?" Asked twice; both answers the same in substance.

| Rank | Score | Chunk |
|---|---|---|
| 1 | 0.510 | `weeks/03/lab.md › 4. The second model (5 minutes)` |
| 2 | 0.393 | `weeks/02/lab.md › 4. Swap the model (10 minutes)` |
| 3 | 0.377 | `weeks/01/setup.md › 1. Accounts and a small budget` |
| 4 | 0.366 | `weeks/02/setup.md › 3. Optional: a local model` |

**What it answered:** both models, as if both were current: `xiaomi/mimo-v2.5` as the "instructor fallback", cited to `weeks/01/setup.md › 1. Accounts and a small budget`, and `xiaomi/mimo-v2.6-flash` as the "second model", cited to `weeks/03/lab.md › 4. The second model (5 minutes)`.

**What misled it:** the Week 1 setup chunk, which still names `mimo-v2.5` from before the September 28 model change. Nothing in either chunk says which page is newer, so the model reconciled the conflict by giving each model a different role instead of noticing that one is out of date.

**One way to prefer the current page:** tag each chunk with the week its page belongs to and tell the model that, when excerpts disagree, the later week wins. The file's last-changed date would not work here: `git log` shows both `weeks/01/setup.md` and `weeks/03/lab.md` last changed on October 19, 2026, because later course edits touched every file. The week number in the path is the signal that actually separates the old page from the current one. Not implemented.
