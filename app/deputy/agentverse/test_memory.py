"""Offline contract checks for the bounded public demo reader."""
import importlib.util
import ast
import json
import os
import re
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# The tests exercise retrieval boundaries, not the provider SDK.
sys.modules.setdefault("openai", types.SimpleNamespace(OpenAI=MagicMock()))
sys.modules.setdefault("requests", types.SimpleNamespace(get=MagicMock(), post=MagicMock()))
spec = importlib.util.spec_from_file_location("deputy_http", Path(__file__).with_name("http_client.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def card_namespace(memory=None):
    tree = ast.parse(Path(__file__).with_name("protocols.py").read_text())
    names = {"wants_direction_card", "wants_workflow_brief", "decision_card_for", "workflow_metadata",
             "workflow_response", "card_response", "commit_metadata"}
    constants = {"WORKFLOW_LINKS", "RECORD_ID", "RECORD_VERSION", "COMMIT_ROWS", "COMMIT_URL", "SNAPSHOT_DATE"}
    nodes = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in names)
             or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in n.targets))]
    namespace = {"re": re, "json": json, "read_memory": lambda: memory}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "card-contract", "exec"), namespace)
    return namespace


class MemoryContract(unittest.TestCase):
    def test_company_deal_count_never_uses_demo_count(self):
        memory = {"connected": True, "organization_counts": {
            "crm_deal_records": {"count": 6102, "scope": "imported_snapshot_rows"},
            "demo_crm_records": {"count": 360}}}
        answer = module.crm_count_reply("how many deals in crm?", memory)
        self.assertIn("6,102", answer)
        self.assertNotIn("360", answer)
        for question in ("How many paid deals?", "How many demo deals?", "How many deals this month?", "How many deals for Acme?"):
            self.assertIsNone(module.crm_count_reply(question, memory))
        self.assertIsNone(module.crm_count_reply("How many deals?", {"connected": False}))

    def test_after_commit_shows_review_card_and_both_links_without_mutation(self):
        memory = {"connected": True, "current_state_records": [{"demo_session_id": "session-a",
            "mandate_status": "committed_mandate", "active_runtime_version": "tool-v1",
            "active_crm_schema_version": "crm-v1", "decision_record": None}]}
        ns = card_namespace(memory)
        reply, card = ns["workflow_response"]("Against the direction I confirmed, what do you recommend?", memory)
        self.assertLess(len(reply.split()), 100)
        payload = json.loads(card["card_payload"])
        self.assertEqual([c["label"] for c in payload["ctas"]], ["Review evidence", "Review proposed change"])
        for cta, frame in zip(payload["ctas"], ["S03", "S04"]):
            result, _ = ns["card_response"](json.dumps(cta["selection"]))
            self.assertIn("#" + frame, result)
            self.assertIn("nothing was changed", result)
        stale = dict(payload["ctas"][0]["selection"], version="old-session")
        self.assertIn("earlier demo", ns["card_response"](json.dumps(stale))[0])
        self.assertIsNone(memory["current_state_records"][0]["decision_record"])

    def test_workflow_cards_distinguish_approval_from_activation(self):
        state = {"demo_session_id": "session-a", "mandate_status": "committed_mandate",
                 "active_runtime_version": "tool-v1", "decision_record": {"decision": "approve"}}
        memory = {"connected": True, "current_state_records": [state]}
        ns = card_namespace(memory)
        reply, _ = ns["workflow_response"]("What should we do next?", memory)
        self.assertIn("not been applied", reply)
        state["active_runtime_version"] = "tool-v2"
        reply, card = ns["workflow_response"]("What should we do next?", memory)
        self.assertIn("active in the demo", reply)
        self.assertIn("View simulation", card["card_payload"])

    def test_confirmed_direction_does_not_require_implementation_approval(self):
        memory = {"current_state_records": [{"demo_session_id": "fresh",
                  "mandate_status": "committed_mandate", "active_mandate_version": "mandate-v2",
                  "decision_record": None, "activation_receipt": None,
                  "active_runtime_version": "tool-v1", "active_crm_schema_version": "crm-v1",
                  "monitoring_status": "mandate_committed_crm_still_blind"}]}
        status = module.current_decisions(memory, {"operation": "search"})["governance_status"]
        self.assertTrue(status["direction"]["confirmed"])
        self.assertIsNone(status["implementation_decision"]["record"])
        self.assertIsNone(status["activation"]["receipt"])
        self.assertEqual(status["activation"]["runtime_version"], "tool-v1")

    def test_implementation_receipt_does_not_imply_direction_or_activation(self):
        memory = {"current_state_records": [{"mandate_status": "draft_pending_owner_commit",
                  "decision_record": {"decision": "approve"}, "activation_receipt": None}]}
        status = module.governance_status(memory)
        self.assertFalse(status["direction"]["confirmed"])
        self.assertIsNotNone(status["implementation_decision"]["record"])
        self.assertIsNone(status["activation"]["receipt"])

    def test_reset_mirror_does_not_reuse_historical_approval(self):
        memory = {"current_state_records": [{"demo_session_id": "fresh", "decision_record": None}],
                  "records": [{"decision_id": "old", "decision": "approve"}]}
        result = module.current_decisions(memory, {"operation": "search"})
        self.assertEqual(result["records"], [])
        self.assertEqual(result["demo_session_id"], "fresh")

    def test_current_receipt_is_visible_and_lookup_cannot_escape_session(self):
        memory = {"current_state_records": [{"demo_session_id": "fresh",
                  "decision_record": {"decision_id": "new", "decision": "approve"}}]}
        self.assertEqual(module.current_decisions(memory, {"operation": "count"})["count"], 1)
        self.assertEqual(module.current_decisions(memory, {"operation": "read", "record_id": "old"})["records"], [])

    def test_missing_mirror_cannot_prove_approval(self):
        self.assertIn("error", module.current_decisions({}, {"operation": "search"}))

    def test_natural_strategy_question_attaches_card_only_to_pending_direction(self):
        namespace = card_namespace()
        memory = {"connected": True, "current_state_records": [{"demo_session_id": "session-a", "mandate_status": "draft_pending_owner_commit"}]}
        for question in ("@theseus-deputy-ceo What is our discount strategy?", "Какая у нас стратегия скидок?", "Show the decision card"):
            self.assertIsNotNone(namespace["decision_card_for"](question, memory))
        self.assertIsNone(namespace["decision_card_for"]("How many CRM records are loaded?", memory))
        memory["current_state_records"][0]["mandate_status"] = "committed_mandate"
        self.assertIn("Review evidence", namespace["decision_card_for"]("What is our discount strategy?", memory)["card_payload"])

    def setUp(self):
        self.environment = patch.dict(os.environ, {"THESEUS_MEMORY_URL": ""})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.client = MagicMock()
        module._mongo = self.client
        self.collection = self.client["theseus_deputy_demo"]["memory"]

    @patch.dict(os.environ, {"THESEUS_MONGODB_URI": "configured"})
    def test_each_question_reads_fresh_fixed_scope(self):
        self.collection.find.return_value.sort.return_value.limit.side_effect = [
            [{"record_id": "test", "statement": "before"}],
            [{"record_id": "test", "statement": "after"}],
        ]
        self.assertEqual(module.read_memory()["records"][0]["statement"], "before")
        self.assertEqual(module.read_memory()["records"][0]["statement"], "after")
        self.assertEqual(self.collection.find.call_count, 2)
        self.collection.find.assert_called_with({"public_safe": True}, {"_id": 0})
        self.collection.find.return_value.sort.return_value.limit.assert_called_with(41)

    @patch.dict(os.environ, {"THESEUS_MONGODB_URI": "configured"})
    def test_no_silent_partial_memory(self):
        self.collection.find.return_value.sort.return_value.limit.return_value = [{}] * 41
        self.assertFalse(module.read_memory()["connected"])

    @patch.dict(os.environ, {"THESEUS_MONGODB_URI": "configured"})
    def test_error_does_not_leak_credentials(self):
        self.collection.find.side_effect = RuntimeError("mongodb://private:secret@host")
        result = module.read_memory()
        self.assertFalse(result["connected"])
        self.assertNotIn("secret", str(result))
        self.assertNotIn("host", str(result))

    @patch.dict(os.environ, {}, clear=True)
    def test_unconfigured_is_not_a_live_connection(self):
        self.assertFalse(module.read_memory()["connected"])
        self.collection.find.assert_not_called()

    @patch.dict(os.environ, {"THESEUS_MEMORY_URL": "https://approved.example", "THESEUS_MEMORY_TOKEN": "test-only"})
    def test_bridge_reads_each_request_without_redirects(self):
        response = MagicMock(status_code=200, content=b"{}")
        response.json.side_effect = [{"connected":True,"records":[{"v":1}]}, {"connected":True,"records":[{"v":2}]}]
        with patch.object(module.requests, "get", return_value=response) as get:
            self.assertEqual(module.read_memory()["records"][0]["v"], 1)
            self.assertEqual(module.read_memory()["records"][0]["v"], 2)
            self.assertEqual(get.call_count, 2)
            self.assertFalse(get.call_args.kwargs["allow_redirects"])

    @patch.dict(os.environ, {"THESEUS_MEMORY_URL": "http://insecure.example"})
    def test_bridge_rejects_plain_http(self):
        with patch.object(module.requests, "get") as get:
            self.assertFalse(module.read_memory()["connected"])
            get.assert_not_called()

    @patch.dict(os.environ, {"THESEUS_MEMORY_URL": "https://approved.example"})
    def test_bridge_auth_failure_is_not_data(self):
        with patch.object(module.requests, "get", return_value=MagicMock(status_code=401)):
            self.assertFalse(module.read_memory()["connected"])


if __name__ == "__main__":
    unittest.main()
