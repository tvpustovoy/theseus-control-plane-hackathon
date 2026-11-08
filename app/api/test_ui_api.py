"""Acceptance tests for the Theseus localhost UI & HTTP API (`S01..S06`)."""
from __future__ import annotations

import json
import unittest

from app.api.server import UI_DIR, TheseusLocalApplication
from database.adapter import IngestionAdapter, LocalDocumentStore
from database.schema import ContractError


class TheseusUiApiAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = LocalDocumentStore()
        self.adapter = IngestionAdapter(backend=self.store, organization_id="recplace")
        self.app = TheseusLocalApplication(adapter=self.adapter, backend_mode="unit_test_store")

    def test_all_six_frames_and_evidence_catalog_present_without_credentials(self) -> None:
        state = self.app.get_state_payload()
        frame_ids = [f["frame_id"] for f in state["navigation_frames"]]
        self.assertEqual(frame_ids, ["S01", "S02", "S03", "S04", "S05", "S06"])
        self.assertIn("ev:import-live-20261107-full", state["evidence_catalog"])
        self.assertIn("ev:culture-crm-blindness", state["evidence_catalog"])
        self.assertEqual(state["s06_track"]["provenance"], "simulated")

        # Verify no credentials or secret key paths leak in state payload or UI files
        serialized = json.dumps(state)
        self.assertNotIn("mongodb+srv://", serialized)
        self.assertNotIn("argon-hackathon.key", serialized)
        for fn in ("index.html", "styles.css", "app.js"):
            content = (UI_DIR / fn).read_text(encoding="utf-8")
            self.assertNotIn("mongodb+srv://", content)

    def test_s01_commit_mandate_does_not_falsify_active_monitoring(self) -> None:
        res = self.app.commit_mandate(
            {
                "authenticated_actor": "owner:taras",
                "goal_text": "goal-v2: Updated by Taras in S01.",
            }
        )
        self.assertEqual(res["committed_version"], "mandate-v2")
        self.assertEqual(res["mandate_status"], "committed_mandate")
        # Saving mandate alone cannot turn monitoring status to active while tool-v1/crm-v1 is active
        self.assertEqual(res["monitoring_status"], "mandate_committed_crm_still_blind")

    def test_s05_same_input_v1_vs_v2_gate_and_rollback(self) -> None:
        # 1. Activation before approval is blocked
        with self.assertRaises(ContractError) as ctx:
            self.app.activate_candidate({})
        self.assertEqual(ctx.exception.code, "missing_human_approval")

        # 2. Under baseline tool-v1 / crm-v1, a 5% discount WITHOUT customer commitment PASSES
        same_input_no_commitment = {
            "deal_code": "DEAL-SAME-INPUT-01",
            "actor_type": "sales_agent",
            "list_amount_rub": 300000,
            "discount_pct": 5,
            "discount_justification": "",
        }
        v1_deal = self.app.submit_demo_crm_deal(same_input_no_commitment)
        self.assertEqual(v1_deal["crm_schema_version"], "crm-v1")
        self.assertEqual(v1_deal["active_tool_version"], "tool-v1")
        self.assertTrue(v1_deal["tool_allowed"])
        self.assertFalse(v1_deal["is_value_exchange"])
        self.assertEqual(len(self.app.crm_submissions), 1)

        # 3. Approval alone does not activate tool-v2
        dec = self.app.approve_proposal({"authenticated_actor": "owner:taras", "decision": "approve"})
        self.assertEqual(dec["decision"], "approve")
        self.assertEqual(self.app.runtime.active_version, "tool-v1")

        # 4. Activation after approval + simulated gate switches active version to tool-v2
        act = self.app.activate_candidate({})
        self.assertEqual(act["active_version"], "tool-v2")
        self.assertEqual(self.app.runtime.active_version, "tool-v2")

        # 5. Exact same input (5% discount WITHOUT customer commitment) is now BLOCKED under tool-v2 / crm-v2,
        #    creates no new CRM deal record, and records a rejected RunEvent with missing_value_exchange_commitment
        with self.assertRaises(ContractError) as crm_err:
            self.app.submit_demo_crm_deal(same_input_no_commitment)
        self.assertEqual(crm_err.exception.code, "crm_validation_failed")
        self.assertFalse(crm_err.exception.details["tool_allowed"])
        self.assertIn("missing_value_exchange_commitment", crm_err.exception.details["tool_reasons"])
        self.assertEqual(len(self.app.crm_submissions), 1)  # still only the earlier v1 deal

        # 6. Supplying a customer commitment (prepayment) on the same 5% discount PASSES under tool-v2 / crm-v2
        good_deal = self.app.submit_demo_crm_deal(
            {
                "deal_code": "DEAL-OK-V2",
                "actor_type": "sales_agent",
                "list_amount_rub": 300000,
                "discount_pct": 5,
                "discount_justification": "prepayment",
                "justification_text": "Annual upfront payment confirmed.",
            }
        )
        self.assertEqual(good_deal["crm_schema_version"], "crm-v2")
        self.assertEqual(good_deal["active_tool_version"], "tool-v2")
        self.assertTrue(good_deal["is_value_exchange"])
        self.assertTrue(good_deal["tool_allowed"])
        self.assertEqual(good_deal["discount_justification"], "prepayment")
        self.assertEqual(len(self.app.crm_submissions), 2)

        # 7. Rollback restores tool-v1
        rb = self.app.rollback_candidate({"authenticated_actor": "owner:taras", "rationale": "Test rollback"})
        self.assertEqual(rb["active_version"], "tool-v1")
        self.assertEqual(self.app.runtime.active_version, "tool-v1")

    def test_truthful_simulated_gate_subq_packet_and_preserved_verdict_on_question(self) -> None:
        state = self.app.get_state_payload()
        # 1. Evaluation report is explicitly labeled simulated_demo_gate, never a fabricated held-out benchmark
        eval_rep = state["s05_application"]["evaluation_report"]
        self.assertEqual(eval_rep["split"], "simulated_demo_gate")
        self.assertEqual(eval_rep["provenance"], "simulated")

        # 2. S03 starts in preview mode against unapproved v2 and loads the 5-pair SubQ discount packet
        s03 = state["s03_drift"]
        self.assertTrue(s03["is_preview_against_unapproved_rule"])
        disc_pkt = s03["discount_subq_packet"]
        self.assertEqual(disc_pkt["claims_total"], 9)
        self.assertEqual(disc_pkt["pairs_total"], 5)
        self.assertEqual(disc_pkt["rule_status"], "mixed_reference_statuses_see_per_claim")
        for pr in disc_pkt["pairs"]:
            self.assertEqual(pr["review_status"], "reviewed_no_proven_contradiction")
            self.assertTrue(pr["claim_a"]["mandate_status"])
            self.assertTrue(pr["claim_b"]["mandate_status"])

        subq_card = next(c for c in s03["cards"] if c["card_id"] == "drift-card-subq-snap-pilot")
        self.assertEqual(subq_card["subq_verdict"], "insufficient_evidence")
        self.assertEqual(len(subq_card["subq_pairs"]), 5)
        self.assertEqual(subq_card["evidence_category"], "Recorded SubQ model response")

        # 3. Questioning a finding preserves original subq_verdict alongside owner decision & reason
        updated_card = self.app.override_drift_verdict(
            {
                "card_id": "drift-card-subq-snap-pilot",
                "verdict": "different_scope",
                "reason": "Historical episodes predate the proposed rule; record commitments going forward.",
            }
        )
        self.assertEqual(updated_card["subq_verdict"], "insufficient_evidence")
        self.assertEqual(updated_card["owner_override_verdict"], "different_scope")
        self.assertIn("predate the proposed rule", updated_card["owner_override_reason"])

        # 4. Request changes blocks activation
        dec = self.app.approve_proposal({"decision": "request_changes", "rationale": "Need CRM cost estimate first."})
        self.assertEqual(dec["action"], "request_clarification")
        with self.assertRaises(ContractError):
            self.app.activate_candidate({})

        # 5. Verify app.js escapes apostrophes and uses delegated data attributes instead of inline onclick IDs
        app_js = (UI_DIR / "app.js").read_text(encoding="utf-8")
        self.assertIn("&#39;", app_js)
        self.assertIn("data-evidence-id=", app_js)
        self.assertNotIn("onclick=\"openEvidenceDrawer(", app_js)
        self.assertNotIn("onclick=\"toggleQuestionFinding(", app_js)
        self.assertNotIn("onclick=\"submitQuestionFinding(", app_js)

    def test_s06_metrics_contract_has_zero_undefined_fields_and_reset_restores_c0(self) -> None:
        state = self.app.get_state_payload()
        ui_metrics = state["s06_track"]["ui_metrics"]
        required_keys = (
            "leads_total",
            "discounted_count",
            "justified_discount_count",
            "value_exchange_discount_count",
            "codex_consistent_count",
            "discount_offer_rate_pct",
            "justified_discount_share_pct",
            "value_exchange_share_pct",
            "codex_consistency_rate_pct",
            "avg_discount_pct_when_offered",
        )
        for arm_name in ("before", "agent_rule_only", "onboarding_only", "crm_field_only", "combined"):
            arm_m = ui_metrics["arms"][arm_name]["overall"]
            for k in required_keys:
                self.assertIn(k, arm_m)
                self.assertIsNotNone(arm_m[k])
        self.assertEqual(ui_metrics["arms"]["before"]["overall"]["leads_total"], 120)
        self.assertEqual(ui_metrics["arms"]["before"]["overall"]["discounted_count"], 84)
        self.assertEqual(ui_metrics["arms"]["combined"]["overall"]["codex_consistent_count"], 116)
        self.assertEqual(ui_metrics["arms"]["combined"]["overall"]["justified_discount_count"], 68)
        self.assertEqual(len(ui_metrics["weekly_timeline"]), 4)
        for wk in ui_metrics["weekly_timeline"]:
            self.assertIn(wk["period"], ("W1", "W2", "W3", "W4"))
            for k in required_keys:
                self.assertIsNotNone(wk["overall"][k])

        # Mutate session state (commit, approve, activate, submit CRM deal), then reset to C0
        old_session = state["demo_session_id"]
        self.app.commit_mandate({"authenticated_actor": "owner:taras"})
        self.app.approve_proposal({"authenticated_actor": "owner:taras", "decision": "approve"})
        self.app.activate_candidate({})
        self.app.submit_demo_crm_deal(
            {"deal_code": "D-1", "discount_pct": 5, "discount_justification": "prepayment"}
        )
        reset_res = self.app.reset_demo_session({})
        self.assertEqual(reset_res["reset_checkpoint"], "C0")
        self.assertNotEqual(reset_res["demo_session_id"], old_session)
        self.assertFalse(reset_res["raw_sources_mutated"])
        self.assertFalse(reset_res["prior_audit_records_deleted"])

        fresh_state = self.app.get_state_payload()
        self.assertEqual(fresh_state["s01_commit"]["committed_version"], "mandate-v1")
        self.assertEqual(fresh_state["s05_application"]["active_runtime_version"], "tool-v1")
        self.assertIsNone(fresh_state["s05_application"]["decision_record"])
        self.assertEqual(len(fresh_state["s05_application"]["crm_submissions"]), 0)
        # Historical decision & CRM deal remain preserved in backend store
        self.assertGreaterEqual(len(self.store.find_many("decisions", {"organization_id": "recplace"})), 1)
        self.assertGreaterEqual(len(self.store.find_many("crm_deals_demo", {"organization_id": "recplace"})), 1)


if __name__ == "__main__":
    unittest.main()
