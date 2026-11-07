"""SubQ Snap Decisions adapter for evidence review (A05).

One bounded Decisions API call (POST https://api.subq.ai/v1/systemone)
judges a claim pair against the fixed label set. The API key is read from
the process environment only and is never logged or returned. Only claim
statements and stable claim IDs are sent; raw source quotes stay private.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request

API_URL = "https://api.subq.ai/v1/systemone"
DEFAULT_MODEL = "subq-snap-1.1"
LABELS = ("consistent", "contradictory", "different_scope_time", "insufficient_evidence")


class SubQCredentialMissing(RuntimeError):
    """Raised when SUBQ_API_KEY is not configured in the environment."""


def require_key() -> str:
    key = os.environ.get("SUBQ_API_KEY")
    if not key:
        raise SubQCredentialMissing(
            "SUBQ_API_KEY is not set in the process environment. Load it "
            "from the private prep env file at call time; never place the "
            "key in Git, Ours messages, status files, or command lines."
        )
    return key


def judge_pair(claim_a: str, claim_b: str, id_a: str, id_b: str,
               model: str = DEFAULT_MODEL, timeout_s: int = 60) -> dict:
    """Run one bounded choice judgment; returns response plus latency."""
    key = require_key()
    state = (
        f"Two business statements from an evidence base must be compared.\n"
        f"Statement {id_a}: {claim_a}\n"
        f"Statement {id_b}: {claim_b}\n"
        "Decide how the two statements relate. A client's observed behavior "
        "that departs from a normative rule is not automatically a logical "
        "contradiction; choose different_scope_time when the statements "
        "operate in different scopes or roles, and insufficient_evidence "
        "when the texts alone cannot settle the relation."
    )
    body = {
        "model": model,
        "state": state,
        "questions": {
            "relation": {
                "type": "choice",
                "instructions": "Select exactly one relation label for the pair.",
                "criteria": {label: None for label in LABELS},
            }
        },
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        result = json.loads(response.read().decode("utf-8"))
    result["_latency_ms"] = round((time.monotonic() - started) * 1000)
    result["_model"] = model
    return result
