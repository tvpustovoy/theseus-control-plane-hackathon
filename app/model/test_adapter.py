"""Unit tests for Argon ↔ Muse Ingestion Contract v0.1, quote gate, version/org isolation, and lossless raw importer."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from app.model.adapter import seed_synthetic_recplace_store
from app.model.versioning import VersionedModelService
from database.adapter import LARGE_PAYLOAD_BYTES_THRESHOLD, IngestionAdapter, LocalDocumentStore
from database.importer import RawRecPlaceImporter, canonical_logical_record_digest, compute_multiset_digest
from database.schema import ContractError, sha256_hex

ROOT = Path(__file__).resolve().parents[2]


class IngestionAdapterContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.store = LocalDocumentStore(
            persist_path=self.tmp_path / "store.json",
            blob_dir=self.tmp_path / "blobs",
        )
        self.adapter = IngestionAdapter(backend=self.store, organization_id="recplace")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_reads_blocked_before_completed_import_run(self) -> None:
        with self.assertRaises(ContractError) as ctx:
            self.adapter.list_sources()
        self.assertEqual(ctx.exception.code, "import_not_completed")

    def test_lossless_raw_import_nulls_decimals_duplicates_and_large_blobs(self) -> None:
        importer = RawRecPlaceImporter(adapter=self.adapter, private_dir=self.tmp_path / "private")
        huge_decimal = "12345678901234567890123456789012345678"  # 38 digits, would lose precision in float64
        large_text = "АБВГД" * ((LARGE_PAYLOAD_BYTES_THRESHOLD // 5) + 500)
        large_v_json = json.dumps({"basket": "sales", "text": large_text}, ensure_ascii=False)

        batches = {
            "raw.EPISODES": [
                # Record 1: 38-digit decimal + null fields
                {
                    "dump_id": None,
                    "src_file": None,
                    "src_row_decimal": huge_decimal,
                    "loaded_at_source": {"value": None, "source_type": "TIMESTAMP"},
                    "v_json": None,
                },
                # Record 2: duplicate (table, dump, file, row) with distinct content -> stored with occurrence=1
                {
                    "dump_id": "D1",
                    "src_file": "sales/ep1.json",
                    "src_row_decimal": "42",
                    "loaded_at_source": {"value": "2026-11-07T01:00:00Z", "source_type": "TIMESTAMP"},
                    "v_json": json.dumps({"basket": "sales", "text": "Первый вариант записи разговора с клиентом."}),
                },
                {
                    "dump_id": "D1",
                    "src_file": "sales/ep1.json",
                    "src_row_decimal": "42",
                    "loaded_at_source": {"value": "2026-11-07T02:00:00Z", "source_type": "TIMESTAMP"},
                    "v_json": json.dumps({"basket": "sales", "text": "Второй вариант с тем же ключом источника."}),
                },
                # Record 3: large payload > 8MB -> externalized to blob ref without truncation
                {
                    "dump_id": "D1",
                    "src_file": "sales/huge_ep.json",
                    "src_row_decimal": "99",
                    "loaded_at_source": {"value": "2026-11-07T03:00:00Z", "source_type": "TIMESTAMP"},
                    "v_json": large_v_json,
                },
            ]
        }
        counts = {"raw.EPISODES": 4}
        summary = importer.import_and_verify_batches(
            source_snapshot="test-snap-1",
            table_batches=batches,
            counts_before=counts,
            counts_after_source=counts,
            import_run_id="import-test-1",
        )
        self.assertEqual(summary["status"], "completed")
        self.assertTrue(summary["all_digests_match"])
        self.assertEqual(summary["counts_imported"]["raw.EPISODES"], 4)
        self.assertEqual(summary["sources_built_count"], 4)
        self.assertEqual(summary["facts_created_count"], 0)

        # Idempotent re-run of same import_run_id does not duplicate records
        rerun = self.adapter.write_raw_record_batch(
            import_run_id="import-test-1",
            records=[{**r, "source_table": "raw.EPISODES"} for r in batches["raw.EPISODES"][:2]],
        )
        self.assertEqual(rerun["inserted_count"], 0)
        self.assertEqual(rerun["idempotent_skips"], 2)

        # Float src_row_decimal is explicitly rejected
        with self.assertRaises(ContractError) as ctx:
            self.adapter.write_raw_record_batch(
                import_run_id="import-test-1",
                records=[
                    {
                        "source_table": "raw.EPISODES",
                        "dump_id": "D1",
                        "src_file": "f",
                        "src_row_decimal": 12.34,
                        "v_json": "{}",
                    }
                ],
            )
        self.assertEqual(ctx.exception.code, "invalid_decimal_type")

    def test_source_drift_marks_import_incomplete(self) -> None:
        importer = RawRecPlaceImporter(adapter=self.adapter)
        batches = {
            "raw.CRM_CLIENTS": [
                {
                    "dump_id": "D1",
                    "src_file": "crm.json",
                    "src_row_decimal": "1",
                    "loaded_at_source": "2026-11-07T00:00:00Z",
                    "v_json": '{"client_id":"C1"}',
                }
            ]
        }
        summary = importer.import_and_verify_batches(
            source_snapshot="drift-snap",
            table_batches=batches,
            counts_before={"raw.CRM_CLIENTS": 1},
            counts_after_source={"raw.CRM_CLIENTS": 2},  # Source changed during export
            import_run_id="import-drift",
        )
        self.assertEqual(summary["status"], "incomplete")
        self.assertEqual(summary["sources_built_count"], 0)

    def test_unknown_source_not_mapped_to_sales_and_truncated_source_rejected(self) -> None:
        seed_synthetic_recplace_store(self.adapter)
        self.adapter.register_source(
            source_id="src-mystery",
            source_type="unknown",
            raw_record_ids=["raw:1"],
            text="Неизвестный документ без корзины и классификации.",
            original_source_metadata={"note": "unclassified"},
            source_version="v1",
        )
        unknown_list = self.adapter.list_sources(source_type="unknown")
        self.assertEqual(len(unknown_list["items"]), 1)
        self.assertEqual(unknown_list["items"][0]["source_id"], "src-mystery")

        sales_ids = {s["source_id"] for s in self.adapter.list_sources(source_type="sales_conversation")["items"]}
        self.assertNotIn("src-mystery", sales_ids)

        # Register a truncated source and verify get_source raises explicit error instead of returning partial copy
        self.adapter.register_source(
            source_id="src-truncated",
            source_type="sales_conversation",
            raw_record_ids=["raw:2"],
            text="Обрезанный текст...",
            original_source_metadata={},
            source_version="v1",
            truncation_status="truncated_at_source",
        )
        with self.assertRaises(ContractError) as ctx:
            self.adapter.get_source("src-truncated", "v1")
        self.assertEqual(ctx.exception.code, "source_truncated")

    def test_full_muse_extraction_workflow_and_rejection_gates(self) -> None:
        seed_synthetic_recplace_store(self.adapter)
        sales_sources = self.adapter.list_sources(source_type="sales_conversation")["items"]
        self.assertEqual(len(sales_sources), 1)
        source_id = sales_sources[0]["source_id"]
        source_doc = self.adapter.get_source(source_id, "v1")
        source_text = source_doc["text"]

        # 1. Reject chunk with mismatched text slice or wrong source_version
        with self.assertRaises(ContractError) as ctx:
            self.adapter.put_chunks(
                source_id=source_id,
                version="v999",
                chunks=[{"chunk_id": "ch0", "char_start": 0, "char_end": len(source_text), "text": source_text}],
                chunker_version="chunker-v1",
            )
        self.assertEqual(ctx.exception.code, "stale_version")

        with self.assertRaises(ContractError) as ctx:
            self.adapter.put_chunks(
                source_id=source_id,
                version="v1",
                chunks=[{"chunk_id": "ch0", "char_start": 0, "char_end": 10, "text": "Неверный кусок"}],
                chunker_version="chunker-v1",
            )
        self.assertEqual(ctx.exception.code, "chunk_text_mismatch")

        # 2. Valid put_chunks
        put_res = self.adapter.put_chunks(
            source_id=source_id,
            version="v1",
            chunks=[
                {
                    "chunk_id": "ch0",
                    "char_start": 0,
                    "char_end": len(source_text),
                    "text": source_text,
                    "text_sha256": sha256_hex(source_text),
                }
            ],
            chunker_version="chunker-v1",
        )
        self.assertEqual(put_res["chunk_ids"], ["ch0"])

        # 3. Start extraction run (and verify idempotency on identical input_hash)
        run1 = self.adapter.start_extraction(
            source_id=source_id,
            source_version="v1",
            prompt_version="sales-v1",
            model="muse-spark-1.3",
            input_hash=sha256_hex(source_text),
        )
        self.assertFalse(run1["idempotent_reuse"])
        run_id = run1["run_id"]

        run1_dup = self.adapter.start_extraction(
            source_id=source_id,
            source_version="v1",
            prompt_version="sales-v1",
            model="muse-spark-1.3",
            input_hash=sha256_hex(source_text),
        )
        self.assertTrue(run1_dup["idempotent_reuse"])
        self.assertEqual(run1_dup["run_id"], run_id)

        # 4. Write claim batch mixing valid candidate and invalid items:
        #    - Valid assert with exact 15..300 char substring quote
        #    - Fabricated quote not present in source text -> rejected
        #    - Quote too short (< 15 chars) -> rejected
        #    - Wrong source_version -> rejected
        #    - Wrong organization_id -> rejected
        #    - Attempt to auto-promote extraction_status="accepted" -> rejected
        valid_quote = "мы зафиксируем для вас скидку 15 процентов до пятницы без дополнительных согласований"
        # Match exact case in source_text: "Мы зафиксируем для вас скидку 15 процентов до пятницы без дополнительных согласований."
        exact_quote = "Мы зафиксируем для вас скидку 15 процентов до пятницы без дополнительных согласований."

        batch_res = self.adapter.write_claim_batch(
            run_id=run_id,
            chunk_id="ch0",
            asserts=[
                {
                    "claim": "Менеджер пообещал клиенту зафиксировать скидку 15% до пятницы без дополнительных согласований.",
                    "fact_type": "promise",
                    "knowledge_state": "known",
                    "quote": exact_quote,
                    "speaker_role": "seller",
                    "zone": "pricing",
                    "subzone": "discount_authority",
                    "target_q": ["Q3", "Q4", "Q5"],
                    "business_fields": {
                        "amount": 15,
                        "currency": "PERCENT",
                        "date": None,
                        "counterparty_role": "client",
                        "authority_scope": "unapproved_promise",
                    },
                },
                {
                    "claim": "Выдуманная цитата, которой нет в исходнике.",
                    "fact_type": "promise",
                    "knowledge_state": "known",
                    "quote": valid_quote,  # lowercase 'м' does not match exact 'М' in sales_conversation
                    "target_q": ["Q4"],
                },
                {
                    "claim": "Слишком короткая цитата.",
                    "fact_type": "observation",
                    "knowledge_state": "known",
                    "quote": "Менеджер:",
                    "target_q": [],
                },
                {
                    "claim": "Неверная версия источника.",
                    "fact_type": "observation",
                    "knowledge_state": "known",
                    "source_version": "v2",
                    "quote": exact_quote,
                    "target_q": [],
                },
                {
                    "claim": "Чужая организация.",
                    "fact_type": "observation",
                    "knowledge_state": "known",
                    "organization_id": "other-org",
                    "quote": exact_quote,
                    "target_q": [],
                },
                {
                    "claim": "Попытка сразу записать accepted в обход проверки человеком.",
                    "fact_type": "rule",
                    "knowledge_state": "known",
                    "extraction_status": "accepted",
                    "quote": exact_quote,
                    "target_q": [],
                },
            ],
            refs=[],
            signals=[
                {
                    "kind": "possible_conflict",
                    "description": "Обещана скидка 15% без согласования при нормативном пороге 5%.",
                    "quote": "скидку 15 процентов до пятницы без дополнительных согласований",
                }
            ],
        )

        self.assertEqual(len(batch_res["accepted_candidate_ids"]), 1)
        self.assertEqual(len(batch_res["rejected_items"]), 5)
        self.assertEqual(len(batch_res["stored_signal_ids"]), 1)

        reasons = [r["reason"] for r in batch_res["rejected_items"]]
        self.assertTrue(any("quote_gate_failed:quote_not_found_in_chunk_text" in r for r in reasons))
        self.assertTrue(any("quote_gate_failed:quote_length_out_of_bounds" in r for r in reasons))
        self.assertTrue(any("stale_version" in r for r in reasons))
        self.assertTrue(any("organization_mismatch" in r for r in reasons))
        self.assertTrue(any("forbidden_status_promotion" in r for r in reasons))

        # 5. Top-level cross-organization call is denied
        with self.assertRaises(ContractError) as ctx:
            self.adapter.write_claim_batch(
                run_id=run_id,
                chunk_id="ch0",
                asserts=[],
                organization_id="intruder-org",
            )
        self.assertEqual(ctx.exception.code, "permission_denied")

        # 6. Finish extraction run and query related claims
        receipt = self.adapter.finish_extraction(
            run_id=run_id,
            usage={"input_tokens": 180, "output_tokens": 95},
            status="completed",
        )
        self.assertEqual(receipt["accepted_candidate_count"], 1)
        self.assertEqual(receipt["rejected_item_count"], 5)

        related = self.adapter.get_related_claims(
            source_id=source_id,
            subject_keys=["Q4", "pricing"],
            scope={"extraction_status": "candidate"},
        )
        self.assertEqual(related["count"], 1)
        stored_claim = related["claims"][0]
        self.assertEqual(stored_claim["extraction_status"], "candidate")
        self.assertEqual(stored_claim["quote_gate"]["mode"], "exact_substring")

        # 7. Versioned model snapshot, provenance trace, and ModelDiff without overwriting v1
        model_svc = VersionedModelService(self.adapter)
        snap_v1 = model_svc.assemble_snapshot(
            version="v1",
            included_claim_ids=[stored_claim["_id"]],
            summary_note="Initial baseline model v1",
        )
        self.assertEqual(snap_v1["version"], "v1")
        self.assertIn(stored_claim["_id"], snap_v1["frame_5x2"]["Relationships"])

        # Attempting to overwrite v1 must fail
        with self.assertRaises(ContractError) as ctx:
            model_svc.assemble_snapshot(version="v1", included_claim_ids=[])
        self.assertEqual(ctx.exception.code, "version_already_exists")

        # Provenance trace links claim -> chunk -> source -> raw_records
        prov = model_svc.trace_claim_provenance(stored_claim["_id"])
        self.assertEqual(prov["source"]["source_id"], source_id)
        self.assertEqual(len(prov["raw_records"]), 1)
        self.assertEqual(prov["raw_records"][0]["source_table"], "raw.EPISODES")

        # Assemble v2 with an additional normative rule claim and compute ModelDiff (v1 -> v2)
        norm_source = self.adapter.list_sources(source_type="normative")["items"][0]
        norm_doc = self.adapter.get_source(norm_source["source_id"], "v1")
        norm_text = norm_doc["text"]
        self.adapter.put_chunks(
            source_id=norm_source["source_id"],
            version="v1",
            chunks=[{"chunk_id": "n0", "char_start": 0, "char_end": len(norm_text), "text": norm_text}],
            chunker_version="chunker-v1",
        )
        norm_run = self.adapter.start_extraction(
            source_id=norm_source["source_id"],
            source_version="v1",
            prompt_version="normative-v1",
            model="muse-spark-1.3",
            input_hash=sha256_hex(norm_text),
        )
        norm_quote = norm_text[:45] if len(norm_text) >= 45 else norm_text
        norm_batch = self.adapter.write_claim_batch(
            run_id=norm_run["run_id"],
            chunk_id="n0",
            asserts=[
                {
                    "claim": "Максимальная скидка без согласования составляет 5 процентов.",
                    "fact_type": "rule",
                    "knowledge_state": "known",
                    "quote": norm_quote,
                    "zone": "pricing",
                    "target_q": ["Q3"],
                }
            ],
        )
        rule_claim_id = norm_batch["accepted_candidate_ids"][0]
        snap_v2 = model_svc.assemble_snapshot(
            version="v2",
            parent_version="v1",
            included_claim_ids=[stored_claim["_id"], rule_claim_id],
            summary_note="Added normative discount rule",
        )
        self.assertEqual(snap_v2["parent_version"], "v1")
        diff = model_svc.compute_model_diff("v1", "v2")
        self.assertEqual(diff["added_ids"], [rule_claim_id])
        self.assertIn(rule_claim_id, diff["affected_rules"])
        self.assertIn(rule_claim_id, diff["affected_tools"])

    def test_cli_json_interface_end_to_end(self) -> None:
        store_file = self.tmp_path / "cli_store.json"
        seed_proc = subprocess.run(
            [sys.executable, "-m", "app.model.adapter", "--store", str(store_file), "seed-synthetic"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        seed_out = json.loads(seed_proc.stdout)
        self.assertEqual(seed_out["status"], "completed")
        self.assertEqual(seed_out["sources_built_count"], 7)

        list_proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "app.model.adapter",
                "--store",
                str(store_file),
                "call",
                "list_sources",
                '{"source_type": "normative", "limit": 5}',
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        list_out = json.loads(list_proc.stdout)
        self.assertEqual(len(list_out["items"]), 2)

    def test_adaptive_mcp_pagination_and_oversize_row_reassembly(self) -> None:
        """Verify that FirnDuckDbMcpClient adaptive pagination handles batch halving and >30k char V slicing."""
        oversize_v = json.dumps({"basket": "sales", "text": "Я" * 45000}, ensure_ascii=False)
        fake_rows = [
            (1, "D1", "sales/c1.json", "1", "2026-11-07T00:00:00", '{"basket":"sales","text":"Короткая запись 1"}', 45),
            (2, "D1", "sales/c2.json", "2", "2026-11-07T00:01:00", oversize_v, len(oversize_v)),
        ]

        class FakeMcpClient:
            def __init__(self) -> None:
                self.calls = 0

            def close(self) -> None:
                pass

            def fetch_table_count(self, table: str) -> int:
                return len(fake_rows)

            def execute_query(self, sql: str, limit: int = 1000) -> dict:
                self.calls += 1
                # Simulate 50,000-char AccessDenied when initial batch_size > 1
                if limit > 1 and "SELECT rn, DUMP_ID" in sql:
                    raise ContractError("mcp_tool_error", "Simulated 50000-char limit exceeded")
                if "SELECT rn, DUMP_ID" in sql:
                    for r in fake_rows:
                        if f"rn > {r[0] - 1} AND rn <= {r[0]}" in sql:
                            rn, d_id, s_file, s_row, l_at, v_str, v_len = r
                            v_inline = v_str if v_len <= 30000 else None
                            return {"rows": [[rn, d_id, s_file, s_row, l_at, v_inline, v_len]]}
                    return {"rows": []}
                if "SELECT SUBSTRING(v_str," in sql:
                    # Parse pos and chunk_char_size
                    import re

                    m = re.search(r"SUBSTRING\(v_str,\s*(\d+),\s*(\d+)\)", sql)
                    assert m is not None
                    pos = int(m.group(1))
                    length = int(m.group(2))
                    return {"rows": [[oversize_v[pos - 1 : pos - 1 + length]]]}
                return {"rows": []}

        # Bind fetch_raw_table_rows_adaptive onto FakeMcpClient
        from database.importer import FirnDuckDbMcpClient

        fake = FakeMcpClient()
        fake.fetch_raw_table_rows_adaptive = FirnDuckDbMcpClient.fetch_raw_table_rows_adaptive.__get__(fake, FakeMcpClient)  # type: ignore

        importer = RawRecPlaceImporter(adapter=self.adapter)
        summary = importer.run_live_mcp_import(
            mcp_client=fake,  # type: ignore
            tables=["raw.EPISODES"],
            source_snapshot="mock-mcp-live-snap",
            import_run_id="import-mcp-test",
        )
        self.assertEqual(summary["status"], "completed")
        self.assertTrue(summary["all_digests_match"])
        self.assertEqual(summary["counts_imported"]["raw.EPISODES"], 2)
        self.assertEqual(summary["sources_built_count"], 2)


if __name__ == "__main__":
    unittest.main()
