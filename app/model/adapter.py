#!/usr/bin/env python3
"""
JSON CLI and programmatic entrypoint for the Argon ↔ Muse ingestion contract (`database/INGESTION-CONTRACT.md` v0.1).

Usage examples for Muse.Hackathon:
  1. Seed synthetic fixture into a local store:
     python3 -m app.model.adapter --store /tmp/theseus_store.json seed-synthetic

  2. List sources:
     python3 -m app.model.adapter --store /tmp/theseus_store.json call list_sources '{"source_type": "sales_conversation", "limit": 10}'

  3. Get a source with provenance:
     python3 -m app.model.adapter --store /tmp/theseus_store.json call get_source '{"source_id": "source-sales-01", "version": "v1"}'

  4. Put chunks:
     python3 -m app.model.adapter --store /tmp/theseus_store.json call put_chunks '{"source_id": "source-sales-01", "version": "v1", "chunker_version": "chunker-v1", "chunks": [...]}'

  5. Start extraction run:
     python3 -m app.model.adapter --store /tmp/theseus_store.json call start_extraction '{"source_id": "source-sales-01", "source_version": "v1", "prompt_version": "sales-v1", "model": "muse-spark-1.3", "input_hash": "abc123"}'

  6. Write claim batch (validates quotes, enums, source_version, organization_id):
     python3 -m app.model.adapter --store /tmp/theseus_store.json call write_claim_batch '{"run_id": "...", "chunk_id": "...", "asserts": [...], "refs": [], "signals": []}'

  7. Finish extraction run:
     python3 -m app.model.adapter --store /tmp/theseus_store.json call finish_extraction '{"run_id": "...", "usage": {"input_tokens": 120, "output_tokens": 45}, "status": "completed", "errors": []}'

  8. Get related claims for SubQ review:
     python3 -m app.model.adapter --store /tmp/theseus_store.json call get_related_claims '{"source_id": "source-sales-01", "subject_keys": ["Q4", "price"], "scope": {"include_all_sources": true}}'
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from database.adapter import IngestionAdapter, LocalDocumentStore
from database.importer import FirnDuckDbMcpClient, RawRecPlaceImporter
from database.schema import DEFAULT_ORGANIZATION_ID, RAW_TABLES, ContractError


def create_adapter(
    organization_id: str = DEFAULT_ORGANIZATION_ID,
    store_path: Optional[Path] = None,
) -> IngestionAdapter:
    """Create an `IngestionAdapter` backed by MongoDB (if `MONGODB_URI` is set) or `LocalDocumentStore`."""
    if store_path is not None:
        return IngestionAdapter(
            backend=LocalDocumentStore(persist_path=Path(store_path)),
            organization_id=organization_id,
        )
    return IngestionAdapter.from_env(organization_id=organization_id)


def seed_synthetic_recplace_store(adapter: IngestionAdapter) -> Dict[str, Any]:
    """
    Seed synthetic raw RecPlace rows across the 7 tables, verify lossless import and digests,
    and build deterministic `sources` so Muse can test the full writer pipeline immediately.
    """
    importer = RawRecPlaceImporter(adapter=adapter)
    synthetic_batches = {
        "raw.CORPUS_MANIFEST": [
            {
                "dump_id": "SYNTH_DUMP_01",
                "src_file": "manifest/normative_pricing_v1.json",
                "src_row_decimal": "1",
                "loaded_at_source": {"value": "2026-11-07T00:00:00Z", "source_type": "TIMESTAMP"},
                "v_json": json.dumps(
                    {
                        "doc_id": "DOC_NORM_01",
                        "basket": "normative",
                        "source_kind": "reglament",
                        "day": "2026-11-01",
                        "text": "Регламент отдела продаж: максимальная скидка без согласования с руководителем составляет 5 процентов.",
                    },
                    ensure_ascii=False,
                ),
            }
        ],
        "raw.CORPUS_TEXTS": [
            {
                "dump_id": "SYNTH_DUMP_01",
                "src_file": "normative/sales_reglament_2026.txt",
                "src_row_decimal": "101",
                "loaded_at_source": {"value": "2026-11-07T00:00:00Z", "source_type": "TIMESTAMP"},
                "v_json": json.dumps(
                    {
                        "basket": "normative",
                        "source_kind": "training_rule",
                        "day": "2026-11-01",
                        "body_text": "По правилу компании менеджер не имеет права обещать скидку более 5% без письменного решения директора.",
                    },
                    ensure_ascii=False,
                ),
            }
        ],
        "raw.EPISODES": [
            {
                "dump_id": "SYNTH_DUMP_01",
                "src_file": "episodes/sales_call_ep_1001.json",
                "src_row_decimal": "1001",
                "loaded_at_source": {"value": "2026-11-07T00:01:00Z", "source_type": "TIMESTAMP"},
                "v_json": json.dumps(
                    {
                        "episode_id": "EP_1001",
                        "client_id": "CLI_501",
                        "basket": "sales",
                        "source_kind": "sales_call",
                        "day": "2026-11-05",
                        "text": "Менеджер: Мы зафиксируем для вас скидку 15 процентов до пятницы без дополнительных согласований.",
                    },
                    ensure_ascii=False,
                ),
            }
        ],
        "raw.EPISODES_TEXT": [
            {
                "dump_id": "SYNTH_DUMP_01",
                "src_file": "episodes_text/founder_strategy_call.json",
                "src_row_decimal": "2001",
                "loaded_at_source": {"value": "2026-11-07T00:02:00Z", "source_type": "TIMESTAMP"},
                "v_json": json.dumps(
                    {
                        "episode_id": "EP_FOUNDER_01",
                        "basket": "founder_meeting",
                        "source_kind": "founder_call",
                        "day": "2026-11-06",
                        "text": "Участник встречи предложил поднять порог самостоятельной скидки менеджера до 10 процентов в декабре.",
                    },
                    ensure_ascii=False,
                ),
            }
        ],
        "raw.CRM_CLIENTS": [
            {
                "dump_id": "SYNTH_DUMP_01",
                "src_file": "crm/clients.json",
                "src_row_decimal": "501",
                "loaded_at_source": {"value": "2026-11-07T00:03:00Z", "source_type": "TIMESTAMP"},
                "v_json": json.dumps({"client_id": "CLI_501", "segment": "B2B_SMB", "status": "active"}, ensure_ascii=False),
            }
        ],
        "raw.CRM_DEALS": [
            {
                "dump_id": "SYNTH_DUMP_01",
                "src_file": "crm/deals.json",
                "src_row_decimal": "9001",
                "loaded_at_source": {"value": "2026-11-07T00:04:00Z", "source_type": "TIMESTAMP"},
                "v_json": json.dumps(
                    {"deal_id": "DEAL_9001", "client_id": "CLI_501", "amount": 120000, "currency": "RUB", "stage": "negotiation"},
                    ensure_ascii=False,
                ),
            }
        ],
        "raw.CRM_DEAL_STAGE_EVENTS": [
            {
                "dump_id": "SYNTH_DUMP_01",
                "src_file": "crm/deal_events.json",
                "src_row_decimal": "70001",
                "loaded_at_source": {"value": "2026-11-07T00:05:00Z", "source_type": "TIMESTAMP"},
                "v_json": json.dumps(
                    {"deal_id": "DEAL_9001", "from_stage": "qualification", "to_stage": "negotiation", "day": "2026-11-05"},
                    ensure_ascii=False,
                ),
            }
        ],
    }
    counts = {k: len(v) for k, v in synthetic_batches.items()}
    summary = importer.import_and_verify_batches(
        source_snapshot="synthetic-fixture-v0.1",
        table_batches=synthetic_batches,
        counts_before=counts,
        counts_after_source=counts,
        import_run_id="import-synthetic-v0.1",
    )
    return summary


DISPATCH_METHODS = {
    "list_sources",
    "get_source",
    "put_chunks",
    "start_extraction",
    "write_claim_batch",
    "finish_extraction",
    "get_related_claims",
}


def dispatch_call(adapter: IngestionAdapter, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if method not in DISPATCH_METHODS:
        raise ContractError("unknown_method", f"Unsupported adapter method {method!r}. Allowed: {sorted(DISPATCH_METHODS)}")
    fn = getattr(adapter, method)
    return fn(**payload)


def main(argv: Optional[ list[str] ] = None) -> int:
    parser = argparse.ArgumentParser(description="Theseus Control Plane — Argon ↔ Muse Ingestion Adapter v0.1 CLI")
    parser.add_argument("--store", type=Path, default=None, help="Path to local JSON store file (when MONGODB_URI is not set)")
    parser.add_argument("--org", type=str, default=DEFAULT_ORGANIZATION_ID, help="Organization scope (default: recplace)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("seed-synthetic", help="Seed synthetic 7-table RecPlace import and build sources")

    live_parser = sub.add_parser("import-live-mcp", help="Run lossless 7-table RecPlace import via firn-duckdb MCP launcher")
    live_parser.add_argument(
        "--launcher",
        type=Path,
        default=Path("/Users/taraspustovoy/Projects/recplace-data-app/mcp-launcher"),
        help="Path to firn-duckdb mcp-launcher",
    )
    live_parser.add_argument("--key-file", type=Path, required=True, help="Path to chmod 600 client key file")
    live_parser.add_argument(
        "--private-dir",
        type=Path,
        default=Path("database/private"),
        help="Private directory for per-record manifest (gitignored)",
    )
    live_parser.add_argument(
        "--public-summary",
        type=Path,
        default=None,
        help="Optional path to write sanitized public summary JSON (counts & digests only)",
    )

    call_parser = sub.add_parser("call", help="Invoke an IngestionAdapter contract operation with JSON arguments")
    call_parser.add_argument("method", choices=sorted(DISPATCH_METHODS), help="Contract method name")
    call_parser.add_argument("json_args", nargs="?", default="{}", help="JSON object with method arguments (or '-' for stdin)")

    args = parser.parse_args(argv)
    try:
        adapter = create_adapter(organization_id=args.org, store_path=args.store)
        if args.command == "seed-synthetic":
            res = seed_synthetic_recplace_store(adapter)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        if args.command == "import-live-mcp":
            mcp_client = FirnDuckDbMcpClient(launcher_path=args.launcher, key_path=args.key_file)
            importer = RawRecPlaceImporter(adapter=adapter, private_dir=args.private_dir)
            res = importer.run_live_mcp_import(
                mcp_client=mcp_client,
                tables=list(RAW_TABLES),
                public_evidence_path=args.public_summary,
            )
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0 if res.get("status") == "completed" else 3
        if args.command == "call":
            raw_json = sys.stdin.read() if args.json_args == "-" else args.json_args
            payload = json.loads(raw_json) if raw_json.strip() else {}
            if not isinstance(payload, dict):
                raise ContractError("invalid_input", "CLI call arguments must be a JSON object.")
            res = dispatch_call(adapter, args.method, payload)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
    except ContractError as exc:
        print(json.dumps(exc.to_dict(), ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    except Exception as exc:
        print(json.dumps({"error": "internal_error", "message": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
