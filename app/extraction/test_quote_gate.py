"""Unit tests for the extraction quote gate (synthetic text only)."""

import unittest

from app.extraction.quote_gate import check_claim, chunk_text, run_gate

TEXT = (
    "Client asks for a 10 percent discount on the annual plan. "
    "Seller promises to confirm the price by Friday. "
    "Training rule: never promise a discount before finance approval."
)


def make_claim(quote, **overrides):
    claim = {
        "claim": "Тестовое утверждение, поддержанное цитатой.",
        "fact_type": "observation",
        "knowledge_state": "known",
        "quote": quote,
    }
    claim.update(overrides)
    return claim


class ChunkTextTests(unittest.TestCase):
    def test_spans_cover_text_and_hashes_match(self):
        chunks = chunk_text(TEXT, max_chars=60)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            piece = TEXT[chunk["char_start"] : chunk["char_end"]]
            self.assertEqual(piece, chunk["text"])

    def test_short_text_single_chunk(self):
        chunks = chunk_text("short text", max_chars=100)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["char_end"], len("short text"))


class QuoteGateTests(unittest.TestCase):
    def test_exact_quote_passes_with_span(self):
        claim = make_claim("Client asks for a 10 percent discount")
        result = run_gate([claim], TEXT)
        self.assertEqual(len(result.accepted), 1)
        self.assertEqual(result.rejected, [])
        span = result.accepted[0]["evidence_locator"]
        self.assertEqual(TEXT[span["char_start"] : span["char_end"]], claim["quote"])
        self.assertEqual(result.accepted[0]["extraction_status"], "candidate")

    def test_paraphrase_rejected(self):
        claim = make_claim("Client wants ten percent off the price")
        result = run_gate([claim], TEXT)
        self.assertEqual(result.accepted, [])
        self.assertIn("quote_not_exact_substring", result.rejected[0]["reasons"])

    def test_short_quote_rejected(self):
        claim = make_claim("discount")
        self.assertIn("quote_too_short", check_claim(claim, TEXT))

    def test_invalid_fact_type_rejected(self):
        claim = make_claim(
            "Seller promises to confirm the price", fact_type="guess"
        )
        self.assertIn("invalid_fact_type", check_claim(claim, TEXT))


class ProvenanceTests(unittest.TestCase):
    def test_src_row_type_preserved(self):
        from app.extraction.run_pilot import record_provenance

        record = {
            "dump_id": "dump",
            "src_file": "f.jsonl.gz",
            "src_row": 13933,
            "table": "raw.EPISODES_TEXT",
            "kind": "sales",
            "source_id": 960,
            "text_sha256": "abc",
        }
        provenance = record_provenance(record)
        self.assertEqual(provenance["src_row"], 13933)
        self.assertIsInstance(provenance["src_row"], int)


class MetaAdapterTests(unittest.TestCase):
    def test_missing_key_is_exact_blocker(self):
        import os

        from app.extraction import meta_adapter

        saved = {k: os.environ.pop(k, None) for k in meta_adapter.KEY_ENV_VARS}
        try:
            with self.assertRaises(meta_adapter.MetaCredentialMissing):
                meta_adapter.require_key()
        finally:
            for key, value in saved.items():
                if value is not None:
                    os.environ[key] = value

    def test_extract_json_object(self):
        from app.extraction.meta_adapter import extract_json_object

        self.assertEqual(extract_json_object('{"asserts": []}'), {"asserts": []})
        with self.assertRaises(ValueError):
            extract_json_object('["not", "an", "object"]')


if __name__ == "__main__":
    unittest.main()
