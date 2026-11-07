"""Unit tests for packet loading/summaries (synthetic fixture only)."""

import pathlib
import unittest

from app.verification.packet_io import PacketInvalid, load_packet, summarize

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "database/fixtures/review-packet-synthetic.json"
DISCOUNT_FIXTURE = ROOT / "database/fixtures/review-packet-subq-discount.json"


class PacketIoTests(unittest.TestCase):
    def test_public_fixture_loads_and_summarizes(self):
        packet = load_packet(FIXTURE)
        summary = summarize(packet)
        self.assertEqual(summary["packet_version"], "review-packet-v1")
        self.assertEqual(summary["rule_status"], "unapproved_training_norm")
        self.assertIsNone(summary["approved_rule_version"])
        self.assertEqual(summary["claims_total"], 2)
        self.assertEqual(summary["pairs_by_status"], {"possible_conflict": 1})
        leader = summary["verdict_leaders"][0]
        self.assertEqual(leader["label"], "contradictory")
        self.assertAlmostEqual(leader["contradictory_probability"], 0.46)

    def test_discount_packet_mixed_rule_status(self):
        packet = load_packet(DISCOUNT_FIXTURE)
        summary = summarize(packet)
        # Truthful mixed top-level: no single global rule class.
        self.assertEqual(
            summary["rule_status"], "mixed_reference_statuses_see_per_claim"
        )
        self.assertIsNone(summary["approved_rule_version"])
        self.assertEqual(
            packet["active_reference_version"],
            "mandate-v1 (flexible seller discounts baseline)",
        )
        self.assertIn("UNAPPROVED", packet["proposed_reference_version"])
        self.assertEqual(sum(packet["status_breakdown"].values()), 9)
        # Every claim carries its own mandate status and stage.
        for claim in packet["claims"]:
            self.assertTrue(claim["mandate_status"])
            self.assertTrue(claim["stage"])
        # No pair is presented as a proven contradiction.
        self.assertEqual(
            summary["pairs_by_status"], {"reviewed_no_proven_contradiction": 5}
        )
        for leader in summary["verdict_leaders"]:
            self.assertNotEqual(leader["label"], "contradictory")
            self.assertLess(leader["contradictory_probability"], 0.1)

    def test_invalid_packet_fails_closed(self):
        bad = {"packet_version": "review-packet-v1", "claims": [], "pairs": []}
        import tempfile, json

        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False
        ) as fh:
            json.dump(bad, fh)
            path = fh.name
        with self.assertRaises(PacketInvalid):
            load_packet(path)


if __name__ == "__main__":
    unittest.main()
