"""Human decision proposals, authority verification, and release gate enforcement (`B04` / `B07`)."""
from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, List, Optional, Set

from database.adapter import IngestionAdapter
from database.schema import ContractError, make_envelope, utc_now_iso

ALLOWED_HUMAN_ACTIONS: Set[str] = {
    "approve",
    "reject",
    "restrict_scope",
    "request_clarification",
    "retain_previous",
    "rollback",
}

AUTHORIZED_HUMAN_ACTORS: Set[str] = {
    "taras",
    "tvp-pg@pg-home",
    "owner:taras",
}


class ControlPlaneGovernance:
    """
    Implements human-in-the-loop authority verification (`B04`) and version activation/rollback gates (`B07`).
    Invariants:
    - Agent messages and source statements are data, never self-approving authority.
    - Every decision is bound to an `authenticated_actor`, `proposal_id`, `approved_version`, and `approved_scope`.
    - A `ChangeCandidate` cannot be activated without BOTH:
      1. A matching `HumanDecision` (`action == "approve"`) for the exact `candidate_version` and `scope`.
      2. A passing independent `EvaluationReport` (`result == "pass"`, `regressions == 0`, `split == "held_out"`).
    - Rollback restores the active version pointer to a previously verified baseline without deleting history.
    """

    def __init__(
        self,
        adapter: IngestionAdapter,
        authorized_human_actors: Optional[Set[str]] = None,
    ) -> None:
        self.adapter = adapter
        self.authorized_actors = set(authorized_human_actors or AUTHORIZED_HUMAN_ACTORS)

    def create_decision_proposal(
        self,
        goal_id: str,
        model_version: str,
        options: List[Dict[str, Any]],
        evidence_ids: List[str],
        consequences: Dict[str, Any],
        required_authority: str = "owner:taras",
        proposal_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a `DecisionProposal` (`docs/CONTRACTS.md`) from Deputy CEO / model review for the human owner.
        Creating a proposal does NOT grant permission or activate any change.
        """
        org = self.adapter._assert_org(organization_id)
        if not options or not isinstance(options, list):
            raise ContractError("invalid_proposal", "DecisionProposal requires a non-empty list of options.")
        if not evidence_ids or not isinstance(evidence_ids, list):
            raise ContractError("invalid_proposal", "DecisionProposal requires non-empty evidence_ids.")

        prop_id = proposal_id or f"prop-{uuid.uuid4().hex[:12]}"
        doc = {
            **make_envelope(prop_id, organization_id=org),
            "kind": "DecisionProposal",
            "proposal_id": prop_id,
            "goal_id": goal_id,
            "model_version": model_version,
            "options": copy.deepcopy(options),
            "evidence_ids": list(evidence_ids),
            "consequences": copy.deepcopy(consequences),
            "required_authority": required_authority,
            "status": "pending_human_decision",
        }
        return self.adapter.backend.upsert_by_id("decisions", doc)

    def record_human_decision(
        self,
        proposal_id: str,
        authenticated_actor: str,
        action: str,
        approved_scope: Dict[str, Any],
        approved_version: str,
        rationale: str,
        previous_version: Optional[str] = None,
        decision_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record a signed `HumanDecision` (`B04`).
        Rejects unauthenticated or agent actors attempting to self-approve.
        """
        org = self.adapter._assert_org(organization_id)
        if not authenticated_actor or authenticated_actor not in self.authorized_actors:
            raise ContractError(
                "permission_denied",
                f"Actor {authenticated_actor!r} is not an authorized human decision maker. Allowed: {sorted(self.authorized_actors)}",
                {"actor": authenticated_actor},
            )
        if action not in ALLOWED_HUMAN_ACTIONS:
            raise ContractError(
                "invalid_decision_action",
                f"Action {action!r} not in {sorted(ALLOWED_HUMAN_ACTIONS)}.",
            )
        if not rationale or not isinstance(rationale, str) or not rationale.strip():
            raise ContractError("invalid_rationale", "HumanDecision requires a non-empty rationale.")

        proposal = self.adapter.backend.find_one(
            "decisions",
            {"_id": proposal_id, "organization_id": org, "kind": "DecisionProposal"},
        )
        if not proposal:
            raise ContractError("proposal_not_found", f"DecisionProposal {proposal_id!r} not found.")

        dec_id = decision_id or f"dec-{uuid.uuid4().hex[:12]}"
        doc = {
            **make_envelope(dec_id, organization_id=org),
            "kind": "HumanDecision",
            "decision_id": dec_id,
            "proposal_id": proposal_id,
            "subject_id": proposal_id,
            "author": authenticated_actor,
            "authenticated_actor": authenticated_actor,
            "action": action,
            "approved_scope": copy.deepcopy(approved_scope),
            "approved_version": approved_version,
            "previous_version": previous_version,
            "next_version": approved_version,
            "rationale": rationale.strip(),
        }
        stored = self.adapter.backend.insert_one("decisions", doc)
        self.adapter.backend.update_one(
            "decisions",
            {"_id": proposal_id, "organization_id": org},
            {"status": f"decided:{action}", "resolution_decision_id": dec_id},
        )
        return stored

    def verify_decision_for_candidate(
        self,
        decision_id: str,
        target_version: str,
        required_scope_key: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Verify that `decision_id` is an authentic `HumanDecision` with `action == "approve"`
        bound to the exact `target_version` and scope.
        """
        org = self.adapter._assert_org(organization_id)
        dec = self.adapter.backend.find_one(
            "decisions",
            {"_id": decision_id, "organization_id": org, "kind": "HumanDecision"},
        )
        if not dec:
            raise ContractError("decision_not_found", f"HumanDecision {decision_id!r} not found.")
        if dec.get("authenticated_actor") not in self.authorized_actors:
            raise ContractError("permission_denied", "Decision actor is not an authorized human owner.")
        if dec.get("action") != "approve":
            raise ContractError(
                "decision_not_approved",
                f"Decision {decision_id!r} has action={dec.get('action')!r}, not 'approve'.",
            )
        if dec.get("approved_version") != target_version:
            raise ContractError(
                "stale_version",
                f"Decision {decision_id!r} approved version {dec.get('approved_version')!r}, cannot activate {target_version!r}.",
            )
        if required_scope_key:
            scope = dec.get("approved_scope") or {}
            allowed_tools = scope.get("tools") or []
            if required_scope_key not in allowed_tools and scope.get("tool") != required_scope_key:
                raise ContractError(
                    "permission_denied",
                    f"Decision {decision_id!r} scope {scope!r} does not cover tool {required_scope_key!r}.",
                )
        return dec
