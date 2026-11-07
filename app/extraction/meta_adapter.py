"""Meta Model API adapter for the extraction layer.

Talks to the Meta Model API (https://dev.meta.ai/docs) over its
Chat Completions protocol. The API key is read from the process environment
only (MODEL_API_KEY, falling back to META_API_KEY); keys are never logged,
returned, or written to disk by this module.

This adapter produces candidate extraction output plus run metadata
(model id, prompt hash, token usage) for the quote gate in
app/extraction/quote_gate.py. It does not persist anything itself.
"""

from __future__ import annotations

import json
import os
import urllib.request

API_BASE = "https://api.meta.ai/v1"
DEFAULT_MODEL = "muse-spark-1.3"  # volume text extraction; see docs/FRAME.md
KEY_ENV_VARS = ("MODEL_API_KEY", "META_API_KEY")


class MetaCredentialMissing(RuntimeError):
    """Raised when no Meta Model API credential is configured."""


def find_key() -> str | None:
    for name in KEY_ENV_VARS:
        value = os.environ.get(name)
        if value:
            return value
    return None


def require_key() -> str:
    key = find_key()
    if key is None:
        raise MetaCredentialMissing(
            "No Meta Model API credential configured: set MODEL_API_KEY "
            "(or META_API_KEY) in the private environment. The key must "
            "come from the activated Meta account and must never be placed "
            "in Git, Ours messages, or status files."
        )
    return key


def chat_completion(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    base_url: str = API_BASE,
    timeout_s: int = 120,
) -> dict:
    """Run one Chat Completions request and return the parsed response."""
    key = api_key if api_key is not None else require_key()
    payload = json.dumps({"model": model, "messages": messages}).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        return json.loads(response.read().decode("utf-8"))


def extract_json_object(content: str) -> dict:
    """Parse a model response body that must be a single JSON object."""
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("Model response is not a JSON object")
    return data
