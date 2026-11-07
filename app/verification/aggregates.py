"""Deterministic culture aggregates over extracted claims (local, no calls).

Aggregates are computed only from already-extracted, quote-gated claims.
Every count carries its denominator (how many sources/claims were in
scope), so an observed pattern is never presented without its base.
Requests and granted discounts are counted separately.
"""

from __future__ import annotations

from collections import Counter

from app.verification.prefilter import topic_keys


def culture_aggregates(claims: list[dict]) -> dict:
    by_kind = Counter(c.get("claim_kind") for c in claims)
    by_fact_type = Counter(c.get("fact_type") for c in claims)
    by_source = Counter((c.get("provenance") or {}).get("kind") for c in claims)
    topics = Counter()
    for claim in claims:
        topics.update(topic_keys(claim))

    discount_claims = [c for c in claims if "price" in topic_keys(c)]
    discount_requests = [
        c for c in discount_claims
        if (c.get("provenance") or {}).get("kind") != "training"
        and c.get("fact_type") in ("price", "need")
        and "просит" in c.get("claim", "") or "запрашивает" in c.get("claim", "")
    ]
    discount_grants = [
        c for c in discount_claims
        if c.get("fact_type") == "decision"
    ]
    return {
        "claims_total": len(claims),
        "sources_total": len({(c.get("provenance") or {}).get("text_sha256") for c in claims}),
        "by_claim_kind": dict(by_kind),
        "by_fact_type": dict(by_fact_type),
        "by_source_kind": dict(by_source),
        "by_topic": dict(topics),
        "discount": {
            "claims_with_price_topic": len(discount_claims),
            "requests_observed": len(discount_requests),
            "grants_observed": len(discount_grants),
            "note": "requests and granted discounts counted separately",
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
