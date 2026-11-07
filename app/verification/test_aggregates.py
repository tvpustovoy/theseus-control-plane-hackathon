"""Unit tests for deterministic culture aggregates (synthetic claims)."""

import unittest

from app.verification.aggregates import culture_aggregates, scenario_mapping


def claim(text, kind="observation", fact="price", source="sales", sha="s1", sid="1"):
    return {
        "claim": text,
        "claim_kind": kind,
        "fact_type": fact,
        "quote": text,
        "provenance": {"kind": source, "text_sha256": sha, "source_id": sid},
    }


CLAIMS = [
    claim("Менеджер просит скидку 20% для филиала.", source="founder", sha="f1", sid="79523"),
    claim("Основатель одобрил скидку решением.", fact="decision", source="founder", sha="f1", sid="79523"),
    claim("Продавец называет цену за филиал.", source="sales", sha="s9", sid="960"),
    claim("Норматив по отзывам.", kind="normative_rule", fact="training_rule", source="training", sha="t1", sid="298"),
]


class AggregatesTests(unittest.TestCase):
    def test_counts_with_denominators(self):
        agg = culture_aggregates(CLAIMS)
        self.assertEqual(agg["claims_total"], 4)
        self.assertEqual(agg["sources_total"], 3)
        self.assertEqual(agg["by_source_kind"]["founder"], 2)

    def test_scenario_mapping(self):
        mapping = scenario_mapping(CLAIMS)
        self.assertEqual(mapping["S01_commit_founder_principle"]["claim_count"], 2)
        self.assertEqual(
            mapping["S01_commit_founder_principle"]["source_ids"], ["79523"]
        )
        self.assertGreaterEqual(
            mapping["S02_culture_discount_practice"]["example_claim_count"], 1
        )


if __name__ == "__main__":
    unittest.main()
