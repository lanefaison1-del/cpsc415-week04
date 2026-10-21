# Spec

## Intent

Implements [`intent/ask-the-course.md`](intent/ask-the-course.md).

## Components

### Indexer (`indexer.py`)

- **What it does:** Reads the course pages from `../ai-integration-course`, splits each page into chunks at its Markdown headings, embeds every chunk, and saves the chunks with their embeddings to `index.json`.
- **Documents:** `syllabus.md`, every `.md` file in `assignments/` except `week04-rag-plan.md` and `week05-vision-tests.md`, and every `.md` file in `weeks/01`, `weeks/02` and `weeks/03`. Non-Markdown files (such as `weeks/01/sonnet18.txt`) and `weeks/04` onward are skipped. The two assignment sheets are excluded because they were posted with Week 4 and later, and the intent puts Week 4 onward out of scope: the index is the course as it stood before this lab.
- **Language:** Python 3.9 or later. **Why:** Weeks 2 and 3 were Python, so the request code and the Keychain-based key loading are already proven on my machine. Java with LangChain4j was the alternative; it would add a Gradle build and a second language for no gain on a program this small.
- **Model:** `openai/text-embedding-3-small` through OpenRouter. **Why:** It is the model the setup checkpoint used (1,536 numbers per text), the one the course's reference RAG code was rehearsed with, and it costs $0.02 per million tokens, so the whole index costs about $0.0005. Compared against `nvidia/nemotron-3-embed-1b:free`, which is free but rate-limited and gives different vector sizes; the free model is a possible later experiment, not the default.
- **Interfaces:** Run as `python indexer.py`. Optional environment variable `COURSE_DIR` (default `../ai-integration-course`). Reads `OPENROUTER_API_KEY`; the embeddings URL is `CHAT_BASE_URL` + `/embeddings` (default `https://openrouter.ai/api/v1`). Writes `index.json`: the embedding model's name, the document list, and for every chunk its `source` (file path), `heading`, `label`, `text`, and `embedding`. Prints the number of files, the number of chunks, the tokens embedded and the cost.
- **Dependencies:** see Dependencies below.

### Asker (`ask.py`)

- **What it does:** Embeds the question with the same model as the index, ranks every chunk by cosine similarity to the question, prints the four closest chunks with their scores, then asks a chat model to answer the question using only those four excerpts, with citations.
- **Language:** Python 3.9 or later. **Why:** same as the indexer; both share one helper module for the HTTP calls.
- **Model:** `minimax/minimax-m3` through OpenRouter. **Why:** In Week 3 I compared it with `xiaomi/mimo-v2.6-flash` on five classification cases; MiniMax passed all five and MiMo truncated a reply on the hardest one. It is cheap, and it is the model the course's reference RAG code was rehearsed on. A frontier model would cost more for an answer that only has to restate an excerpt.
- **Interfaces:** Run as `python ask.py "the question"`, or `python ask.py --no-retrieval "the question"` for the baseline that sends the question with no excerpts. Reads `OPENROUTER_API_KEY`, `CHAT_BASE_URL`, `CHAT_MODEL` and `index.json`. Prints the retrieved chunks, then the answer, then a usage line (model, tokens).

### Eval (`eval.py`)

- **What it does:** Runs every question in `questions.json` through the asker twice, once with retrieval and once without, checks each answer against its expected key phrases, and prints a pass/fail table for both runs plus the chunk labels retrieved for every failure.
- **Interfaces:** `questions.json` is a list of `{id, question, kind, expect}`. `kind` is `single`, `spread` or `unanswerable`. `expect` is a list of phrases that must all appear in the answer (case-insensitive); for `unanswerable` it is the refusal line.

## Dependencies

- `numpy` (installed with `pip` into a `.venv`, listed in `requirements.txt`). **Reason:** ranks all chunks against the question in one matrix operation (normalized dot products) instead of a Python loop over about 135 vectors of 1,536 numbers. Everything else uses the standard library: `urllib.request` for HTTP (the same code as Weeks 2 and 3), `json`, `pathlib`, `re`, `argparse`.

## Behavior

1. The indexer reads exactly the documents listed above from `COURSE_DIR` and never copies a page into this repository; `index.json` holds chunk text only as part of the index.
2. The indexer splits each page at headings of level 1 to 3. A section longer than 2,000 characters is split further at blank lines into pieces of at most about 1,500 characters, each keeping its heading. A section with a heading and no text under it (for example `syllabus.md › Trinity College`) is not a chunk; it is skipped, because it carries no answer but could still take one of the four retrieval slots.
3. Every chunk is labeled `file › heading`, for example `weeks/03/lab.md › 4. The second model`, and the label is the first line of the text that gets embedded.
4. The indexer embeds chunks in batches, writes `index.json`, and prints the file count, chunk count, tokens and cost. It stops with an error if it finds zero files or zero chunks.
5. The asker refuses to run if `index.json` is missing, or was built with a different embedding model, and says to run the indexer.
6. The asker ranks every chunk by cosine similarity to the question and keeps the top 4.
7. Before the answer, the asker prints the four chunks in rank order: rank, score to three decimals, and label.
8. The chat prompt gives the four excerpts numbered, each starting with its label, and tells the model to answer only from them, cite the label of every excerpt it used, and reply with exactly `I can't find that in the course documents.` when they do not contain the answer.
9. When the excerpts answer only part of the question, the answer covers that part with citations and says the rest is not in the course documents.
10. With `--no-retrieval`, no excerpts are sent and no chunks are printed; the model gets the question alone, with one line saying it is about the CPSC 415 course at Trinity College.
11. After the answer, the asker prints the model name and the prompt and completion tokens.
12. The eval runs all five questions with and without retrieval, marks each pass or fail by its expected phrases, prints both tables and the retrieved chunk labels for every failure, and exits 0 even when questions fail.

## Failure handling

- Missing `OPENROUTER_API_KEY` or `CHAT_MODEL`: print which variable is missing and exit 1, without calling the network.
- Course folder missing or empty: the indexer prints the path it tried and exits 1.
- HTTP error (401, 402, 404, 429, 5xx) or a timeout (60 seconds): print the status and the first 200 characters of the response body, exit 1. The key is never printed.
- Empty chat reply: print "The model returned an empty answer." with the `finish_reason`, exit 1.
- A reply that ignores the excerpts or invents a citation is not caught by the program; the eval and the printed chunks are how I check it.

## Cost estimate

- Index: about 22,000 tokens embedded at $0.02 per million, about $0.0005 per rebuild.
- One question: one embedding call (about 15 tokens) plus one chat call of about 1,500 prompt tokens and 150 completion tokens on `minimax/minimax-m3`, well under $0.001.
- One full eval (5 questions × 2 runs): well under one cent. A semester of use is under a dollar.

## Out of scope

Carried over from the intent: a web page, Moodle, slides and PDFs, `weeks/04` and later, remembering earlier questions, and fixing out-of-date pages. Also ruled out: a vector database (one JSON file is enough for about 135 chunks), a RAG framework (the program must print its chunks and scores, which is clearer when retrieval is our own code), and a similarity cutoff that refuses before calling the model.
