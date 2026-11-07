"""Schema definitions, collection specifications, and validation rules for INGESTION-CONTRACT v0.1."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Set, Tuple

SCHEMA_VERSION = "0.1.0"
DEFAULT_DATABASE_NAME = "theseus_recplace"
DEFAULT_ORGANIZATION_ID = "recplace"

RAW_TABLES: Tuple[str, ...] = (
    "raw.CORPUS_MANIFEST",
    "raw.CORPUS_TEXTS",
    "raw.EPISODES",
    "raw.EPISODES_TEXT",
    "raw.CRM_CLIENTS",
    "raw.CRM_DEALS",
    "raw.CRM_DEAL_STAGE_EVENTS",
)

EXPECTED_RAW_TABLE_COUNTS: Dict[str, int] = {
    "raw.CORPUS_MANIFEST": 1088,
    "raw.CORPUS_TEXTS": 1088,
    "raw.EPISODES": 22576,
    "raw.EPISODES_TEXT": 14144,
    "raw.CRM_CLIENTS": 1157,
    "raw.CRM_DEALS": 6102,
    "raw.CRM_DEAL_STAGE_EVENTS": 7276,
}

COLLECTIONS: Tuple[str, ...] = (
    "raw_records",
    "import_runs",
    "sources",
    "source_chunks",
    "claims",
    "fact_refs",
    "review_signals",
    "extraction_runs",
    "model_versions",
    "decisions",
    "simulation_runs",
    "simulation_events",
    "crm_deals_demo",
)

PROVENANCE_TAGS: Set[str] = {
    "observed",
    "inferred",
    "simulated",
}

DISCOUNT_JUSTIFICATION_ENUM: Set[str] = {
    "longer_term",
    "prepayment",
    "referral",
    "volume",
    "other_with_text",
}

VALUE_EXCHANGE_JUSTIFICATIONS: Set[str] = {
    "longer_term",
    "prepayment",
    "referral",
    "volume",
}

SIMULATION_ARMS: Tuple[str, ...] = (
    "before",
    "agent_rule_only",
    "onboarding_only",
    "crm_field_only",
    "combined",
)

SIMULATION_ACTOR_TYPES: Set[str] = {
    "sales_agent",
    "simulated_human_seller",
}

SOURCE_TYPES: Set[str] = {
    "sales_conversation",
    "normative",
    "founder_meeting",
    "crm_record",
    "unknown",
}

TRUNCATION_STATUSES: Set[str] = {
    "complete",
    "truncated_at_source",
    "blob_externalized",
    "unknown",
}

FACT_TYPES: Set[str] = {
    # Sales & general business fact types (app/extraction/prompts/sales-v1.md)
    "observation",
    "promise",
    "objection",
    "need",
    "price",
    "status",
    "rule",
    "decision",
    "risk",
    # Normative extensions (docs/agents/muse/EXTRACTION.md)
    "prohibition",
    "canon_value",
    "definition",
    "training_rule",
    # Founder / general contract v0 kinds
    "statement",
    "inference",
    "proposal",
}

KNOWLEDGE_STATES: Set[str] = {
    "known",
    "hypothesis",
}

EXTRACTION_STATUSES: Set[str] = {
    "candidate",
    "accepted",
    "rejected",
    "disputed",
}

TARGET_Q_VALUES: Set[str] = {f"Q{i}" for i in range(1, 10)}

FACT_REF_RELATIONS: Set[str] = {
    "reinforces",
    "contradicts",
    "updates",
}

SIGNAL_KINDS: Set[str] = {
    "missing_context",
    "ambiguity",
    "possible_conflict",
    "unsupported_attribution",
    "incomplete_extraction",
    "gap",
    "contradiction",
    "uncertainty",
}

QUOTE_MIN_LEN = 15
QUOTE_MAX_LEN = 300

INDEX_SPECS: Dict[str, List[Dict[str, Any]]] = {
    "raw_records": [
        {"keys": [("organization_id", 1), ("record_key", 1)], "unique": True, "name": "uniq_org_record_key"},
        {"keys": [("organization_id", 1), ("import_run_id", 1), ("source_table", 1)], "unique": False, "name": "idx_org_import_run_table"},
        {"keys": [("organization_id", 1), ("payload_sha256", 1)], "unique": False, "name": "idx_org_payload_sha256"},
    ],
    "import_runs": [
        {"keys": [("organization_id", 1), ("_id", 1), ("status", 1)], "unique": False, "name": "idx_org_import_run_status"},
    ],
    "sources": [
        {"keys": [("organization_id", 1), ("_id", 1), ("source_version", 1)], "unique": True, "name": "uniq_org_source_version"},
        {"keys": [("organization_id", 1), ("source_type", 1), ("_id", 1)], "unique": False, "name": "idx_org_source_type"},
        {"keys": [("organization_id", 1), ("text_sha256", 1)], "unique": False, "name": "idx_org_source_text_sha256"},
    ],
    "source_chunks": [
        {"keys": [("organization_id", 1), ("source_id", 1), ("source_version", 1), ("chunk_id", 1)], "unique": True, "name": "uniq_org_source_ver_chunk"},
    ],
    "extraction_runs": [
        {"keys": [("organization_id", 1), ("source_id", 1), ("source_version", 1), ("prompt_version", 1), ("model", 1), ("input_hash", 1)], "unique": False, "name": "idx_org_extraction_idempotency"},
    ],
    "claims": [
        {"keys": [("organization_id", 1), ("source_id", 1), ("chunk_id", 1), ("extraction_status", 1)], "unique": False, "name": "idx_org_source_chunk_status"},
        {"keys": [("organization_id", 1), ("fact_type", 1), ("zone", 1), ("extraction_status", 1)], "unique": False, "name": "idx_org_fact_type_zone_status"},
    ],
    "fact_refs": [
        {"keys": [("organization_id", 1), ("run_id", 1), ("chunk_id", 1)], "unique": False, "name": "idx_org_fact_refs_run_chunk"},
    ],
    "review_signals": [
        {"keys": [("organization_id", 1), ("source_id", 1), ("kind", 1)], "unique": False, "name": "idx_org_signals_source_kind"},
    ],
    "model_versions": [
        {"keys": [("organization_id", 1), ("version", 1)], "unique": True, "name": "uniq_org_model_version"},
    ],
    "decisions": [
        {"keys": [("organization_id", 1), ("subject_id", 1), ("created_at", -1)], "unique": False, "name": "idx_org_decision_subject"},
    ],
    "simulation_runs": [
        {"keys": [("organization_id", 1), ("arm", 1), ("seed", 1)], "unique": False, "name": "idx_org_sim_arm_seed"},
    ],
    "simulation_events": [
        {"keys": [("organization_id", 1), ("simulation_run_id", 1), ("period", 1), ("actor_type", 1)], "unique": False, "name": "idx_org_sim_run_period_actor"},
    ],
    "crm_deals_demo": [
        {"keys": [("organization_id", 1), ("deal_id", 1), ("crm_schema_version", 1)], "unique": True, "name": "uniq_org_demo_deal_schema"},
    ],
}


class ContractError(ValueError):
    """Raised when an operation violates database/INGESTION-CONTRACT.md invariants."""

    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def sha256_hex(text: Optional[str]) -> Optional[str]:
    """Compute SHA-256 hex digest of UTF-8 string; preserve None as None."""
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_decimal_string(val: Any) -> Optional[str]:
    """Preserve DECIMAL(38,0) as an exact string without float/JS Number rounding."""
    if val is None:
        return None
    if isinstance(val, float):
        raise ContractError(
            "invalid_decimal_type",
            "src_row_decimal must not be passed as float (risk of precision loss); use str, int, or Decimal.",
        )
    s = str(val).strip()
    try:
        d = Decimal(s)
    except InvalidOperation as exc:
        raise ContractError("invalid_decimal_value", f"Invalid decimal string: {val!r}") from exc
    if d != d.to_integral_value():
        raise ContractError("invalid_decimal_scale", f"Expected integral DECIMAL(38,0), got: {val!r}")
    return str(d.to_integral_value())


def make_envelope(
    record_id: str,
    organization_id: str = DEFAULT_ORGANIZATION_ID,
    schema_version: str = SCHEMA_VERSION,
    created_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Construct the mandatory envelope required on all collections."""
    if not organization_id or not isinstance(organization_id, str):
        raise ContractError("permission_denied", "organization_id must be a non-empty string.")
    if not record_id or not isinstance(record_id, str):
        raise ContractError("invalid_id", "_id must be a non-empty string.")
    return {
        "_id": record_id,
        "schema_version": schema_version,
        "organization_id": organization_id,
        "created_at": created_at or utc_now_iso(),
    }


def normalize_whitespace(text: str) -> str:
    """Collapse consecutive whitespace into single spaces for fallback normative quote check."""
    return re.sub(r"\s+", " ", text).strip()


def validate_quote_in_text(
    quote: Any,
    chunk_text: str,
    allow_normalized_whitespace: bool = False,
    min_len: int = QUOTE_MIN_LEN,
    max_len: int = QUOTE_MAX_LEN,
) -> Dict[str, Any]:
    """
    Validate that `quote` is an exact continuous substring of `chunk_text` within length bounds.
    Returns a quote_gate metadata dictionary with `passed`, `mode`, `char_start`, `char_end`, and `reason`.
    """
    if not isinstance(quote, str) or not quote:
        return {
            "passed": False,
            "mode": "none",
            "char_start": None,
            "char_end": None,
            "reason": "quote_missing_or_not_string",
        }
    q_len = len(quote)
    if q_len < min_len or q_len > max_len:
        return {
            "passed": False,
            "mode": "length_check",
            "char_start": None,
            "char_end": None,
            "quote_length": q_len,
            "reason": f"quote_length_out_of_bounds({q_len} not in {min_len}..{max_len})",
        }
    idx = chunk_text.find(quote)
    if idx != -1:
        return {
            "passed": True,
            "mode": "exact_substring",
            "char_start": idx,
            "char_end": idx + q_len,
            "quote_length": q_len,
            "reason": None,
        }
    if allow_normalized_whitespace:
        norm_quote = normalize_whitespace(quote)
        norm_chunk = normalize_whitespace(chunk_text)
        norm_idx = norm_chunk.find(norm_quote)
        if norm_idx != -1:
            return {
                "passed": True,
                "mode": "normalized_whitespace",
                "char_start": None,
                "char_end": None,
                "quote_length": q_len,
                "reason": None,
            }
    return {
        "passed": False,
        "mode": "exact_substring",
        "char_start": None,
        "char_end": None,
        "quote_length": q_len,
        "reason": "quote_not_found_in_chunk_text",
    }


def validate_discount_justification(
    discount_pct: float,
    justification: Optional[str],
    justification_text: Optional[str] = None,
    require_field: bool = True,
) -> Dict[str, Any]:
    """
    Validate the Step 4 environment lever (`discount_justification` CRM field):
    - Allowed values: `longer_term`, `prepayment`, `referral`, `volume`, `other_with_text`.
    - When `discount_pct > 0` and `require_field=True`, `justification` must be one of `DISCOUNT_JUSTIFICATION_ENUM`.
    - When `justification == "other_with_text"`, `justification_text` must be a non-empty explanation (>= 10 chars).
    - Returns structured validation result including `has_justification` and `is_value_exchange`.
    """
    if discount_pct <= 0:
        return {
            "valid": True,
            "has_justification": False,
            "is_value_exchange": False,
            "justification": None,
            "reason": None,
        }
    if not justification:
        if require_field:
            return {
                "valid": False,
                "has_justification": False,
                "is_value_exchange": False,
                "justification": None,
                "reason": "missing_required_discount_justification",
            }
        return {
            "valid": True,
            "has_justification": False,
            "is_value_exchange": False,
            "justification": None,
            "reason": None,
        }
    if justification not in DISCOUNT_JUSTIFICATION_ENUM:
        return {
            "valid": False,
            "has_justification": False,
            "is_value_exchange": False,
            "justification": justification,
            "reason": f"invalid_discount_justification_enum({justification!r})",
        }
    if justification == "other_with_text":
        txt = (justification_text or "").strip()
        if len(txt) < 10:
            return {
                "valid": False,
                "has_justification": False,
                "is_value_exchange": False,
                "justification": justification,
                "reason": "other_with_text_requires_explanation_min_10_chars",
            }
    return {
        "valid": True,
        "has_justification": True,
        "is_value_exchange": justification in VALUE_EXCHANGE_JUSTIFICATIONS,
        "justification": justification,
        "reason": None,
    }
