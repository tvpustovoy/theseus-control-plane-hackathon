import unittest

from app.api.server import TheseusLocalApplication
from database.adapter import IngestionAdapter, LocalDocumentStore
from database.schema import ContractError


class CommitmentLedgerTests(unittest.TestCase):
    def setUp(self):
        self.adapter = IngestionAdapter(backend=LocalDocumentStore(), organization_id='recplace')
        self.app = TheseusLocalApplication(self.adapter, 'unit_test_store')

    def test_add_update_select_restart_and_reset(self):
        app = self.app
        self.assertEqual(app.list_commitments(), [])
        app.commit_mandate({'goal_text': 'First goal', 'scenario_key': 'discount-demo'})
        first = app.active_commitment_id
        first_date = app.list_commitments()[0]['confirmed_at']
        app.commit_mandate({'goal_text': 'Second goal'})
        second = app.active_commitment_id
        self.assertNotEqual(first, second)
        self.assertEqual(len(app.list_commitments()), 2)
        app.commit_mandate({'commitment_id': first, 'goal_text': 'First goal revised'})
        self.assertEqual(len(app.list_commitments()), 2)
        self.assertEqual(app._commitments[first]['confirmed_at'], first_date)
        self.assertEqual(app._commitments[first]['version'], 2)
        app.select_commitment({'commitment_id': second})
        self.assertEqual(app.commit_state['intent_and_goal']['proposed_text'], 'Second goal')
        with self.assertRaises(ContractError):
            app._require_scenario()
        restarted = TheseusLocalApplication(self.adapter, 'unit_test_store')
        self.assertEqual(restarted.active_commitment_id, second)
        self.assertEqual(len(restarted.list_commitments()), 2)
        old_session = restarted.demo_session_id
        restarted.reset_demo_session()
        self.assertEqual(restarted.list_commitments(), [])
        self.assertIsNone(restarted.active_commitment_id)
        self.assertNotEqual(old_session, restarted.demo_session_id)
        history = self.adapter.backend.find_one('deputy_public_state', {
            '_id': f'commitment_workspace:recplace:{old_session}'})
        self.assertEqual(len(history['records']), 2)
        with self.assertRaises(ContractError):
            restarted.select_commitment({'commitment_id': first})

    def test_implementation_state_does_not_leak_between_records(self):
        app = self.app
        app.commit_mandate({'goal_text': 'First', 'scenario_key': 'discount-demo'})
        first = app.active_commitment_id
        app.approve_proposal({'decision': 'approve', 'authenticated_actor': 'owner:taras'})
        app.activate_candidate({})
        app.commit_mandate({'goal_text': 'Second', 'scenario_key': 'discount-demo'})
        self.assertIsNone(app.decision_record)
        self.assertEqual(app.runtime.active_version, 'tool-v1')
        app.select_commitment({'commitment_id': first})
        self.assertIsNotNone(app.decision_record)
        self.assertEqual(app.runtime.active_version, 'tool-v2')


if __name__ == '__main__':
    unittest.main()
