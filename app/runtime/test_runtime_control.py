"""Unit tests for Phase A/B Runtime, Human Control Governance, and Scoped Deputy CEO (`A07`, `B04`, `B05`, `B07`, `F01`)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.control import ControlPlaneGovernance
from app.deputy import ScopedDeputyCEOTools
from app.model.adapter import seed_synthetic_recplace_store
from app.model.versioning import VersionedModelService
from app.runtime import VersionedRuntimeEngine
from database.adapter import IngestionAdapter, LocalDocumentStore
from database.schema import ContractError, sha256_hex


class ControlRuntimeDeputyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = LocalDocumentStore(persist_path=Path(self.tmp.name) / "store.json")
        self.adapter = IngestionAdapter(backend=self.store, organization_id="recplace")
        seed_synthetic_recplace_store(self.adapter)
        self.model_svc = VersionedModelService(self.adapter)
        self.gov = ControlPlaneGovernance(self.adapter)
        self.runtime = VersionedRuntimeEngine(self.adapter, self.gov)
        self.deputy = ScopedDeputyCEOTools(
            adapter=self.adapter,
            model_service=self.model_svc,
            governance=self.gov,
            runtime=self.runtime,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_baseline_tool_execution_and_deputy_scoped_access(self) -> None:
        # 1. Baseline tool-v1 allows 5% discount without promise deadline, blocks 15% unapproved discount
        ev_ok = self.runtime.execute_active_tool(
            {"amount": 100000, "discount_pct": 5.0, "has_director_approval": False, "promise_deadline": None}
        )
        self.assertTrue(ev_ok["outcome"]["allowed"])
        self.assertEqual(ev_ok["tool_version"], "tool-v1")

        ev_blocked = self.runtime.execute_active_tool(
            {"amount": 100000, "discount_pct": 15.0, "has_director_approval": False, "promise_deadline": "2026-11-10"}
        )
        self.assertFalse(ev_blocked["outcome"]["allowed"])
        self.assertEqual(ev_blocked["outcome"]["required_authority"], "sales_director")

        # 2. Deputy CEO can call allowlisted overview tool, but is denied arbitrary/unauthorized methods
        overview = self.deputy.invoke_scoped_tool("get_organization_overview")
        self.assertEqual(overview["organization_id"], "recplace")
        self.assertEqual(overview["sources_count"], 7)
        self.assertEqual(overview["active_runtime_tool_version"], "tool-v1")

        with self.assertRaises(ContractError) as ctx:
            self.deputy.invoke_scoped_tool("activate_candidate", {"candidate_id": "tool-v2"})
        self.assertEqual(ctx.exception.code, "permission_denied")

    def test_phase_b_governance_evaluation_gate_activation_and_rollback(self) -> None:
        # Seed a claim so Deputy CEO has evidence_ids to cite in DecisionProposal
        founder_src = self.adapter.list_sources(source_type="founder_meeting")["items"][0]
        f_doc = self.adapter.get_source(founder_src["source_id"], "v1")
        f_text = f_doc["text"]
        self.adapter.put_chunks(
            source_id=founder_src["source_id"],
            version="v1",
            chunks=[{"chunk_id": "f0", "char_start": 0, "char_end": len(f_text), "text": f_text}],
            chunker_version="chunker-v1",
        )
        f_run = self.adapter.start_extraction(
            source_id=founder_src["source_id"],
            source_version="v1",
            prompt_version="founder-v1",
            model="muse-spark-1.3",
            input_hash=sha256_hex(f_text),
        )
        f_quote = "предложил поднять порог самостоятельной скидки менеджера до 10 процентов"
        f_batch = self.adapter.write_claim_batch(
            run_id=f_run["run_id"],
            chunk_id="f0",
            asserts=[
                {
                    "claim": "На встрече основателей предложено поднять порог самостоятельной скидки менеджера до 10%.",
                    "fact_type": "proposal",
                    "knowledge_state": "hypothesis",
                    "quote": f_quote,
                    "zone": "pricing",
                    "target_q": ["Q3", "Q8"],
                }
            ],
        )
        claim_id = f_batch["accepted_candidate_ids"][0]
        self.model_svc.assemble_snapshot("v1", included_claim_ids=[], summary_note="Baseline empty")
        self.model_svc.assemble_snapshot("v2", parent_version="v1", included_claim_ids=[claim_id])

        # 1. Deputy CEO proposes a decision to owner
        proposal = self.deputy.invoke_scoped_tool(
            "propose_decision_to_owner",
            {
                "goal_id": "goal:prevent-margin-leakage",
                "model_version": "v2",
                "options": [
                    {"id": "opt1", "summary": "Raise auto discount to 10% AND require explicit promise deadline"},
                    {"id": "opt2", "summary": "Keep 5% limit"},
                ],
                "evidence_ids": [claim_id],
                "consequences": {"affected_tools": ["discount_commitment_guard"]},
            },
        )
        proposal_id = proposal["proposal_id"]

        # 2. Agent attempting to self-approve decision is rejected
        with self.assertRaises(ContractError) as ctx:
            self.gov.record_human_decision(
                proposal_id=proposal_id,
                authenticated_actor="Argon.Hackathon",
                action="approve",
                approved_scope={"tools": ["discount_commitment_guard"]},
                approved_version="tool-v2",
                rationale="Self-approval attempt",
            )
        self.assertEqual(ctx.exception.code, "permission_denied")

        # 3. Authorized human owner (Taras) approves tool-v2
        decision = self.gov.record_human_decision(
            proposal_id=proposal_id,
            authenticated_actor="taras",
            action="approve",
            approved_scope={"tools": ["discount_commitment_guard"]},
            approved_version="tool-v2",
            previous_version="tool-v1",
            rationale="Approve 10% auto-discount threshold only when promise_deadline is mandatory.",
        )
        decision_id = decision["decision_id"]

        # 4. Register ChangeCandidate tool-v2 (does NOT activate automatically)
        self.runtime.register_change_candidate(
            candidate_version="tool-v2",
            base_code_version="tool-v1",
            model_version="v2",
            rule_version="normative-v2",
            skill_config={
                "max_auto_discount_pct": 10.0,
                "max_director_discount_pct": 15.0,
                "require_promise_deadline": True,
            },
            code_diff_ref="app/runtime/__init__.py#DiscountCommitmentTool",
            skill_context_routing_diff_ref="skill_config:max_auto_discount_pct=10.0,require_promise_deadline=True",
            decision_id=decision_id,
            development_run_ids=["dev-run-01"],
            description="Raise auto discount to 10% and enforce mandatory promise deadline.",
        )
        self.assertEqual(self.runtime.active_version, "tool-v1")

        # 5. Bad evaluation (with regressions or non-held_out split) is blocked by release gate
        bad_eval = self.runtime.record_evaluation_report(
            candidate_id="tool-v2",
            baseline_id="tool-v1",
            suite_version="eval-v1",
            split="held_out",
            numerator=8,
            denominator=10,
            regressions=1,
            cost={"usd": 0.02},
            result="fail",
        )
        with self.assertRaises(ContractError) as ctx:
            self.runtime.activate_candidate(
                candidate_id="tool-v2",
                decision_id=decision_id,
                evaluation_id=bad_eval["evaluation_id"],
            )
        self.assertEqual(ctx.exception.code, "evaluation_gate_blocked")
        self.assertEqual(self.runtime.active_version, "tool-v1")

        # 6. Passing held-out evaluation unlocks activation
        good_eval = self.runtime.record_evaluation_report(
            candidate_id="tool-v2",
            baseline_id="tool-v1",
            suite_version="eval-v1",
            split="held_out",
            numerator=10,
            denominator=10,
            regressions=0,
            cost={"usd": 0.02},
            result="pass",
        )
        act_receipt = self.runtime.activate_candidate(
            candidate_id="tool-v2",
            decision_id=decision_id,
            evaluation_id=good_eval["evaluation_id"],
        )
        self.assertEqual(act_receipt["active_version"], "tool-v2")
        self.assertEqual(self.runtime.active_version, "tool-v2")

        # 7. Verify new behavior on tool-v2: 8% discount WITH deadline is allowed, WITHOUT deadline is blocked
        ev_v2_blocked = self.runtime.execute_active_tool(
            {"amount": 100000, "discount_pct": 8.0, "has_director_approval": False, "promise_deadline": None}
        )
        self.assertFalse(ev_v2_blocked["outcome"]["allowed"])
        self.assertIn("missing_promise_deadline", ev_v2_blocked["outcome"]["reasons"])

        ev_v2_allowed = self.runtime.execute_active_tool(
            {"amount": 100000, "discount_pct": 8.0, "has_director_approval": False, "promise_deadline": "2026-11-15"}
        )
        self.assertTrue(ev_v2_allowed["outcome"]["allowed"])

        # 8. Verify rollback restores tool-v1 and preserves full history
        rb_receipt = self.runtime.rollback_to_version(
            target_version="tool-v1",
            authenticated_actor="taras",
            rationale="Verify rollback drill to baseline tool-v1.",
        )
        self.assertEqual(rb_receipt["previous_version"], "tool-v2")
        self.assertEqual(rb_receipt["active_version"], "tool-v1")
        self.assertEqual(self.runtime.active_version, "tool-v1")

        behavior = self.deputy.invoke_scoped_tool("get_runtime_behavior_summary")
        self.assertEqual(len(behavior["activation_history"]), 2)
        self.assertEqual(behavior["run_event_count"], 2)


if __name__ == "__main__":
    unittest.main()
