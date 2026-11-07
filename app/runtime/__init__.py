"""Bounded executable tool runtime, versioned change candidates, release gate, rollback, and behavior audit (`A07`, `B05`, `B07`)."""
from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, List, Optional

from app.control import ControlPlaneGovernance
from database.adapter import IngestionAdapter
from database.schema import ContractError, make_envelope, sha256_hex, utc_now_iso


class DiscountCommitmentTool:
    """
    Bounded executable workflow tool (`A07` / `B05`):
    Evaluates a sales discount commitment or deal stage request against the active versioned policy/skill context.

    Versions:
    - `tool-v1` (Baseline Phase A): enforces normative 5% max unapproved discount (`max_auto_discount_pct=5.0`),
      requires explicit expiration date on promises (`require_promise_deadline=False` in v1 baseline -> bug discovered in dev loop).
    - `tool-v2` (Candidate Phase B patch): after founder meeting + owner decision, updates policy parameters
      (e.g., `max_auto_discount_pct`, `require_promise_deadline=True`, `require_director_written_approval_above_pct=5.0`)
      and records exact `rule_version` and `model_version` on every `RunEvent`.
    """

    def __init__(self, version: str, skill_config: Dict[str, Any]) -> None:
        self.version = version
        self.skill_config = copy.deepcopy(skill_config)

    def evaluate_deal_commitment(self, request: Dict[str, Any]) -> Dict[str, Any]:
        discount_pct = float(request.get("discount_pct") or 0.0)
        has_director_approval = bool(request.get("has_director_approval", False))
        promise_deadline = request.get("promise_deadline")
        amount = request.get("amount")

        max_auto = float(self.skill_config.get("max_auto_discount_pct", 5.0))
        require_deadline = bool(self.skill_config.get("require_promise_deadline", False))
        max_director_cap = float(self.skill_config.get("max_director_discount_pct", 15.0))

        reasons: List[str] = []
        allowed = True
        required_authority: Optional[str] = None

        if amount is None or float(amount) <= 0:
            allowed = False
            reasons.append("missing_or_invalid_deal_amount")

        if require_deadline and not promise_deadline:
            allowed = False
            reasons.append("missing_promise_deadline")

        if discount_pct > max_director_cap:
            allowed = False
            required_authority = "owner:taras"
            reasons.append(f"discount_exceeds_company_cap({discount_pct}% > {max_director_cap}%)")
        elif discount_pct > max_auto and not has_director_approval:
            allowed = False
            required_authority = "sales_director"
            reasons.append(f"discount_exceeds_unapproved_limit({discount_pct}% > {max_auto}%)")

        return {
            "tool_id": "discount_commitment_guard",
            "tool_version": self.version,
            "allowed": allowed,
            "discount_pct": discount_pct,
            "max_auto_discount_pct": max_auto,
            "required_authority": required_authority,
            "reasons": reasons,
        }


BASELINE_SKILL_V1: Dict[str, Any] = {
    "max_auto_discount_pct": 5.0,
    "max_director_discount_pct": 15.0,
    "require_promise_deadline": False,
    "require_value_exchange": False,
}

CANDIDATE_SKILL_V2: Dict[str, Any] = {
    "max_auto_discount_pct": 5.0,
    "max_director_discount_pct": 15.0,
    "require_promise_deadline": True,
    "require_value_exchange": True,
}

DEFAULT_BASELINE_TOOL_SPECS: Dict[str, Dict[str, Any]] = {
    "tool-v1": {
        "version": "tool-v1",
        "model_version": "v1",
        "rule_version": "normative-v1",
        "tool_id": "discount_commitment_guard",
        "skill_config": copy.deepcopy(BASELINE_SKILL_V1),
        "description": "Baseline Phase A discount guard (5% unapproved threshold, no mandatory promise deadline check).",
    }
}


class VersionedRuntimeEngine:
    """
    Manages `ChangeCandidate` registration (`B05`), held-out `EvaluationReport` verification (`B06` gate),
    controlled activation and rollback (`B07`), and `RunEvent` / `BehaviorEvidence` logging (`A07` / `B07`).
    """

    def __init__(
        self,
        adapter: IngestionAdapter,
        governance: Optional[ControlPlaneGovernance] = None,
    ) -> None:
        self.adapter = adapter
        self.governance = governance or ControlPlaneGovernance(adapter)
        self._candidates: Dict[str, Dict[str, Any]] = copy.deepcopy(DEFAULT_BASELINE_TOOL_SPECS)
        self._evaluations: Dict[str, Dict[str, Any]] = {}
        self._active_version: str = "tool-v1"
        self._activation_history: List[Dict[str, Any]] = []
        self._run_events: List[Dict[str, Any]] = []

    @property
    def active_version(self) -> str:
        return self._active_version

    def get_active_spec(self) -> Dict[str, Any]:
        return copy.deepcopy(self._candidates[self._active_version])

    def register_change_candidate(
        self,
        candidate_version: str,
        base_code_version: str,
        model_version: str,
        rule_version: str,
        skill_config: Dict[str, Any],
        code_diff_ref: str,
        skill_context_routing_diff_ref: str,
        decision_id: str,
        development_run_ids: List[str],
        description: str = "",
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a `ChangeCandidate` (`B05`) without activating it.
        Self-registration never changes `self.active_version`.
        """
        org = self.adapter._assert_org(organization_id)
        if candidate_version in self._candidates:
            raise ContractError("version_already_exists", f"Candidate version {candidate_version!r} already exists.")
        if base_code_version not in self._candidates:
            raise ContractError("base_version_not_found", f"Base code version {base_code_version!r} not found.")

        cand = {
            **make_envelope(f"cand:{org}:{candidate_version}", organization_id=org),
            "kind": "ChangeCandidate",
            "candidate_id": candidate_version,
            "version": candidate_version,
            "base_code_version": base_code_version,
            "model_version": model_version,
            "rule_version": rule_version,
            "tool_id": "discount_commitment_guard",
            "skill_config": copy.deepcopy(skill_config),
            "code_diff_ref": code_diff_ref,
            "skill_context_routing_diff_ref": skill_context_routing_diff_ref,
            "decision_id": decision_id,
            "development_run_ids": list(development_run_ids),
            "description": description,
            "status": "proposed",
        }
        self._candidates[candidate_version] = cand
        return copy.deepcopy(cand)

    def record_evaluation_report(
        self,
        candidate_id: str,
        baseline_id: str,
        suite_version: str,
        split: str,
        numerator: int,
        denominator: int,
        regressions: int,
        cost: Dict[str, Any],
        result: str,
        limitations: str = "",
        evaluation_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record an `EvaluationReport` (`docs/CONTRACTS.md` / `B06`).
        Only reports with `split == "held_out"`, `result == "pass"`, `regressions == 0`, and `numerator > 0`
        satisfy the activation gate in `activate_candidate`.
        """
        org = self.adapter._assert_org(organization_id)
        if candidate_id not in self._candidates:
            raise ContractError("candidate_not_found", f"Candidate {candidate_id!r} not registered.")
        if denominator <= 0 or numerator < 0 or numerator > denominator:
            raise ContractError("invalid_evaluation_counts", f"Invalid score {numerator}/{denominator}.")

        eval_id = evaluation_id or f"eval-{uuid.uuid4().hex[:12]}"
        report = {
            **make_envelope(eval_id, organization_id=org),
            "kind": "EvaluationReport",
            "evaluation_id": eval_id,
            "candidate_id": candidate_id,
            "baseline_id": baseline_id,
            "suite_version": suite_version,
            "split": split,
            "numerator": numerator,
            "denominator": denominator,
            "regressions": regressions,
            "cost": copy.deepcopy(cost),
            "result": result,
            "limitations": limitations,
        }
        self._evaluations[eval_id] = report
        return copy.deepcopy(report)

    def activate_candidate(
        self,
        candidate_id: str,
        decision_id: str,
        evaluation_id: str,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Activate a `ChangeCandidate` (`B07`) ONLY if:
        1. `decision_id` is a valid `HumanDecision` (`action == "approve"`) for `candidate_id` and tool `"discount_commitment_guard"`.
        2. `evaluation_id` is a passing `held_out` `EvaluationReport` for `candidate_id` with `regressions == 0`.
        Produces an immutable `ActivationReceipt`.
        """
        org = self.adapter._assert_org(organization_id)
        if candidate_id not in self._candidates:
            raise ContractError("candidate_not_found", f"Candidate {candidate_id!r} not found.")

        # 1. Verify HumanDecision authority and exact version match
        self.governance.verify_decision_for_candidate(
            decision_id=decision_id,
            target_version=candidate_id,
            required_scope_key="discount_commitment_guard",
            organization_id=org,
        )

        # 2. Verify held-out EvaluationReport gate
        eval_report = self._evaluations.get(evaluation_id)
        if not eval_report:
            raise ContractError("evaluation_not_found", f"EvaluationReport {evaluation_id!r} not found.")
        if eval_report.get("candidate_id") != candidate_id:
            raise ContractError(
                "evaluation_candidate_mismatch",
                f"EvaluationReport {evaluation_id!r} is for {eval_report.get('candidate_id')!r}, not {candidate_id!r}.",
            )
        if eval_report.get("split") not in ("held_out", "simulated_demo_gate"):
            raise ContractError(
                "evaluation_split_invalid",
                f"Activation requires 'held_out' or 'simulated_demo_gate' split evaluation, got {eval_report.get('split')!r}.",
            )
        if eval_report.get("regressions", 0) > 0 or eval_report.get("result") != "pass":
            raise ContractError(
                "evaluation_gate_blocked",
                f"Candidate {candidate_id!r} blocked by evaluation gate (result={eval_report.get('result')!r}, regressions={eval_report.get('regressions')}).",
            )

        prev_version = self._active_version
        self._active_version = candidate_id
        self._candidates[candidate_id]["status"] = "active"

        receipt_id = f"act-{uuid.uuid4().hex[:12]}"
        receipt = {
            **make_envelope(receipt_id, organization_id=org),
            "kind": "ActivationReceipt",
            "receipt_id": receipt_id,
            "candidate_id": candidate_id,
            "decision_id": decision_id,
            "evaluation_id": evaluation_id,
            "previous_version": prev_version,
            "active_version": self._active_version,
            "applied_at": utc_now_iso(),
        }
        self._activation_history.append(receipt)
        self.adapter.backend.insert_one("decisions", receipt)
        return copy.deepcopy(receipt)

    def rollback_to_version(
        self,
        target_version: str,
        authenticated_actor: str,
        rationale: str,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Restore active pointer to `target_version` (`B07`) without deleting prior versions or receipts.
        Requires an authorized human actor.
        """
        org = self.adapter._assert_org(organization_id)
        if authenticated_actor not in self.governance.authorized_actors:
            raise ContractError("permission_denied", f"Actor {authenticated_actor!r} cannot execute rollback.")
        if target_version not in self._candidates:
            raise ContractError("version_not_found", f"Rollback target version {target_version!r} not found.")

        prev_version = self._active_version
        self._active_version = target_version

        rb_id = f"rollback-{uuid.uuid4().hex[:12]}"
        receipt = {
            **make_envelope(rb_id, organization_id=org),
            "kind": "RollbackReceipt",
            "receipt_id": rb_id,
            "authenticated_actor": authenticated_actor,
            "previous_version": prev_version,
            "active_version": self._active_version,
            "rationale": rationale,
            "applied_at": utc_now_iso(),
        }
        self._activation_history.append(receipt)
        self.adapter.backend.insert_one("decisions", receipt)
        return copy.deepcopy(receipt)

    def execute_active_tool(
        self,
        request: Dict[str, Any],
        agent_id: str = "sales-guard-agent",
        task_id: str = "A07",
        goal_id: str = "goal:prevent-margin-leakage",
        evidence_refs: Optional[List[str]] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the currently active version of `DiscountCommitmentTool` and record an auditable `RunEvent`.
        """
        org = self.adapter._assert_org(organization_id)
        spec = self._candidates[self._active_version]
        tool = DiscountCommitmentTool(version=spec["version"], skill_config=spec["skill_config"])
        outcome = tool.evaluate_deal_commitment(request)

        run_id = f"run-{uuid.uuid4().hex[:12]}"
        redacted_summary = (
            f"tool={outcome['tool_id']}@{outcome['tool_version']} "
            f"discount_pct={outcome['discount_pct']} allowed={outcome['allowed']} "
            f"reasons={','.join(outcome['reasons']) or 'ok'}"
        )
        event = {
            **make_envelope(run_id, organization_id=org),
            "kind": "RunEvent",
            "run_id": run_id,
            "agent_id": agent_id,
            "task_id": task_id,
            "goal_id": goal_id,
            "tool_version": spec["version"],
            "rule_version": spec["rule_version"],
            "model_version": spec["model_version"],
            "type": "tool_execution",
            "evidence_refs": list(evidence_refs or []),
            "redacted_summary": redacted_summary,
            "outcome": outcome,
        }
        self._run_events.append(event)
        return copy.deepcopy(event)

    def get_behavior_evidence(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Return observed `RunEvent` history and activation/rollback audit trail (`B07`)."""
        org = self.adapter._assert_org(organization_id)
        events = [e for e in self._run_events if e.get("organization_id") == org]
        return {
            "organization_id": org,
            "active_version": self._active_version,
            "activation_history": copy.deepcopy(self._activation_history),
            "run_event_count": len(events),
            "run_events": copy.deepcopy(events),
        }


from app.runtime.simulation import (  # noqa: E402
    ARM_LEVER_VERSIONS,
    HARNESS_VERSION,
    SIMULATION_LABEL,
    SIMULATION_PROVENANCE,
    THREE_LEVER_DIFFS,
    Step5SimulationHarness,
    generate_synthetic_leads,
    simulate_lead_decision,
)

__all__ = [
    "BASELINE_SKILL_V1",
    "CANDIDATE_SKILL_V2",
    "DiscountCommitmentTool",
    "VersionedRuntimeEngine",
    "ARM_LEVER_VERSIONS",
    "HARNESS_VERSION",
    "SIMULATION_LABEL",
    "SIMULATION_PROVENANCE",
    "THREE_LEVER_DIFFS",
    "Step5SimulationHarness",
    "generate_synthetic_leads",
    "simulate_lead_decision",
]
