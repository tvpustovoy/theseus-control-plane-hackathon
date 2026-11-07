"""Lossless RecPlace raw importer, multiset digest verifier, and deterministic source builder."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from database.adapter import IngestionAdapter
from database.schema import (
    DEFAULT_ORGANIZATION_ID,
    EXPECTED_RAW_TABLE_COUNTS,
    RAW_TABLES,
    ContractError,
    normalize_decimal_string,
    sha256_hex,
    utc_now_iso,
)

IMPORTER_VERSION = "0.1.0"
CANONICALIZATION_PROTOCOL = "theseus-raw-canonical-v1"
MAPPING_VERSION = "0.1.0"


def canonical_logical_record_digest(
    source_table: str,
    dump_id: Optional[str],
    src_file: Optional[str],
    src_row_decimal: Optional[str],
    loaded_at_value: Optional[str],
    loaded_at_type: str,
    v_json: Optional[str],
) -> str:
    """
    Compute the deterministic SHA-256 hex digest of a single logical `raw.*` row
    under protocol `theseus-raw-canonical-v1`.
    Preserves nulls, exact decimal strings, and exact `v_json` text without float rounding.
    """
    norm_row = normalize_decimal_string(src_row_decimal)
    canonical_obj = {
        "protocol": CANONICALIZATION_PROTOCOL,
        "source_table": source_table,
        "dump_id": dump_id,
        "src_file": src_file,
        "src_row_decimal": norm_row,
        "loaded_at": {
            "value": loaded_at_value,
            "source_type": loaded_at_type or "TIMESTAMP",
        },
        "v_json_sha256": sha256_hex(v_json),
        "v_json_is_null": v_json is None,
    }
    serialized = json.dumps(canonical_obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_multiset_digest(record_digests: Iterable[str]) -> str:
    """
    Compute the aggregate SHA-256 digest of a sorted multiset of logical record digests.
    Preserves duplicate records (each occurrence contributes to the sorted sequence).
    """
    sorted_hashes = sorted(record_digests)
    joined = "\n".join(sorted_hashes)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def classify_recplace_source_type(
    source_table: str,
    src_file: Optional[str],
    v_parsed: Optional[Dict[str, Any]],
    doc_hint: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Deterministically map a raw RecPlace record to `sources.source_type`:
    - `sales_conversation`
    - `normative`
    - `founder_meeting`
    - `crm_record`
    - `unknown` (never silently mapped to `sales_conversation`)

    Verified against live `firn-duckdb` `raw.CORPUS_MANIFEST` (`basket`, `agreed_category`, `source_kind`)
    and `raw.EPISODES` / `raw.EPISODES_TEXT` (`kind`):
    - `01-sales-training`, `02-product-kb-wiki` -> `normative`
    - `03-founder-insights` -> `founder_meeting`
    - `04-sales-calls` -> `sales_conversation`
    - `90-engagement-context`, `99-public-context` -> `unknown`
    - `raw.EPISODES` / `raw.EPISODES_TEXT` with `kind in {'deal', 'crm'}` -> `crm_record`
    - `raw.EPISODES` / `raw.EPISODES_TEXT` with `kind in {'chat', 'call', 'meeting', 'archive', 'note'}` -> `sales_conversation`
    """
    if source_table in {"raw.CRM_CLIENTS", "raw.CRM_DEALS", "raw.CRM_DEAL_STAGE_EVENTS"}:
        return "crm_record"

    basket = ""
    source_kind = ""
    ep_kind = ""
    if doc_hint:
        basket = str(doc_hint.get("BASKET") or doc_hint.get("basket") or "").lower()
        source_kind = str(doc_hint.get("SOURCE_KIND") or doc_hint.get("source_kind") or "").lower()
        ep_kind = str(doc_hint.get("kind") or "").lower()
    if v_parsed and isinstance(v_parsed, dict):
        basket = basket or str(v_parsed.get("basket") or v_parsed.get("BASKET") or "").lower()
        source_kind = source_kind or str(
            v_parsed.get("source_kind") or v_parsed.get("SOURCE_KIND") or ""
        ).lower()
        ep_kind = ep_kind or str(v_parsed.get("kind") or "").lower()

    # Exact live `raw.CORPUS_MANIFEST` baskets
    if basket in {"01-sales-training", "02-product-kb-wiki"}:
        return "normative"
    if basket == "03-founder-insights":
        return "founder_meeting"
    if basket == "04-sales-calls":
        return "sales_conversation"
    if basket in {"90-engagement-context", "99-public-context"}:
        return "unknown"

    # Exact live `raw.EPISODES` / `raw.EPISODES_TEXT` kinds
    if source_table in {"raw.EPISODES", "raw.EPISODES_TEXT"} and ep_kind:
        if ep_kind in {"deal", "crm"}:
            return "crm_record"
        if ep_kind in {"chat", "call", "meeting", "archive", "note"}:
            return "sales_conversation"

    file_lower = (src_file or "").lower()
    combined = f"{basket} {source_kind} {ep_kind} {file_lower}"

    if any(tok in combined for tok in ("normative", "script", "canon", "price", "reglament", "training", "manual", "kb-wiki")):
        return "normative"
    if any(tok in combined for tok in ("founder", "board", "strategy_call", "founders")):
        return "founder_meeting"
    if any(tok in combined for tok in ("sales", "episode", "dialog", "call", "chat", "client_call")):
        return "sales_conversation"

    return "unknown"


def extract_text_and_metadata_from_v(
    source_table: str,
    v_json: Optional[str],
) -> Tuple[Optional[str], Dict[str, Any], Optional[str], Optional[str], str]:
    """
    Unpack `V` JSON string losslessly without LLM calls or semantic filtering.
    Returns `(text, metadata, day, client_ref, truncation_status)`.
    """
    if v_json is None:
        return None, {"v_is_null": True}, None, None, "complete"

    try:
        parsed = json.loads(v_json)
    except Exception:
        # Preserve raw string as text if V is non-object JSON or raw text
        return v_json, {"raw_unparsed": True}, None, None, "complete"

    if not isinstance(parsed, dict):
        return v_json, {"json_type": type(parsed).__name__}, None, None, "complete"

    # Inspect actual candidate text keys in V without discarding structure
    text_candidates = ("text", "body_text", "BODY_TEXT", "content", "transcript", "utterance_text", "message")
    extracted_text: Optional[str] = None
    for key in text_candidates:
        val = parsed.get(key)
        if isinstance(val, str) and val.strip():
            extracted_text = val
            break

    # For structured CRM records or manifest rows without a free-text body, serialize canonical JSON
    if extracted_text is None:
        extracted_text = v_json

    day = parsed.get("day") or parsed.get("DAY") or parsed.get("date") or parsed.get("created_date")
    if day is not None:
        day = str(day)

    client_ref = (
        parsed.get("client_id")
        or parsed.get("CLIENT_ID")
        or parsed.get("deal_id")
        or parsed.get("DEAL_ID")
        or parsed.get("episode_id")
        or parsed.get("EPISODE_ID")
    )
    if client_ref is not None:
        client_ref = str(client_ref)

    is_truncated = bool(parsed.get("is_truncated") or parsed.get("truncated") or parsed.get("IS_TRUNCATED"))
    truncation_status = "truncated_at_source" if is_truncated else "complete"

    metadata = {
        "source_table": source_table,
        "v_top_level_keys": sorted(parsed.keys()),
    }
    return extracted_text, metadata, day, client_ref, truncation_status


class RawRecPlaceImporter:
    """
    Executes and verifies lossless transfer of the 7 RecPlace `raw.*` tables into `raw_records`,
    produces a private manifest and a sanitized public verification summary, and builds `sources`.
    """

    def __init__(
        self,
        adapter: IngestionAdapter,
        private_dir: Optional[Path] = None,
    ) -> None:
        self.adapter = adapter
        self.private_dir = Path(private_dir) if private_dir else None

    def import_and_verify_batches(
        self,
        source_snapshot: str,
        table_batches: Dict[str, List[Dict[str, Any]]],
        counts_before: Dict[str, int],
        counts_after_source: Dict[str, int],
        import_run_id: Optional[str] = None,
        doc_hints_by_key: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Run a complete verified import from provided table rows, comparing source vs target
        counts and sorted multiset digests per table, then building `sources` in MongoDB.
        """
        tables = list(table_batches.keys())
        prev_auto_save = getattr(self.adapter.backend, "auto_save", None)
        if prev_auto_save is not None:
            setattr(self.adapter.backend, "auto_save", False)
        try:
            run_doc = self.adapter.start_import_run(
                source_snapshot=source_snapshot,
                tables=tables,
                importer_version=IMPORTER_VERSION,
                import_run_id=import_run_id,
            )
            run_id = run_doc["_id"]

            source_digests_by_table: Dict[str, List[str]] = {}
            source_multiset_digest: Dict[str, str] = {}
            target_multiset_digest: Dict[str, str] = {}
            target_counts: Dict[str, int] = {}
            errors: List[str] = []

            for table in tables:
                rows = table_batches.get(table, [])
                row_hashes: List[str] = []
                for r in rows:
                    loaded_at = r.get("loaded_at_source")
                    if isinstance(loaded_at, dict):
                        l_val = loaded_at.get("value")
                        l_type = loaded_at.get("source_type", "TIMESTAMP")
                    else:
                        l_val = str(loaded_at) if loaded_at is not None else None
                        l_type = r.get("loaded_at_source_type", "TIMESTAMP")

                    h = canonical_logical_record_digest(
                        source_table=table,
                        dump_id=r.get("dump_id"),
                        src_file=r.get("src_file"),
                        src_row_decimal=r.get("src_row_decimal"),
                        loaded_at_value=l_val,
                        loaded_at_type=l_type,
                        v_json=r.get("v_json"),
                    )
                    row_hashes.append(h)

                source_digests_by_table[table] = row_hashes
                source_multiset_digest[table] = compute_multiset_digest(row_hashes)

                normalized_rows = [{**r, "source_table": table} for r in rows]
                self.adapter.write_raw_record_batch(import_run_id=run_id, records=normalized_rows)

                stored_docs = self.adapter.backend.find_many(
                    "raw_records",
                    {
                        "organization_id": self.adapter.organization_id,
                        "import_run_id": run_id,
                        "source_table": table,
                    },
                )
                target_counts[table] = len(stored_docs)
                stored_hashes = [
                    canonical_logical_record_digest(
                        source_table=d["source_table"],
                        dump_id=d.get("dump_id"),
                        src_file=d.get("src_file"),
                        src_row_decimal=d.get("src_row_decimal"),
                        loaded_at_value=(d.get("loaded_at_source") or {}).get("value"),
                        loaded_at_type=(d.get("loaded_at_source") or {}).get("source_type", "TIMESTAMP"),
                        v_json=d.get("v_json"),
                    )
                    for d in stored_docs
                ]
                target_multiset_digest[table] = compute_multiset_digest(stored_hashes)

                if counts_before.get(table) != counts_after_source.get(table):
                    errors.append(
                        f"source_changed_during_export:{table}(before={counts_before.get(table)},after={counts_after_source.get(table)})"
                    )
                if target_counts[table] != counts_before.get(table):
                    errors.append(
                        f"row_count_mismatch:{table}(source={counts_before.get(table)},target={target_counts[table]})"
                    )
                if source_multiset_digest[table] != target_multiset_digest[table]:
                    errors.append(f"multiset_digest_mismatch:{table}")

            status = "completed" if not errors else "incomplete"
            finished_run = self.adapter.finish_import_run(
                import_run_id=run_id,
                status=status,
                counts_before=counts_before,
                counts_after=target_counts,
                table_digests=target_multiset_digest,
                errors=errors,
            )

            sources_built = 0
            if finished_run["status"] == "completed":
                sources_built = self.build_sources_from_raw(
                    import_run_id=run_id,
                    doc_hints_by_key=doc_hints_by_key,
                )
        finally:
            if prev_auto_save is not None:
                setattr(self.adapter.backend, "auto_save", prev_auto_save)
            if hasattr(self.adapter.backend, "flush"):
                self.adapter.backend.flush()

        public_summary = {
            "import_run_id": run_id,
            "organization_id": self.adapter.organization_id,
            "importer_version": IMPORTER_VERSION,
            "canonicalization_protocol": CANONICALIZATION_PROTOCOL,
            "source_snapshot": source_snapshot,
            "status": finished_run["status"],
            "counts_before": counts_before,
            "counts_after_source": counts_after_source,
            "counts_imported": target_counts,
            "source_multiset_digests": source_multiset_digest,
            "target_multiset_digests": target_multiset_digest,
            "all_digests_match": source_multiset_digest == target_multiset_digest,
            "sources_built_count": sources_built,
            "facts_created_count": 0,  # RAW_IMPORT_VERIFIED never fabricates facts
            "errors": finished_run["errors"],
            "completed_at": finished_run["completed_at"],
        }

        if self.private_dir:
            self.private_dir.mkdir(parents=True, exist_ok=True)
            private_manifest = {
                **public_summary,
                "per_table_record_digests": source_digests_by_table,
            }
            (self.private_dir / f"manifest-{run_id}.json").write_text(
                json.dumps(private_manifest, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        return public_summary

    def build_sources_from_raw(
        self,
        import_run_id: str,
        doc_hints_by_key: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> int:
        """
        Deterministically build `sources` from `raw_records` in MongoDB without LLM calls.
        Preserves `raw_record_ids`, `text_sha256`, and routes unknown sources to `unknown`.
        """
        doc_hints_by_key = doc_hints_by_key or {}
        raw_docs = self.adapter.backend.find_many(
            "raw_records",
            {
                "organization_id": self.adapter.organization_id,
                "import_run_id": import_run_id,
            },
            sort_key="record_key",
        )

        # Index raw.CORPUS_MANIFEST by raw_path and raw.EPISODES by id for exact cross-table provenance linking
        manifest_by_raw_path: Dict[str, Tuple[str, Dict[str, Any]]] = {}
        episode_by_id: Dict[str, Tuple[str, Dict[str, Any]]] = {}

        for raw_doc in raw_docs:
            v_json = raw_doc.get("v_json")
            if v_json is None and raw_doc.get("v_blob_ref"):
                v_json = self.adapter.backend.load_blob(raw_doc["v_blob_ref"])
            if not isinstance(v_json, str):
                continue
            try:
                loaded = json.loads(v_json)
            except Exception:
                continue
            if not isinstance(loaded, dict):
                continue
            if raw_doc["source_table"] == "raw.CORPUS_MANIFEST":
                rp = loaded.get("raw_path")
                if isinstance(rp, str) and rp:
                    manifest_by_raw_path[rp] = (raw_doc["_id"], loaded)
            elif raw_doc["source_table"] == "raw.EPISODES":
                ep_id = loaded.get("id")
                if ep_id is not None:
                    episode_by_id[str(ep_id)] = (raw_doc["_id"], loaded)

        built = 0
        for raw_doc in raw_docs:
            v_json = raw_doc.get("v_json")
            if v_json is None and raw_doc.get("v_blob_ref"):
                v_json = self.adapter.backend.load_blob(raw_doc["v_blob_ref"])

            parsed_v: Optional[Dict[str, Any]] = None
            if isinstance(v_json, str):
                try:
                    loaded = json.loads(v_json)
                    if isinstance(loaded, dict):
                        parsed_v = loaded
                except Exception:
                    parsed_v = None

            hint = dict(doc_hints_by_key.get(raw_doc["record_key"]) or {})
            raw_record_ids = [raw_doc["_id"]]

            # Link raw.CORPUS_TEXTS <-> raw.CORPUS_MANIFEST via raw_path
            if raw_doc["source_table"] == "raw.CORPUS_TEXTS" and parsed_v:
                rp = parsed_v.get("raw_path")
                if isinstance(rp, str) and rp in manifest_by_raw_path:
                    m_id, m_obj = manifest_by_raw_path[rp]
                    if m_id not in raw_record_ids:
                        raw_record_ids.append(m_id)
                    hint.setdefault("basket", m_obj.get("basket"))
                    hint.setdefault("source_kind", m_obj.get("source_kind"))
                    hint.setdefault("agreed_category", m_obj.get("agreed_category"))

            # Link raw.EPISODES_TEXT <-> raw.EPISODES via episode_id == id
            if raw_doc["source_table"] == "raw.EPISODES_TEXT" and parsed_v:
                ep_id = parsed_v.get("episode_id")
                if ep_id is not None and str(ep_id) in episode_by_id:
                    e_id, e_obj = episode_by_id[str(ep_id)]
                    if e_id not in raw_record_ids:
                        raw_record_ids.append(e_id)
                    hint.setdefault("kind", e_obj.get("kind"))

            source_type = classify_recplace_source_type(
                source_table=raw_doc["source_table"],
                src_file=raw_doc.get("src_file"),
                v_parsed=parsed_v,
                doc_hint=hint,
            )
            text, metadata, day, client_ref, truncation_status = extract_text_and_metadata_from_v(
                source_table=raw_doc["source_table"],
                v_json=v_json,
            )
            metadata.update(
                {
                    "dump_id": raw_doc.get("dump_id"),
                    "src_file": raw_doc.get("src_file"),
                    "src_row_decimal": raw_doc.get("src_row_decimal"),
                    "record_key": raw_doc["record_key"],
                }
            )
            if hint:
                metadata["linked_hint"] = {
                    k: hint[k] for k in ("basket", "source_kind", "agreed_category", "kind") if k in hint and hint[k] is not None
                }
            source_id = f"src:{sha256_hex(raw_doc['record_key'])[:20]}"
            self.adapter.register_source(
                source_id=source_id,
                source_type=source_type,
                raw_record_ids=raw_record_ids,
                text=text,
                original_source_metadata=metadata,
                source_version="v1",
                mapping_version=MAPPING_VERSION,
                day=day,
                client_ref=client_ref,
                truncation_status=truncation_status,
                import_run_id=import_run_id,
            )
            built += 1
        return built

    def run_live_mcp_import(
        self,
        mcp_client: "FirnDuckDbMcpClient",
        tables: Optional[List[str]] = None,
        source_snapshot: Optional[str] = None,
        import_run_id: Optional[str] = None,
        public_evidence_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Execute a full live lossless import from `firn-duckdb` MCP into the configured `IngestionAdapter`:
        1. Snapshot `counts_before` across all 7 `raw.*` tables.
        2. Adaptively paginate each table under the 1,000-row / 50,000-char MCP guard.
        3. Snapshot `counts_after_source` to detect any source mutation during export.
        4. Verify per-table row counts and sorted multiset digests, build `sources`, and write
           both the private manifest (`database/private/`) and the sanitized public summary.
        """
        target_tables = list(tables or RAW_TABLES)
        snap = source_snapshot or f"firn-duckdb-live-{utc_now_iso()}"
        cache_dir = (self.private_dir / "table_cache") if self.private_dir else None
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            counts_before = {t: mcp_client.fetch_table_count(t) for t in target_tables}
            table_batches: Dict[str, List[Dict[str, Any]]] = {}
            for t in target_tables:
                safe_t = t.replace(".", "_")
                cache_file = (cache_dir / f"{safe_t}.json") if cache_dir else None
                if cache_file and cache_file.exists():
                    try:
                        cached_rows = json.loads(cache_file.read_text(encoding="utf-8"))
                        if isinstance(cached_rows, list) and len(cached_rows) == counts_before[t]:
                            table_batches[t] = cached_rows
                            continue
                    except Exception:
                        pass
                rows = mcp_client.fetch_raw_table_rows_adaptive(
                    table=t,
                    expected_count=counts_before[t],
                    partial_cache_path=(cache_dir / f"{safe_t}.partial.jsonl") if cache_dir else None,
                )
                table_batches[t] = rows
                if cache_file:
                    cache_file.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            counts_after_source = {t: mcp_client.fetch_table_count(t) for t in target_tables}
        finally:
            mcp_client.close()

        summary = self.import_and_verify_batches(
            source_snapshot=snap,
            table_batches=table_batches,
            counts_before=counts_before,
            counts_after_source=counts_after_source,
            import_run_id=import_run_id,
        )
        if public_evidence_path:
            public_evidence_path = Path(public_evidence_path)
            public_evidence_path.parent.mkdir(parents=True, exist_ok=True)
            public_evidence_path.write_text(
                json.dumps(summary, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        return summary


class FirnDuckDbMcpClient:
    """
    Read-only MCP client wrapper for `/Users/taraspustovoy/Projects/recplace-data-app/mcp-launcher <key_path>`.
    Respects SQL guard limits (max 1000 rows, max 50000 serialized chars, no `json_keys` calls).
    """

    def __init__(self, launcher_path: Path, key_path: Path) -> None:
        self.launcher_path = Path(launcher_path)
        self.key_path = Path(key_path)
        if not self.launcher_path.is_file():
            raise ContractError("mcp_launcher_missing", f"Launcher not found at {self.launcher_path}")
        if not self.key_path.is_file():
            raise ContractError("mcp_key_missing", f"Scoped key file not found at {self.key_path}")
        self._proc: Optional[subprocess.Popen[str]] = None
        self._req_id: int = 1

    def _ensure_proc(self) -> subprocess.Popen[str]:
        if self._proc is not None and self._proc.poll() is None:
            return self._proc
        proc = subprocess.Popen(
            [str(self.launcher_path), str(self.key_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        init_req = {
            "jsonrpc": "2.0",
            "id": self._req_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "argon-raw-importer", "version": IMPORTER_VERSION},
            },
        }
        self._req_id += 1
        assert proc.stdin is not None and proc.stdout is not None
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
        _ = proc.stdout.readline()
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        proc.stdin.flush()
        self._proc = proc
        return proc

    def close(self) -> None:
        if self._proc is not None:
            self._proc.terminate()
            self._proc = None

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        proc = self._ensure_proc()
        assert proc.stdin is not None and proc.stdout is not None
        call_req = {
            "jsonrpc": "2.0",
            "id": self._req_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        self._req_id += 1
        proc.stdin.write(json.dumps(call_req) + "\n")
        proc.stdin.flush()
        resp_line = proc.stdout.readline()
        if not resp_line:
            raise ContractError("mcp_empty_response", f"Empty response from firn-duckdb for {tool_name}")
        parsed = json.loads(resp_line)
        if "error" in parsed:
            raise ContractError("mcp_rpc_error", f"firn-duckdb RPC error: {parsed['error']}")
        result = parsed.get("result", {})
        if result.get("isError"):
            text_err = ""
            for c in result.get("content", []):
                if isinstance(c, dict) and c.get("type") == "text":
                    text_err += c.get("text", "")
            raise ContractError("mcp_tool_error", f"firn-duckdb tool {tool_name} failed: {text_err or result}")
        return result

    def execute_query(self, sql: str, limit: int = 1000) -> Dict[str, Any]:
        """Execute a read-only SQL query via `execute_query` MCP tool and parse its JSON content."""
        res = self.call_tool("execute_query", {"sql": sql, "limit": min(max(int(limit), 1), 1000)})
        for c in res.get("content", []):
            if isinstance(c, dict) and c.get("type") == "text":
                txt = c.get("text", "").strip()
                try:
                    parsed = json.loads(txt)
                    if isinstance(parsed, dict) and "rows" in parsed:
                        return parsed
                except Exception:
                    pass
        if isinstance(res, dict) and "rows" in res:
            return res
        raise ContractError("unexpected_query_response", f"Unexpected execute_query response: {res!r}")

    def fetch_table_count(self, table: str) -> int:
        if table not in RAW_TABLES:
            raise ContractError("invalid_table", f"Table {table!r} not in allowlisted RAW_TABLES.")
        out = self.execute_query(f"SELECT COUNT(*) AS cnt FROM {table}", limit=1)
        rows = out.get("rows", [])
        if rows:
            row0 = rows[0]
            if isinstance(row0, list) and row0:
                return int(row0[0])
            if isinstance(row0, dict) and row0:
                return int(next(iter(row0.values())))
        raise ContractError("unexpected_count_format", f"Could not parse COUNT(*) response for {table}: {out!r}")

    def fetch_raw_table_rows_adaptive(
        self,
        table: str,
        expected_count: Optional[int] = None,
        initial_batch_size: int = 200,
        chunk_char_size: int = 24000,
        partial_cache_path: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """
        Export all rows of a `raw.*` table losslessly through the read-only `firn-duckdb` MCP `execute_query` tool,
        respecting the 1,000-row and 50,000-serialized-character response guard without modifying or bypassing ACLs.
        - Uses deterministic ordering via `ROW_NUMBER() OVER (ORDER BY DUMP_ID NULLS FIRST, SRC_FILE NULLS FIRST, SRC_ROW NULLS FIRST, CAST(LOADED_AT AS VARCHAR) NULLS FIRST, MD5(COALESCE(CAST(V AS VARCHAR), '')))`.
        - Automatically halves batch size on 50,000-char response limit errors, and slices oversize individual `V` strings
          across `SUBSTRING(CAST(V AS VARCHAR), start, length)` calls when a single row exceeds `chunk_char_size` chars.
        - Appends each completed batch to `partial_cache_path` (JSONL) so resumed runs never re-read exported rows.
        """
        if table not in RAW_TABLES:
            raise ContractError("invalid_table", f"Table {table!r} not in allowlisted RAW_TABLES.")
        total = expected_count if expected_count is not None else self.fetch_table_count(table)
        if total == 0:
            return []

        order_expr = (
            "DUMP_ID NULLS FIRST, SRC_FILE NULLS FIRST, SRC_ROW NULLS FIRST, "
            "CAST(LOADED_AT AS VARCHAR) NULLS FIRST, MD5(COALESCE(CAST(V AS VARCHAR), ''))"
        )
        collected: List[Dict[str, Any]] = []
        if partial_cache_path and partial_cache_path.exists():
            with partial_cache_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            collected.append(json.loads(line))
                        except Exception:
                            break
            if len(collected) > total:
                collected = []
                partial_cache_path.unlink(missing_ok=True)

        cursor_rn = len(collected)
        batch_size = min(max(initial_batch_size, 1), 1000)
        char_budget = 25000

        while cursor_rn < total:
            upper_rn = min(cursor_rn + batch_size, total)
            first_rn = cursor_rn + 1
            sql = (
                "WITH numbered AS ("
                f"SELECT ROW_NUMBER() OVER (ORDER BY {order_expr}) AS rn, "
                "DUMP_ID, SRC_FILE, CAST(SRC_ROW AS VARCHAR) AS src_row_str, "
                "CAST(LOADED_AT AS VARCHAR) AS loaded_at_str, "
                "CAST(V AS VARCHAR) AS v_str, "
                "CHAR_LENGTH(CAST(V AS VARCHAR)) AS v_len "
                f"FROM {table}"
                "), windowed AS ("
                "SELECT rn, DUMP_ID, SRC_FILE, src_row_str, loaded_at_str, "
                f"CASE WHEN v_len IS NULL OR v_len <= {chunk_char_size} THEN v_str ELSE NULL END AS v_inline, "
                "v_len, "
                f"SUM(CASE WHEN v_len IS NULL OR v_len > {chunk_char_size} THEN 240 ELSE CAST(v_len * 1.25 AS INTEGER) + 240 END) "
                "OVER (ORDER BY rn) AS cum_chars "
                f"FROM numbered WHERE rn > {cursor_rn} AND rn <= {upper_rn}"
                ") "
                "SELECT rn, DUMP_ID, SRC_FILE, src_row_str, loaded_at_str, v_inline, v_len "
                f"FROM windowed WHERE cum_chars <= {char_budget} OR rn = {first_rn} ORDER BY rn"
            )
            try:
                res = self.execute_query(sql, limit=batch_size)
            except ContractError as exc:
                if batch_size > 1:
                    batch_size = max(1, batch_size // 2)
                    char_budget = max(10000, char_budget // 2)
                    continue
                raise exc

            rows = res.get("rows", [])
            if not rows:
                break

            batch_new_items: List[Dict[str, Any]] = []
            for row in rows:
                rn, dump_id, src_file, src_row_str, loaded_at_str, v_inline, v_len = row
                v_full: Optional[str]
                if v_len is None:
                    v_full = None
                elif v_inline is not None:
                    v_full = str(v_inline)
                else:
                    # Reassemble oversize V string in exact substrings of `chunk_char_size`
                    parts: List[str] = []
                    pos = 1
                    total_chars = int(v_len)
                    while pos <= total_chars:
                        sub_sql = (
                            "WITH numbered AS ("
                            f"SELECT ROW_NUMBER() OVER (ORDER BY {order_expr}) AS rn, "
                            f"CAST(V AS VARCHAR) AS v_str FROM {table}"
                            ") "
                            f"SELECT SUBSTRING(v_str, {pos}, {chunk_char_size}) "
                            f"FROM numbered WHERE rn = {int(rn)}"
                        )
                        sub_res = self.execute_query(sub_sql, limit=1)
                        sub_rows = sub_res.get("rows", [])
                        if not sub_rows or not sub_rows[0]:
                            raise ContractError(
                                "oversize_row_slice_failed",
                                f"Failed to read substring at pos={pos} for {table} rn={rn}",
                            )
                        parts.append(str(sub_rows[0][0] or ""))
                        pos += chunk_char_size
                    v_full = "".join(parts)

                item = {
                    "source_table": table,
                    "dump_id": dump_id,
                    "src_file": src_file,
                    "src_row_decimal": src_row_str,
                    "loaded_at_source": {"value": loaded_at_str, "source_type": "TIMESTAMP"},
                    "v_json": v_full,
                }
                collected.append(item)
                batch_new_items.append(item)
                cursor_rn = int(rn)

            if partial_cache_path and batch_new_items:
                partial_cache_path.parent.mkdir(parents=True, exist_ok=True)
                with partial_cache_path.open("a", encoding="utf-8") as fh:
                    for it in batch_new_items:
                        fh.write(json.dumps(it, ensure_ascii=False) + "\n")

            char_budget = 25000
            if batch_size < initial_batch_size:
                batch_size = min(initial_batch_size, max(batch_size * 2, 64))

        return collected
