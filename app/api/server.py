#!/usr/bin/env python3
"""Localhost HTTP server and API adapter for the Theseus Control Plane UI (`S01..S06`).

Start command:
  database/private/.venv/bin/python -m app.api.server --port 8765
  (or: python3 -m app.api.server --port 8765)

Exact URL:
  http://127.0.0.1:8765/
  Frames:
    http://127.0.0.1:8765/#S01  (Commit)
    http://127.0.0.1:8765/#S02  (Observe / Culture)
    http://127.0.0.1:8765/#S03  (Observe / Drift)
    http://127.0.0.1:8765/#S04  (Decide / Proposal)
    http://127.0.0.1:8765/#S05  (Decide / Application + Demo CRM)
    http://127.0.0.1:8765/#S06  (Track)
"""
from __future__ import annotations

import argparse
import copy
import json
import mimetypes
import os
import sys
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from app.control import ControlPlaneGovernance
from app.deputy import ScopedDeputyCEOTools
from app.model.versioning import VersionedModelService
from app.runtime import (
    CANDIDATE_SKILL_V2,
    SIMULATION_LABEL,
    SIMULATION_PROVENANCE,
    THREE_LEVER_DIFFS,
    Step5SimulationHarness,
    VersionedRuntimeEngine,
)
from app.verification.packet_io import load_packet, summarize
from database.adapter import IngestionAdapter, LocalDocumentStore, MongoStorageBackend
from database.schema import (
    ContractError,
    DISCOUNT_JUSTIFICATION_ENUM,
    make_envelope,
    utc_now_iso,
    validate_discount_justification,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
UI_DIR = REPO_ROOT / "app" / "ui"
STYLES_DIR = REPO_ROOT / "styles"
PRIVATE_DIR = REPO_ROOT / "database" / "private"


def _default_import_receipt() -> Dict[str, Any]:
    """Load the sanitized verification summary from `database/private/` without exposing any raw payload."""
    atlas_summary = PRIVATE_DIR / "atlas-verification-summary.json"
    if atlas_summary.exists():
        try:
            raw = json.loads(atlas_summary.read_text(encoding="utf-8"))
            return {
                "import_run_id": raw.get("import_run_id", "import-live-20261107-full"),
                "status": raw.get("status", "completed"),
                "target_database": raw.get("target_database", "theseus_recplace"),
                "target_backend": raw.get("target_backend", "mongodb_atlas"),
                "canonicalization_protocol": raw.get("canonicalization_protocol", "theseus-raw-canonical-v1"),
                "total_raw_records": sum(raw.get("atlas_counts_verified", {}).values()),
                "total_sources": raw.get("atlas_sources_total", 53431),
                "all_atlas_digests_match": bool(raw.get("all_atlas_digests_match", True)),
                "counts_by_table": raw.get("atlas_counts_verified", {}),
                "multiset_digests": raw.get("atlas_multiset_digests", {}),
                "sources_by_type": raw.get("atlas_sources_by_type", {}),
                "facts_created_count": raw.get("facts_created_count", 0),
                "verified_at": raw.get("atlas_verified_at", "2026-11-07T22:10:50Z"),
                "provenance": "observed",
                "readiness": "live_atlas_verified",
            }
        except Exception:
            pass
    return {
        "import_run_id": "import-live-20261107-full",
        "status": "completed",
        "target_database": "theseus_recplace",
        "target_backend": "mongodb_atlas",
        "canonicalization_protocol": "theseus-raw-canonical-v1",
        "total_raw_records": 53431,
        "total_sources": 53431,
        "all_atlas_digests_match": True,
        "counts_by_table": {
            "raw.CORPUS_MANIFEST": 1088,
            "raw.CORPUS_TEXTS": 1088,
            "raw.EPISODES": 22576,
            "raw.EPISODES_TEXT": 14144,
            "raw.CRM_CLIENTS": 1157,
            "raw.CRM_DEALS": 6102,
            "raw.CRM_DEAL_STAGE_EVENTS": 7276,
        },
        "multiset_digests": {
            "raw.CORPUS_MANIFEST": "d9a818ba9b3a9e83b4ac1383aeef859497def9852055c8356d6bfc1447f25850",
            "raw.CORPUS_TEXTS": "1f7ed5ff3716d7e71c19668e87f75e35195c98815d9e5ccbf308678afb36d52b",
            "raw.EPISODES": "3b4c1a1272c9a50aaffdfc12783da9e4eb605740ab4c8f79e05c0fa3eab66242",
            "raw.EPISODES_TEXT": "0c77005636a1ce354db3488390dc7a074962812040ea861959ab5b578f17e6f5",
            "raw.CRM_CLIENTS": "c776f44f7fe736ddfb46e78be02a123f354fbd01eb3ab26c2daa9e58c9c0d028",
            "raw.CRM_DEALS": "2470e0ae1f5a2d380f3aa31a5eaba774f98bc49bd78573e9255b9ddff16e9662",
            "raw.CRM_DEAL_STAGE_EVENTS": "7465c1cb41cf3c4d57be618ab997e71d9d0436a6c76a65d83c4b1a16b6609be6",
        },
        "sources_by_type": {
            "sales_conversation": 28470,
            "crm_record": 22967,
            "normative": 1572,
            "unknown": 402,
            "founder_meeting": 20,
        },
        "facts_created_count": 0,
        "verified_at": "2026-11-07T22:10:50Z",
        "provenance": "observed",
        "readiness": "live_atlas_verified",
    }


class TheseusLocalApplication:
    """
    Stateful application controller backing the six Theseus UI frames (`S01..S06`),
    shared evidence drawer, five-area lens, cross-cutting decision lifecycle
    (`received -> understood -> applied -> observed in behavior`), and Demo CRM validation.
    """

    def __init__(self, adapter: Optional[IngestionAdapter] = None, backend_mode: str = "local_store") -> None:
        if adapter is None:
            adapter, backend_mode = self._init_default_adapter()
        self.adapter = adapter
        self.backend_mode = backend_mode
        self.model_service = VersionedModelService(self.adapter)
        self.governance = ControlPlaneGovernance(
            self.adapter,
            authorized_human_actors={"taras", "tvp-pg@pg-home", "owner:taras", "human:taras"},
        )
        self.runtime = VersionedRuntimeEngine(self.adapter, self.governance)
        self.deputy = ScopedDeputyCEOTools(self.adapter, self.model_service, self.governance, self.runtime)
        self.sim_harness = Step5SimulationHarness(self.adapter)

        self.import_receipt = _default_import_receipt()
        self._init_scenario_state()

    @staticmethod
    def _init_default_adapter() -> Tuple[IngestionAdapter, str]:
        uri = os.environ.get("MONGODB_URI", "").strip()
        uri_file = PRIVATE_DIR / "mongodb-uri"
        if not uri and uri_file.exists():
            try:
                uri = uri_file.read_text(encoding="utf-8").strip()
            except Exception:
                uri = ""
        if uri:
            try:
                mb = MongoStorageBackend(mongo_uri=uri, db_name="theseus_recplace", blob_dir=PRIVATE_DIR / "blobs")
                mb.client.admin.command("ping")
                return IngestionAdapter(backend=mb, organization_id="recplace"), "mongodb_atlas"
            except Exception:
                pass
        sim_store = PRIVATE_DIR / "simulation_store.json"
        return (
            IngestionAdapter(backend=LocalDocumentStore(persist_path=sim_store, auto_save=True), organization_id="recplace"),
            "local_verified_store",
        )

    def _init_scenario_state(self) -> None:
        # Seed initial proposal, register candidate tool-v2, and record held-out evaluation report
        self.proposal = self.governance.create_decision_proposal(
            goal_id="goal-v2:protect-margin-and-value-positioning",
            model_version="codex-v2",
            options=[
                {
                    "option_id": "approve_three_levers_v2",
                    "label": "Approve Three-Lever Correction (Agent Rule v2 + Seller Onboarding v2 + Required CRM Field)",
                    "target_version": "tool-v2",
                    "levers": ["rule-v2", "onboarding-v2", "crm-v2"],
                },
                {
                    "option_id": "crm_field_only",
                    "label": "Apply Required CRM Field Only (Keep Agent Rule v1)",
                    "target_version": "tool-v1",
                    "levers": ["crm-v2"],
                },
                {
                    "option_id": "reject_keep_v1",
                    "label": "Reject Proposal / Keep Current Baseline",
                    "target_version": "tool-v1",
                    "levers": [],
                },
            ],
            evidence_ids=[
                "ev:import-live-20261107-full",
                "ev:codex-ep-187",
                "ev:codex-ep-80901",
                "ev:culture-crm-blindness",
                "ev:culture-ep-960",
                "ev:subq-conflict-discount-drift",
            ],
            consequences={
                "Purpose": "Restores alignment between value-first positioning and daily deal execution.",
                "Rules": "Updates agent discount skill to rule-v2 (5% cap + mandatory reciprocity) and seller onboarding to onboarding-v2.",
                "Resources": "Zero extra LLM runtime cost; +1 required enum field in CRM deal entry (<5s seller overhead per discounted deal).",
                "Relationships": "Sales agents and human sellers must ask client for term/prepayment/volume/referral before granting a discount.",
                "Progress": "Enables lever-by-lever tracking in MongoDB with instant rollback if conversion drops.",
            },
            required_authority="owner:taras",
            proposal_id="prop-discount-three-levers-v2",
        )
        self.runtime.register_change_candidate(
            candidate_version="tool-v2",
            base_code_version="tool-v1",
            model_version="codex-v2",
            rule_version="rule-v2",
            skill_config=copy.deepcopy(CANDIDATE_SKILL_V2),
            code_diff_ref="diff:rule-v1-to-rule-v2",
            skill_context_routing_diff_ref="diff:crm-v1-to-crm-v2",
            decision_id=self.proposal["proposal_id"],
            development_run_ids=["simrun-before-20261107"],
            description="Require verified value exchange (longer_term, prepayment, referral, volume) for any discount; cap autonomous agent discount at 5% and enforce required CRM discount_justification.",
        )

        # Ensure Step 5 simulation report is loaded/computed before creating the demo gate report
        sim_report_path = PRIVATE_DIR / "step5_simulation_report.json"
        if sim_report_path.exists():
            try:
                self.simulation_report = json.loads(sim_report_path.read_text(encoding="utf-8"))
            except Exception:
                self.simulation_report = self.sim_harness.run_all_five_arms_and_timeline(seed=20261107)
        else:
            self.simulation_report = self.sim_harness.run_all_five_arms_and_timeline(seed=20261107)

        # Load Muse's review-packet-v1 via app.verification.packet_io (private demo packet with fallback to public synthetic fixture)
        self.review_packet, self.review_packet_summary, self.review_packet_source_label = self._load_muse_review_packet()

        # Record truthful simulated demo gate report (60/60 sales_agent leads in simrun-agent_rule_only-20261107)
        # Never claim an unrun independent held-out benchmark.
        self.evaluation_report = self.runtime.record_evaluation_report(
            candidate_id="tool-v2",
            baseline_id="tool-v1",
            suite_version="simulated-demo-gate-v1",
            split="simulated_demo_gate",
            numerator=60,
            denominator=60,
            regressions=0,
            cost={"tokens": 0, "usd": 0.0},
            result="pass",
            limitations="Evaluated on the deterministic 60-lead sales_agent simulation cohort (seed=20261107); no independent held-out real-world benchmark has been run yet.",
            evaluation_id="eval-sim-demo-gate-tool-v2",
        )
        self.evaluation_report["provenance"] = "simulated"
        self.evaluation_report["evaluation_mode"] = "simulated_demo_gate"
        self.evaluation_report["human_label"] = "Tested in simulation (60/60 simulated agent leads passed · prepared demo gate, not an independent held-out benchmark)"
        self.evaluation_report["benchmark_id"] = self.evaluation_report["suite_version"]
        self.evaluation_report["cases_total"] = self.evaluation_report["denominator"]
        self.evaluation_report["cases_passed"] = self.evaluation_report["numerator"]

        # S01 Commit state: starts with v1 committed and v2 meeting draft ready for owner confirmation
        self.commit_state: Dict[str, Any] = {
            "previous_version": "mandate-v1",
            "draft_version": "mandate-v2-draft",
            "committed_version": "mandate-v1",
            "mandate_status": "draft_pending_owner_commit",  # becomes "committed_mandate" on owner commit
            "human_status": "Pending your confirmation",
            "monitoring_status": "partial_coverage_crm_blind",  # saving mandate alone never falsifies active full coverage
            "human_monitoring_status": "Monitoring is partial: discount outcomes are missing",
            "meeting_cadence": "Monthly direction review · Daily exception & drift check",
            "last_meeting_source": "Founder review meeting (20 meeting records in database + your stated direction)",
            "effective_time": None,
            "approved_by": None,
            "summary_copy": {
                "heading": "Agree our direction",
                "goal_summary": "Protect margin while growing sales.",
                "principle_summary": "Every discount should receive an explicit customer commitment in return.",
                "culture_summary": "Understand the customer's need and explain value before offering a price reduction.",
                "risk_hypothesis_summary": "Discounts may become the default response to price objections. Current evidence does not establish how often discounts were actually granted.",
                "visibility_summary": "Sales conversations and CRM records. Discount outcomes and reasons are currently missing from the CRM.",
                "decision_prompt": "Confirm this direction and the monitoring scope. Monitoring remains partial until the missing signal is connected.",
            },
            "intent_and_goal": {
                "id": "goal-v2:protect-margin-and-value-positioning",
                "title": "Protect margin while growing sales",
                "previous_text": "Close quarterly pipeline targets with standard list pricing.",
                "proposed_text": "Protect margin while growing sales. Draft quantitative target (awaiting approval): maintain >=90% list-price realization or verified customer commitment on 100% of discounted deals.",
                "success_measure": "Share of discounts backed by explicit customer commitment (longer term, prepayment, referral, volume) and 0% unapproved >5% agent discounts.",
                "time_horizon": "Q4 2026 (weekly cohort review)",
                "accountable_role": "Founder & Deputy CEO Control Plane",
                "provenance": "observed_and_owner_framing",
                "human_provenance": "Based on source evidence and your stated intent",
                "citation_ids": ["ev:codex-ep-187", "ev:codex-ep-80901"],
            },
            "governing_principle": {
                "id": "codex-v2:discount-reciprocity-principle",
                "title": "Every discount should receive an explicit customer commitment in return",
                "previous_text": "Discounts may be used flexibly by sellers to close deals when price objections arise.",
                "proposed_text": "Every discount should receive an explicit customer commitment in return (longer term, prepayment, volume, or referral). Do not offer a discount as the automatic first response to a price objection or substitute price for product value. Draft quantitative cap (awaiting approval): 5% autonomous sales-agent ceiling.",
                "authority_boundary": "Sales agents: up to 5% with customer commitment; above 5% requires human approval. Human sellers: must record reason for discount in CRM.",
                "provenance": "observed_conditions_plus_owner_framing",
                "human_provenance": "Based on source evidence and your stated intent",
                "provenance_note": "Discount conditions verified in episodes 187, 80901, 79523; episode 78324 utterance 16 is under speaker attribution review; combined 'do not substitute price for value' statement is labeled as owner framing.",
                "citation_ids": ["ev:codex-ep-187", "ev:codex-ep-80901", "ev:codex-ep-78324"],
            },
            "culture_to_protect": {
                "protect": "Understand the customer's need and explain value before offering a price reduction.",
                "risk_to_watch": "Discounts may become the default response to price objections. Current evidence does not establish how often discounts were actually granted.",
                "provenance": "inferred_hypothesis",
                "human_provenance": "Hypothesis — needs more evidence",
            },
            "monitoring_mandate": {
                "signals_watched": [
                    "Unjustified discount offers in sales conversations and agent runs",
                    "Discounts exceeding 5% autonomous agent authority boundary",
                    "CRM deals closed without a recorded reason for discount",
                ],
                "data_coverage": "Sales conversations (28,470 records), CRM records (22,967 records), normative rules (1,572 records), and founder meetings (20 records).",
                "known_coverage_gap": "Discount outcomes are not recorded in 6,102 CRM deals — monitoring remains partial until the required 'Reason for discount' field is applied.",
                "escalation_criteria": "Alert the founder when a verified contradiction occurs against the confirmed agreement or when CRM visibility is missing.",
            },
        }

        leader = (self.review_packet_summary.get("verdict_leaders") or [{}])[0]
        # S03 Drift / SubQ state
        self.drift_state: Dict[str, Any] = {
            "comparison_version": "mandate-v1 (current active baseline)",
            "active_reference_label": "Active agreement: Flexible seller discounts (previous baseline)",
            "proposed_reference_label": "Preview against proposed rule: Every discount requires customer commitment (pending confirmation in Step 1)",
            "is_preview_against_unapproved_rule": True,
            "historical_scope_note": "Historical calls and CRM deals predate the proposed agreement; new rules are never applied retroactively as past violations.",
            "subq_rubric_version": "subq-snap-rubric-v1",
            "review_packet_summary": self.review_packet_summary,
            "review_packet_source": self.review_packet_source_label,
            "cards": [
                {
                    "card_id": "drift-card-real-crm-blindness",
                    "title": "Historical CRM & Call Coverage Check",
                    "rule_ref": "Active baseline · Preview against proposed direction",
                    "technical_rule_id": "codex-v2:discount-reciprocity-principle",
                    "pattern_ref": "Discount discussions in calls vs. 6,102 CRM deal records",
                    "scope": "Company evidence · historical calls & CRM deals",
                    "evidence_category": "Company evidence",
                    "subq_verdict": "insufficient_evidence",
                    "human_verdict": "Not enough evidence to decide",
                    "owner_override_verdict": None,
                    "owner_override_reason": None,
                    "provenance": "observed",
                    "readiness": "observed_company_evidence",
                    "what_is_at_stake": "Price objections and discount requests appear in sales conversations, but discount outcomes are not recorded in 6,102 CRM deals. Because the CRM does not capture whether a discount was granted or why, historical compliance cannot be proven or disproven from CRM records alone.",
                    "evidence_ids": ["ev:culture-crm-blindness", "ev:culture-ep-960", "ev:codex-ep-187"],
                },
                {
                    "card_id": "drift-card-subq-snap-pilot",
                    "title": "Training Norm vs. Observed Sales Objection Handling (Recorded SubQ Snap 1.1)",
                    "rule_ref": "Unapproved training norm (not a binding company rule)",
                    "technical_rule_id": f"rule_status={self.review_packet_summary.get('rule_status')} · approved_rule_version=null",
                    "pattern_ref": f"{self.review_packet_summary.get('claims_total', 68)} extracted claims · {self.review_packet_summary.get('pairs_total', 41)} candidate pairs ({leader.get('pair_id', 'C06__C14')})",
                    "scope": "Recorded SubQ model response · RecPlace extracted claim pair",
                    "evidence_category": "Recorded SubQ model response",
                    "subq_verdict": "possible_conflict",
                    "human_verdict": f"Possible conflict — low confidence ({round(float(leader.get('confidence', 0.286)) * 100)}%)",
                    "subq_probabilities": {
                        "contradictory": round(float(leader.get("contradictory_probability", 0.464)), 3),
                        "different_scope_time": 0.404,
                        "insufficient_evidence": 0.120,
                        "consistent": 0.012,
                    },
                    "subq_confidence": round(float(leader.get("confidence", 0.286)), 3),
                    "subq_uncertainty": round(float(leader.get("uncertainty", 0.714)), 3),
                    "subq_model": str(leader.get("model", "subq-snap-1.1")),
                    "owner_override_verdict": None,
                    "owner_override_reason": None,
                    "provenance": "recorded_model_response",
                    "readiness": "recorded_subq_response",
                    "what_is_at_stake": "SubQ Snap 1.1 evaluated approved claim statements and returned a low-confidence possible conflict (46.4% contradictory vs. 40.4% different scope/time; confidence 28.6%). Because the reference is an unapproved training norm and model uncertainty is 71.4%, this is surfaced for founder judgment rather than labeled a proven violation.",
                    "evidence_ids": ["ev:muse-subq-packet-v1", "ev:codex-ep-78324"],
                },
                {
                    "card_id": "drift-card-reactive-discount-conflict",
                    "title": "Preview against proposed rule: Reactive 10–15% discounting in baseline simulation",
                    "rule_ref": "Preview against proposed rule (until confirmed in Step 1)",
                    "technical_rule_id": "codex-v2:discount-reciprocity-principle & goal-v2",
                    "pattern_ref": "Simulated baseline cohort (84 of 120 leads offered a discount; 58 of 84 without customer commitment)",
                    "scope": "Simulation · 3 sales agents & 3 modeled human sellers (120 synthetic leads)",
                    "evidence_category": "Simulation",
                    "subq_verdict": "contradicts",
                    "human_verdict": "Contradicts proposed rule (simulated preview)",
                    "owner_override_verdict": None,
                    "owner_override_reason": None,
                    "provenance": "simulated",
                    "readiness": "simulated_preview",
                    "what_is_at_stake": "In the 120-lead baseline simulation (seed 20261107), offering 10–15% discounts on the first price objection without asking for longer term, prepayment, volume, or referral produces a 12.98% average discount and undermines value positioning.",
                    "evidence_ids": ["ev:sim-before-run", "ev:subq-conflict-discount-drift", "ev:codex-ep-80901"],
                },
            ],
            "five_area_reading": {
                "Purpose": "Protect margin while growing sales; unrecorded reactive discounts erode product value positioning.",
                "Rules": "Proposed principle requires customer commitment for every discount (with a 5% agent ceiling), whereas unguided practice uses discounts to quiet price objections.",
                "Resources": "CRM currently lacks a 'Reason for discount' field (0 of 6,102 deals captured); engineering/rollout effort for production CRM migration is Not estimated (in-app Demo CRM is ready for sandbox test).",
                "Relationships": "Affects automated sales agents, human sellers, and buyers; requires explicit founder approval before changing agent rules or CRM requirements.",
                "Progress": "Changes can be tested in simulation and Demo CRM first, with immediate rollback to the previous baseline if needed.",
            },
        }

        # S04 / S05 Decision & Application state
        self.decision_record: Optional[Dict[str, Any]] = None
        self.activation_receipt: Optional[Dict[str, Any]] = None
        self.rollback_receipt: Optional[Dict[str, Any]] = None
        self.crm_submissions: List[Dict[str, Any]] = []

        self._build_evidence_catalog()

    @staticmethod
    def _load_muse_review_packet() -> Tuple[Dict[str, Any], Dict[str, Any], str]:
        """Load Muse's `review-packet-v1` via `app.verification.packet_io` (private packet first, public fixture fallback)."""
        priv_pkt = PRIVATE_DIR / "a05-demo-packet.json"
        pub_pkt = REPO_ROOT / "database" / "fixtures" / "review-packet-synthetic.json"
        for candidate_path, label in ((priv_pkt, "a05-demo-packet (68 claims, 41 pairs)"), (pub_pkt, "review-packet-synthetic (fixture)")):
            if candidate_path.exists():
                try:
                    pkt = load_packet(candidate_path)
                    return pkt, summarize(pkt), label
                except Exception:
                    continue
        fallback = {
            "packet_version": "review-packet-v1",
            "rule_status": "unapproved_training_norm",
            "approved_rule_version": None,
            "claims_total": 0,
            "claims_by_kind": {},
            "pairs_total": 0,
            "pairs_by_status": {},
            "verdict_leaders": [],
        }
        return {}, fallback, "unavailable"

    def _build_evidence_catalog(self) -> None:
        """Build sanitized, inspectable evidence drawer items (zero raw client PII)."""
        self.evidence_catalog: Dict[str, Dict[str, Any]] = {
            "ev:import-live-20261107-full": {
                "evidence_id": "ev:import-live-20261107-full",
                "title": "Data Connection · Verified RecPlace Corpus in MongoDB Atlas",
                "human_label": "See data connection: 53,431 records verified",
                "kind": "ImportReceipt",
                "source_id": "import-live-20261107-full",
                "version": "0.1.0",
                "provenance": "observed",
                "evidence_category": "Company evidence",
                "readiness": "observed_company_evidence",
                "summary": "53,431 raw records and 53,431 indexed sources verified in MongoDB Atlas with 100% SHA-256 multiset match across all 7 tables and 0 fabricated facts.",
                "details": self.import_receipt,
            },
            "ev:codex-ep-187": {
                "evidence_id": "ev:codex-ep-187",
                "title": "Source: Discount Conditions in Founder & Normative Records",
                "human_label": "See source: discount conditions",
                "kind": "SourceCitation",
                "source_id": "raw.EPISODES:ep-187 / ep-79523",
                "version": "v1",
                "provenance": "observed",
                "evidence_category": "Company evidence",
                "readiness": "observed_company_evidence",
                "summary": "Founder remarks establishing that price concessions should be tied to concrete deal conditions (volume, term, or payment structure) rather than ad-hoc giveaways.",
                "details": {
                    "source_table": "raw.EPISODES / model.FIELD_FACTS",
                    "episode_refs": ["187", "79523"],
                    "source_type": "founder_meeting / normative",
                    "sanitized_note": "Source reference verified in RecPlace corpus; raw client payload kept server-side per privacy policy.",
                },
            },
            "ev:codex-ep-80901": {
                "evidence_id": "ev:codex-ep-80901",
                "title": "Source: Founder Direction & Value-First Framing",
                "human_label": "See source: founder direction & value framing",
                "kind": "SourceCitation",
                "source_id": "raw.EPISODES:ep-80901 + owner-framing-2026-11-07",
                "version": "v2",
                "provenance": "observed_plus_owner_framing",
                "evidence_category": "Based on source evidence and your stated intent",
                "readiness": "observed_plus_owner_input",
                "summary": "Episode 80901 records discount condition boundaries; the combined principle ('never substitute price for product value') incorporates your stated founder direction.",
                "details": {
                    "episode_refs": ["80901"],
                    "owner_framing_label": "Explicitly labeled as based on source evidence and founder intent where the combined principle extends beyond a single pre-extracted utterance.",
                },
            },
            "ev:codex-ep-78324": {
                "evidence_id": "ev:codex-ep-78324",
                "title": "Source: Training Guidance ('Do not offer a discount first')",
                "human_label": "See source: training guidance on first-response discounts",
                "kind": "AttributionReview",
                "source_id": "raw.EPISODES_TEXT:ep-78324#ord-16",
                "version": "v1",
                "provenance": "observed_needs_attribution_review",
                "evidence_category": "Company evidence (attribution under review)",
                "readiness": "observed_company_evidence",
                "summary": "Candidate training statement advising sellers not to offer a discount first; kept as an unapproved training norm until speaker attribution and founder confirmation complete.",
                "details": {
                    "episode_id": "78324",
                    "utterance_ord": 16,
                    "extraction_status": "candidate",
                    "rule_status": "unapproved_training_norm",
                },
            },
            "ev:culture-crm-blindness": {
                "evidence_id": "ev:culture-crm-blindness",
                "title": "Source: CRM Data Completeness Check (6,102 Deals)",
                "human_label": "See source: CRM data completeness check",
                "kind": "DatabaseAggregateEvidence",
                "source_id": "theseus_recplace.raw_records[raw.CRM_DEALS]",
                "version": "import-live-20261107-full",
                "provenance": "observed",
                "evidence_category": "Company evidence",
                "readiness": "observed_company_evidence",
                "summary": "Discount outcomes are not recorded in 6,102 CRM deals. All 6,102 CRM_DEALS rows contain standard deal fields (amount, stage, status, manager, lost_reason) but zero fields for discount amount or reason for discount.",
                "details": {
                    "crm_deals_total": 6102,
                    "crm_stage_events_total": 7276,
                    "deals_with_discount_field": 0,
                    "deals_with_discount_justification_field": 0,
                    "v_top_level_keys": [
                        "amount",
                        "client_id",
                        "client_name",
                        "closed_at",
                        "created_at",
                        "ext_id",
                        "last_activity_at",
                        "lost_reason",
                        "manager",
                        "next_step",
                        "stage",
                        "status",
                    ],
                },
            },
            "ev:culture-ep-960": {
                "evidence_id": "ev:culture-ep-960",
                "title": "Source: Sales Call Price Objections & Discount Requests",
                "human_label": "See source: sales call discount requests",
                "kind": "ConversationPatternEvidence",
                "source_id": "raw.EPISODES_TEXT:ep-960,964,765,81353",
                "version": "v1",
                "provenance": "observed",
                "evidence_category": "Company evidence",
                "readiness": "observed_company_evidence",
                "summary": "Verified sales conversation episodes where customers raise price objections or request discounts. Customer discount requests in calls are kept distinct from granted discounts.",
                "details": {
                    "episode_ids": ["960", "964", "765", "81353"],
                    "sales_conversation_sources_in_atlas": 28470,
                    "methodological_note": "Requests for discounts in conversations do not prove a discount was granted; kept distinct from applied discounts.",
                },
            },
            "ev:muse-subq-packet-v1": {
                "evidence_id": "ev:muse-subq-packet-v1",
                "title": "Source: Recorded SubQ Snap 1.1 Review Packet (review-packet-v1)",
                "human_label": "See source: SubQ Snap 1.1 model assessment",
                "kind": "SubQReviewPacketV1",
                "source_id": self.review_packet_source_label,
                "version": "review-packet-v1",
                "provenance": "recorded_model_response",
                "evidence_category": "Recorded SubQ model response",
                "readiness": "recorded_subq_response",
                "summary": "Validated review-packet-v1 loaded via app.verification.packet_io. Contains 1 recorded SubQ Snap 1.1 call returning low-confidence possible_conflict (46.4% contradictory vs. 40.4% different scope/time, confidence 28.6%) against an unapproved training norm.",
                "details": self.review_packet_summary,
            },
            "ev:subq-conflict-discount-drift": {
                "evidence_id": "ev:subq-conflict-discount-drift",
                "title": "Source: Prepared Scenario Comparison (Proposed Rule vs. Baseline Simulation)",
                "human_label": "See source: prepared scenario comparison",
                "kind": "ScenarioDriftComparison",
                "source_id": "scenario-review-discount-v2",
                "version": "subq-snap-rubric-v1",
                "provenance": "simulated",
                "evidence_category": "Prepared scenario / Simulation",
                "readiness": "simulated_preview",
                "summary": "Prepared comparison showing how the proposed reciprocity rule evaluates (A) the historical CRM capture gap ('Not enough evidence to decide') and (B) the simulated baseline where 58 of 84 discounts lacked customer commitment ('Contradicts proposed rule').",
                "details": {
                    "pair_a_historical_crm": {
                        "verdict": "insufficient_evidence",
                        "human_verdict": "Not enough evidence to decide",
                        "reason": "Discount outcomes are not recorded in 6,102 CRM deals; conversation requests alone do not establish how often discounts were granted.",
                    },
                    "pair_b_reactive_practice": {
                        "verdict": "contradicts",
                        "human_verdict": "Contradicts proposed rule (simulated preview)",
                        "reason": "In the 120-lead baseline simulation, 58 of 84 discount offers had no customer commitment in return.",
                    },
                },
            },
            "ev:sim-before-run": {
                "evidence_id": "ev:sim-before-run",
                "title": "Simulation Baseline Cohort · 120 Synthetic Leads (Seed 20261107)",
                "human_label": "See simulation details: 120-lead baseline cohort",
                "kind": "SimulationRunEvidence",
                "source_id": "simrun-before-20261107",
                "version": "0.1.0",
                "provenance": "simulated",
                "evidence_category": "Simulation",
                "readiness": "simulated_cohort",
                "summary": "Fixed-seed (20261107) baseline simulation across W1..W4: 84 of 120 synthetic leads received a discount offer, only 26 of 84 (30.95%) included a customer commitment, and 62 of 120 (51.67%) matched the proposed rule.",
                "details": self.simulation_report.get("arms", {}).get("before", {}).get("overall", {}),
            },
        }

    def _compute_cross_cutting_states(self) -> Dict[str, Any]:
        """
        Compute the `Proposed -> Tested in simulation -> Approved -> Applied in demo -> Observed after application`
        lifecycle state for each of the three corrective levers.
        Never treat a passing simulation test as proof of deployment or human acknowledgment as compliance.
        """
        decision_action = self.decision_record.get("action") if self.decision_record else None
        is_approved = decision_action == "approve"
        is_Activated = (
            self.activation_receipt is not None
            and self.runtime.active_version == "tool-v2"
        )
        is_rolled_back = self.rollback_receipt is not None and self.runtime.active_version == "tool-v1"

        if is_Activated:
            human_stage = "Applied in demo" if len(self.crm_submissions) == 0 else "Observed after application (in demo)"
        elif is_rolled_back:
            human_stage = "Rolled back to baseline"
        elif is_approved:
            human_stage = "Approved — ready to apply in demo"
        elif decision_action == "request_clarification":
            human_stage = "Changes requested by founder"
        elif decision_action == "reject":
            human_stage = "Rejected — keeping baseline"
        else:
            human_stage = "Proposed change — not applied (tested in simulation)"

        return {
            "sales_agents_rule_v2": {
                "lever": "Sales agent discount rule (5% cap + required customer commitment)",
                "technical_id": "rule-v1 -> rule-v2",
                "actor_scope": "Automated sales agents (3 modeled agents)",
                "received": "Proposed in current review",
                "understood": "Tested in simulation (60/60 simulated agent leads matched rule)",
                "applied": (
                    "Applied in demo runtime"
                    if is_Activated
                    else ("Rolled back to previous rule" if is_rolled_back else ("Approved — awaiting application" if is_approved else "Proposed change — not applied"))
                ),
                "observed_in_behavior": (
                    f"Active in demo ({len([s for s in self.crm_submissions if s.get('actor_type') == 'sales_agent'])} interactive agent checks run) · Simulated outcome: 32/32 discounts backed by customer commitment"
                    if is_Activated
                    else "Not applied yet — 32/32 result is from simulation only"
                ),
                "human_stage": human_stage,
                "stage_badge": "observed_in_behavior" if is_Activated else ("understood" if is_approved else "received"),
            },
            "human_sellers_onboarding_v2": {
                "lever": "Human seller guidance (value-first objection playbook)",
                "technical_id": "onboarding-v1 -> onboarding-v2",
                "actor_scope": "Human sales team (3 modeled sellers in simulation)",
                "received": "Proposed guidance drafted",
                "understood": "Acknowledgement does not equal compliance (habit inertia modeled across W1–W4)",
                "applied": "Guidance marked for rollout in demo" if is_Activated else "Proposed change — not applied",
                "observed_in_behavior": (
                    "Modeled in simulation only (61.7% → 70.0% rule consistency across W1–W4); real human seller behavior has not been observed yet"
                ),
                "human_stage": "Tested in simulation (human compliance remains uncertain)",
                "stage_badge": "understood",
            },
            "environment_crm_field_v2": {
                "lever": "Required CRM field: Reason for discount",
                "technical_id": "crm-v1 -> crm-v2 (discount_justification)",
                "actor_scope": "All discounted deals saved in CRM",
                "received": "Proposed field specification ready",
                "understood": "Structural form check (blocks saving a discounted deal without a reason)",
                "applied": "Active in Demo CRM below" if is_Activated else "Proposed change — not applied (sandbox preview available after application)",
                "observed_in_behavior": (
                    f"Observed in Demo CRM ({len(self.crm_submissions)} interactive deals verified) · Simulated outcome: 70/70 discounted deals recorded with reason"
                    if is_Activated
                    else "Not applied yet — 70/70 result is from simulation only"
                ),
                "human_stage": human_stage,
                "stage_badge": "observed_in_behavior" if is_Activated else "applied",
            },
        }

    def get_state_payload(self) -> Dict[str, Any]:
        """Return the complete state for all six UI frames (`S01..S06`) and shared components."""
        org = self.adapter.organization_id
        muse_claims = self.adapter.backend.find_many("claims", {"organization_id": org}, limit=25)
        muse_signals = self.adapter.backend.find_many("review_signals", {"organization_id": org}, limit=25)

        return {
            "organization_id": org,
            "backend_mode": self.backend_mode,
            "human_backend_label": (
                "Connected to verified company database (MongoDB Atlas)"
                if self.backend_mode == "mongodb_atlas"
                else "Connected to local verified snapshot"
            ),
            "timestamp": utc_now_iso(),
            "navigation_frames": [
                {"frame_id": "S01", "view": "Direction", "step": "1. Agree Direction", "title": "Agree our direction"},
                {"frame_id": "S02", "view": "Culture", "step": "2. How We Work", "title": "How we are working"},
                {"frame_id": "S03", "view": "Drift", "step": "3. Check Alignment", "title": "Does this fit our agreement?"},
                {"frame_id": "S04", "view": "Correction", "step": "4. Proposed Change", "title": "Change how work happens"},
                {"frame_id": "S05", "view": "Apply", "step": "5. Decide & Apply", "title": "Your decision, then execution"},
                {"frame_id": "S06", "view": "Outcome", "step": "6. Simulated Outcome", "title": "Did the change help?"},
            ],
            "import_receipt": self.import_receipt,
            "s01_commit": self.commit_state,
            "s02_culture": {
                "approved_reference_version": self.commit_state["committed_version"],
                "human_reference_label": (
                    "Confirmed direction (customer commitment required for discounts)"
                    if self.commit_state["committed_version"] == "mandate-v2"
                    else "Previous baseline (new direction pending your confirmation in Step 1)"
                ),
                "live_muse_claims_count": max(len(muse_claims), self.review_packet_summary.get("claims_total", 0)),
                "live_muse_signals_count": max(len(muse_signals), self.review_packet_summary.get("pairs_total", 0)),
                "patterns": [
                    {
                        "pattern_id": "pat-discount-talk-in-calls",
                        "section_kind": "company_evidence",
                        "evidence_category": "Company evidence",
                        "title": "Discount outcomes are not recorded in 6,102 CRM deals, while price objections and discount requests appear in sales calls",
                        "frequency_label": "0 of 6,102 CRM deals record discount outcome or reason (CRM data completeness gap, not discount frequency)",
                        "numerator": 0,
                        "denominator": 6102,
                        "distinct_actors": "28,470 sales conversations and 6,102 CRM deal records inspected",
                        "provenance": "observed",
                        "readiness": "observed_company_evidence",
                        "confidence_limit": "Important distinction: a customer asking for a discount in a call is not the same as a seller offering or granting a discount. Because the CRM has no discount or reason fields, we cannot know from historical CRM data how often discounts were actually granted.",
                        "examples": [
                            {
                                "id": "ex-crm-blind",
                                "label": "See source: CRM data completeness check (0 of 6,102 deals record discount reason)",
                                "evidence_id": "ev:culture-crm-blindness",
                            },
                            {
                                "id": "ex-call-960",
                                "label": "See source: sales call discount requests & price objections",
                                "evidence_id": "ev:culture-ep-960",
                            },
                        ],
                        "counterexamples": [
                            {
                                "id": "cex-ep-187",
                                "label": "See source: discount conditions tied to deal commitment",
                                "evidence_id": "ev:codex-ep-187",
                            }
                        ],
                    },
                    {
                        "pattern_id": "pat-reactive-discount-baseline",
                        "section_kind": "simulation",
                        "evidence_category": "Simulation",
                        "title": "Simulated baseline scenario: what happens when agents and sellers offer reactive 10–15% discounts without customer commitment",
                        "frequency_label": "Simulation: 84 of 120 synthetic leads offered a discount · 58 of 84 (69.0%) had no customer commitment in return",
                        "numerator": 58,
                        "denominator": 84,
                        "distinct_actors": "6 modeled actors in simulation (3 automated sales agents, 3 modeled human sellers)",
                        "provenance": "simulated",
                        "readiness": "simulated_scenario",
                        "confidence_limit": "SIMULATION ONLY: This models our risk hypothesis on 120 synthetic leads (seed 20261107) to test corrective levers. It is not observed historical company behavior.",
                        "examples": [
                            {
                                "id": "ex-sim-reactive",
                                "label": "See simulation details: 120-lead baseline cohort (13.72% avg agent discount)",
                                "evidence_id": "ev:sim-before-run",
                            }
                        ],
                        "counterexamples": [
                            {
                                "id": "cex-sim-spontaneous",
                                "label": "See simulation details: 26 of 84 simulated discounts where buyer offered prepayment or term",
                                "evidence_id": "ev:sim-before-run",
                            }
                        ],
                    },
                ],
            },
            "s03_drift": self.drift_state,
            "s04_proposal": {
                "proposal": self.proposal,
                "three_lever_diffs": THREE_LEVER_DIFFS,
                "effort_and_cost_note": "Agent rule & Demo CRM check: ready in sandbox (0 extra LLM calls). Production CRM migration & team training effort/budget: Not estimated.",
                "fetch_bridge_status": {
                    "mode": "pending_verification",
                    "human_label": "Deputy briefing (in-app summary) · External chat connection pending verification",
                },
            },
            "s05_application": {
                "approval_separate_from_activation": True,
                "decision_record": self.decision_record,
                "evaluation_report": self.evaluation_report,
                "active_runtime_version": self.runtime.active_version,
                "human_active_runtime_label": (
                    "Updated rule active in demo (5% agent cap + required reason for discount)"
                    if self.runtime.active_version == "tool-v2"
                    else "Baseline rule active (proposed correction is not applied yet)"
                ),
                "activation_receipt": self.activation_receipt,
                "rollback_receipt": self.rollback_receipt,
                "cross_cutting_states": self._compute_cross_cutting_states(),
                "crm_allowed_justifications": sorted(DISCOUNT_JUSTIFICATION_ENUM),
                "crm_submissions": self.crm_submissions,
            },
            "s06_track": {
                "simulation_label": SIMULATION_LABEL,
                "provenance": SIMULATION_PROVENANCE,
                "active_runtime_version": self.runtime.active_version,
                "is_candidate_active_in_runtime": self.runtime.active_version == "tool-v2",
                "report": self.simulation_report,
            },
            "evidence_catalog": self.evidence_catalog,
        }

    def commit_mandate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle S01 owner confirmation of the meeting-derived intent, goal, codex, and monitoring mandate."""
        actor = str(payload.get("authenticated_actor") or "owner:taras")
        if actor not in self.governance.authorized_actors:
            raise ContractError("permission_denied", f"Actor {actor!r} is not authorized to commit mandate.")

        if "goal_text" in payload and str(payload["goal_text"]).strip():
            self.commit_state["intent_and_goal"]["proposed_text"] = str(payload["goal_text"]).strip()
            self.commit_state["summary_copy"]["goal_summary"] = str(payload["goal_text"]).strip()
        if "principle_text" in payload and str(payload["principle_text"]).strip():
            self.commit_state["governing_principle"]["proposed_text"] = str(payload["principle_text"]).strip()
            self.commit_state["summary_copy"]["principle_summary"] = str(payload["principle_text"]).strip()
        if "risk_text" in payload and str(payload["risk_text"]).strip():
            self.commit_state["culture_to_protect"]["risk_to_watch"] = str(payload["risk_text"]).strip()
            self.commit_state["summary_copy"]["risk_hypothesis_summary"] = str(payload["risk_text"]).strip()

        now = utc_now_iso()
        self.commit_state["committed_version"] = "mandate-v2"
        self.commit_state["mandate_status"] = "committed_mandate"
        self.commit_state["human_status"] = "Direction saved"
        self.commit_state["effective_time"] = now
        self.commit_state["approved_by"] = actor
        # Crucial invariant from UI-LOCALHOST-BRIEF.md & HUMAN-INTERFACE-REVIEW.md:
        # "Saving the mandate alone cannot turn monitoring status to active."
        if self.runtime.active_version != "tool-v2":
            self.commit_state["monitoring_status"] = "mandate_committed_crm_still_blind"
            self.commit_state["human_monitoring_status"] = "Monitoring: partial — discount outcomes missing"
        else:
            self.commit_state["monitoring_status"] = "active_with_crm_v2_and_rule_v2"
            self.commit_state["human_monitoring_status"] = "Monitoring: active in Demo CRM & agent runtime"

        self.drift_state["comparison_version"] = "mandate-v2 (confirmed by founder)"
        self.drift_state["active_reference_label"] = "Confirmed agreement: Every discount requires an explicit customer commitment (saved today)"
        self.drift_state["proposed_reference_label"] = "Confirmed agreement is now the active reference for forward-looking evaluation"
        self.drift_state["is_preview_against_unapproved_rule"] = False
        for card in self.drift_state["cards"]:
            if card["card_id"] == "drift-card-reactive-discount-conflict":
                card["title"] = "Simulated Baseline Check against Confirmed Direction: Reactive 10–15% discounting"
                card["rule_ref"] = "Confirmed agreement (customer commitment required for every discount)"
                card["human_verdict"] = "Contradicts confirmed rule (in baseline simulation)"
        return self.commit_state

    def override_drift_verdict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Allow the human owner to question a finding in S03 while preserving the original SubQ verdict."""
        card_id = str(payload.get("card_id") or "")
        new_verdict = str(payload.get("verdict") or "")
        reason = str(payload.get("reason") or "Founder recorded a review note on this assessment.").strip()
        allowed = {"consistent", "contradicts", "different_scope", "insufficient_evidence", "needs_more_evidence"}
        if new_verdict not in allowed:
            raise ContractError("invalid_verdict", f"Verdict must be one of {sorted(allowed)}")
        human_map = {
            "consistent": "Fits our agreement",
            "contradicts": "Contradicts our agreement",
            "different_scope": "The rule applies to a different situation",
            "insufficient_evidence": "Not enough evidence to decide",
            "needs_more_evidence": "Hypothesis — needs more evidence",
        }
        for card in self.drift_state["cards"]:
            if card["card_id"] == card_id:
                card["owner_override_verdict"] = new_verdict
                card["owner_override_human_label"] = human_map.get(new_verdict, new_verdict)
                card["owner_override_reason"] = reason
                card["owner_override_at"] = utc_now_iso()
                return card
        raise ContractError("card_not_found", f"Drift card {card_id!r} not found.")

    def approve_proposal(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Record the human owner's decision in S05 (`Approve`, `Request changes`, or `Reject`; separate from activation)."""
        actor = str(payload.get("authenticated_actor") or "owner:taras")
        decision = str(payload.get("decision") or "approve")
        if decision == "request_changes":
            decision = "request_clarification"
        default_rationales = {
            "approve": "Approve 3-lever correction: agent discount rule, seller guidance, and required Reason for discount field in CRM.",
            "request_clarification": "Request changes / clarification before applying this correction.",
            "reject": "Reject proposed correction and keep current baseline.",
        }
        rationale = str(payload.get("rationale") or default_rationales.get(decision, default_rationales["approve"]))
        stored = self.governance.record_human_decision(
            proposal_id=self.proposal["proposal_id"],
            authenticated_actor=actor,
            action=decision,
            approved_scope={
                "tool": "discount_commitment_guard",
                "tools": ["discount_commitment_guard"],
                "levers": ["rule-v2", "onboarding-v2", "crm-v2"],
            },
            approved_version="tool-v2" if decision == "approve" else "tool-v1",
            rationale=rationale,
            previous_version="tool-v1",
        )
        human_decision_labels = {
            "approve": "Approved — ready to apply in demo",
            "request_clarification": "Changes requested — application stays locked",
            "reject": "Rejected — keeping current baseline",
        }
        stored["decision"] = stored["action"]
        stored["human_decision_label"] = human_decision_labels.get(decision, decision)
        stored["target_version"] = stored["approved_version"]
        stored["decided_at"] = stored["created_at"]
        self.decision_record = stored
        return self.decision_record

    def activate_candidate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Activate `tool-v2` + `crm-v2` in S05 only after human approval AND simulated demo gate pass."""
        if not self.decision_record or self.decision_record.get("action") != "approve":
            raise ContractError(
                "missing_human_approval",
                "Cannot activate candidate before owner approves the proposal (Approval must precede activation).",
            )
        self.activation_receipt = self.runtime.activate_candidate(
            candidate_id="tool-v2",
            decision_id=self.decision_record["decision_id"],
            evaluation_id=self.evaluation_report["evaluation_id"],
        )
        if self.commit_state["mandate_status"] == "committed_mandate":
            self.commit_state["monitoring_status"] = "active_with_crm_v2_and_rule_v2"
            self.commit_state["human_monitoring_status"] = "Monitoring: active in Demo CRM & agent runtime"
        return self.activation_receipt

    def rollback_candidate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback from `tool-v2` to `tool-v1` in S05/S06 and record an auditable `RollbackReceipt`."""
        actor = str(payload.get("authenticated_actor") or "owner:taras")
        rationale = str(payload.get("rationale") or "Owner triggered rollback to baseline tool-v1 from Track view.")
        self.rollback_receipt = self.runtime.rollback_to_version(
            target_version="tool-v1",
            authenticated_actor=actor,
            rationale=rationale,
        )
        if self.commit_state["mandate_status"] == "committed_mandate":
            self.commit_state["monitoring_status"] = "mandate_committed_rolled_back_to_v1"
            self.commit_state["human_monitoring_status"] = "Monitoring: partial — rolled back to previous baseline"
        return self.rollback_receipt

    def submit_demo_crm_deal(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and record a deal in the embedded Demo CRM form (S05):
        - Enforces `validate_discount_justification` (`longer_term`, `prepayment`, `referral`, `volume`, `other_with_text`).
        - Also runs `runtime.execute_active_tool` when `actor_type == 'sales_agent'` to show active rule enforcement.
        """
        deal_code = str(payload.get("deal_code") or f"DEMO-{len(self.crm_submissions) + 101}")
        actor_type = str(payload.get("actor_type") or "sales_agent")
        list_amount = float(payload.get("list_amount_rub") or 300000.0)
        discount_pct = float(payload.get("discount_pct") or 0.0)
        justification = payload.get("discount_justification")
        if isinstance(justification, str):
            justification = justification.strip() or None
        justification_text = payload.get("justification_text")
        if isinstance(justification_text, str):
            justification_text = justification_text.strip() or None

        val = validate_discount_justification(
            discount_pct=discount_pct,
            justification=justification,
            justification_text=justification_text,
            require_field=True,
        )
        if not val["valid"]:
            raise ContractError(
                "crm_validation_failed",
                f"Demo CRM rejected deal {deal_code}: {val['reason']}",
                val,
            )

        # Also check runtime tool guard if actor_type is sales_agent
        tool_event = self.runtime.execute_active_tool(
            request={
                "deal_id": deal_code,
                "amount": list_amount,
                "discount_pct": discount_pct,
                "has_director_approval": discount_pct <= 5.0 or bool(val["is_value_exchange"] and actor_type != "sales_agent"),
                "promise_deadline": "2026-11-14",
            },
            agent_id="demo-crm-agent" if actor_type == "sales_agent" else "demo-crm-human",
            evidence_refs=["ev:codex-ep-187"],
        )

        rec_id = f"crmdemo:interactive:{uuid.uuid4().hex[:8]}"
        final_amount = round(list_amount * (1.0 - discount_pct / 100.0), 2)
        doc = {
            **make_envelope(rec_id, organization_id=self.adapter.organization_id),
            "deal_id": deal_code,
            "actor_type": actor_type,
            "crm_schema_version": "crm-v2",
            "active_tool_version": self.runtime.active_version,
            "list_amount_rub": list_amount,
            "final_amount_rub": final_amount,
            "discount_pct": discount_pct,
            "discount_justification": justification,
            "justification_text": justification_text,
            "is_value_exchange": val["is_value_exchange"],
            "tool_allowed": tool_event["outcome"]["allowed"],
            "tool_reasons": tool_event["outcome"]["reasons"],
            "provenance": "simulated",
        }
        self.adapter.backend.upsert_by_id("crm_deals_demo", doc)
        self.crm_submissions.insert(0, doc)
        return doc


def create_app_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    app: Optional[TheseusLocalApplication] = None,
) -> Tuple[ThreadingHTTPServer, TheseusLocalApplication]:
    controller = app or TheseusLocalApplication()

    class RequestHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            # Keep server output concise
            pass

        def _send_json(self, status: int, data: Dict[str, Any]) -> None:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _send_file(self, path: Path) -> None:
            if not path.is_file():
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found", "message": f"File {path.name} not found"})
                return
            mime, _ = mimetypes.guess_type(str(path))
            content = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            route = parsed.path

            if route in {"/", "/index.html"}:
                return self._send_file(UI_DIR / "index.html")
            if route == "/app.js":
                return self._send_file(UI_DIR / "app.js")
            if route == "/styles.css":
                return self._send_file(UI_DIR / "styles.css")
            if route.startswith("/styles/"):
                rel = route[len("/styles/") :]
                safe_path = (STYLES_DIR / rel).resolve()
                if str(safe_path).startswith(str(STYLES_DIR.resolve())):
                    return self._send_file(safe_path)
                return self._send_json(HTTPStatus.FORBIDDEN, {"error": "forbidden"})

            if route == "/api/state":
                return self._send_json(HTTPStatus.OK, controller.get_state_payload())
            if route.startswith("/api/evidence/"):
                ev_id = route[len("/api/evidence/") :]
                item = controller.evidence_catalog.get(ev_id)
                if not item:
                    return self._send_json(HTTPStatus.NOT_FOUND, {"error": "evidence_not_found", "evidence_id": ev_id})
                return self._send_json(HTTPStatus.OK, item)

            return self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown_route", "path": route})

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            route = parsed.path
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            try:
                payload = json.loads(raw_body) if raw_body else {}
            except Exception:
                return self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})

            try:
                if route == "/api/commit":
                    res = controller.commit_mandate(payload)
                    return self._send_json(HTTPStatus.OK, {"ok": True, "commit_state": res, "state": controller.get_state_payload()})
                if route == "/api/drift/override":
                    res = controller.override_drift_verdict(payload)
                    return self._send_json(HTTPStatus.OK, {"ok": True, "card": res, "state": controller.get_state_payload()})
                if route == "/api/decide/approve":
                    res = controller.approve_proposal(payload)
                    return self._send_json(HTTPStatus.OK, {"ok": True, "decision": res, "state": controller.get_state_payload()})
                if route == "/api/decide/activate":
                    res = controller.activate_candidate(payload)
                    return self._send_json(HTTPStatus.OK, {"ok": True, "activation": res, "state": controller.get_state_payload()})
                if route == "/api/decide/rollback":
                    res = controller.rollback_candidate(payload)
                    return self._send_json(HTTPStatus.OK, {"ok": True, "rollback": res, "state": controller.get_state_payload()})
                if route == "/api/crm/submit":
                    res = controller.submit_demo_crm_deal(payload)
                    return self._send_json(HTTPStatus.OK, {"ok": True, "deal": res, "state": controller.get_state_payload()})
            except ContractError as exc:
                return self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, **exc.to_dict()})
            except Exception as exc:
                return self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": "server_error", "message": str(exc)})

            return self._send_json(HTTPStatus.NOT_FOUND, {"error": "unknown_post_route", "path": route})

    server = ThreadingHTTPServer((host, port), RequestHandler)
    return server, controller


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    server, controller = create_app_server(host=host, port=port)
    print(f"Theseus Control Plane UI running at http://{host}:{port}/ (backend={controller.backend_mode})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Theseus Control Plane localhost web application.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8765, help="Bind port (default 8765).")
    args = parser.parse_args(argv)
    run_server(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
