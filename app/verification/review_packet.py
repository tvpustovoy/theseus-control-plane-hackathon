"""Versioned review packet for Argon's UI (A05 continuation).

A review packet bundles traceable claim references, candidate pair verdicts
(probabilities plus uncertainty), and private evidence references. It carries
no raw source text: evidence_ref points to a private artifact and the exact
span/hash inside it, so the UI can render everything except the quote itself
unless it has private access.

Contract: review-packet-v1. A verdict label alone is never a proven
contradiction; packets keep the review status explicit.
"""

from __future__ import annotations

import hashlib

PACKET_VERSION = "review-packet-v1"
SCHEMA_VERSION = 1
VERDICT_LABELS = ("consistent", "contradictory", "different_scope_time", "insufficient_evidence")
PROVENANCE_LABEL = "Muse Code exploratory"


def artifact_ref(path: str, content: bytes) -> dict:
    return {"artifact": path, "sha256": hashlib.sha256(content).hexdigest()}


def claim_entry(claim_id: str, claim: dict) -> dict:
    locator = claim.get("evidence_locator") or {}
    provenance = claim.get("provenance") or {}
    return {
        "claim_id": claim_id,
        "claim_kind": claim.get("claim_kind"),
        "fact_type": claim.get("fact_type"),
        "knowledge_state": claim.get("knowledge_state"),
        "source_kind": provenance.get("kind"),
        "provenance_label": PROVENANCE_LABEL,
        "source_ref": {
            "source_id": provenance.get("source_id"),
            "source_text_sha256": provenance.get("text_sha256"),
            "dump_id": provenance.get("dump_id"),
            "src_file": provenance.get("src_file"),
            "src_row": provenance.get("src_row"),
        },
        "evidence_ref": {
            "quote_sha256": locator.get("quote_sha256"),
            "char_start": locator.get("char_start"),
            "char_end": locator.get("char_end"),
        },
    }


def pair_entry(pair: dict, verdict: dict | None) -> dict:
    entry = {
        "pair_id": pair["pair_id"],
        "a": pair["a"],
        "b": pair["b"],
        "shared_topics": pair.get("shared_topics", []),
        "review_status": "possible_conflict" if verdict else "unreviewed",
        "verdict": None,
    }
    if verdict:
        probabilities = verdict["probabilities"]
        entry["verdict"] = {
            "label": verdict["choice"],
            "probabilities": probabilities,
            "confidence": verdict["confidence"],
            "uncertainty": round(1.0 - verdict["confidence"], 6),
            "model": verdict["model"],
        }
    return entry


def build_packet(claims_by_id: dict, candidate_pairs: list, verdicts: dict,
                 scope: dict, generated_from: list[dict]) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "packet_version": PACKET_VERSION,
        # Training norms in this packet are observed source statements, not an
        # approved binding codex; encode that explicitly instead of implying it.
        "approved_rule_version": None,
        "rule_status": "unapproved_training_norm",
        "scope": scope,
        "generated_from": generated_from,
        "claims": [claim_entry(cid, c) for cid, c in claims_by_id.items()],
        "pairs": [
            pair_entry(pair, verdicts.get(pair["pair_id"])) for pair in candidate_pairs
        ],
    }


def validate_packet(packet: dict) -> list[str]:
    """Return contract violations; empty means the packet is well-formed."""
    errors: list[str] = []
    if packet.get("packet_version") != PACKET_VERSION:
        errors.append("unknown_packet_version")
    claim_ids = [c["claim_id"] for c in packet.get("claims", [])]
    if len(claim_ids) != len(set(claim_ids)):
        errors.append("duplicate_claim_id")
    if "approved_rule_version" not in packet or "rule_status" not in packet:
        errors.append("missing_rule_status")
    for claim in packet.get("claims", []):
        ref = claim.get("source_ref") or {}
        if not ref.get("source_id") or not ref.get("source_text_sha256"):
            errors.append(f"claim_missing_source_ref:{claim['claim_id']}")
    known = set(claim_ids)
    for pair in packet.get("pairs", []):
        if pair["a"] not in known or pair["b"] not in known:
            errors.append(f"pair_unknown_claim:{pair['pair_id']}")
        verdict = pair.get("verdict")
        if verdict:
            if verdict["label"] not in VERDICT_LABELS:
                errors.append(f"pair_bad_label:{pair['pair_id']}")
            total = sum(verdict["probabilities"].values())
            if abs(total - 1.0) > 0.01:
                errors.append(f"pair_probabilities_not_normalized:{pair['pair_id']}")
    return errors
