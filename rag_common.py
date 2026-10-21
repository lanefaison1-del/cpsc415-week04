"""Shared helpers for the indexer and the asker: settings, HTTP calls, errors."""

import json
import os
import socket
import sys
import urllib.error
import urllib.request

EMBED_MODEL = "openai/text-embedding-3-small"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
REFUSAL = "I can't find that in the course documents."
TIMEOUT_SECONDS = 60


def fail(message):
    """Print an error and stop with exit code 1."""
    print("Error: " + message, file=sys.stderr)
    sys.exit(1)


def require_env(names):
    """Return the values of the named environment variables, or stop if any is missing."""
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        fail("missing environment variable(s): " + ", ".join(missing))
    return [os.environ[name] for name in names]


def base_url():
    return os.environ.get("CHAT_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def post_json(path, payload):
    """POST a JSON body to the API and return the decoded JSON reply."""
    (key,) = require_env(["OPENROUTER_API_KEY"])
    request = urllib.request.Request(
        base_url() + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:200]
        fail("HTTP %d from %s: %s" % (error.code, path, detail))
    except (socket.timeout, TimeoutError):
        fail("no reply from %s within %d seconds" % (path, TIMEOUT_SECONDS))
    except urllib.error.URLError as error:
        if isinstance(error.reason, (socket.timeout, TimeoutError)):
            fail("no reply from %s within %d seconds" % (path, TIMEOUT_SECONDS))
        fail("could not reach %s: %s" % (base_url(), error.reason))
    try:
        return json.loads(body)
    except ValueError:
        fail("reply from %s was not JSON: %s" % (path, body[:200]))


def embed(texts):
    """Embed a list of texts. Returns (vectors, usage) with vectors in input order."""
    reply = post_json("/embeddings", {"model": EMBED_MODEL, "input": texts})
    data = reply.get("data")
    if not isinstance(data, list) or len(data) != len(texts):
        fail("the embeddings reply did not contain one vector per text")
    ordered = sorted(enumerate(data), key=lambda pair: pair[1].get("index", pair[0]))
    vectors = [item["embedding"] for _, item in ordered]
    return vectors, reply.get("usage", {})


def chat(messages, model):
    """Send one chat request. Returns (answer text, model name, usage)."""
    reply = post_json("/chat/completions", {"model": model, "messages": messages, "temperature": 0})
    choices = reply.get("choices") or []
    if not choices:
        fail("the chat reply had no choices: %s" % json.dumps(reply)[:200])
    content = (choices[0].get("message") or {}).get("content") or ""
    if not content.strip():
        fail("The model returned an empty answer. (finish_reason: %s)" % choices[0].get("finish_reason"))
    return content.strip(), reply.get("model", model), reply.get("usage", {})
