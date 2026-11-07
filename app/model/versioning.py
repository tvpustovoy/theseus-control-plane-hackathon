"""Versioned model assembly, provenance queries, and model diff computation (`A04` / `B01`)."""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from database.adapter import IngestionAdapter
from database.schema import ContractError, make_envelope, sha256_hex


class VersionedModelService:
    """
    Builds immutable `model_versions` snapshots from candidate/reviewed `claims` and `review_signals`,
    answers provenance queries back to `sources` and `raw_records`, and computes `ModelDiff` (`B01`)
    between any two model versions without overwriting prior history.
    """

    def __init__(self, adapter: IngestionAdapter) -> None:
        self.adapter = adapter

    def assemble_snapshot(
        self,
        version: str,
        parent_version: Optional[str] = None,
        included_claim_ids: Optional[List[str]] = None,
        approved_decision_ids: Optional[List[str]] = None,
        summary_note: str = "",
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new immutable `model_versions` record anchored in specific claims and decisions.
        Never overwrites an existing version.
        """
        org = self.adapter._assert_org(organization_id)
        if not version or not isinstance(version, str):
            raise ContractError("invalid_version", "version must be a non-empty string.")

        existing = self.adapter.backend.find_one("model_versions", {"organization_id": org, "version": version})
        if existing:
            raise ContractError(
                "version_already_exists",
                f"model_version {version!r} already exists in organization {org!r}; versions are immutable.",
            )

        if parent_version is not None:
            parent_doc = self.adapter.backend.find_one(
                "model_versions",
                {"organization_id": org, "version": parent_version},
            )
            if not parent_doc:
                raise ContractError(
                    "parent_version_not_found",
                    f"parent_version {parent_version!r} not found in organization {org!r}.",
                )

        all_org_claims = self.adapter.backend.find_many("claims", {"organization_id": org}, sort_key="_id")
        claims_by_id = {c["_id"]: c for c in all_org_claims}

        if included_claim_ids is not None:
            selected_claims = []
            for cid in included_claim_ids:
                if cid not in claims_by_id:
                    raise ContractError("claim_not_found", f"Claim {cid!r} not found in organization {org!r}.")
                selected_claims.append(claims_by_id[cid])
        else:
            selected_claims = [
                c for c in all_org_claims if c.get("extraction_status") in {"candidate", "accepted", "disputed"}
            ]

        # Group into 5x2 upper-level frame buckets: Purpose, Rules, Resources, Relationships, Progress
        frame_5x2: Dict[str, List[str]] = {
            "Purpose": [],
            "Rules": [],
            "Resources": [],
            "Relationships": [],
            "Progress": [],
        }
        for c in selected_claims:
            ft = c.get("fact_type")
            cid = c["_id"]
            if ft in {"rule", "prohibition", "training_rule", "canon_value", "definition"}:
                frame_5x2["Rules"].append(cid)
            elif ft in {"price", "need"}:
                frame_5x2["Resources"].append(cid)
            elif ft in {"promise", "objection"}:
                frame_5x2["Relationships"].append(cid)
            elif ft in {"decision", "proposal"}:
                frame_5x2["Purpose"].append(cid)
            else:
                frame_5x2["Progress"].append(cid)

        signals = self.adapter.backend.find_many("review_signals", {"organization_id": org}, sort_key="_id")
        open_signal_ids = [s["_id"] for s in signals]

        claim_ids_sorted = sorted(c["_id"] for c in selected_claims)
        snapshot_hash = sha256_hex("|".join(claim_ids_sorted))

        doc_id = f"model:{org}:{version}"
        snapshot_doc = {
            **make_envelope(doc_id, organization_id=org),
            "version": version,
            "parent_version": parent_version,
            "snapshot_hash": snapshot_hash,
            "claim_ids": claim_ids_sorted,
            "decision_ids": list(approved_decision_ids or []),
            "open_signal_ids": open_signal_ids,
            "frame_5x2": frame_5x2,
            "summary_note": summary_note,
        }
        return self.adapter.backend.insert_one("model_versions", snapshot_doc)

    def trace_claim_provenance(self, claim_id: str, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Trace a single claim all the way back to its `source_chunks`, `sources`, and `raw_records`.
        """
        org = self.adapter._assert_org(organization_id)
        claim = self.adapter.backend.find_one("claims", {"_id": claim_id, "organization_id": org})
        if not claim:
            raise ContractError("claim_not_found", f"Claim {claim_id!r} not found in organization {org!r}.")

        chunk = self.adapter.backend.find_one(
            "source_chunks",
            {
                "organization_id": org,
                "source_id": claim["source_id"],
                "source_version": claim["source_version"],
                "chunk_id": claim["chunk_id"],
            },
        )
        source = self.adapter._find_source_doc(org, claim["source_id"], claim["source_version"])
        raw_records = [
            self.adapter.backend.find_one("raw_records", {"_id": rid, "organization_id": org})
            for rid in source.get("raw_record_ids", [])
        ]

        return {
            "organization_id": org,
            "claim_id": claim_id,
            "claim": claim["claim"],
            "fact_type": claim["fact_type"],
            "extraction_status": claim["extraction_status"],
            "quote": claim["quote"],
            "quote_gate": claim["quote_gate"],
            "evidence_locator": claim["evidence_locator"],
            "chunk": {
                "chunk_id": chunk["chunk_id"] if chunk else None,
                "text_sha256": chunk["text_sha256"] if chunk else None,
                "char_start": chunk["char_start"] if chunk else None,
                "char_end": chunk["char_end"] if chunk else None,
            },
            "source": {
                "source_id": source["source_id"],
                "source_version": source["source_version"],
                "source_type": source["source_type"],
                "text_sha256": source["text_sha256"],
            },
            "raw_records": [
                {
                    "raw_record_id": r["_id"],
                    "source_table": r["source_table"],
                    "record_key": r["record_key"],
                    "payload_sha256": r["payload_sha256"],
                    "import_run_id": r["import_run_id"],
                }
                for r in raw_records
                if r is not None
            ],
        }

    def compute_model_diff(
        self,
        base_version: str,
        candidate_version: str,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute `ModelDiff` per `docs/CONTRACTS.md` (`B01`):
        `base_version`, `candidate_version`, `added_ids`, `removed_ids`, `changed_ids`, `disputed_ids`,
        `affected_goals`, `affected_rules`, `affected_tools`, `unresolved`.
        """
        org = self.adapter._assert_org(organization_id)
        base_doc = self.adapter.backend.find_one("model_versions", {"organization_id": org, "version": base_version})
        if not base_doc:
            raise ContractError("version_not_found", f"base_version {base_version!r} not found.")
        cand_doc = self.adapter.backend.find_one(
            "model_versions",
            {"organization_id": org, "version": candidate_version},
        )
        if not cand_doc:
            raise ContractError("version_not_found", f"candidate_version {candidate_version!r} not found.")

        base_ids = set(base_doc.get("claim_ids", []))
        cand_ids = set(cand_doc.get("claim_ids", []))

        added_ids = sorted(cand_ids - base_ids)
        removed_ids = sorted(base_ids - cand_ids)

        changed_ids: List[str] = []
        disputed_ids: List[str] = []
        affected_goals: List[str] = []
        affected_rules: List[str] = []
        affected_tools: List[str] = []

        for cid in sorted(cand_ids):
            c = self.adapter.backend.find_one("claims", {"_id": cid, "organization_id": org})
            if not c:
                continue
            if c.get("extraction_status") == "disputed":
                disputed_ids.append(cid)
            if cid in added_ids:
                ft = c.get("fact_type")
                if ft in {"rule", "prohibition", "training_rule", "canon_value"}:
                    affected_rules.append(cid)
                if ft in {"decision", "proposal", "need"}:
                    affected_goals.append(cid)
                if c.get("zone") in {"pricing", "discount_authority", "delegation"} or "Q3" in (c.get("target_q") or []):
                    affected_tools.append(cid)

        # Also check `fact_refs` where relation in {"updates", "contradicts"}
        refs = self.adapter.backend.find_many("fact_refs", {"organization_id": org})
        for r in refs:
            if r.get("from_claim_id") in cand_ids and r.get("to_claim_id") in base_ids:
                if r.get("relation") == "updates":
                    changed_ids.append(r["to_claim_id"])
                elif r.get("relation") == "contradicts":
                    disputed_ids.append(r["from_claim_id"])

        diff_id = f"diff:{org}:{base_version}->{candidate_version}"
        return {
            **make_envelope(diff_id, organization_id=org),
            "base_version": base_version,
            "candidate_version": candidate_version,
            "added_ids": added_ids,
            "removed_ids": removed_ids,
            "changed_ids": sorted(set(changed_ids)),
            "disputed_ids": sorted(set(disputed_ids)),
            "affected_goals": sorted(set(affected_goals)),
            "affected_rules": sorted(set(affected_rules)),
            "affected_tools": sorted(set(affected_tools)),
            "unresolved": cand_doc.get("open_signal_ids", []),
        }
