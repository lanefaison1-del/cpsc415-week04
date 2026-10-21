"""Split the course pages into labeled chunks, embed them, and save index.json."""

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

from rag_common import EMBED_MODEL, embed, fail, require_env

HERE = Path(__file__).resolve().parent
INDEX_PATH = HERE / "index.json"
EXCLUDED_ASSIGNMENTS = {"week04-rag-plan.md", "week05-vision-tests.md"}
HEADING = re.compile(r"^(#{1,3})\s+(.*\S)\s*$")
SPLIT_ABOVE = 2000
PIECE_SIZE = 1500
BATCH_SIZE = 50


def course_dir():
    raw = os.environ.get("COURSE_DIR", "../ai-integration-course")
    path = Path(raw)
    return path if path.is_absolute() else (HERE / path).resolve()


def find_documents(root):
    """The pages to index, as paths relative to the course folder."""
    docs = []
    if (root / "syllabus.md").is_file():
        docs.append("syllabus.md")
    docs += sorted("assignments/" + p.name for p in (root / "assignments").glob("*.md")
                   if p.name not in EXCLUDED_ASSIGNMENTS)
    for week in ("01", "02", "03"):
        docs += sorted("weeks/%s/%s" % (week, p.name) for p in (root / "weeks" / week).glob("*.md"))
    return docs


def sections(text):
    """Yield (heading, section text) for each heading of level 1-3, ignoring code blocks."""
    heading, lines, in_code = "", [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
        match = None if in_code else HEADING.match(line)
        if match:
            if lines:
                yield heading, "\n".join(lines)
            heading, lines = match.group(2).strip("*_ "), [line]
        else:
            lines.append(line)
    if lines:
        yield heading, "\n".join(lines)


def pieces(section):
    """Split a section over SPLIT_ABOVE characters at blank lines; each piece keeps the heading."""
    if len(section) <= SPLIT_ABOVE:
        return [section]
    first_line, rest = section.split("\n", 1)
    units = []
    for paragraph in re.split(r"\n\s*\n", rest.strip()):
        # a long bullet list has no blank lines, so split it at line breaks instead
        units += paragraph.split("\n") if len(paragraph) > PIECE_SIZE else [paragraph]
    out, current = [], ""
    for paragraph in units:
        if current and len(current) + len(paragraph) > PIECE_SIZE:
            out.append(first_line + "\n\n" + current)
            current = ""
        current = (current + "\n\n" + paragraph) if current else paragraph
    if current:
        out.append(first_line + "\n\n" + current)
    return out


def chunk_documents(root, docs):
    chunks = []
    for source in docs:
        text = (root / source).read_text(encoding="utf-8")
        for heading, section in sections(text):
            body = section.split("\n", 1)[1] if HEADING.match(section.split("\n", 1)[0]) else section
            if not body.strip():
                continue  # a heading with no text under it is not a chunk (spec behavior 2)
            label = "%s › %s" % (source, heading or "(top)")
            for piece in pieces(section.strip()):
                chunks.append({"source": source, "heading": heading, "label": label,
                               "text": label + "\n" + piece})
    return chunks


def main():
    require_env(["OPENROUTER_API_KEY"])
    root = course_dir()
    if not root.is_dir():
        fail("course folder not found: %s (set COURSE_DIR)" % root)
    docs = find_documents(root)
    if not docs:
        fail("no course pages found in %s (set COURSE_DIR)" % root)
    chunks = chunk_documents(root, docs)
    if not chunks:
        fail("the course pages in %s produced no chunks" % root)

    tokens, cost = 0, 0.0
    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]
        vectors, usage = embed([c["text"] for c in batch])
        for chunk, vector in zip(batch, vectors):
            chunk["embedding"] = vector
        tokens += usage.get("total_tokens", usage.get("prompt_tokens", 0)) or 0
        cost += usage.get("cost", 0) or 0

    index = {"embedding_model": EMBED_MODEL, "built": date.today().isoformat(),
             "documents": docs, "chunks": chunks}
    INDEX_PATH.write_text(json.dumps(index), encoding="utf-8")

    sizes = sorted(len(c["text"]) for c in chunks)
    print("Indexed %d files into %d chunks -> %s" % (len(docs), len(chunks), INDEX_PATH.name))
    print("Chunk size in characters: smallest %d, median %d, largest %d"
          % (sizes[0], sizes[len(sizes) // 2], sizes[-1]))
    print("Embedded %d tokens with %s, cost $%.6f" % (tokens, EMBED_MODEL, cost))


if __name__ == "__main__":
    sys.exit(main())
