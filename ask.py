"""Answer a question about CPSC 415 from the course pages, citing the chunks used."""

import argparse
import json
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:
    print("Error: numpy is not installed for this Python. "
          "Run with .venv/bin/python (see README).", file=sys.stderr)
    sys.exit(1)

from rag_common import EMBED_MODEL, REFUSAL, chat, embed, fail, require_env

INDEX_PATH = Path(__file__).resolve().parent / "index.json"
TOP_K = 4

SYSTEM_WITH_EXCERPTS = (
    "You answer questions about CPSC 415 (AI Integration, Trinity College) using only "
    "the numbered course excerpts in the user's message. Do not use anything you know "
    "from outside the excerpts.\n"
    "- Cite every excerpt you use by its full label: the first line of the excerpt, which "
    "starts with the file path. Copy it exactly, in square brackets, for example "
    "[weeks/NN/file.md › Section heading]. Never cite an excerpt by its number.\n"
    "- If the excerpts answer only part of the question, answer that part with citations "
    "and say that the rest is not in the course documents.\n"
    "- If the excerpts do not contain the answer at all, reply with exactly this sentence "
    "and nothing else: " + REFUSAL
)
SYSTEM_NO_EXCERPTS = "You are answering a question about the CPSC 415 course (AI Integration) at Trinity College."


def load_index():
    if not INDEX_PATH.is_file():
        fail("index.json not found. Build it first: .venv/bin/python indexer.py")
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    if index.get("embedding_model") != EMBED_MODEL:
        fail("index.json was built with %s, but questions are embedded with %s. "
             "Rebuild it: .venv/bin/python indexer.py" % (index.get("embedding_model"), EMBED_MODEL))
    return index


def retrieve(question, index):
    """Return the TOP_K chunks closest to the question as (score, chunk) pairs."""
    vectors, _ = embed([question])
    q = np.array(vectors[0])
    matrix = np.array([chunk["embedding"] for chunk in index["chunks"]])
    scores = (matrix @ q) / (np.linalg.norm(matrix, axis=1) * np.linalg.norm(q))
    best = np.argsort(-scores)[:TOP_K]
    return [(float(scores[i]), index["chunks"][i]) for i in best]


def build_messages(question, retrieved):
    if retrieved is None:
        return [{"role": "system", "content": SYSTEM_NO_EXCERPTS},
                {"role": "user", "content": question}]
    excerpts = "\n\n".join("--- Excerpt %d ---\n%s" % (n, chunk["text"]) for n, (_, chunk) in enumerate(retrieved, 1))
    return [{"role": "system", "content": SYSTEM_WITH_EXCERPTS},
            {"role": "user", "content": "Excerpts:\n\n%s\n\nQuestion: %s" % (excerpts, question)}]


def ask(question, model, use_retrieval=True, index=None):
    """Run one question. Returns a dict with the answer, the retrieved chunks, model and usage."""
    retrieved = None
    if use_retrieval:
        retrieved = retrieve(question, index if index is not None else load_index())
    text, model_name, usage = chat(build_messages(question, retrieved), model)
    return {"answer": text, "retrieved": retrieved or [], "model": model_name, "usage": usage}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--no-retrieval", action="store_true",
                        help="send the question alone, with no course excerpts")
    args = parser.parse_args()
    _, model = require_env(["OPENROUTER_API_KEY", "CHAT_MODEL"])

    result = ask(args.question, model, use_retrieval=not args.no_retrieval)
    if args.no_retrieval:
        print("Retrieval: off (no excerpts sent)\n")
    else:
        print("Retrieved chunks:")
        for rank, (score, chunk) in enumerate(result["retrieved"], 1):
            print("  %d. %.3f  %s" % (rank, score, chunk["label"]))
        print()
    print(result["answer"])
    usage = result["usage"]
    print("\nmodel: %s | tokens: prompt %s, completion %s"
          % (result["model"], usage.get("prompt_tokens", "?"), usage.get("completion_tokens", "?")))


if __name__ == "__main__":
    main()
