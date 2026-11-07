"""Quote gate and chunker for the Muse extraction layer.

Implements the local verification half of the Argon<->Muse ingestion
contract (database/INGESTION-CONTRACT.md): every candidate claim must be
supported by an exact quote from the exact source text version, quotes are
15-300 characters, and rejected items are preserved with reasons instead of
being silently dropped.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

QUOTE_MIN = 15
QUOTE_MAX = 300

FACT_TYPES = {
    "observation",
    "promise",
    "objection",
    "need",
    "price",
    "status",
    "rule",
    "decision",
    "risk",
    "prohibition",
    "canon_value",
    "definition",
    "training_rule",
}

KNOWLEDGE_STATES = {"known", "hypothesis"}


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(text: str, max_chars: int = 1800, overlap: int = 0) -> list[dict]:
    """Split text into chunks with exact char spans and per-chunk hashes.

    Boundaries prefer sentence/newline ends inside the window so quotes stay
    inside one chunk. Spans always reference the original text offsets.
    """
    chunks: list[dict] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        if end < n:
            for sep in ("\n", ". ", "! ", "? "):
                cut = text.rfind(sep, start, end)
                if cut > start + max_chars // 3:
                    end = cut + len(sep)
                    break
        piece = text[start:end]
        chunks.append(
            {
                "chunk_index": len(chunks),
                "char_start": start,
                "char_end": end,
                "text": piece,
                "text_sha256": text_sha256(piece),
            }
        )
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


@dataclass
class GateResult:
    accepted: list[dict] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)


def check_claim(claim: dict, source_text: str) -> list[str]:
    """Return a list of rejection reasons; empty means the claim passes."""
    reasons: list[str] = []
    quote = claim.get("quote")
    if not isinstance(quote, str) or not quote:
        return ["missing_quote"]
    if len(quote) < QUOTE_MIN:
        reasons.append("quote_too_short")
    if len(quote) > QUOTE_MAX:
        reasons.append("quote_too_long")
    if quote not in source_text:
        reasons.append("quote_not_exact_substring")
    if claim.get("fact_type") not in FACT_TYPES:
        reasons.append("invalid_fact_type")
    if claim.get("knowledge_state") not in KNOWLEDGE_STATES:
        reasons.append("invalid_knowledge_state")
    if not isinstance(claim.get("claim"), str) or not claim["claim"].strip():
        reasons.append("empty_claim")
    return reasons


def run_gate(claims: list[dict], source_text: str) -> GateResult:
    """Split candidate claims into accepted (span attached) and rejected."""
    result = GateResult()
    for claim in claims:
        reasons = check_claim(claim, source_text)
        if reasons:
            result.rejected.append({"claim": claim, "reasons": reasons})
            continue
        quote = claim["quote"]
        start = source_text.find(quote)
        enriched = dict(claim)
        enriched["evidence_locator"] = {
            "char_start": start,
            "char_end": start + len(quote),
            "quote_sha256": text_sha256(quote),
        }
        enriched["quote_gate"] = "pass"
        enriched["extraction_status"] = "candidate"
        result.accepted.append(enriched)
    return result


def load_jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]
