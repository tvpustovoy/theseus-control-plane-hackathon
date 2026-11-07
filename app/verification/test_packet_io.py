"""Unit tests for packet loading/summaries (synthetic fixture only)."""

import pathlib
import unittest

from app.verification.packet_io import PacketInvalid, load_packet, summarize

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "database/fixtures/review-packet-synthetic.json"


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
