"""Bounded, provenance-aware Organization Memory for the localhost demo."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from database.schema import ContractError, SOURCE_TYPES, utc_now_iso

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / "database" / "private"
HANDOFF = ROOT / "database" / "fixtures" / "evidence-handoff.json"
MUSE_STATUS = ROOT / "docs" / "status" / "Muse.Hackathon.md"
MODEL = os.environ.get("THESEUS_AI_MODEL", "claude-opus-5-5")


def _checkpoint() -> Dict[str, Any]:
    """Read the latest durable Muse status; never infer full coverage from claim count."""
    if not MUSE_STATUS.is_file():
        return {"state": "unavailable"}
    text = MUSE_STATUS.read_text(encoding="utf-8")
    matches = re.findall(
        r"Batch-(\d+).*?Packet merged: ([\d,]+) claims.*?EXACT coverage: "
        r"([\d,]+) distinct source_id / ([\d,]+) distinct text_sha256 of ([\d,]+)",
        text,
    )
    if not matches:
        return {"state": "unavailable"}
    batch, claims, sources, hashes, candidate = matches[-1]
    return {
        "state": "partial_candidate_grade",
        "storage": "local_private_muse_packet_not_atlas_claims",
        "batch": int(batch),
        "candidate_claims": int(claims.replace(",", "")),
        "distinct_source_ids": int(sources.replace(",", "")),
        "distinct_text_hashes": int(hashes.replace(",", "")),
        "candidate_text_hashes": int(candidate.replace(",", "")),
        "provenance": "docs/status/Muse.Hackathon.md",
        "qualification": "Quote-gated candidate claims; not exhaustive semantic review or prevalence.",
    }


class OrganizationMemory:
    def __init__(self, controller: Any):
        self.controller = controller

    def overview(self) -> Dict[str, Any]:
        receipt_file = PRIVATE / "atlas-verification-summary.json"
        receipt = None
        if receipt_file.is_file():
            raw = json.loads(receipt_file.read_text(encoding="utf-8"))
            counts = raw.get("atlas_counts_verified") or {}
            if raw.get("all_atlas_digests_match") is True and len(counts) == 7:
                receipt = {
                    "state": "verified_snapshot",
                    "raw_records": sum(int(v) for v in counts.values()),
                    "sources": raw.get("atlas_sources_total"),
                    "tables": counts,
                    "sources_by_type": raw.get("atlas_sources_by_type") or {},
                    "verified_at": raw.get("atlas_verified_at"),
                    "import_run_id": raw.get("import_run_id"),
                    "provenance": "database/private/atlas-verification-summary.json",
                }
        if receipt is None:
            receipt = {"state": "unverified", "provenance": "verification receipt unavailable"}
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        org = self.controller.adapter.organization_id
        atlas_derived = {name: self.controller.adapter.backend.count(name, {"organization_id": org})
                         for name in ("claims", "source_chunks", "extraction_runs")}
        return {
            "backend_mode": self.controller.backend_mode,
            "snapshot": receipt,
            "distillation": _checkpoint(),
            "atlas_derived": atlas_derived,
            "review": {
                "discount_pairs": len(handoff["subq_statuses"]["discount_pairs"]),
                "proven_contradictions": 0,
                "conclusion": handoff["subq_statuses"]["conclusion"],
                "provenance": "database/fixtures/evidence-handoff.json",
            },
            "scope": "One goal: protect value and margin while growing sales through discount rules and culture.",
            "limitations": handoff["cannot_claim"],
        }

    def list_sources(self, source_type: Optional[str], cursor: Optional[str], limit: int) -> Dict[str, Any]:
        if source_type and source_type not in SOURCE_TYPES:
            raise ContractError("unsupported_type", "Unknown source type.")
        if limit < 1 or limit > 25:
            raise ContractError("invalid_limit", "Page size must be between 1 and 25.")
        if cursor and (len(cursor) > 256 or not re.fullmatch(r"[A-Za-z0-9_:./-]+", cursor)):
            raise ContractError("invalid_cursor", "Invalid source cursor.")
        page = self.controller.adapter.list_sources(source_type=source_type, cursor=cursor, limit=limit)
        return {
            "items": [
                {k: item.get(k) for k in ("source_id", "source_version", "source_type", "day", "truncation_status", "mapping_version")}
                for item in page["items"]
            ],
            "next_cursor": page["next_cursor"],
            "scope": "Metadata only. Raw text is not exposed by this public-ready browser.",
        }

    def ask(self, question: str) -> Dict[str, Any]:
        question = question.strip()
        if not question or len(question) > 600:
            raise ContractError("invalid_question", "Question must contain 1–600 characters.")
        overview = self.overview()
        # Only sanitized, source-linked demo evidence enters the model context.
        catalog = self.controller.evidence_catalog
        terms = set(re.findall(r"[\w]{4,}", question.casefold()))
        ranked = sorted(
            catalog.values(),
            key=lambda item: len(terms & set(re.findall(r"[\w]{4,}", (item.get("title", "") + " " + item.get("summary", "")).casefold()))),
            reverse=True,
        )
        selected = [
            {"citation_id": item["evidence_id"], "title": item.get("title"), "summary": item.get("summary"),
             "readiness": item.get("readiness"), "provenance": item.get("provenance")}
            for item in ranked[:6]
        ]
        context = {"snapshot": {**overview["snapshot"], "citation_id": "ev:import-live-20261107-full"},
                   "distillation": {**overview["distillation"], "citation_id": "memory:muse-status"},
                   "atlas_derived": overview["atlas_derived"],
                   "review": {**overview["review"], "citation_id": "ev:muse-subq-packet-v1"},
                   "scope": overview["scope"], "limitations": overview["limitations"],
                   "evidence": selected}
        key_file = Path(os.environ.get("ANTHROPIC_API_KEY_FILE", str(PRIVATE / "anthropic-dashboard-key")))
        if not key_file.is_file():
            raise ContractError("model_unavailable", "Anthropic key is unavailable on this server.")
        payload = {
            "model": MODEL, "max_tokens": 1000,
            "system": "Answer only from the supplied scoped evidence. Cite citation_id values in square brackets. Separate observed snapshot counts, candidate claims, model reviews, proposals and simulation. Say plainly when evidence is insufficient. Do not infer discount prevalence, CRM revenue, causality, full distillation or retroactive violations. Keep the answer concise.",
            "messages": [{"role": "user", "content": json.dumps({"question": question, "context": context}, ensure_ascii=False)}],
        }
        run_id = uuid.uuid4().hex
        log_dir = PRIVATE / "organization-memory-qa"
        log_dir.mkdir(mode=0o700, exist_ok=True)
        log_path = log_dir / f"{run_id}.json"
        trace = {"run_id": run_id, "started_at": utc_now_iso(), "question": question, "request": payload,
                 "context_citation_ids": [item["citation_id"] for item in selected]}
        log_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
        os.chmod(log_path, 0o600)
        try:
            request = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"x-api-key": key_file.read_text(encoding="utf-8").strip(),
                         "anthropic-version": "2023-06-01", "content-type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=90) as response:
                raw_response = json.load(response)
            answer = "\n".join(block.get("text", "") for block in raw_response.get("content", []) if block.get("type") == "text")
            trace.update({"finished_at": utc_now_iso(), "response": raw_response})
            return {"answer": answer, "citation_ids": ["ev:import-live-20261107-full", "memory:muse-status",
                    "ev:muse-subq-packet-v1"] + [item["citation_id"] for item in selected],
                    "model": MODEL, "run_id": run_id, "scope": "sanitized evidence only"}
        except (urllib.error.URLError, TimeoutError) as exc:
            trace.update({"finished_at": utc_now_iso(), "error": type(exc).__name__})
            raise ContractError("model_request_failed", "The model request failed; inspect the private run log.") from exc
        finally:
            log_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
            os.chmod(log_path, 0o600)
