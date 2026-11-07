import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("tracker", Path(__file__).parents[1] / "build.py")
tracker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tracker)

class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "proof.txt").write_text("accepted result")
        self.data = {"tasks": [
            {"id": "A", "status": "done", "depends_on": [], "blockers": [], "approval": "user", "evidence": ["proof.txt"]},
            {"id": "B", "status": "todo", "depends_on": ["A"], "blockers": [], "approval": "pending", "evidence": []}
        ]}
    def tearDown(self):
        self.tmp.cleanup()
    def test_ready_does_not_grant_approval(self):
        by = tracker.validate(self.data, self.root)
        self.assertEqual(tracker.readiness(by["B"], by), "Входы готовы")
        self.assertEqual(by["B"]["approval"], "pending")
    def test_blocker_overrides_ready_dependencies(self):
        self.data["tasks"][1]["blockers"] = ["key missing"]
        by = tracker.validate(self.data, self.root)
        self.assertIn("key missing", tracker.readiness(by["B"], by))
    def test_done_requires_existing_evidence(self):
        self.data["tasks"][0]["evidence"] = ["missing.txt"]
        with self.assertRaises(ValueError): tracker.validate(self.data, self.root)
    def test_done_cannot_skip_unfinished_dependency(self):
        self.data["tasks"][0]["status"] = "todo"
        self.data["tasks"][1].update(status="done", approval="user", evidence=["proof.txt"])
        with self.assertRaises(ValueError): tracker.validate(self.data, self.root)
    def test_cycle_and_unknown_dependency_rejected(self):
        for deps in [["B"], ["unknown"]]:
            data = copy.deepcopy(self.data)
            data["tasks"][0].update(status="todo", depends_on=deps)
            with self.assertRaises(ValueError): tracker.validate(data, self.root)
    def test_unauthorized_work_rejected(self):
        self.data["tasks"][1]["status"] = "doing"
        with self.assertRaises(ValueError): tracker.validate(self.data, self.root)
    def test_outside_evidence_rejected(self):
        self.data["tasks"][0]["evidence"] = ["../outside.txt"]
        with self.assertRaises(ValueError): tracker.validate(self.data, self.root)

if __name__ == "__main__": unittest.main()

