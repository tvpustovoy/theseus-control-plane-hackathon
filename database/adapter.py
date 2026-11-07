"""Ingestion and storage adapter implementing database/INGESTION-CONTRACT.md v0.1."""
from __future__ import annotations

import copy
import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from database.schema import (
    COLLECTIONS,
    DEFAULT_DATABASE_NAME,
    DEFAULT_ORGANIZATION_ID,
    EXTRACTION_STATUSES,
    FACT_REF_RELATIONS,
    FACT_TYPES,
    INDEX_SPECS,
    KNOWLEDGE_STATES,
    SCHEMA_VERSION,
    SIGNAL_KINDS,
    SOURCE_TYPES,
    TARGET_Q_VALUES,
    TRUNCATION_STATUSES,
    ContractError,
    make_envelope,
    normalize_decimal_string,
    sha256_hex,
    utc_now_iso,
    validate_quote_in_text,
)

LARGE_PAYLOAD_BYTES_THRESHOLD = 8 * 1024 * 1024  # 8 MB threshold before externalizing to private blob/GridFS


class StorageBackend:
    """Abstract storage interface supporting both MongoDB and local JSON/memory persistence."""

    def ensure_indexes(self) -> None:
        raise NotImplementedError

    def insert_one(self, collection: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def upsert_by_id(self, collection: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def update_one(self, collection: str, query: Dict[str, Any], updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def find_many(
        self,
        collection: str,
        query: Dict[str, Any],
        sort_key: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def count(self, collection: str, query: Dict[str, Any]) -> int:
        raise NotImplementedError

    def store_blob(self, blob_key: str, content: str) -> str:
        raise NotImplementedError

    def load_blob(self, blob_ref: str) -> str:
        raise NotImplementedError


def _matches(doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
    for k, expected in query.items():
        val = doc.get(k)
        if isinstance(expected, dict):
            if "$in" in expected:
                if isinstance(val, list):
                    if not any(item in expected["$in"] for item in val):
                        return False
                elif val not in expected["$in"]:
                    return False
            elif "$gt" in expected:
                if val is None or not (val > expected["$gt"]):
                    return False
            elif "$gte" in expected:
                if val is None or not (val >= expected["$gte"]):
                    return False
            elif "$ne" in expected:
                if val == expected["$ne"]:
                    return False
            else:
                if val != expected:
                    return False
        else:
            if val != expected:
                return False
    return True


class LocalDocumentStore(StorageBackend):
    """
    Deterministic in-memory / JSON-file-backed store that enforces the exact
    unique index invariants of `database/indexes.mongosh.js` with O(1) index lookups.
    """

    def __init__(
        self,
        persist_path: Optional[Path] = None,
        blob_dir: Optional[Path] = None,
        auto_save: bool = True,
    ) -> None:
        self.persist_path = Path(persist_path) if persist_path else None
        self.blob_dir = Path(blob_dir) if blob_dir else None
        self.auto_save = auto_save
        self._collections: Dict[str, List[Dict[str, Any]]] = {c: [] for c in COLLECTIONS}
        self._id_index: Dict[str, Dict[str, int]] = {c: {} for c in COLLECTIONS}
        self._unique_indexes: Dict[Tuple[str, Tuple[str, ...]], Dict[Tuple[Any, ...], int]] = {}
        self._blobs: Dict[str, str] = {}
        self._dirty = False
        if self.persist_path and self.persist_path.exists():
            self._load()
        else:
            self._rebuild_indexes()

    def _rebuild_collection_index(self, coll_name: str) -> None:
        docs = self._collections.setdefault(coll_name, [])
        id_map: Dict[str, int] = {}
        for idx, d in enumerate(docs):
            doc_id = d.get("_id")
            if doc_id is not None:
                id_map[str(doc_id)] = idx
        self._id_index[coll_name] = id_map

        for spec in INDEX_SPECS.get(coll_name, []):
            if not spec.get("unique"):
                continue
            key_names = tuple(k for k, _ in spec["keys"])
            u_map: Dict[Tuple[Any, ...], int] = {}
            for idx, d in enumerate(docs):
                kt = tuple(d.get(k) for k in key_names)
                u_map[kt] = idx
            self._unique_indexes[(coll_name, key_names)] = u_map

    def _rebuild_indexes(self) -> None:
        for coll_name in list(self._collections.keys()):
            self._rebuild_collection_index(coll_name)

    def _index_doc_at(self, collection: str, idx: int, doc: Dict[str, Any]) -> None:
        doc_id = doc.get("_id")
        if doc_id is not None:
            self._id_index.setdefault(collection, {})[str(doc_id)] = idx
        for spec in INDEX_SPECS.get(collection, []):
            if not spec.get("unique"):
                continue
            key_names = tuple(k for k, _ in spec["keys"])
            kt = tuple(doc.get(k) for k in key_names)
            self._unique_indexes.setdefault((collection, key_names), {})[kt] = idx

    def _unindex_doc(self, collection: str, doc: Dict[str, Any]) -> None:
        doc_id = doc.get("_id")
        if doc_id is not None:
            self._id_index.setdefault(collection, {}).pop(str(doc_id), None)
        for spec in INDEX_SPECS.get(collection, []):
            if not spec.get("unique"):
                continue
            key_names = tuple(k for k, _ in spec["keys"])
            kt = tuple(doc.get(k) for k in key_names)
            self._unique_indexes.setdefault((collection, key_names), {}).pop(kt, None)

    def _load(self) -> None:
        if not self.persist_path or not self.persist_path.exists():
            return
        raw = json.loads(self.persist_path.read_text(encoding="utf-8"))
        for c in COLLECTIONS:
            self._collections[c] = raw.get("collections", {}).get(c, [])
        self._blobs = raw.get("blobs", {})
        self._rebuild_indexes()
        self._dirty = False

    def flush(self) -> None:
        if not self.persist_path or not self._dirty:
            return
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "updated_at": utc_now_iso(),
            "collections": self._collections,
            "blobs": self._blobs,
        }
        self.persist_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        self._dirty = False

    def _save(self) -> None:
        self._dirty = True
        if self.auto_save:
            self.flush()

    def ensure_indexes(self) -> None:
        for coll_name, specs in INDEX_SPECS.items():
            docs = self._collections.get(coll_name, [])
            for spec in specs:
                if not spec.get("unique"):
                    continue
                seen = set()
                for d in docs:
                    key_tuple = tuple(d.get(k) for k, _ in spec["keys"])
                    if key_tuple in seen:
                        raise ContractError(
                            "duplicate_key",
                            f"Unique index {spec['name']} violated on {coll_name}: {key_tuple}",
                        )
                    seen.add(key_tuple)
        self._rebuild_indexes()

    def _check_unique(self, collection: str, candidate: Dict[str, Any], ignore_id: Optional[str] = None) -> None:
        docs = self._collections.setdefault(collection, [])
        id_map = self._id_index.setdefault(collection, {})
        cand_id = str(candidate.get("_id")) if candidate.get("_id") is not None else None
        if cand_id is not None and cand_id in id_map:
            if ignore_id is None or cand_id != str(ignore_id):
                raise ContractError(
                    "duplicate_key",
                    f"Duplicate _id {candidate.get('_id')!r} in collection {collection}",
                )
        for spec in INDEX_SPECS.get(collection, []):
            if not spec.get("unique"):
                continue
            key_names = tuple(k for k, _ in spec["keys"])
            cand_tuple = tuple(candidate.get(k) for k in key_names)
            u_map = self._unique_indexes.setdefault((collection, key_names), {})
            if cand_tuple in u_map:
                existing_idx = u_map[cand_tuple]
                existing_doc = docs[existing_idx]
                if ignore_id is not None and existing_doc.get("_id") == ignore_id:
                    continue
                raise ContractError(
                    "duplicate_key",
                    f"Unique index {spec['name']} violated in {collection} for key {cand_tuple}",
                )

    def insert_one(self, collection: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        copied = dict(doc)
        self._check_unique(collection, copied)
        docs = self._collections.setdefault(collection, [])
        idx = len(docs)
        docs.append(copied)
        self._index_doc_at(collection, idx, copied)
        self._save()
        return dict(copied)

    def upsert_by_id(self, collection: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        copied = dict(doc)
        doc_id = copied.get("_id")
        self._check_unique(collection, copied, ignore_id=doc_id)
        docs = self._collections.setdefault(collection, [])
        id_map = self._id_index.setdefault(collection, {})
        if doc_id is not None and str(doc_id) in id_map:
            idx = id_map[str(doc_id)]
            self._unindex_doc(collection, docs[idx])
            docs[idx] = copied
            self._index_doc_at(collection, idx, copied)
            self._save()
            return dict(copied)
        idx = len(docs)
        docs.append(copied)
        self._index_doc_at(collection, idx, copied)
        self._save()
        return dict(copied)

    def update_one(self, collection: str, query: Dict[str, Any], updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        docs = self._collections.setdefault(collection, [])
        id_map = self._id_index.setdefault(collection, {})
        if "_id" in query and not isinstance(query["_id"], dict) and str(query["_id"]) in id_map:
            idx = id_map[str(query["_id"])]
            existing = docs[idx]
            if _matches(existing, query):
                updated = copy.deepcopy(existing)
                updated.update(copy.deepcopy(updates))
                self._check_unique(collection, updated, ignore_id=existing.get("_id"))
                self._unindex_doc(collection, existing)
                docs[idx] = updated
                self._index_doc_at(collection, idx, updated)
                self._save()
                return copy.deepcopy(updated)
            return None
        for i, existing in enumerate(docs):
            if _matches(existing, query):
                updated = copy.deepcopy(existing)
                updated.update(copy.deepcopy(updates))
                self._check_unique(collection, updated, ignore_id=existing.get("_id"))
                self._unindex_doc(collection, existing)
                docs[i] = updated
                self._index_doc_at(collection, i, updated)
                self._save()
                return copy.deepcopy(updated)
        return None

    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        docs = self._collections.get(collection, [])
        if not docs:
            return None
        id_map = self._id_index.get(collection, {})
        if "_id" in query and not isinstance(query["_id"], dict):
            idx = id_map.get(str(query["_id"]))
            if idx is not None and _matches(docs[idx], query):
                return copy.deepcopy(docs[idx])
            return None
        for spec in INDEX_SPECS.get(collection, []):
            if not spec.get("unique"):
                continue
            key_names = tuple(k for k, _ in spec["keys"])
            if all(k in query and not isinstance(query[k], dict) for k in key_names):
                kt = tuple(query[k] for k in key_names)
                u_map = self._unique_indexes.get((collection, key_names), {})
                idx = u_map.get(kt)
                if idx is not None and _matches(docs[idx], query):
                    return copy.deepcopy(docs[idx])
                return None
        for doc in docs:
            if _matches(doc, query):
                return copy.deepcopy(doc)
        return None

    def find_many(
        self,
        collection: str,
        query: Dict[str, Any],
        sort_key: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        results = [dict(d) for d in self._collections.get(collection, []) if _matches(d, query)]
        if sort_key:
            results.sort(key=lambda x: str(x.get(sort_key, "")))
        if limit is not None and limit >= 0:
            results = results[:limit]
        return results

    def count(self, collection: str, query: Dict[str, Any]) -> int:
        return sum(1 for d in self._collections.get(collection, []) if _matches(d, query))

    def store_blob(self, blob_key: str, content: str) -> str:
        ref = f"blob://{blob_key}"
        if self.blob_dir:
            self.blob_dir.mkdir(parents=True, exist_ok=True)
            safe_name = blob_key.replace("/", "_").replace(":", "_")
            (self.blob_dir / f"{safe_name}.blob").write_text(content, encoding="utf-8")
        self._blobs[ref] = content
        self._save()
        return ref

    def load_blob(self, blob_ref: str) -> str:
        if blob_ref in self._blobs:
            return self._blobs[blob_ref]
        if self.blob_dir and blob_ref.startswith("blob://"):
            blob_key = blob_ref[len("blob://") :]
            safe_name = blob_key.replace("/", "_").replace(":", "_")
            p = self.blob_dir / f"{safe_name}.blob"
            if p.exists():
                return p.read_text(encoding="utf-8")
        raise ContractError("blob_not_found", f"Blob reference {blob_ref!r} not found.")


class MongoStorageBackend(StorageBackend):
    """PyMongo-backed storage backend for live MongoDB (`theseus_recplace`)."""

    def __init__(self, mongo_uri: str, db_name: str = DEFAULT_DATABASE_NAME, blob_dir: Optional[Path] = None) -> None:
        try:
            import pymongo  # type: ignore
        except ImportError as exc:
            raise ContractError(
                "mongo_driver_missing",
                "pymongo is not installed in the active Python environment.",
            ) from exc
        self._pymongo = pymongo
        kwargs: Dict[str, Any] = {"serverSelectionTimeoutMS": 10000}
        try:
            import certifi  # type: ignore

            kwargs["tlsCAFile"] = certifi.where()
        except ImportError:
            pass
        self.client = pymongo.MongoClient(mongo_uri, **kwargs)
        self.db = self.client[db_name]
        self.blob_dir = Path(blob_dir) if blob_dir else None

    def ensure_indexes(self) -> None:
        for coll_name, specs in INDEX_SPECS.items():
            coll = self.db[coll_name]
            for spec in specs:
                coll.create_index(spec["keys"], unique=spec.get("unique", False), name=spec["name"])

    def insert_one(self, collection: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        copied = copy.deepcopy(doc)
        try:
            self.db[collection].insert_one(copied)
        except Exception as exc:
            raise ContractError("duplicate_key", f"MongoDB insert failed in {collection}: {exc}") from exc
        return copy.deepcopy(doc)

    def upsert_by_id(self, collection: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        copied = copy.deepcopy(doc)
        try:
            self.db[collection].replace_one({"_id": copied["_id"]}, copied, upsert=True)
        except Exception as exc:
            raise ContractError("duplicate_key", f"MongoDB upsert failed in {collection}: {exc}") from exc
        return copy.deepcopy(doc)

    def bulk_upsert_by_id(self, collection: str, docs: List[Dict[str, Any]], batch_size: int = 2000) -> int:
        if not docs:
            return 0
        coll = self.db[collection]
        ReplaceOne = self._pymongo.ReplaceOne
        total = 0
        for i in range(0, len(docs), batch_size):
            chunk = docs[i : i + batch_size]
            ops = [ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in chunk]
            coll.bulk_write(ops, ordered=False)
            total += len(chunk)
        return total

    def update_one(self, collection: str, query: Dict[str, Any], updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        res = self.db[collection].find_one_and_update(
            query,
            {"$set": updates},
            return_document=self._pymongo.ReturnDocument.AFTER,
        )
        return dict(res) if res else None

    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        res = self.db[collection].find_one(query)
        return dict(res) if res else None

    def find_many(
        self,
        collection: str,
        query: Dict[str, Any],
        sort_key: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        cursor = self.db[collection].find(query)
        if sort_key:
            cursor = cursor.sort(sort_key, 1)
        if limit is not None and limit >= 0:
            cursor = cursor.limit(limit)
        return [dict(d) for d in cursor]

    def count(self, collection: str, query: Dict[str, Any]) -> int:
        return int(self.db[collection].count_documents(query))

    def store_blob(self, blob_key: str, content: str) -> str:
        ref = f"blob://{blob_key}"
        self.db["private_blobs"].replace_one(
            {"_id": ref},
            {"_id": ref, "content": content, "sha256": sha256_hex(content), "created_at": utc_now_iso()},
            upsert=True,
        )
        if self.blob_dir:
            self.blob_dir.mkdir(parents=True, exist_ok=True)
            safe_name = blob_key.replace("/", "_").replace(":", "_")
            (self.blob_dir / f"{safe_name}.blob").write_text(content, encoding="utf-8")
        return ref

    def load_blob(self, blob_ref: str) -> str:
        doc = self.db["private_blobs"].find_one({"_id": blob_ref})
        if doc and "content" in doc:
            return str(doc["content"])
        raise ContractError("blob_not_found", f"Blob reference {blob_ref!r} not found in MongoDB.")


class IngestionAdapter:
    """
    Shared Argon ↔ Muse contract implementation (`database/INGESTION-CONTRACT.md` v0.1).

    Provides both:
    - Importer / Argon methods (`start_import_run`, `write_raw_record_batch`, `finish_import_run`, `register_source`)
    - Muse extraction interface:
      1. `list_sources(source_type, cursor, limit)`
      2. `get_source(source_id, version)`
      3. `put_chunks(source_id, version, chunks, chunker_version)`
      4. `start_extraction(source_id, source_version, prompt_version, model, input_hash)`
      5. `write_claim_batch(run_id, chunk_id, asserts, refs, signals)`
      6. `finish_extraction(run_id, usage, status, errors)`
      7. `get_related_claims(source_id, subject_keys, scope)`
    """

    def __init__(
        self,
        backend: Optional[StorageBackend] = None,
        organization_id: str = DEFAULT_ORGANIZATION_ID,
        require_completed_import_for_reads: bool = True,
    ) -> None:
        if not organization_id or not isinstance(organization_id, str):
            raise ContractError("permission_denied", "organization_id must be a non-empty string.")
        self.organization_id = organization_id
        self.backend = backend or LocalDocumentStore()
        self.require_completed_import_for_reads = require_completed_import_for_reads
        self.backend.ensure_indexes()

    @classmethod
    def from_env(
        cls,
        organization_id: str = DEFAULT_ORGANIZATION_ID,
        fallback_json_path: Optional[Path] = None,
    ) -> "IngestionAdapter":
        mongo_uri = os.environ.get("MONGODB_URI", "").strip()
        db_name = os.environ.get("MONGODB_DATABASE", DEFAULT_DATABASE_NAME).strip() or DEFAULT_DATABASE_NAME
        if mongo_uri:
            backend: StorageBackend = MongoStorageBackend(mongo_uri=mongo_uri, db_name=db_name)
        else:
            backend = LocalDocumentStore(persist_path=fallback_json_path)
        return cls(backend=backend, organization_id=organization_id)

    def _assert_org(self, org_id: Optional[str]) -> str:
        target = org_id if org_id is not None else self.organization_id
        if target != self.organization_id:
            raise ContractError(
                "permission_denied",
                f"Organization scope mismatch: adapter bound to {self.organization_id!r}, got {target!r}.",
                {"expected_organization_id": self.organization_id, "received_organization_id": target},
            )
        return target

    # -------------------------------------------------------------------------
    # Argon Raw Import & Source Registration Operations
    # -------------------------------------------------------------------------

    def start_import_run(
        self,
        source_snapshot: str,
        tables: List[str],
        importer_version: str = "0.1.0",
        import_run_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        org = self._assert_org(organization_id)
        run_id = import_run_id or f"import-{uuid.uuid4().hex[:12]}"
        existing = self.backend.find_one("import_runs", {"_id": run_id, "organization_id": org})
        if existing:
            return existing
        doc = {
            **make_envelope(run_id, organization_id=org),
            "source_snapshot": source_snapshot,
            "tables": list(tables),
            "importer_version": importer_version,
            "status": "running",
            "counts_before": {},
            "counts_after": {},
            "table_digests": {},
            "errors": [],
            "completed_at": None,
        }
        return self.backend.insert_one("import_runs", doc)

    def write_raw_record_batch(
        self,
        import_run_id: str,
        records: Iterable[Dict[str, Any]],
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Persist raw RecPlace records losslessly per `database/INGESTION-CONTRACT.md`:
        - Preserves `null` as `None`.
        - Preserves `src_row_decimal` as exact integral decimal string (rejects float).
        - Preserves `v_json` as exact raw text string; externalizes oversize payloads to blob without truncation.
        - Handles duplicate `(source_table, dump_id, src_file, src_row_decimal)` with explicit `occurrence` counter
          when content differs, and makes re-running the same `import_run_id` idempotent.
        """
        org = self._assert_org(organization_id)
        run = self.backend.find_one("import_runs", {"_id": import_run_id, "organization_id": org})
        if not run:
            raise ContractError("invalid_import_run", f"import_run_id {import_run_id!r} not found for org {org!r}.")
        if run.get("status") not in {"running", "completed"}:
            raise ContractError(
                "invalid_import_run_state",
                f"Cannot write raw records to import_run {import_run_id!r} with status {run.get('status')!r}.",
            )

        inserted_ids: List[str] = []
        idempotent_skips: int = 0

        for raw in records:
            if "organization_id" in raw:
                self._assert_org(raw["organization_id"])
            source_table = raw.get("source_table")
            if not source_table or not isinstance(source_table, str):
                raise ContractError("invalid_raw_record", "source_table is required and must be a string.")

            dump_id = raw.get("dump_id")
            if dump_id is not None and not isinstance(dump_id, str):
                dump_id = str(dump_id)

            src_file = raw.get("src_file")
            if src_file is not None and not isinstance(src_file, str):
                src_file = str(src_file)

            src_row_decimal = normalize_decimal_string(raw.get("src_row_decimal"))

            loaded_at_val = raw.get("loaded_at_source")
            if isinstance(loaded_at_val, dict):
                loaded_at_source = {
                    "value": loaded_at_val.get("value"),
                    "source_type": loaded_at_val.get("source_type", "TIMESTAMP"),
                }
            else:
                loaded_at_source = {
                    "value": str(loaded_at_val) if loaded_at_val is not None else None,
                    "source_type": raw.get("loaded_at_source_type", "TIMESTAMP"),
                }

            v_json = raw.get("v_json")
            if v_json is not None and not isinstance(v_json, str):
                raise ContractError(
                    "invalid_v_json",
                    "v_json must be the lossless raw JSON string (or None if SQL NULL); do not pass pre-parsed dict.",
                )

            payload_sha256 = sha256_hex(v_json)
            v_blob_ref: Optional[str] = None
            stored_v_json = v_json

            if v_json is not None and len(v_json.encode("utf-8")) > LARGE_PAYLOAD_BYTES_THRESHOLD:
                blob_key = f"{org}/{import_run_id}/{payload_sha256}"
                v_blob_ref = self.backend.store_blob(blob_key, v_json)

            base_identity = (
                f"{source_table}|"
                f"{dump_id if dump_id is not None else '<NULL>'}|"
                f"{src_file if src_file is not None else '<NULL>'}|"
                f"{src_row_decimal if src_row_decimal is not None else '<NULL>'}"
            )

            occurrence = int(raw.get("occurrence", 0))
            while True:
                record_key = f"{base_identity}#occ={occurrence}"
                existing = self.backend.find_one(
                    "raw_records",
                    {"organization_id": org, "record_key": record_key},
                )
                if existing is None:
                    break
                # Idempotent retry within the same import run and identical payload hash
                if (
                    existing.get("import_run_id") == import_run_id
                    and existing.get("payload_sha256") == payload_sha256
                    and existing.get("loaded_at_source") == loaded_at_source
                    and "occurrence" not in raw
                ):
                    idempotent_skips += 1
                    record_key = ""
                    break
                occurrence += 1

            if not record_key:
                continue

            rec_id = f"raw:{ sha256_hex(f'{org}:{record_key}')[:24] }"
            doc: Dict[str, Any] = {
                **make_envelope(rec_id, organization_id=org),
                "source_table": source_table,
                "dump_id": dump_id,
                "src_file": src_file,
                "src_row_decimal": src_row_decimal,
                "loaded_at_source": loaded_at_source,
                "v_json": stored_v_json,
                "v_blob_ref": v_blob_ref,
                "payload_sha256": payload_sha256,
                "record_key": record_key,
                "occurrence": occurrence,
                "import_run_id": import_run_id,
            }
            if "payload_parsed" in raw and raw["payload_parsed"] is not None:
                doc["payload_parsed"] = raw["payload_parsed"]

            self.backend.insert_one("raw_records", doc)
            inserted_ids.append(rec_id)

        return {
            "import_run_id": import_run_id,
            "inserted_count": len(inserted_ids),
            "inserted_ids": inserted_ids,
            "idempotent_skips": idempotent_skips,
        }

    def finish_import_run(
        self,
        import_run_id: str,
        status: str,
        counts_before: Dict[str, int],
        counts_after: Dict[str, int],
        table_digests: Dict[str, str],
        errors: Optional[List[str]] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        org = self._assert_org(organization_id)
        if status not in {"completed", "incomplete", "failed"}:
            raise ContractError("invalid_import_status", f"Invalid import run status: {status!r}")
        # If counts_before != counts_after, force incomplete status per RECPLACE-SOURCES.md
        if status == "completed" and counts_before != counts_after:
            status = "incomplete"
            errors = list(errors or []) + ["counts_before_after_mismatch"]
        updated = self.backend.update_one(
            "import_runs",
            {"_id": import_run_id, "organization_id": org},
            {
                "status": status,
                "counts_before": counts_before,
                "counts_after": counts_after,
                "table_digests": table_digests,
                "errors": list(errors or []),
                "completed_at": utc_now_iso(),
            },
        )
        if not updated:
            raise ContractError("invalid_import_run", f"import_run_id {import_run_id!r} not found.")
        return updated

    def register_source(
        self,
        source_id: str,
        source_type: str,
        raw_record_ids: List[str],
        text: Optional[str],
        original_source_metadata: Dict[str, Any],
        source_version: str = "v1",
        mapping_version: str = "0.1.0",
        day: Optional[str] = None,
        client_ref: Optional[str] = None,
        truncation_status: str = "complete",
        import_run_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deterministically register a `sources` record linked to `raw_record_ids`.
        Never silently maps `unknown` to `sales_conversation`.
        """
        org = self._assert_org(organization_id)
        if source_type not in SOURCE_TYPES:
            raise ContractError(
                "unsupported_type",
                f"Invalid source_type {source_type!r}. Allowed: {sorted(SOURCE_TYPES)}",
            )
        if truncation_status not in TRUNCATION_STATUSES:
            raise ContractError(
                "invalid_truncation_status",
                f"Invalid truncation_status {truncation_status!r}. Allowed: {sorted(TRUNCATION_STATUSES)}",
            )
        if not isinstance(raw_record_ids, list) or not raw_record_ids:
            raise ContractError("invalid_provenance", "sources must reference non-empty raw_record_ids.")
        if not source_version or not isinstance(source_version, str):
            raise ContractError("stale_version", "source_version must be a non-empty string.")

        text_sha256 = sha256_hex(text)
        text_blob_ref: Optional[str] = None
        if text is not None and len(text.encode("utf-8")) > LARGE_PAYLOAD_BYTES_THRESHOLD:
            text_blob_ref = self.backend.store_blob(f"{org}/sources/{source_id}/{source_version}", text)

        composite_id = source_id if source_version == "v1" else f"{source_id}@{source_version}"
        doc = {
            **make_envelope(composite_id, organization_id=org),
            "source_id": source_id,
            "source_version": source_version,
            "source_type": source_type,
            "raw_record_ids": list(raw_record_ids),
            "original_source_metadata": copy.deepcopy(original_source_metadata),
            "text": text,
            "text_blob_ref": text_blob_ref,
            "text_sha256": text_sha256,
            "day": day,
            "client_ref": client_ref,
            "truncation_status": truncation_status,
            "mapping_version": mapping_version,
            "import_run_id": import_run_id,
        }
        return self.backend.upsert_by_id("sources", doc)

    # -------------------------------------------------------------------------
    # Muse Interface (database/INGESTION-CONTRACT.md v0.1)
    # -------------------------------------------------------------------------

    def _ensure_completed_import_if_required(self, org: str) -> None:
        if not self.require_completed_import_for_reads:
            return
        completed = self.backend.find_one("import_runs", {"organization_id": org, "status": "completed"})
        if not completed:
            raise ContractError(
                "import_not_completed",
                "Cannot list/read sources before at least one import_run has status='completed'.",
            )

    def _find_source_doc(self, org: str, source_id: str, version: Optional[str] = None) -> Dict[str, Any]:
        query: Dict[str, Any] = {"organization_id": org, "source_id": source_id}
        if version is not None:
            query["source_version"] = version
            doc = self.backend.find_one("sources", query)
            if not doc:
                # Check if source_id exists with another version to report stale_version clearly
                any_ver = self.backend.find_one("sources", {"organization_id": org, "source_id": source_id})
                if any_ver:
                    raise ContractError(
                        "stale_version",
                        f"Source {source_id!r} version {version!r} not found (available version: {any_ver.get('source_version')!r}).",
                        {"source_id": source_id, "requested_version": version, "available_version": any_ver.get("source_version")},
                    )
                raise ContractError("source_not_found", f"Source {source_id!r} not found in organization {org!r}.")
            return doc

        docs = self.backend.find_many("sources", query, sort_key="created_at")
        if not docs:
            raise ContractError("source_not_found", f"Source {source_id!r} not found in organization {org!r}.")
        return docs[-1]

    def list_sources(
        self,
        source_type: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 100,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        `list_sources(source_type, cursor, limit) -> {items, next_cursor}`
        Reads only after a completed import run.
        """
        org = self._assert_org(organization_id)
        self._ensure_completed_import_if_required(org)

        if limit <= 0 or limit > 1000:
            raise ContractError("invalid_limit", "limit must be between 1 and 1000.")

        query: Dict[str, Any] = {"organization_id": org}
        if source_type is not None:
            if source_type not in SOURCE_TYPES:
                raise ContractError("unsupported_type", f"Unknown source_type {source_type!r}.")
            query["source_type"] = source_type
        if cursor is not None:
            query["_id"] = {"$gt": cursor}

        docs = self.backend.find_many("sources", query, sort_key="_id", limit=limit + 1)
        has_more = len(docs) > limit
        items = docs[:limit]
        next_cursor = items[-1]["_id"] if has_more and items else None

        # Summarize items for listing while keeping provenance metadata
        summary_items = [
            {
                "source_id": d["source_id"],
                "source_version": d["source_version"],
                "source_type": d["source_type"],
                "raw_record_ids": d["raw_record_ids"],
                "text_sha256": d["text_sha256"],
                "day": d.get("day"),
                "client_ref": d.get("client_ref"),
                "truncation_status": d.get("truncation_status"),
                "mapping_version": d.get("mapping_version"),
                "organization_id": d["organization_id"],
                "schema_version": d["schema_version"],
                "created_at": d["created_at"],
            }
            for d in items
        ]
        return {
            "items": summary_items,
            "next_cursor": next_cursor,
        }

    def get_source(
        self,
        source_id: str,
        version: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        `get_source(source_id, version) -> full Source and provenance`
        Raises explicit error instead of returning truncated text.
        """
        org = self._assert_org(organization_id)
        self._ensure_completed_import_if_required(org)
        doc = self._find_source_doc(org, source_id, version)

        if doc.get("truncation_status") == "truncated_at_source":
            raise ContractError(
                "source_truncated",
                f"Source {source_id!r} is marked truncated_at_source; refusing to serve partial text as a complete raw copy.",
                {"source_id": source_id, "truncation_status": doc.get("truncation_status")},
            )

        text = doc.get("text")
        if text is None and doc.get("text_blob_ref"):
            text = self.backend.load_blob(doc["text_blob_ref"])
            doc["text"] = text

        if text is not None and sha256_hex(text) != doc.get("text_sha256"):
            raise ContractError(
                "corrupted_source_text",
                f"SHA-256 mismatch when reading source {source_id!r}@{doc.get('source_version')!r}.",
            )

        raw_records = [
            self.backend.find_one("raw_records", {"_id": rid, "organization_id": org})
            for rid in doc.get("raw_record_ids", [])
        ]
        doc["provenance"] = {
            "raw_record_ids": doc.get("raw_record_ids", []),
            "raw_records_found": sum(1 for r in raw_records if r is not None),
            "import_run_id": doc.get("import_run_id"),
            "original_source_metadata": doc.get("original_source_metadata", {}),
        }
        return doc

    def put_chunks(
        self,
        source_id: str,
        version: str,
        chunks: List[Dict[str, Any]],
        chunker_version: str,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        `put_chunks(source_id, version, chunks, chunker_version) -> {chunk_ids}`
        Verifies exact character boundaries (`char_start`, `char_end`) and `text_sha256` against the target `source_version` text.
        """
        org = self._assert_org(organization_id)
        if not version or not isinstance(version, str):
            raise ContractError("stale_version", "version is required for put_chunks.")
        if not chunker_version or not isinstance(chunker_version, str):
            raise ContractError("invalid_chunker_version", "chunker_version is required.")
        if not isinstance(chunks, list) or not chunks:
            raise ContractError("invalid_chunks", "chunks must be a non-empty list.")

        source_doc = self._find_source_doc(org, source_id, version)
        source_text = source_doc.get("text")
        if source_text is None and source_doc.get("text_blob_ref"):
            source_text = self.backend.load_blob(source_doc["text_blob_ref"])
        if not isinstance(source_text, str):
            raise ContractError("source_has_no_text", f"Source {source_id!r}@{version!r} has no text content.")

        chunk_ids: List[str] = []
        prepared_docs: List[Dict[str, Any]] = []

        for idx, ch in enumerate(chunks):
            if "organization_id" in ch:
                self._assert_org(ch["organization_id"])
            if "source_version" in ch and ch["source_version"] != version:
                raise ContractError(
                    "stale_version",
                    f"Chunk {idx} source_version {ch['source_version']!r} does not match put_chunks version {version!r}.",
                )

            chunk_id = ch.get("chunk_id") or f"{source_id}:{version}:ch{idx:04d}"
            char_start = ch.get("char_start")
            char_end = ch.get("char_end")
            chunk_text = ch.get("text")

            if not isinstance(char_start, int) or not isinstance(char_end, int):
                raise ContractError(
                    "invalid_chunk_bounds",
                    f"Chunk {chunk_id!r} requires integer char_start and char_end.",
                )
            if char_start < 0 or char_end <= char_start or char_end > len(source_text):
                raise ContractError(
                    "invalid_chunk_bounds",
                    f"Chunk {chunk_id!r} bounds [{char_start}:{char_end}] out of range for source text of length {len(source_text)}.",
                )
            expected_slice = source_text[char_start:char_end]
            if chunk_text != expected_slice:
                raise ContractError(
                    "chunk_text_mismatch",
                    f"Chunk {chunk_id!r} text does not match source_text[{char_start}:{char_end}].",
                    {"chunk_id": chunk_id, "char_start": char_start, "char_end": char_end},
                )

            computed_hash = sha256_hex(chunk_text)
            provided_hash = ch.get("text_sha256")
            if provided_hash is not None and provided_hash != computed_hash:
                raise ContractError(
                    "chunk_hash_mismatch",
                    f"Chunk {chunk_id!r} provided text_sha256 {provided_hash!r} != computed {computed_hash!r}.",
                )

            doc_id = f"chunk:{org}:{source_id}:{version}:{chunk_id}"
            chunk_doc = {
                **make_envelope(doc_id, organization_id=org),
                "source_id": source_id,
                "source_version": version,
                "chunk_id": chunk_id,
                "text": chunk_text,
                "text_sha256": computed_hash,
                "char_start": char_start,
                "char_end": char_end,
                "transcript_locator": ch.get("transcript_locator"),
                "media_locator": ch.get("media_locator"),
                "chunker_version": chunker_version,
            }
            prepared_docs.append(chunk_doc)
            chunk_ids.append(chunk_id)

        for d in prepared_docs:
            self.backend.upsert_by_id("source_chunks", d)

        return {
            "source_id": source_id,
            "source_version": version,
            "chunker_version": chunker_version,
            "chunk_ids": chunk_ids,
        }

    def start_extraction(
        self,
        source_id: str,
        source_version: str,
        prompt_version: str,
        model: str,
        input_hash: str,
        organization_id: Optional[str] = None,
        allow_rerun: bool = False,
    ) -> Dict[str, Any]:
        """
        `start_extraction(source_id, source_version, prompt_version, model, input_hash) -> {run_id, ...}`
        Enforces source_version existence and idempotency on `(source_id, source_version, prompt_version, model, input_hash, organization_id)`.
        """
        org = self._assert_org(organization_id)
        if not source_version or not isinstance(source_version, str):
            raise ContractError("stale_version", "source_version is required.")
        if not prompt_version or not isinstance(prompt_version, str):
            raise ContractError("invalid_prompt_version", "prompt_version is required.")
        if not model or not isinstance(model, str):
            raise ContractError("invalid_model", "model is required.")
        if not input_hash or not isinstance(input_hash, str):
            raise ContractError("invalid_input_hash", "input_hash is required.")

        # Ensure exact (source_id, source_version) exists
        self._find_source_doc(org, source_id, source_version)

        existing = self.backend.find_one(
            "extraction_runs",
            {
                "organization_id": org,
                "source_id": source_id,
                "source_version": source_version,
                "prompt_version": prompt_version,
                "model": model,
                "input_hash": input_hash,
            },
        )
        if existing and not allow_rerun and existing.get("status") in {"running", "completed"}:
            return {
                "run_id": existing["_id"],
                "idempotent_reuse": True,
                "status": existing["status"],
                "source_id": source_id,
                "source_version": source_version,
            }

        run_id = f"ext-{uuid.uuid4().hex[:12]}"
        doc = {
            **make_envelope(run_id, organization_id=org),
            "run_id": run_id,
            "source_id": source_id,
            "source_version": source_version,
            "prompt_version": prompt_version,
            "model": model,
            "input_hash": input_hash,
            "status": "running",
            "usage": {},
            "errors": [],
            "accepted_candidate_count": 0,
            "rejected_item_count": 0,
            "rejected_items": [],
            "finished_at": None,
        }
        self.backend.insert_one("extraction_runs", doc)
        return {
            "run_id": run_id,
            "idempotent_reuse": False,
            "status": "running",
            "source_id": source_id,
            "source_version": source_version,
        }

    def write_claim_batch(
        self,
        run_id: str,
        chunk_id: str,
        asserts: List[Dict[str, Any]],
        refs: Optional[List[Dict[str, Any]]] = None,
        signals: Optional[List[Dict[str, Any]]] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        `write_claim_batch(run_id, chunk_id, asserts, refs, signals) -> {accepted_candidate_ids, rejected_items, ...}`

        Enforces `database/INGESTION-CONTRACT.md` invariants:
        - `write_claim_batch` creates ONLY `extraction_status="candidate"`. Any attempt to write `accepted` or `approved_rule`
          is rejected or blocked.
        - Validates `organization_id`, `source_version`, `chunk_id`, enums (`fact_type`, `knowledge_state`, `target_q`),
          and exact continuous 15-300 char `quote` against the stored `source_chunks` text.
        - Invalid items are returned in `rejected_items` with explicit reason codes and preserved on the `extraction_runs` audit log.
        """
        org = self._assert_org(organization_id)
        run_doc = self.backend.find_one("extraction_runs", {"_id": run_id, "organization_id": org})
        if not run_doc:
            raise ContractError("invalid_run_id", f"extraction_run {run_id!r} not found in organization {org!r}.")
        if run_doc.get("status") != "running":
            raise ContractError(
                "run_not_active",
                f"extraction_run {run_id!r} is in status {run_doc.get('status')!r}; cannot write claims.",
            )

        source_id = run_doc["source_id"]
        source_version = run_doc["source_version"]
        source_doc = self._find_source_doc(org, source_id, source_version)

        chunk_doc = self.backend.find_one(
            "source_chunks",
            {
                "organization_id": org,
                "source_id": source_id,
                "source_version": source_version,
                "chunk_id": chunk_id,
            },
        )
        if not chunk_doc:
            # Check if chunk_id exists under a different source_version
            other_ver_chunk = self.backend.find_one(
                "source_chunks",
                {"organization_id": org, "source_id": source_id, "chunk_id": chunk_id},
            )
            if other_ver_chunk:
                raise ContractError(
                    "stale_version",
                    f"Chunk {chunk_id!r} belongs to source_version {other_ver_chunk.get('source_version')!r}, expected {source_version!r}.",
                )
            raise ContractError(
                "chunk_not_found",
                f"Chunk {chunk_id!r} not found for source {source_id!r}@{source_version!r}.",
            )

        chunk_text: str = chunk_doc["text"]
        allow_norm_ws = source_doc.get("source_type") == "normative"

        accepted_candidate_ids: List[str] = []
        rejected_items: List[Dict[str, Any]] = []
        stored_ref_ids: List[str] = []
        stored_signal_ids: List[str] = []

        if not isinstance(asserts, list):
            raise ContractError("invalid_asserts", "asserts must be a list of candidate claim dicts.")

        for idx, item in enumerate(asserts):
            if not isinstance(item, dict):
                rejected_items.append({"index": idx, "item_type": "assert", "reason": "not_an_object", "item": item})
                continue

            # 1. Check organization_id override if supplied
            if "organization_id" in item and item["organization_id"] != org:
                rejected_items.append(
                    {
                        "index": idx,
                        "item_type": "assert",
                        "reason": f"organization_mismatch({item['organization_id']} != {org})",
                        "item": item,
                    }
                )
                continue

            # 2. Check source_version override if supplied
            if "source_version" in item and item["source_version"] != source_version:
                rejected_items.append(
                    {
                        "index": idx,
                        "item_type": "assert",
                        "reason": f"stale_version({item['source_version']} != {source_version})",
                        "item": item,
                    }
                )
                continue

            # 3. Forbid automatic promotion to accepted / approved_rule
            requested_status = item.get("extraction_status", "candidate")
            if requested_status != "candidate":
                rejected_items.append(
                    {
                        "index": idx,
                        "item_type": "assert",
                        "reason": f"forbidden_status_promotion(extraction_status={requested_status!r}; only 'candidate' allowed in write_claim_batch)",
                        "item": item,
                    }
                )
                continue

            claim_text = item.get("claim")
            if not isinstance(claim_text, str) or not claim_text.strip():
                rejected_items.append({"index": idx, "item_type": "assert", "reason": "missing_or_empty_claim", "item": item})
                continue

            fact_type = item.get("fact_type")
            if fact_type not in FACT_TYPES:
                rejected_items.append(
                    {
                        "index": idx,
                        "item_type": "assert",
                        "reason": f"invalid_fact_type({fact_type!r})",
                        "item": item,
                    }
                )
                continue

            knowledge_state = item.get("knowledge_state")
            if knowledge_state not in KNOWLEDGE_STATES:
                rejected_items.append(
                    {
                        "index": idx,
                        "item_type": "assert",
                        "reason": f"invalid_knowledge_state({knowledge_state!r})",
                        "item": item,
                    }
                )
                continue

            target_q = item.get("target_q", [])
            if not isinstance(target_q, list) or any(q not in TARGET_Q_VALUES for q in target_q):
                rejected_items.append(
                    {
                        "index": idx,
                        "item_type": "assert",
                        "reason": f"invalid_target_q({target_q!r})",
                        "item": item,
                    }
                )
                continue

            # 4. Quote gate validation against exact chunk text
            quote = item.get("quote")
            quote_gate = validate_quote_in_text(
                quote=quote,
                chunk_text=chunk_text,
                allow_normalized_whitespace=allow_norm_ws,
            )
            if not quote_gate["passed"]:
                rejected_items.append(
                    {
                        "index": idx,
                        "item_type": "assert",
                        "reason": f"quote_gate_failed:{quote_gate['reason']}",
                        "quote_gate": quote_gate,
                        "item": item,
                    }
                )
                continue

            business_fields_raw = item.get("business_fields") or {}
            if not isinstance(business_fields_raw, dict):
                rejected_items.append(
                    {"index": idx, "item_type": "assert", "reason": "invalid_business_fields", "item": item}
                )
                continue

            business_fields = {
                "amount": business_fields_raw.get("amount"),
                "currency": business_fields_raw.get("currency"),
                "date": business_fields_raw.get("date"),
                "counterparty_role": business_fields_raw.get("counterparty_role"),
                "authority_scope": business_fields_raw.get("authority_scope"),
            }

            abs_char_start = (
                chunk_doc["char_start"] + quote_gate["char_start"]
                if quote_gate["char_start"] is not None
                else None
            )
            abs_char_end = (
                chunk_doc["char_start"] + quote_gate["char_end"]
                if quote_gate["char_end"] is not None
                else None
            )

            evidence_locator = item.get("evidence_locator") or {
                "chunk_id": chunk_id,
                "chunk_char_start": quote_gate["char_start"],
                "chunk_char_end": quote_gate["char_end"],
                "source_char_start": abs_char_start,
                "source_char_end": abs_char_end,
            }

            claim_hash = sha256_hex(f"{run_id}:{chunk_id}:{idx}:{claim_text}:{quote}")[:20]
            claim_id = item.get("claim_id") or f"claim-{claim_hash}"

            claim_doc = {
                **make_envelope(claim_id, organization_id=org),
                "source_id": source_id,
                "source_version": source_version,
                "chunk_id": chunk_id,
                "run_id": run_id,
                "claim": claim_text.strip(),
                "fact_type": fact_type,
                "zone": item.get("zone"),
                "subzone": item.get("subzone"),
                "speaker_role": item.get("speaker_role"),
                "knowledge_state": knowledge_state,
                "target_q": list(target_q),
                "quote": quote,
                "evidence_locator": evidence_locator,
                "business_fields": business_fields,
                "extraction_status": "candidate",
                "status": "candidate",  # Compatibility alias for database/SCHEMA.md queries
                "subject": item.get("subject") or item.get("zone") or source_id,
                "predicate": item.get("predicate") or fact_type,
                "value": item.get("value") if "value" in item else claim_text.strip(),
                "quote_gate": quote_gate,
                "model": run_doc["model"],
                "prompt_version": run_doc["prompt_version"],
            }
            self.backend.insert_one("claims", claim_doc)
            accepted_candidate_ids.append(claim_id)

        # Process fact_refs
        for r_idx, ref in enumerate(refs or []):
            if not isinstance(ref, dict):
                rejected_items.append({"index": r_idx, "item_type": "ref", "reason": "not_an_object", "item": ref})
                continue
            relation = ref.get("relation")
            if relation not in FACT_REF_RELATIONS:
                rejected_items.append(
                    {"index": r_idx, "item_type": "ref", "reason": f"invalid_relation({relation!r})", "item": ref}
                )
                continue
            from_claim_id = ref.get("from_claim_id")
            to_claim_id = ref.get("to_claim_id")
            if not from_claim_id or not to_claim_id:
                rejected_items.append(
                    {"index": r_idx, "item_type": "ref", "reason": "missing_claim_endpoints", "item": ref}
                )
                continue
            ref_id = f"ref-{sha256_hex(f'{run_id}:{chunk_id}:{r_idx}:{from_claim_id}:{to_claim_id}:{relation}')[:18]}"
            ref_doc = {
                **make_envelope(ref_id, organization_id=org),
                "run_id": run_id,
                "source_id": source_id,
                "source_version": source_version,
                "chunk_id": chunk_id,
                "from_claim_id": from_claim_id,
                "to_claim_id": to_claim_id,
                "relation": relation,
                "quote": ref.get("quote"),
                "rationale": ref.get("rationale"),
            }
            self.backend.insert_one("fact_refs", ref_doc)
            stored_ref_ids.append(ref_id)

        # Process review_signals
        for s_idx, sig in enumerate(signals or []):
            if not isinstance(sig, dict):
                rejected_items.append({"index": s_idx, "item_type": "signal", "reason": "not_an_object", "item": sig})
                continue
            kind = sig.get("kind")
            if kind not in SIGNAL_KINDS:
                rejected_items.append(
                    {"index": s_idx, "item_type": "signal", "reason": f"invalid_signal_kind({kind!r})", "item": sig}
                )
                continue
            sig_quote = sig.get("quote")
            if sig_quote is not None:
                if not isinstance(sig_quote, str) or sig_quote not in chunk_text:
                    rejected_items.append(
                        {
                            "index": s_idx,
                            "item_type": "signal",
                            "reason": "signal_quote_not_in_chunk_text",
                            "item": sig,
                        }
                    )
                    continue
            sig_desc = sig.get("description", "")
            sig_id = f"sig-{sha256_hex(f'{run_id}:{chunk_id}:{s_idx}:{kind}:{sig_desc}')[:18]}"
            sig_doc = {
                **make_envelope(sig_id, organization_id=org),
                "run_id": run_id,
                "source_id": source_id,
                "source_version": source_version,
                "chunk_id": chunk_id,
                "kind": kind,
                "description": sig.get("description", ""),
                "quote": sig_quote,
                "claim_ids": sig.get("claim_ids", []),
            }
            self.backend.insert_one("review_signals", sig_doc)
            stored_signal_ids.append(sig_id)

        # Update run counters & rejected audit trail
        prev_rejected = list(run_doc.get("rejected_items", []))
        prev_rejected.extend(rejected_items)
        self.backend.update_one(
            "extraction_runs",
            {"_id": run_id, "organization_id": org},
            {
                "accepted_candidate_count": int(run_doc.get("accepted_candidate_count", 0)) + len(accepted_candidate_ids),
                "rejected_item_count": int(run_doc.get("rejected_item_count", 0)) + len(rejected_items),
                "rejected_items": prev_rejected,
            },
        )

        return {
            "run_id": run_id,
            "chunk_id": chunk_id,
            "accepted_candidate_ids": accepted_candidate_ids,
            "rejected_items": rejected_items,
            "stored_ref_ids": stored_ref_ids,
            "stored_signal_ids": stored_signal_ids,
        }

    def finish_extraction(
        self,
        run_id: str,
        usage: Dict[str, Any],
        status: str = "completed",
        errors: Optional[List[str]] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        `finish_extraction(run_id, usage, status, errors) -> receipt`
        """
        org = self._assert_org(organization_id)
        if status not in {"completed", "failed", "incomplete"}:
            raise ContractError("invalid_extraction_status", f"Invalid status {status!r}.")
        run_doc = self.backend.find_one("extraction_runs", {"_id": run_id, "organization_id": org})
        if not run_doc:
            raise ContractError("invalid_run_id", f"extraction_run {run_id!r} not found.")

        finished_at = utc_now_iso()
        updated = self.backend.update_one(
            "extraction_runs",
            {"_id": run_id, "organization_id": org},
            {
                "status": status,
                "usage": copy.deepcopy(usage or {}),
                "errors": list(errors or []),
                "finished_at": finished_at,
            },
        )
        assert updated is not None
        return {
            "run_id": run_id,
            "organization_id": org,
            "source_id": updated["source_id"],
            "source_version": updated["source_version"],
            "status": updated["status"],
            "accepted_candidate_count": updated.get("accepted_candidate_count", 0),
            "rejected_item_count": updated.get("rejected_item_count", 0),
            "usage": updated.get("usage", {}),
            "errors": updated.get("errors", []),
            "finished_at": finished_at,
        }

    def get_related_claims(
        self,
        source_id: Optional[str] = None,
        subject_keys: Optional[List[str]] = None,
        scope: Optional[Dict[str, Any]] = None,
        limit: int = 200,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        `get_related_claims(source_id, subject_keys, scope) -> bounded package for SubQ / consistency review`
        """
        org = self._assert_org(organization_id)
        if limit <= 0 or limit > 1000:
            raise ContractError("invalid_limit", "limit must be between 1 and 1000.")

        scope = scope or {}
        query: Dict[str, Any] = {"organization_id": org}
        if source_id and not scope.get("include_all_sources", False):
            query["source_id"] = source_id
        if "fact_type" in scope and scope["fact_type"]:
            query["fact_type"] = scope["fact_type"]
        if "zone" in scope and scope["zone"]:
            query["zone"] = scope["zone"]
        if "extraction_status" in scope and scope["extraction_status"]:
            query["extraction_status"] = scope["extraction_status"]

        candidates = self.backend.find_many("claims", query, sort_key="created_at", limit=limit * 4)
        if subject_keys:
            key_set = set(subject_keys)
            filtered = []
            for c in candidates:
                c_keys = {
                    c.get("subject"),
                    c.get("zone"),
                    c.get("subzone"),
                    c.get("fact_type"),
                    *(c.get("target_q") or []),
                }
                if c_keys.intersection(key_set):
                    filtered.append(c)
            candidates = filtered

        bounded = candidates[:limit]
        return {
            "organization_id": org,
            "source_id": source_id,
            "subject_keys": list(subject_keys or []),
            "scope": scope,
            "count": len(bounded),
            "claims": bounded,
        }
