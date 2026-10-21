"""Run the questions in questions.json with and without retrieval and report pass/fail."""

import json
import re
from pathlib import Path

from ask import ask, load_index
from rag_common import REFUSAL, require_env

QUESTIONS_PATH = Path(__file__).resolve().parent / "questions.json"


def normalize(text):
    """Lowercase, straighten curly apostrophes, collapse whitespace."""
    return re.sub(r"\s+", " ", text.replace("’", "'").lower()).strip()


def passes(question, answer):
    """A question passes when every expected phrase appears in the answer."""
    expected = [REFUSAL] if question["kind"] == "unanswerable" else question["expect"]
    return all(normalize(phrase) in normalize(answer) for phrase in expected)


def main():
    _, model = require_env(["OPENROUTER_API_KEY", "CHAT_MODEL"])
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    index = load_index()

    runs = {}
    for use_retrieval in (True, False):
        mode = "with retrieval" if use_retrieval else "without retrieval"
        runs[mode] = []
        prompt_tokens = completion_tokens = 0
        for q in questions:
            result = ask(q["question"], model, use_retrieval=use_retrieval, index=index)
            result["passed"] = passes(q, result["answer"])
            runs[mode].append(result)
            prompt_tokens += result["usage"].get("prompt_tokens", 0) or 0
            completion_tokens += result["usage"].get("completion_tokens", 0) or 0
        passed = sum(r["passed"] for r in runs[mode])
        print("== %s: %d/%d passed (%s, tokens: prompt %d, completion %d)"
              % (mode, passed, len(questions), model, prompt_tokens, completion_tokens))
        for q, r in zip(questions, runs[mode]):
            print("  %-4s %-14s %s" % ("PASS" if r["passed"] else "FAIL", q["kind"], q["id"]))
        print()

    for mode, results in runs.items():
        for q, r in zip(questions, results):
            if r["passed"]:
                continue
            print("-- FAIL %s, %s: %s" % (q["id"], mode, q["question"]))
            print("   expected: %s" % (REFUSAL if q["kind"] == "unanswerable" else " + ".join(q["expect"])))
            print("   answer:   %s" % r["answer"].replace("\n", " ")[:400])
            for score, chunk in r["retrieved"]:
                print("   chunk:    %.3f  %s" % (score, chunk["label"]))
            print()


if __name__ == "__main__":
    main()
