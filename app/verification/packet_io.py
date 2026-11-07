"""Loader and UI summary for review-packet-v1 (Argon UI integration).

The UI should never parse a packet ad hoc: load_packet validates the
contract first and fails closed on violations, and summarize produces the
small deterministic view model (counts, verdict leaders, rule status)
without touching raw evidence.
"""

from __future__ import annotations

import json
import pathlib

from app.verification.review_packet import validate_packet


class PacketInvalid(RuntimeError):
    """Raised when a review packet violates the v1 contract."""


def load_packet(path: str | pathlib.Path) -> dict:
    packet = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    errors = validate_packet(packet)
    if errors:
        raise PacketInvalid(f"Invalid review packet {path}: {errors}")
    return packet


def summarize(packet: dict) -> dict:
    claims_by_kind: dict[str, int] = {}
    for claim in packet["claims"]:
        kind = claim.get("claim_kind") or "unknown"
        claims_by_kind[kind] = claims_by_kind.get(kind, 0) + 1

    pairs_by_status: dict[str, int] = {}
    leaders: list[dict] = []
    for pair in packet["pairs"]:
        status = pair["review_status"]
        pairs_by_status[status] = pairs_by_status.get(status, 0) + 1
        verdict = pair.get("verdict")
        if verdict:
            leaders.append(
                {
                    "pair_id": pair["pair_id"],
                    "label": verdict["label"],
                    "contradictory_probability": verdict["probabilities"].get(
                        "contradictory", 0.0
                    ),
                    "confidence": verdict["confidence"],
                    "uncertainty": verdict["uncertainty"],
                    "model": verdict["model"],
                }
            )
    leaders.sort(key=lambda item: item["contradictory_probability"], reverse=True)

    return {
        "packet_version": packet["packet_version"],
        "rule_status": packet["rule_status"],
        "approved_rule_version": packet["approved_rule_version"],
        "claims_total": len(packet["claims"]),
        "claims_by_kind": claims_by_kind,
        "pairs_total": len(packet["pairs"]),
        "pairs_by_status": pairs_by_status,
        "verdict_leaders": leaders,
    }
