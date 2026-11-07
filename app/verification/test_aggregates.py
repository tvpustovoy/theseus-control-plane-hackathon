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


class DiscountStageTests(unittest.TestCase):
    def test_request_marker_needs_all_filters(self):
        claims = [
            claim("Клиент запрашивает отчёт без цены.", fact="status", source="training", sha="t9", sid="9"),
            claim("Клиент просит скидку на тариф.", fact="need", source="sales", sha="s7", sid="7"),
        ]
        agg = culture_aggregates(claims)
        self.assertEqual(agg["discount"]["requests_observed"], 1)

    def test_decision_alone_is_not_a_grant(self):
        claims = [
            claim("Решили по цене: перенести оплату.", fact="decision", source="sales", sha="s8", sid="8"),
            claim("Менеджер согласовал скидку клиенту.", fact="decision", source="sales", sha="s6", sid="6"),
        ]
        agg = culture_aggregates(claims)
        self.assertEqual(agg["discount"]["grants_observed"], 1)

    def test_offer_and_refusal_counted_separately(self):
        claims = [
            claim("Для партнёров скидка 30% на тариф.", fact="price", source="sales", sha="s5", sid="5"),
            claim("Скидку отказали: цена уже минимальная.", fact="decision", source="sales", sha="s4", sid="4"),
        ]
        agg = culture_aggregates(claims)
        self.assertEqual(agg["discount"]["offers_observed"], 1)
        self.assertEqual(agg["discount"]["refusals_observed"], 1)
        self.assertEqual(agg["discount"]["grants_observed"], 0)


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
