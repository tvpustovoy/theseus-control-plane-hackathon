"""Coverage and disclosure checks for the opening Organization Memory screen."""
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import app.api.organization_memory as memory_module
from app.api.organization_memory import OrganizationMemory
from app.api.server import TheseusLocalApplication, _default_import_receipt
from database.adapter import IngestionAdapter, LocalDocumentStore
from database.schema import ContractError


class OrganizationMemoryTests(unittest.TestCase):
    def setUp(self):
        adapter = IngestionAdapter(backend=LocalDocumentStore(), organization_id="recplace")
        self.memory = OrganizationMemory(TheseusLocalApplication(adapter=adapter, backend_mode="test_store"))

    def test_overview_separates_verified_import_from_partial_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = {"all_atlas_digests_match": True, "atlas_counts_verified": {f"raw.T{i}": i for i in range(1, 8)},
                       "atlas_sources_total": 28, "atlas_verified_at": "2026-11-07T00:00:00Z"}
            (Path(tmp) / "atlas-verification-summary.json").write_text(json.dumps(receipt), encoding="utf-8")
            with patch.object(memory_module, "PRIVATE", Path(tmp)):
                overview = self.memory.overview()
        self.assertEqual(overview["snapshot"]["raw_records"], 28)
        self.assertEqual(overview["snapshot"]["state"], "verified_snapshot")
        self.assertEqual(overview["distillation"]["state"], "partial_candidate_grade")
        self.assertGreater(overview["distillation"]["candidate_text_hashes"], overview["distillation"]["distinct_source_ids"])
        self.assertEqual(overview["review"]["proven_contradictions"], 0)

    def test_source_page_exposes_metadata_but_never_client_or_raw_text(self):
        source = {"source_id": "source-1", "source_version": "v1", "source_type": "crm_record",
                  "day": None, "truncation_status": "complete", "mapping_version": "v1",
                  "client_ref": "private-client", "text": "private source text", "raw_record_ids": ["private-row"]}
        with patch.object(self.memory.controller.adapter, "list_sources", return_value={"items": [source], "next_cursor": None}):
            page = self.memory.list_sources("crm_record", None, 12)
        self.assertEqual(len(page["items"]), 1)
        self.assertNotIn("client_ref", page["items"][0])
        self.assertNotIn("text", page["items"][0])
        self.assertNotIn("raw_record_ids", page["items"][0])

    def test_missing_receipt_does_not_fabricate_verified_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("app.api.server.PRIVATE_DIR", Path(tmp)):
                receipt = _default_import_receipt()
        self.assertEqual(receipt["status"], "unverified")
        self.assertIsNone(receipt["total_raw_records"])
        self.assertFalse(receipt["all_atlas_digests_match"])

    def test_question_and_pagination_bounds(self):
        for question in ("", "x" * 601):
            with self.assertRaises(ContractError):
                self.memory.ask(question)
        with self.assertRaises(ContractError):
            self.memory.list_sources(None, None, 26)


if __name__ == "__main__":
    unittest.main()
