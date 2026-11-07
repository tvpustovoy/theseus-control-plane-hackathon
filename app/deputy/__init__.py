"""Scoped Deputy CEO interface and state inspection tools (`F01`).

Note: `app/deputy/agentverse/` is reserved for Taras and `Viveka.Hackathon` and is not modified here.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from app.control import ControlPlaneGovernance
from app.model.versioning import VersionedModelService
from app.runtime import Step5SimulationHarness, THREE_LEVER_DIFFS, VersionedRuntimeEngine
from database.adapter import IngestionAdapter
from database.schema import ContractError

DEPUTY_ALLOWED_TOOLS: Set[str] = {
    "get_organization_overview",
    "list_open_conflicts_and_signals",
    "trace_evidence",
    "propose_decision_to_owner",
    "inspect_version_diff",
    "get_runtime_behavior_summary",
    "inspect_three_lever_diffs",
    "get_step5_simulation_timeline",
}


class ScopedDeputyCEOTools:
    """
    Provides strictly scoped read + proposal tools for the Fetch.ai Deputy CEO interface (`F01`).
    Invariants:
    - No arbitrary database collection access (`raw_records` direct mutation, `decisions` self-approval,
      or `activate_candidate` execution are forbidden to Deputy CEO).
    - Can inspect the 5×2 model state, trace claim provenance, inspect `ModelDiff`, and submit a
      `DecisionProposal` (`status="pending_human_decision"`) for human approval.
    """

    def __init__(
        self,
        adapter: IngestionAdapter,
        model_service: Optional[VersionedModelService] = None,
        governance: Optional[ControlPlaneGovernance] = None,
        runtime: Optional[VersionedRuntimeEngine] = None,
    ) -> None:
        self.adapter = adapter
        self.model_service = model_service or VersionedModelService(adapter)
        self.governance = governance or ControlPlaneGovernance(adapter)
        self.runtime = runtime or VersionedRuntimeEngine(adapter, self.governance)

    def invoke_scoped_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Dispatch only allowlisted Deputy CEO tools; reject any unauthorized operation."""
        if tool_name not in DEPUTY_ALLOWED_TOOLS:
            raise ContractError(
                "permission_denied",
                f"Deputy CEO is not authorized to invoke {tool_name!r}. Allowed tools: {sorted(DEPUTY_ALLOWED_TOOLS)}",
                {"requested_tool": tool_name, "allowed_tools": sorted(DEPUTY_ALLOWED_TOOLS)},
            )
        fn = getattr(self, tool_name)
        return fn(**(arguments or {}))

    def get_organization_overview(self, version: Optional[str] = None) -> Dict[str, Any]:
        """Return 5×2 summary (Purpose, Rules, Resources, Relationships, Progress), source counts, and active tool version."""
        org = self.adapter.organization_id
        snapshots = self.adapter.backend.find_many("model_versions", {"organization_id": org}, sort_key="created_at")
        target_snap = None
        if version:
            target_snap = self.adapter.backend.find_one(
                "model_versions",
                {"organization_id": org, "version": version},
            )
            if not target_snap:
                raise ContractError("version_not_found", f"Model version {version!r} not found.")
        elif snapshots:
            target_snap = snapshots[-1]

        sources_count = self.adapter.backend.count("sources", {"organization_id": org})
        candidate_claims_count = self.adapter.backend.count(
            "claims",
            {"organization_id": org, "extraction_status": "candidate"},
        )
        signals_count = self.adapter.backend.count("review_signals", {"organization_id": org})
        pending_proposals = self.adapter.backend.find_many(
            "decisions",
            {"organization_id": org, "kind": "DecisionProposal", "status": "pending_human_decision"},
        )

        return {
            "organization_id": org,
            "model_version": target_snap["version"] if target_snap else None,
            "frame_5x2_counts": (
                {k: len(v) for k, v in target_snap.get("frame_5x2", {}).items()} if target_snap else {}
            ),
            "sources_count": sources_count,
            "candidate_claims_count": candidate_claims_count,
            "open_signals_count": signals_count,
            "pending_proposals_count": len(pending_proposals),
            "active_runtime_tool_version": self.runtime.active_version,
        }

    def list_open_conflicts_and_signals(self, limit: int = 50) -> Dict[str, Any]:
        """Return review signals and contradicting fact references requiring owner attention."""
        org = self.adapter.organization_id
        signals = self.adapter.backend.find_many(
            "review_signals",
            {"organization_id": org},
            sort_key="created_at",
            limit=limit,
        )
        contradictions = self.adapter.backend.find_many(
            "fact_refs",
            {"organization_id": org, "relation": "contradicts"},
            sort_key="created_at",
            limit=limit,
        )
        return {
            "organization_id": org,
            "signals_count": len(signals),
            "signals": signals,
            "contradictions_count": len(contradictions),
            "contradictions": contradictions,
        }

    def trace_evidence(self, claim_id: str) -> Dict[str, Any]:
        """Trace a specific claim back to its exact quote, chunk, source, and raw record provenance."""
        return self.model_service.trace_claim_provenance(claim_id=claim_id)

    def inspect_version_diff(self, base_version: str, candidate_version: str) -> Dict[str, Any]:
        """Compute the impact diff (`ModelDiff`) between two model versions."""
        return self.model_service.compute_model_diff(
            base_version=base_version,
            candidate_version=candidate_version,
        )

    def propose_decision_to_owner(
        self,
        goal_id: str,
        model_version: str,
        options: List[Dict[str, Any]],
        evidence_ids: List[str],
        consequences: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Submit a structured `DecisionProposal` for the human owner.
        Deputy CEO cannot approve its own proposal or activate runtime changes.
        """
        return self.governance.create_decision_proposal(
            goal_id=goal_id,
            model_version=model_version,
            options=options,
            evidence_ids=evidence_ids,
            consequences=consequences,
            required_authority="owner:taras",
        )

    def get_runtime_behavior_summary(self) -> Dict[str, Any]:
        """Inspect active tool version, activation/rollback history, and observed `RunEvent` records."""
        return self.runtime.get_behavior_evidence()

    def inspect_three_lever_diffs(self) -> Dict[str, Any]:
        """Return the Step 4 three-lever versioned proposal diffs (`sales_agents`, `human_sellers`, `environment`)."""
        return {
            "organization_id": self.adapter.organization_id,
            "three_lever_diffs": THREE_LEVER_DIFFS,
        }

    def get_step5_simulation_timeline(
        self,
        seed: int = 20261107,
        weeks: int = 4,
        leads_per_week: int = 30,
    ) -> Dict[str, Any]:
        """Run or inspect the Step 5 signed simulation timeline (`provenance="simulated"`)."""
        harness = Step5SimulationHarness(adapter=self.adapter)
        return harness.run_all_five_arms_and_timeline(seed=seed, weeks=weeks, leads_per_week=leads_per_week)
