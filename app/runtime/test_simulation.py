"""Unit tests for Step 4 & Step 5 deterministic simulation harness and CRM field validation."""
from __future__ import annotations

import unittest

from app.deputy import ScopedDeputyCEOTools
from app.runtime.simulation import (
    SIMULATION_LABEL,
    SIMULATION_PROVENANCE,
    Step5SimulationHarness,
    generate_synthetic_leads,
)
from database.adapter import IngestionAdapter, LocalDocumentStore
from database.schema import SIMULATION_ARMS, validate_discount_justification


class Step5SimulationHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = LocalDocumentStore()
        self.adapter = IngestionAdapter(backend=self.store, organization_id="recplace")
        self.harness = Step5SimulationHarness(adapter=self.adapter)

    def test_fixed_seed_lead_generator_determinism_and_actor_split(self) -> None:
        leads_a = generate_synthetic_leads(seed=20261107, weeks=4, leads_per_week=20)
        leads_b = generate_synthetic_leads(seed=20261107, weeks=4, leads_per_week=20)
        self.assertEqual(leads_a, leads_b)
        self.assertEqual(len(leads_a), 80)

        agent_leads = [l for l in leads_a if l["actor_type"] == "sales_agent"]
        human_leads = [l for l in leads_a if l["actor_type"] == "simulated_human_seller"]
        self.assertEqual(len(agent_leads), 40)
        self.assertEqual(len(human_leads), 40)
        for lead in leads_a:
            self.assertEqual(lead["provenance"], SIMULATION_PROVENANCE)
            self.assertEqual(lead["simulation_label"], SIMULATION_LABEL)

    def test_crm_discount_justification_validation_contract(self) -> None:
        # 0% discount does not require justification
        ok_zero = validate_discount_justification(0.0, None, require_field=True)
        self.assertTrue(ok_zero["valid"])

        # >0% discount in crm-v2 requires valid enum
        missing = validate_discount_justification(10.0, None, require_field=True)
        self.assertFalse(missing["valid"])
        self.assertEqual(missing["reason"], "missing_required_discount_justification")

        bad_enum = validate_discount_justification(10.0, "friend_discount", require_field=True)
        self.assertFalse(bad_enum["valid"])

        # other_with_text requires >= 10 chars explanation
        short_other = validate_discount_justification(10.0, "other_with_text", "short", require_field=True)
        self.assertFalse(short_other["valid"])

        ok_other = validate_discount_justification(
            10.0,
            "other_with_text",
            "Approved competitive match exception for Q4 renewal.",
            require_field=True,
        )
        self.assertTrue(ok_other["valid"])
        self.assertTrue(ok_other["has_justification"])
        self.assertFalse(ok_other["is_value_exchange"])

        # Value exchange justifications
        for ve in ("longer_term", "prepayment", "referral", "volume"):
            res = validate_discount_justification(5.0, ve, require_field=True)
            self.assertTrue(res["valid"])
            self.assertTrue(res["has_justification"])
            self.assertTrue(res["is_value_exchange"])

    def test_five_counterfactual_arms_isolation_and_provenance(self) -> None:
        report = self.harness.run_all_five_arms_and_timeline(seed=20261107, weeks=4, leads_per_week=30)
        self.assertEqual(report["provenance"], SIMULATION_PROVENANCE)
        self.assertEqual(report["simulation_label"], SIMULATION_LABEL)
        self.assertEqual(set(report["arms"].keys()), set(SIMULATION_ARMS))

        # Check persisted collections have provenance="simulated" on every single document
        runs = self.store.find_many("simulation_runs", {"organization_id": "recplace"})
        self.assertEqual(len(runs), 5)
        for r in runs:
            self.assertEqual(r["provenance"], "simulated")
            self.assertEqual(r["simulation_label"], SIMULATION_LABEL)

        events = self.store.find_many("simulation_events", {"organization_id": "recplace"})
        self.assertEqual(len(events), 5 * 120)
        for ev in events:
            self.assertEqual(ev["provenance"], "simulated")

        # Lever isolation checks:
        # 1. `agent_rule_only` changes `sales_agent` metrics, while `simulated_human_seller` stays identical to `before`
        before_agent = report["arms"]["before"]["overall"]["sales_agent"]
        before_human = report["arms"]["before"]["overall"]["simulated_human_seller"]
        rule_only_agent = report["arms"]["agent_rule_only"]["overall"]["sales_agent"]
        rule_only_human = report["arms"]["agent_rule_only"]["overall"]["simulated_human_seller"]

        self.assertGreater(rule_only_agent["codex_consistency_share"], before_agent["codex_consistency_share"])
        self.assertEqual(rule_only_human, before_human)

        # 2. `onboarding_only` changes `simulated_human_seller` metrics, while `sales_agent` stays identical to `before`
        onboard_agent = report["arms"]["onboarding_only"]["overall"]["sales_agent"]
        onboard_human = report["arms"]["onboarding_only"]["overall"]["simulated_human_seller"]

        self.assertEqual(onboard_agent, before_agent)
        self.assertGreater(onboard_human["codex_consistency_share"], before_human["codex_consistency_share"])

        # 3. `crm_field_only` achieves 100% justified_discount_share across all offered discounts
        crm_only_all = report["arms"]["crm_field_only"]["overall"]["all"]
        self.assertEqual(crm_only_all["justified_discount_share"], 1.0)
        self.assertGreater(
            crm_only_all["justified_discount_share"],
            report["arms"]["before"]["overall"]["all"]["justified_discount_share"],
        )

        # 4. Staged rollout timeline has 4 periods (W1..W4) and Deputy CEO can query it
        self.assertEqual([p["period"] for p in report["staged_rollout_timeline"]], ["W1", "W2", "W3", "W4"])
        deputy = ScopedDeputyCEOTools(adapter=self.adapter)
        diffs = deputy.invoke_scoped_tool("inspect_three_lever_diffs")
        self.assertIn("environment_crm_schema", diffs["three_lever_diffs"])
        sim_via_deputy = deputy.invoke_scoped_tool(
            "get_step5_simulation_timeline",
            {"seed": 20261107, "weeks": 4, "leads_per_week": 30},
        )
        self.assertEqual(
            sim_via_deputy["combined_vs_before_summary"],
            report["combined_vs_before_summary"],
        )


if __name__ == "__main__":
    unittest.main()
