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

    def test_s05_approval_precedes_activation_crm_validation_and_rollback(self) -> None:
        # 1. Activation before approval is blocked
        with self.assertRaises(ContractError) as ctx:
            self.app.activate_candidate({})
        self.assertEqual(ctx.exception.code, "missing_human_approval")

        # 2. Approval alone does not activate tool-v2
        dec = self.app.approve_proposal({"authenticated_actor": "owner:taras", "decision": "approve"})
        self.assertEqual(dec["decision"], "approve")
        self.assertEqual(self.app.runtime.active_version, "tool-v1")

        # 3. Activation after approval + held-out check switches active version to tool-v2
        act = self.app.activate_candidate({})
        self.assertEqual(act["active_version"], "tool-v2")
        self.assertEqual(self.app.runtime.active_version, "tool-v2")

        # 4. Invalid CRM submission (discount > 0 without justification) is rejected
        with self.assertRaises(ContractError) as crm_err:
            self.app.submit_demo_crm_deal(
                {
                    "deal_code": "DEAL-BAD-01",
                    "actor_type": "sales_agent",
                    "list_amount_rub": 300000,
                    "discount_pct": 10,
                    "discount_justification": "",
                }
            )
        self.assertEqual(crm_err.exception.code, "crm_validation_failed")

        # 5. Valid CRM submission succeeds
        good_deal = self.app.submit_demo_crm_deal(
            {
                "deal_code": "DEAL-OK-01",
                "actor_type": "sales_agent",
                "list_amount_rub": 300000,
                "discount_pct": 5,
                "discount_justification": "prepayment",
                "justification_text": "Annual upfront payment confirmed.",
            }
        )
        self.assertTrue(good_deal["is_value_exchange"])
        self.assertEqual(good_deal["discount_justification"], "prepayment")

        # 6. Rollback restores tool-v1
        rb = self.app.rollback_candidate({"authenticated_actor": "owner:taras", "rationale": "Test rollback"})
        self.assertEqual(rb["active_version"], "tool-v1")
        self.assertEqual(self.app.runtime.active_version, "tool-v1")

    def test_truthful_simulated_gate_subq_packet_and_preserved_verdict_on_question(self) -> None:
        state = self.app.get_state_payload()
        # 1. Evaluation report is explicitly labeled simulated_demo_gate, never a fabricated held-out benchmark
        eval_rep = state["s05_application"]["evaluation_report"]
        self.assertEqual(eval_rep["split"], "simulated_demo_gate")
        self.assertEqual(eval_rep["provenance"], "simulated")

        # 2. S03 starts in preview mode against unapproved v2 and includes recorded SubQ Snap 1.1 packet card
        s03 = state["s03_drift"]
        self.assertTrue(s03["is_preview_against_unapproved_rule"])
        subq_card = next(c for c in s03["cards"] if c["card_id"] == "drift-card-subq-snap-pilot")
        self.assertEqual(subq_card["subq_verdict"], "possible_conflict")
        self.assertEqual(subq_card["evidence_category"], "Recorded SubQ model response")

        # 3. Questioning a finding preserves original subq_verdict alongside owner decision & reason
        updated_card = self.app.override_drift_verdict(
            {
                "card_id": "drift-card-subq-snap-pilot",
                "verdict": "different_scope",
                "reason": "Unapproved training norm applies to a different sales situation.",
            }
        )
        self.assertEqual(updated_card["subq_verdict"], "possible_conflict")
        self.assertEqual(updated_card["owner_override_verdict"], "different_scope")
        self.assertIn("different sales situation", updated_card["owner_override_reason"])

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


if __name__ == "__main__":
    unittest.main()
