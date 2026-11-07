"""Deterministic culture aggregates over extracted claims (local, no calls).

Aggregates are computed only from already-extracted, quote-gated claims.
Every count carries its denominator (how many sources/claims were in
scope), so an observed pattern is never presented without its base.
Requests, seller offers, granted discounts and refusals are counted
separately: a bare ``fact_type == "decision"`` never proves a grant, and
request markers are only counted when every other filter also holds.
"""

from __future__ import annotations

from collections import Counter

from app.verification.prefilter import topic_keys

REQUEST_WORDS = ("просит", "просят", "прошу", "запрашивает", "запрашивают", "запросил")
GRANT_WORDS = (
    "согласовал скидк", "согласована скидк", "согласовали скидк",
    "одобрил скидк", "одобрена скидк", "одобрили скидк",
    "предоставим скидк", "предоставили скидк", "предоставить скидк",
    "даём скидк", "даем скидк", "сделаем скидк", "утвердил скидк",
)
REFUSAL_WORDS = (
    "скидку отказал", "скидки отказал", "отказал в скидке", "отказали в скидке",
    "отказ в скидке", "скидку не да", "скидки не будет",
)


def discount_stage(claim: dict) -> str | None:
    """Classify one price-topic claim: request/offer/grant/refusal/None.

    Conservative by design: a customer request needs a request verb, an
    offer is a seller-stated discount term, and a grant needs an explicit
    granting verb next to the discount — a bare decision is never a grant.
    """
    text = claim.get("claim", "").lower()
    fact = claim.get("fact_type")
    if any(word in text for word in REFUSAL_WORDS):
        return "refusal"
    if fact == "decision" and any(word in text for word in GRANT_WORDS):
        return "grant"
    if any(word in text for word in REQUEST_WORDS):
        return "request"
    if fact in ("price", "promise") and "скидк" in text:
        return "offer"
    return None


def culture_aggregates(claims: list[dict]) -> dict:
    by_kind = Counter(c.get("claim_kind") for c in claims)
    by_fact_type = Counter(c.get("fact_type") for c in claims)
    by_source = Counter((c.get("provenance") or {}).get("kind") for c in claims)
    topics = Counter()
    for claim in claims:
        topics.update(topic_keys(claim))

    discount_claims = [
        c for c in claims
        if "price" in topic_keys(c)
        and (c.get("provenance") or {}).get("kind") != "training"
    ]
    stages = Counter(
        stage for stage in (discount_stage(c) for c in discount_claims) if stage
    )
    return {
        "claims_total": len(claims),
        "sources_total": len({(c.get("provenance") or {}).get("text_sha256") for c in claims}),
        "by_claim_kind": dict(by_kind),
        "by_fact_type": dict(by_fact_type),
        "by_source_kind": dict(by_source),
        "by_topic": dict(topics),
        "discount": {
            "claims_with_price_topic": len(discount_claims),
            "requests_observed": stages.get("request", 0),
            "offers_observed": stages.get("offer", 0),
            "grants_observed": stages.get("grant", 0),
            "refusals_observed": stages.get("refusal", 0),
            "note": "customer requests, seller offers, actual grants and refusals counted separately; grant needs an explicit granting verb",
        },
    }


def scenario_mapping(claims: list[dict]) -> dict:
    """Map pilot claims onto the S01/S02 demo evidence needs.

    S01 (Commit) needs the founder principle source; S02 (Culture) needs an
    observed practice with examples and counterexamples. Mapping is by
    source kind and topics only; it does not upgrade any claim's status.
    """
    s01 = [
        c for c in claims
        if (c.get("provenance") or {}).get("kind") == "founder"
    ]
    s02_examples = [
        c for c in claims
        if (c.get("provenance") or {}).get("kind") == "sales" and "price" in topic_keys(c)
    ]
    return {
        "S01_commit_founder_principle": {
            "claim_count": len(s01),
            "source_ids": sorted(
                {(c.get("provenance") or {}).get("source_id") for c in s01}
            ),
        },
        "S02_culture_discount_practice": {
            "example_claim_count": len(s02_examples),
            "denominator_claims": len(claims),
            "note": "pilot scope only (3 sources); batch-scale counts need the approved next batch",
        },
    }
