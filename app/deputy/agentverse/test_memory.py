"""Offline contract checks for the bounded public demo reader."""
import importlib.util
import ast
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


class MemoryContract(unittest.TestCase):
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
        tree = ast.parse(Path(__file__).with_name("protocols.py").read_text())
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name in {"wants_direction_card", "decision_card_for"}]
        namespace = {"re": re, "commit_metadata": lambda: {"card_kind": "detail"}}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "card-intent", "exec"), namespace)
        memory = {"connected": True, "current_state_records": [{"mandate_status": "draft_pending_owner_commit"}]}
        for question in ("@theseus-deputy-ceo What is our discount strategy?", "Какая у нас стратегия скидок?", "Show the decision card"):
            self.assertIsNotNone(namespace["decision_card_for"](question, memory))
        self.assertIsNone(namespace["decision_card_for"]("How many CRM records are loaded?", memory))
        memory["current_state_records"][0]["mandate_status"] = "committed_mandate"
        self.assertIsNone(namespace["decision_card_for"]("What is our discount strategy?", memory))

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
