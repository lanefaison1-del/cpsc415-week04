# Project conventions

## What this repository is

The Week 4 lab for CPSC 415: a command-line program that answers a question about the course using only the course's own Markdown pages, cites the pages it used, and says "I can't find that in the course documents" when they don't contain the answer. An indexer splits the pages into chunks and embeds them; an asker retrieves the closest chunks and answers from them. The intent is in [`intent/ask-the-course.md`](intent/ask-the-course.md) and the design in [`spec.md`](spec.md).

## Commands

```
# build: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python indexer.py
# test:  .venv/bin/python eval.py
# run:   .venv/bin/python ask.py "your question"   (add --no-retrieval for the baseline)
# lint:  none
```

## Conventions

- Language: Python; code must run on Python 3.9 or later.
- Default chat model: `minimax/minimax-m3` through OpenRouter. Embedding model: `openai/text-embedding-3-small`. Final choices and reasons are recorded in `spec.md`.
- Configuration comes only from the environment: `CHAT_BASE_URL`, `CHAT_MODEL`, `OPENROUTER_API_KEY`. No key or secret in code or in the repo.
- File naming: lowercase snake_case (`indexer.py`, `ask.py`, `questions.json`).
- Eval questions live in `questions.json`; run results go in `CHECKS.md`.

## Working rules

For an introductory lab, follow its explicitly assigned stages; the full chain below applies to major projects. Week 1 uses its own minimal repository.

- This is the Week 4 introductory lab. Stages assigned: intent, spec, and plan.
  No branches or pull requests yet. Commit to main.
- Libraries and build tools are allowed (pip or uv, Gradle or Maven). Name
  each dependency in spec.md with the reason for it. A RAG framework such as
  LangChain, LangChain4j, or Spring AI is fine, but the program must print
  the chunks it retrieved and their scores for every answer.
- The documents are the course repository at ../ai-integration-course:
  syllabus.md, assignments/, and weeks/01 through weeks/03 (the course as it
  stood before this lab). Skip weeks/04. Never copy the pages into this repo.
- Ensure all commits are authored by Lane Faison.
- Course requirement: intent and spec come before code, and `plan.md` is approved before implementation starts.
- Never commit `.env` or `.claude/settings.local.json`.

## Common mistakes

Previous bugs to avoid. Add to this list as they happen.

- The model cited excerpts by their number (`[1 › Week 3: ...]`) instead of the `file › heading` label the intent asks for. The prompt now marks excerpts `--- Excerpt N ---`, puts the label on the first line, and says to copy the full label and never cite by number.
- Plain `python3` on this Mac is 3.9 and has no numpy. Always run the programs with `.venv/bin/python`.
