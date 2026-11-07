"""Unit tests for the deterministic pair prefilter (synthetic claims)."""

import unittest

from app.verification.prefilter import audit_sample, classify_pairs


def make_claim(text, quote, kind="observation", source="sales"):
    return {
        "claim": text,
        "quote": quote,
        "claim_kind": kind,
        "provenance": {"kind": source},
    }


CLAIMS = [
    make_claim("Клиент отказывается от ответов на отзывы.", "quote about reviews one"),
    make_claim(
        "Норматив: отвечать на отзывы в первые сутки.",
        "quote about reviews two",
        kind="normative_rule",
        source="training",
    ),
    make_claim("Цена за филиал составляет 20 000.", "quote about price one"),
    make_claim("Цена за филиал составляет 20 000.", "quote about price one"),
]


class PrefilterTests(unittest.TestCase):
    def test_duplicate_filtered_and_conflict_candidate_kept(self):
        result = classify_pairs(CLAIMS)
        reasons = {(p["a"], p["b"]): p["reason"] for p in result["filtered"]}
        self.assertIn("duplicate_evidence", reasons.values())
        candidate_pairs = {(p["a"], p["b"]) for p in result["candidates"]}
        ids = result["claim_ids"]
        self.assertIn((ids[0], ids[1]), candidate_pairs)

    def test_cross_kind_candidate_ranked_first(self):
        result = classify_pairs(CLAIMS)
        self.assertTrue(result["candidates"][0]["cross_kind"])

    def test_audit_sample_prefers_cross_source(self):
        result = classify_pairs(CLAIMS)
        by_id = dict(zip(result["claim_ids"], CLAIMS))
        sample = audit_sample(result["filtered"], by_id, size=2)
        for pair in sample:
            kinds = {
                by_id[pair["a"]]["provenance"]["kind"],
                by_id[pair["b"]]["provenance"]["kind"],
            }
            self.assertEqual(len(kinds), 2)


if __name__ == "__main__":
    unittest.main()
