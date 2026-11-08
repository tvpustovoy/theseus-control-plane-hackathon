"""Offline contract checks for the bounded public demo reader."""
import importlib.util
import os
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
