# Intent: Ask the course

## Goal

A command-line program that answers a question about CPSC 415 using only the course's own Markdown pages, cites the page and section it used for each part of the answer, and replies "I can't find that in the course documents" when the pages don't contain the answer.

## Who it is for

A CPSC 415 student, starting with me. Today, finding a due date, a grade weight, or a lab step means digging through the course repository on GitHub or through Moodle by hand.

## Constraints

- Python, runnable on Python 3.9.
- Models are called through OpenRouter with my existing key: one embedding model for the pages and the question, one chat model for the answer.
- Indexing every page costs under one cent; one question costs a fraction of a cent.
- The pages are read from my clone of the course repository (`../ai-integration-course`): `syllabus.md`, `assignments/`, and `weeks/01` through `weeks/03`. They are never copied into this repository.
- Every answer prints the chunks it was given and their similarity scores.

## Not in scope

- A web page or chat window; this is a command-line program.
- Moodle, the slides, PDFs, and anything outside the course's Markdown pages.
- `weeks/04` and later.
- Remembering earlier questions.
- Fixing out-of-date pages. When two pages disagree, I observe what happens.

## Success looks like

- A due-date question gets the right date, with its citation.
- A question the pages cannot answer gets exactly "I can't find that in the course documents."
- Every answer shows which chunks were used and their scores.
- Citations name the file and the section heading, for example `weeks/03/lab.md › 4. The second model`, so I can go straight to the spot.

## Decisions from the interview

- A citation is the file name plus the section heading, not the file name alone; `syllabus.md` is too long to search by hand.
- When the pages answer only part of a question, the program answers that part, cites it, and says the rest is not in the course documents.
- When two pages disagree, there is no special rule: the program answers from the closest chunks. Step 4 of the lab observes what that does.

## Open questions

None.

**Approved by:** Lane Faison, October 21, 2026
