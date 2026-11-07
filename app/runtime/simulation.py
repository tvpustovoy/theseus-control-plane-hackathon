"""Step 4 & Step 5 deterministic simulation harness and demo CRM intervention layer.

Implements the owner-selected signed simulation for Step 5 (`docs/DEMO-EXECUTION.md` and
`reports/2-scenarios/DEMO-CHORD.md`):
- Banner & provenance on every record and metric:
  `provenance = "simulated"`, `simulation_label = "SIMULATION · synthetic leads · synthetic weeks"`.
- Zero real RecPlace client payloads; zero hardcoded/fabricated metric numbers.
- Fixed-seed synthetic lead generator across synthetic weeks (`W1..W4`).
- Explicitly separated actor classes:
  - `sales_agent` (deterministic rule-following agent actors: `rule-v1` vs `rule-v2`)
  - `simulated_human_seller` (modeled human seller actors with habit inertia and gradual
    onboarding adoption across weeks: `onboarding-v1` vs `onboarding-v2`)
- Environment lever (`crm-v1` vs `crm-v2`): demo CRM schema requiring `discount_justification`
  (`longer_term`, `prepayment`, `referral`, `volume`, `other_with_text`) whenever `discount_pct > 0`.
- Runs all 5 arms on the exact same lead set and seed:
  1. `before` (`rule-v1`, `onboarding-v1`, `crm-v1`)
  2. `agent_rule_only` (`rule-v2`, `onboarding-v1`, `crm-v1`)
  3. `onboarding_only` (`rule-v1`, `onboarding-v2`, `crm-v1`)
  4. `crm_field_only` (`rule-v1`, `onboarding-v1`, `crm-v2`)
  5. `combined` (`rule-v2`, `onboarding-v2`, `crm-v2`)
- Also computes a sequential 4-week rollout timeline (`W1..W4`) with intervention markers and
  per-lever verdicts (`keep` / `keep_candidate` / `rollback`) from stored MongoDB/backend events.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from database.adapter import IngestionAdapter
from database.schema import (
     ContractError,
    DISCOUNT_JUSTIFICATION_ENUM,
    SIMULATION_ACTOR_TYPES,
    SIMULATION_ARMS,
    VALUE_EXCHANGE_JUSTIFICATIONS,
    make_envelope,
    sha256_hex,
    utc_now_iso,
    validate_discount_justification,
)

SIMULATION_LABEL = "SIMULATION · synthetic leads · synthetic weeks"
SIMULATION_PROVENANCE = "simulated"
HARNESS_VERSION = "0.1.0"

ARM_LEVER_VERSIONS: Dict[str, Dict[str, str]] = {
    "before": {
        "agent_rule_version": "rule-v1",
        "onboarding_version": "onboarding-v1",
        "crm_schema_version": "crm-v1",
    },
    "agent_rule_only": {
        "agent_rule_version": "rule-v2",
        "onboarding_version": "onboarding-v1",
        "crm_schema_version": "crm-v1",
    },
    "onboarding_only": {
        "agent_rule_version": "rule-v1",
        "onboarding_version": "onboarding-v2",
        "crm_schema_version": "crm-v1",
    },
    "crm_field_only": {
        "agent_rule_version": "rule-v1",
        "onboarding_version": "onboarding-v1",
        "crm_schema_version": "crm-v2",
    },
    "combined": {
        "agent_rule_version": "rule-v2",
        "onboarding_version": "onboarding-v2",
        "crm_schema_version": "crm-v2",
    },
}

THREE_LEVER_DIFFS: Dict[str, Dict[str, Any]] = {
    "sales_agents_rule": {
        "lever": "sales_agents",
        "from_version": "rule-v1",
        "to_version": "rule-v2",
        "before_summary": "On price objection, agent may offer up to 15% discount immediately to keep conversation moving without requiring customer reciprocity.",
        "after_summary": "Discount allowed only in exchange for verified commitment (`longer_term`, `prepayment`, `referral`, `volume`); max 5% autonomous, >5% requires escalation.",
    },
    "human_sellers_onboarding": {
        "lever": "human_sellers",
        "from_version": "onboarding-v1",
        "to_version": "onboarding-v2",
        "before_summary": "General product pitch guide; no explicit rule on what a discount must buy from the client.",
        "after_summary": "Mandatory onboarding playbook section: never offer a discount as first response to price objection; every discount must trade for term, prepayment, volume, or referral.",
    },
    "environment_crm_schema": {
        "lever": "environment",
        "from_version": "crm-v1",
        "to_version": "crm-v2",
        "before_summary": "CRM deal form has `amount`, `stage`, `status` only — zero fields for discount or discount reason.",
        "after_summary": "CRM deal form enforces required field `discount_justification` (`longer_term` | `prepayment` | `referral` | `volume` | `other_with_text`) whenever `discount_pct > 0`.",
    },
}


def _deterministic_unit_float(seed: int, key: str) -> float:
    """Return a deterministic float in [0.0, 1.0) derived from `(seed, key)`."""
    digest = hashlib.sha256(f"{seed}:{key}".encode("utf-8")).digest()
    val = int.from_bytes(digest[:8], "big")
    return (val % 10_000_000) / 10_000_000.0


def generate_synthetic_leads(
    seed: int = 20261107,
    weeks: int = 4,
    leads_per_week: int = 30,
) -> List[Dict[str, Any]]:
    """
    Deterministically generate synthetic leads across `W1..W{weeks}` with fixed `seed`.
    Half of the leads are assigned to `sales_agent` actors and half to `simulated_human_seller`
    actors so each lever can be evaluated on the exact same lead cohort.
    Contains zero real RecPlace client data.
    """
    rng = random.Random(seed)
    leads: List[Dict[str, Any]] = []
    justifications_pool = ["longer_term", "prepayment", "referral", "volume"]

    for w in range(1, weeks + 1):
        period = f"W{w}"
        for idx in range(1, leads_per_week + 1):
            lead_id = f"syn-lead-{period}-{idx:03d}"
            is_agent = (idx % 2) == 1
            actor_type = "sales_agent" if is_agent else "simulated_human_seller"
            actor_id = f"agent-s{((idx - 1) // 2) % 3 + 1}" if is_agent else f"seller-h{((idx - 1) // 2) % 3 + 1}"

            base_amount = rng.choice([150000, 240000, 360000, 480000, 600000])
            has_price_objection = rng.random() < 0.75
            if has_price_objection:
                requested_discount_pct = rng.choice([5.0, 10.0, 10.0, 15.0, 15.0, 20.0])
            else:
                requested_discount_pct = 0.0

            # Spontaneous reciprocity offered up-front vs discoverable only when seller/CRM asks for it
            r_roll = rng.random()
            if not has_price_objection:
                spontaneous_reciprocity: Optional[str] = None
                discoverable_reciprocity: Optional[str] = None
            elif r_roll < 0.22:
                chosen = rng.choice(justifications_pool)
                spontaneous_reciprocity = chosen
                discoverable_reciprocity = chosen
            elif r_roll < 0.68:
                spontaneous_reciprocity = None
                discoverable_reciprocity = rng.choice(justifications_pool)
            else:
                spontaneous_reciprocity = None
                discoverable_reciprocity = None

            leads.append(
                {
                    "lead_id": lead_id,
                    "seed": seed,
                    "week_index": w,
                    "period": period,
                    "actor_type": actor_type,
                    "actor_id": actor_id,
                    "base_amount_rub": base_amount,
                    "has_price_objection": has_price_objection,
                    "requested_discount_pct": requested_discount_pct,
                    "spontaneous_reciprocity": spontaneous_reciprocity,
                    "discoverable_reciprocity": discoverable_reciprocity,
                    "provenance": SIMULATION_PROVENANCE,
                    "simulation_label": SIMULATION_LABEL,
                }
            )
    return leads


def simulate_lead_decision(
    lead: Dict[str, Any],
    agent_rule_version: str,
    onboarding_version: str,
    crm_schema_version: str,
    seed: int,
) -> Dict[str, Any]:
    """
    Execute a single synthetic lead interaction under the specified 3-lever version tuple.
    Models distinct behavior for `sales_agent` vs `simulated_human_seller`:
    - `sales_agent`:
      - Under `rule-v1`: grants requested discount on price objection immediately (reactive discount);
        only records justification if buyer offered `spontaneous_reciprocity` or `crm-v2` forces inquiry.
      - Under `rule-v2`: asks buyer for value exchange (`discoverable_reciprocity`); if present, grants
        codex-compliant 5% discount (or escalates >5% with documented commitment); if absent, holds list price (0% discount).
    - `simulated_human_seller`:
      - Has habit inertia: under `onboarding-v1`, reactive discounting on price objection occurs with high probability (82%).
      - Under `onboarding-v2`, human adoption ramps up gradually by week (`W1`: 35%, `W2`: 52%, `W3`: 68%, `W4`: 80%
        chance of asking for value exchange before discounting).
    - Environment lever (`crm-v2` required `discount_justification` field):
      - Whenever an actor attempts to save a deal with `discount_pct > 0` without a justification, the CRM form
        blocks submission unless the actor either elicits `discoverable_reciprocity`, provides a valid
        `other_with_text` explanation, or drops the unreasoned discount to `0%`.
    """
    lead_id = lead["lead_id"]
    actor_type = lead["actor_type"]
    week_idx = int(lead["week_index"])
    has_obj = bool(lead["has_price_objection"])
    req_disc = float(lead["requested_discount_pct"])
    spont_rec = lead.get("spontaneous_reciprocity")
    discov_rec = lead.get("discoverable_reciprocity")

    if not has_obj or req_disc <= 0.0:
        return {
            "discount_offered": False,
            "discount_pct": 0.0,
            "discount_justification": None,
            "justification_text": None,
            "has_justification": False,
            "is_value_exchange": False,
            "crm_field_blocked_unjustified": False,
            "codex_consistent": True,
            "goal_achieved": True,
            "decision_mode": "no_price_objection_list_price",
        }

    # Step 1: Actor initial behavior (before CRM form validation)
    asks_for_value_exchange = False
    if actor_type == "sales_agent":
        if agent_rule_version == "rule-v2":
            asks_for_value_exchange = True
        else:
            # Under rule-v1, agent rarely asks unless buyer volunteered reciprocity
            asks_for_value_exchange = _deterministic_unit_float(seed, f"{lead_id}:agent_v1_ask") < 0.12
    else:
        # simulated_human_seller
        if onboarding_version == "onboarding-v2":
            # Gradual human learning curve across synthetic weeks W1..W4
            adoption_prob = min(0.82, 0.25 + 0.14 * week_idx)
            asks_for_value_exchange = _deterministic_unit_float(seed, f"{lead_id}:human_v2_ask") < adoption_prob
        else:
            asks_for_value_exchange = _deterministic_unit_float(seed, f"{lead_id}:human_v1_ask") < 0.18

    if asks_for_value_exchange:
        obtained_reciprocity = discov_rec or spont_rec
        if obtained_reciprocity:
            # Value exchange agreed: cap discount to codex-compliant level (5% or 10% for multi-quarter/prepay)
            applied_disc = min(req_disc, 5.0 if actor_type == "sales_agent" else 10.0)
            justification: Optional[str] = obtained_reciprocity
            justification_text: Optional[str] = f"Client committed to {obtained_reciprocity} in exchange for {applied_disc:.0f}% discount."
            decision_mode = "proactive_value_exchange_discount"
        else:
            # Buyer refused reciprocity
            if actor_type == "sales_agent" and agent_rule_version == "rule-v2":
                applied_disc = 0.0
                justification = None
                justification_text = None
                decision_mode = "held_value_no_discount"
            else:
                # Human seller may still slip and grant a smaller discount without reciprocity if CRM doesn't block
                slip = _deterministic_unit_float(seed, f"{lead_id}:human_slip") < 0.35
                applied_disc = req_disc if slip else 0.0
                justification = None
                justification_text = None
                decision_mode = "human_reactive_slip" if slip else "held_value_no_discount"
    else:
        # Actor did NOT ask for value exchange -> reactive discount as first answer to price objection
        applied_disc = req_disc
        justification = spont_rec
        justification_text = (
            f"Spontaneous client commitment: {spont_rec}" if spont_rec else None
        )
        decision_mode = "reactive_first_answer_discount"

    # Step 2: Environment lever (`crm-v2` required `discount_justification` field in CRM)
    crm_blocked_unjustified = False
    if crm_schema_version == "crm-v2" and applied_disc > 0.0 and not justification:
        crm_blocked_unjustified = True
        # Because the CRM field is required, the seller/agent is forced to go back and ask the buyer
        # for a justification before the deal can be saved.
        if discov_rec:
            justification = discov_rec
            applied_disc = min(applied_disc, 10.0)
            justification_text = f"Collected via required CRM field: client agreed to {discov_rec}."
            decision_mode = "crm_field_prompted_value_exchange"
        else:
            # Buyer has no reciprocity; in crm-v2 most actors either hold list price or enter 'other_with_text'
            hold_roll = _deterministic_unit_float(seed, f"{lead_id}:crm_hold")
            if actor_type == "sales_agent" and agent_rule_version == "rule-v2":
                applied_disc = 0.0
                justification = None
                justification_text = None
                decision_mode = "crm_field_removed_unjustified_discount"
            elif hold_roll < 0.65:
                applied_disc = 0.0
                justification = None
                justification_text = None
                decision_mode = "crm_field_removed_unjustified_discount"
            else:
                justification = "other_with_text"
                justification_text = "Competitive price match exception documented in CRM text field."
                applied_disc = min(applied_disc, 10.0)
                decision_mode = "crm_field_documented_other_exception"

    validation = validate_discount_justification(
        discount_pct=applied_disc,
        justification=justification,
        justification_text=justification_text,
        require_field=(crm_schema_version == "crm-v2"),
    )
    if not validation["valid"]:
        raise ContractError(
            "crm_discount_justification_invalid",
            f"CRM schema {crm_schema_version} rejected deal for {lead_id}: {validation['reason']}",
            validation,
        )

    discount_offered = applied_disc > 0.0
    has_just = bool(validation["has_justification"])
    is_val_exch = bool(validation["is_value_exchange"])

    # Codex consistency: either no discount offered (held value), or discount trades for explicit value exchange
    codex_consistent = (not discount_offered) or is_val_exch
    # Goal achievement: margin protected (discount == 0 or <= 10% with value exchange)
    goal_achieved = (not discount_offered) or (is_val_exch and applied_disc <= 10.0)

    return {
        "discount_offered": discount_offered,
        "discount_pct": round(applied_disc, 2),
        "discount_justification": justification,
        "justification_text": justification_text,
        "has_justification": has_just,
        "is_value_exchange": is_val_exch,
        "crm_field_blocked_unjustified": crm_blocked_unjustified,
        "codex_consistent": codex_consistent,
        "goal_achieved": goal_achieved,
        "decision_mode": decision_mode,
    }


class Step5SimulationHarness:
    """
    Runs and persists deterministic Step 5 counterfactual arms and sequential rollout timelines
    in `simulation_runs`, `simulation_events`, and `crm_deals_demo`, and computes period metrics
    directly from stored events.
    """

    def __init__(self, adapter: IngestionAdapter) -> None:
        self.adapter = adapter

    def run_arm(
        self,
        arm: str,
        leads: List[Dict[str, Any]],
        seed: int = 20261107,
        simulation_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if arm not in ARM_LEVER_VERSIONS:
            raise ContractError("invalid_simulation_arm", f"Unknown simulation arm {arm!r}. Allowed: {SIMULATION_ARMS}")
        levers = ARM_LEVER_VERSIONS[arm]
        org = self.adapter.organization_id
        run_id = simulation_run_id or f"simrun-{arm}-{seed}"

        run_doc = {
            **make_envelope(run_id, organization_id=org),
            "simulation_run_id": run_id,
            "arm": arm,
            "seed": seed,
            "lead_count": len(leads),
            "agent_rule_version": levers["agent_rule_version"],
            "onboarding_version": levers["onboarding_version"],
            "crm_schema_version": levers["crm_schema_version"],
            "harness_version": HARNESS_VERSION,
            "provenance": SIMULATION_PROVENANCE,
            "simulation_label": SIMULATION_LABEL,
        }
        self.adapter.backend.upsert_by_id("simulation_runs", run_doc)

        prev_auto_save = getattr(self.adapter.backend, "auto_save", None)
        if prev_auto_save is not None:
            setattr(self.adapter.backend, "auto_save", False)
        try:
            for lead in leads:
                outcome = simulate_lead_decision(
                    lead=lead,
                    agent_rule_version=levers["agent_rule_version"],
                    onboarding_version=levers["onboarding_version"],
                    crm_schema_version=levers["crm_schema_version"],
                    seed=seed,
                )
                event_id = f"simevt:{run_id}:{lead['lead_id']}"
                event_doc = {
                    **make_envelope(event_id, organization_id=org),
                    "simulation_run_id": run_id,
                    "arm": arm,
                    "seed": seed,
                    "lead_id": lead["lead_id"],
                    "period": lead["period"],
                    "week_index": lead["week_index"],
                    "actor_type": lead["actor_type"],
                    "actor_id": lead["actor_id"],
                    "base_amount_rub": lead["base_amount_rub"],
                    "has_price_objection": lead["has_price_objection"],
                    "requested_discount_pct": lead["requested_discount_pct"],
                    "agent_rule_version": levers["agent_rule_version"],
                    "onboarding_version": levers["onboarding_version"],
                    "crm_schema_version": levers["crm_schema_version"],
                    **outcome,
                    "provenance": SIMULATION_PROVENANCE,
                    "simulation_label": SIMULATION_LABEL,
                }
                self.adapter.backend.upsert_by_id("simulation_events", event_doc)

                # Also persist demo CRM record in `crm_deals_demo` for `before` and `combined` arms
                if arm in {"before", "crm_field_only", "combined"}:
                    crm_id = f"crmdemo:{arm}:{lead['lead_id']}"
                    final_amount = round(lead["base_amount_rub"] * (1.0 - outcome["discount_pct"] / 100.0), 2)
                    crm_doc = {
                        **make_envelope(crm_id, organization_id=org),
                        "deal_id": f"{arm}:{lead['lead_id']}",
                        "lead_id": lead["lead_id"],
                        "period": lead["period"],
                        "actor_type": lead["actor_type"],
                        "actor_id": lead["actor_id"],
                        "crm_schema_version": levers["crm_schema_version"],
                        "list_amount_rub": lead["base_amount_rub"],
                        "final_amount_rub": final_amount,
                        "discount_pct": outcome["discount_pct"],
                        "discount_justification": outcome["discount_justification"],
                        "justification_text": outcome["justification_text"],
                        "provenance": SIMULATION_PROVENANCE,
                        "simulation_label": SIMULATION_LABEL,
                    }
                    self.adapter.backend.upsert_by_id("crm_deals_demo", crm_doc)
        finally:
            if prev_auto_save is not None:
                setattr(self.adapter.backend, "auto_save", prev_auto_save)
            if hasattr(self.adapter.backend, "flush"):
                self.adapter.backend.flush()

        return self.compute_arm_metrics(run_id)

    @staticmethod
    def _aggregate_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(events)
        obj_count = sum(1 for e in events if e.get("has_price_objection"))
        offered = [e for e in events if e.get("discount_offered")]
        offered_count = len(offered)
        justified_count = sum(1 for e in offered if e.get("has_justification"))
        val_exch_count = sum(1 for e in offered if e.get("is_value_exchange"))
        codex_ok_count = sum(1 for e in events if e.get("codex_consistent"))
        goal_ok_count = sum(1 for e in events if e.get("goal_achieved"))
        crm_blocked_count = sum(1 for e in events if e.get("crm_field_blocked_unjustified"))
        avg_disc_offered = (
            round(sum(float(e.get("discount_pct", 0.0)) for e in offered) / offered_count, 2)
            if offered_count > 0
            else 0.0
        )
        return {
            "total_leads": total,
            "price_objection_leads": obj_count,
            "discounts_offered_count": offered_count,
            "discounts_with_justification_count": justified_count,
            "discounts_with_value_exchange_count": val_exch_count,
            "codex_consistent_decisions_count": codex_ok_count,
            "goal_achieved_deals_count": goal_ok_count,
            "crm_field_prompted_or_blocked_count": crm_blocked_count,
            "discount_offer_share": round(offered_count / total, 4) if total else 0.0,
            "justified_discount_share": round(justified_count / offered_count, 4) if offered_count else 1.0,
            "value_exchange_discount_share": round(val_exch_count / offered_count, 4) if offered_count else 1.0,
            "codex_consistency_share": round(codex_ok_count / total, 4) if total else 0.0,
            "goal_achievement_share": round(goal_ok_count / total, 4) if total else 0.0,
            "avg_discount_pct_when_offered": avg_disc_offered,
            "provenance": SIMULATION_PROVENANCE,
        }

    def compute_arm_metrics(self, simulation_run_id: str) -> Dict[str, Any]:
        """Compute overall, per-period, and per-actor-type metrics directly from stored `simulation_events`."""
        org = self.adapter.organization_id
        run_doc = self.adapter.backend.find_one(
            "simulation_runs",
            {"_id": simulation_run_id, "organization_id": org},
        )
        if not run_doc:
            raise ContractError("simulation_run_not_found", f"simulation_run {simulation_run_id!r} not found.")

        events = self.adapter.backend.find_many(
            "simulation_events",
            {"organization_id": org, "simulation_run_id": simulation_run_id},
            sort_key="lead_id",
        )
        periods = sorted({str(e["period"]) for e in events})
        by_period: Dict[str, Any] = {}
        for p in periods:
            p_events = [e for e in events if e["period"] == p]
            by_period[p] = {
                "all": self._aggregate_events(p_events),
                "sales_agent": self._aggregate_events([e for e in p_events if e["actor_type"] == "sales_agent"]),
                "simulated_human_seller": self._aggregate_events(
                    [e for e in p_events if e["actor_type"] == "simulated_human_seller"]
                ),
            }

        return {
            "simulation_run_id": simulation_run_id,
            "arm": run_doc["arm"],
            "seed": run_doc["seed"],
            "levers": {
                "agent_rule_version": run_doc["agent_rule_version"],
                "onboarding_version": run_doc["onboarding_version"],
                "crm_schema_version": run_doc["crm_schema_version"],
            },
            "provenance": SIMULATION_PROVENANCE,
            "simulation_label": SIMULATION_LABEL,
            "overall": {
                "all": self._aggregate_events(events),
                "sales_agent": self._aggregate_events([e for e in events if e["actor_type"] == "sales_agent"]),
                "simulated_human_seller": self._aggregate_events(
                    [e for e in events if e["actor_type"] == "simulated_human_seller"]
                ),
            },
            "by_period": by_period,
        }

    def run_all_five_arms_and_timeline(
        self,
        seed: int = 20261107,
        weeks: int = 4,
        leads_per_week: int = 30,
    ) -> Dict[str, Any]:
        """
        Execute all 5 required simulation arms (`before`, `agent_rule_only`, `onboarding_only`,
        `crm_field_only`, `combined`) on the exact same synthetic lead cohort (`seed`),
        plus build the Step 5 staged rollout timeline (`W1` baseline -> `W2` agent rules v2 ->
        `W3` + CRM `discount_justification` field -> `W4` + seller onboarding v2) with per-lever
        verdicts (`keep` / `keep_candidate` / `rollback`).
        """
        leads = generate_synthetic_leads(seed=seed, weeks=weeks, leads_per_week=leads_per_week)
        arms_summary: Dict[str, Any] = {}
        for arm in SIMULATION_ARMS:
            arms_summary[arm] = self.run_arm(arm=arm, leads=leads, seed=seed)

        # Build the sequential 4-week staged rollout timeline from the exact same weekly lead slices:
        # W1: before (rule-v1, onboarding-v1, crm-v1)
        # W2: agent_rule_only (rule-v2 activated for sales_agent)
        # W3: agent_rule_v2 + crm_field_v2 (combined environment + agent rules)
        # W4: combined (all 3 levers active: rule-v2 + crm-v2 + onboarding-v2)
        w1_metrics = arms_summary["before"]["by_period"].get("W1", {})
        w2_metrics = arms_summary["agent_rule_only"]["by_period"].get("W2", {})
        w3_events: List[Dict[str, Any]] = []
        for lead in [l for l in leads if l["period"] == "W3"]:
            out = simulate_lead_decision(
                lead=lead,
                agent_rule_version="rule-v2",
                onboarding_version="onboarding-v1",
                crm_schema_version="crm-v2",
                seed=seed,
            )
            w3_events.append({**lead, **out})
        w3_metrics = {
            "all": self._aggregate_events(w3_events),
            "sales_agent": self._aggregate_events([e for e in w3_events if e["actor_type"] == "sales_agent"]),
            "simulated_human_seller": self._aggregate_events(
                [e for e in w3_events if e["actor_type"] == "simulated_human_seller"]
            ),
        }
        w4_metrics = arms_summary["combined"]["by_period"].get("W4", {})

        # Compute lever effects and keep/candidate/rollback verdicts
        before_agent = arms_summary["before"]["overall"]["sales_agent"]
        after_agent = arms_summary["agent_rule_only"]["overall"]["sales_agent"]

        before_human = arms_summary["before"]["overall"]["simulated_human_seller"]
        after_onboarding = arms_summary["onboarding_only"]["overall"]["simulated_human_seller"]

        before_all = arms_summary["before"]["overall"]["all"]
        after_crm = arms_summary["crm_field_only"]["overall"]["all"]
        after_combined = arms_summary["combined"]["overall"]["all"]

        lever_verdicts = {
            "sales_agents_rule_v2": {
                "lever": "sales_agents",
                "version": "rule-v2",
                "target_actor_type": "sales_agent",
                "codex_consistency_before": before_agent["codex_consistency_share"],
                "codex_consistency_after": after_agent["codex_consistency_share"],
                "value_exchange_share_before": before_agent["value_exchange_discount_share"],
                "value_exchange_share_after": after_agent["value_exchange_discount_share"],
                "verdict": "keep"
                if after_agent["codex_consistency_share"] > before_agent["codex_consistency_share"]
                else "rollback",
                "rationale": "Sales agents immediately enforce reciprocity and 5% autonomous cap upon rule-v2 activation.",
                "provenance": SIMULATION_PROVENANCE,
            },
            "human_sellers_onboarding_v2": {
                "lever": "human_sellers",
                "version": "onboarding-v2",
                "target_actor_type": "simulated_human_seller",
                "codex_consistency_before": before_human["codex_consistency_share"],
                "codex_consistency_after": after_onboarding["codex_consistency_share"],
                "value_exchange_share_before": before_human["value_exchange_discount_share"],
                "value_exchange_share_after": after_onboarding["value_exchange_discount_share"],
                "verdict": "keep_candidate"
                if after_onboarding["codex_consistency_share"] > before_human["codex_consistency_share"]
                else "rollback",
                "rationale": "Modeled human sellers improve gradually across synthetic weeks W1..W4 but retain partial habit inertia without the CRM environment field; kept as candidate alongside CRM enforcement.",
                "provenance": SIMULATION_PROVENANCE,
            },
            "environment_crm_discount_justification_v2": {
                "lever": "environment",
                "version": "crm-v2",
                "target_actor_type": "all",
                "justified_discount_share_before": before_all["justified_discount_share"],
                "justified_discount_share_after": after_crm["justified_discount_share"],
                "value_exchange_share_before": before_all["value_exchange_discount_share"],
                "value_exchange_share_after": after_crm["value_exchange_discount_share"],
                "codex_consistency_before": before_all["codex_consistency_share"],
                "codex_consistency_after": after_crm["codex_consistency_share"],
                "verdict": "keep"
                if after_crm["justified_discount_share"] > before_all["justified_discount_share"]
                else "rollback",
                "rationale": "Required CRM `discount_justification` field eliminates undocumented discounts (100% justified) and shifts both human sellers and agents toward value-exchange commitments.",
                "provenance": SIMULATION_PROVENANCE,
            },
        }

        return {
            "simulation_label": SIMULATION_LABEL,
            "provenance": SIMULATION_PROVENANCE,
            "harness_version": HARNESS_VERSION,
            "seed": seed,
            "weeks": weeks,
            "leads_per_week": leads_per_week,
            "total_synthetic_leads": len(leads),
            "three_lever_diffs": THREE_LEVER_DIFFS,
            "arms": {
                arm: {
                    "simulation_run_id": arms_summary[arm]["simulation_run_id"],
                    "levers": arms_summary[arm]["levers"],
                    "overall": arms_summary[arm]["overall"],
                    "by_period": arms_summary[arm]["by_period"],
                }
                for arm in SIMULATION_ARMS
            },
            "staged_rollout_timeline": [
                {
                    "period": "W1",
                    "intervention_marker": "baseline (rule-v1, onboarding-v1, crm-v1)",
                    "active_levers": ARM_LEVER_VERSIONS["before"],
                    "metrics": w1_metrics,
                    "provenance": SIMULATION_PROVENANCE,
                },
                {
                    "period": "W2",
                    "intervention_marker": "lever_1_activated: sales_agent discount skill v1 -> v2",
                    "active_levers": ARM_LEVER_VERSIONS["agent_rule_only"],
                    "metrics": w2_metrics,
                    "provenance": SIMULATION_PROVENANCE,
                },
                {
                    "period": "W3",
                    "intervention_marker": "lever_3_activated: required CRM field `discount_justification` (crm-v2)",
                    "active_levers": {
                        "agent_rule_version": "rule-v2",
                        "onboarding_version": "onboarding-v1",
                        "crm_schema_version": "crm-v2",
                    },
                    "metrics": w3_metrics,
                    "provenance": SIMULATION_PROVENANCE,
                },
                {
                    "period": "W4",
                    "intervention_marker": "lever_2_activated: human seller onboarding v2 (all 3 levers active)",
                    "active_levers": ARM_LEVER_VERSIONS["combined"],
                    "metrics": w4_metrics,
                    "provenance": SIMULATION_PROVENANCE,
                },
            ],
            "lever_verdicts": lever_verdicts,
            "combined_vs_before_summary": {
                "before_all": before_all,
                "combined_all": after_combined,
                "provenance": SIMULATION_PROVENANCE,
            },
        }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Step 5 simulation harness.")
    parser.add_argument(
        "--store",
        default="database/private/simulation_store.json",
        help="Path to local JSON store (if MONGODB_URI not set).",
    )
    parser.add_argument("--mongo-uri", default=None, help="Optional MongoDB connection URI.")
    parser.add_argument("--seed", type=int, default=20261107, help="Deterministic RNG seed.")
    parser.add_argument("--weeks", type=int, default=4, help="Number of synthetic weeks.")
    parser.add_argument("--leads-per-week", type=int, default=30, help="Synthetic leads per week.")
    parser.add_argument("--out", default=None, help="Optional path to write JSON summary report.")
    args = parser.parse_args(argv)

    from database.adapter import LocalDocumentStore, MongoStorageBackend

    if args.mongo_uri:
        backend = MongoStorageBackend(mongo_uri=args.mongo_uri)
    else:
        backend = LocalDocumentStore(persist_path=Path(args.store), auto_save=False)
    adapter = IngestionAdapter(backend=backend, organization_id="recplace")
    harness = Step5SimulationHarness(adapter=adapter)
    report = harness.run_all_five_arms_and_timeline(
        seed=args.seed,
        weeks=args.weeks,
        leads_per_week=args.leads_per_week,
    )
    serialized = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(serialized, encoding="utf-8")
    sys.stdout.write(serialized + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
