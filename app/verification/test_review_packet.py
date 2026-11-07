"""Unit tests for the review packet contract (synthetic data only)."""

import unittest

from app.verification.review_packet import build_packet, validate_packet


def synthetic_inputs():
    claims = {
        "C01-aaa": {
            "claim": "Synthetic client declines review replies.",
            "claim_kind": "observation",
            "fact_type": "objection",
            "knowledge_state": "known",
            "provenance": {"kind": "sales", "source_id": "synthetic-sales-1", "text_sha256": "t1"},
            "evidence_locator": {"quote_sha256": "q1", "char_start": 0, "char_end": 20},
        },
        "C02-bbb": {
            "claim": "Synthetic norm: reply to reviews within a day.",
            "claim_kind": "normative_rule",
            "fact_type": "training_rule",
            "knowledge_state": "known",
            "provenance": {"kind": "training", "source_id": "synthetic-training-1", "text_sha256": "t2"},
            "evidence_locator": {"quote_sha256": "q2", "char_start": 5, "char_end": 40},
        },
    }
    pairs = [
        {
            "pair_id": "C01-aaa__C02-bbb",
            "a": "C01-aaa",
            "b": "C02-bbb",
            "shared_topics": ["reviews"],
        }
    ]
    verdicts = {
        "C01-aaa__C02-bbb": {
            "choice": "contradictory",
            "probabilities": {
                "consistent": 0.01,
                "contradictory": 0.46,
                "different_scope_time": 0.40,
                "insufficient_evidence": 0.13,
            },
            "confidence": 0.29,
            "model": "subq-snap-1.1",
        }
    }
    return claims, pairs, verdicts


class ReviewPacketTests(unittest.TestCase):
    def test_packet_builds_and_validates(self):
        claims, pairs, verdicts = synthetic_inputs()
        packet = build_packet(claims, pairs, verdicts, {"pilot": "synthetic"}, [])
        self.assertEqual(validate_packet(packet), [])
        pair = packet["pairs"][0]
        self.assertEqual(pair["review_status"], "possible_conflict")
        self.assertAlmostEqual(pair["verdict"]["uncertainty"], 0.71, places=5)

    def test_no_raw_text_in_packet(self):
        claims, pairs, verdicts = synthetic_inputs()
        packet = build_packet(claims, pairs, verdicts, {}, [])
        text = str(packet)
        self.assertNotIn("quote\"", text.replace("quote_sha256", ""))

    def test_missing_source_ref_flagged(self):
        claims, pairs, verdicts = synthetic_inputs()
        claims["C01-aaa"]["provenance"] = {"kind": "sales"}
        packet = build_packet(claims, pairs, verdicts, {}, [])
        self.assertTrue(any("missing_source_ref" in e for e in validate_packet(packet)))
        self.assertIsNone(packet["approved_rule_version"])
        self.assertEqual(packet["rule_status"], "unapproved_training_norm")

    def test_bad_probabilities_flagged(self):
        claims, pairs, verdicts = synthetic_inputs()
        verdicts["C01-aaa__C02-bbb"]["probabilities"]["contradictory"] = 0.9
        packet = build_packet(claims, pairs, verdicts, {}, [])
        self.assertTrue(any("not_normalized" in e for e in validate_packet(packet)))


if __name__ == "__main__":
    unittest.main()
