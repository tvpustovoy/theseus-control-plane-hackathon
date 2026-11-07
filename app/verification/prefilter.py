"""Deterministic candidate-pair prefilter for evidence review (A05).

Given candidate claims (from the extraction layer), this module:
  1. assigns stable claim IDs and deterministic topic keys,
  2. generates all pairs and classifies each pair as a review candidate or
     filtered out, with a recorded reason (duplicate evidence, no shared
     topic/scope),
  3. emits a traceable audit sample of filtered-out cross-group pairs so a
     reviewer can check for missed conflicts.

It performs no model calls and never decides a contradiction; pairs marked
as candidates still need a real review step. A pair that merely looks
conflicting stays a signal until that review happens.
"""

from __future__ import annotations

import hashlib
import itertools
import re

TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "reviews": ("отзыв", "review"),
    "price": ("цен", "стоимост", "скидк", "тариф", "бюджет", "оплат", "₽", "price", "discount"),
    "branches": ("филиал", "branch"),
    "timing": ("срок", "минут", "час", "сутк", "недел", "месяц", "deadline", "timing"),
    "terminology": ("слов", "термин", "произнос", "называ", "terminolog"),
    "preparation": ("подготов", "аудит", "платформ", "preparat", "audit"),
    "closing": ("закрыт", "закрывающ", "счёт", "счет", "реквизит", "closing", "invoice"),
    "discount_approval": ("согласова", "пф", "approv"),
}


def claim_id(index: int, claim: dict) -> str:
    digest = hashlib.sha256(
        (claim.get("quote", "") + "|" + claim.get("claim", "")).encode("utf-8")
    ).hexdigest()[:10]
    return f"C{index + 1:02d}-{digest}"


def topic_keys(claim: dict) -> set[str]:
    text = (claim.get("claim", "") + " " + claim.get("quote", "")).lower()
    keys: set[str] = set()
    for topic, words in TOPIC_KEYWORDS.items():
        if any(word in text for word in words):
            keys.add(topic)
    return keys


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def classify_pairs(claims: list[dict]) -> dict:
    """Split all claim pairs into candidates and filtered-out, with reasons."""
    ids = [claim_id(i, claim) for i, claim in enumerate(claims)]
    topics = [topic_keys(claim) for claim in claims]
    candidates: list[dict] = []
    filtered: list[dict] = []

    for (i, a), (j, b) in itertools.combinations(enumerate(claims), 2):
        pair = {"pair_id": f"{ids[i]}__{ids[j]}", "a": ids[i], "b": ids[j]}
        same_quote = a.get("quote") and a["quote"] == b.get("quote")
        same_text = normalize_text(a.get("claim", "")) == normalize_text(b.get("claim", ""))
        if same_quote or same_text:
            filtered.append({**pair, "reason": "duplicate_evidence"})
            continue
        shared = topics[i] & topics[j]
        if not shared:
            filtered.append({**pair, "reason": "no_shared_topic"})
            continue
        cross_kind = a.get("claim_kind") != b.get("claim_kind")
        candidates.append(
            {
                **pair,
                "shared_topics": sorted(shared),
                "cross_kind": cross_kind,
                "reason": "shared_topic",
            }
        )

    # Strongest first: cross-kind pairs (observation vs normative rule) with
    # the most shared topics are the most promising genuine review inputs.
    candidates.sort(key=lambda p: (p["cross_kind"], len(p["shared_topics"])), reverse=True)
    return {"candidates": candidates, "filtered": filtered, "claim_ids": ids}


def audit_sample(filtered: list[dict], claims_by_id: dict[str, dict], size: int = 8) -> list[dict]:
    """Pick filtered-out pairs that cross source kinds for manual audit."""
    cross = [
        pair
        for pair in filtered
        if claims_by_id[pair["a"]].get("provenance", {}).get("kind")
        != claims_by_id[pair["b"]].get("provenance", {}).get("kind")
    ]
    return cross[:size]
