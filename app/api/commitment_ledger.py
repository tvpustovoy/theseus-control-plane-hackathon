"""Session-scoped commitments, durable revisions and isolated scenario contexts."""
import copy
import uuid

from database.schema import ContractError, make_envelope, utc_now_iso


class CommitmentLedger:
    _context_fields = (
        'commit_state', 'drift_state', 'proposal', 'evaluation_report',
        'decision_record', 'activation_receipt', 'rollback_receipt',
        'crm_submissions', 'simulation_report', 'last_simulation_run_at',
    )
    _runtime_fields = ('_candidates', '_evaluations', '_active_version', '_activation_history', '_run_events')

    def _capture_context(self):
        return copy.deepcopy({
            'fields': {key: getattr(self, key) for key in self._context_fields},
            'runtime': {key: getattr(self.runtime, key) for key in self._runtime_fields},
        })

    def _restore_context(self, context):
        for key, value in context['fields'].items():
            if key in self._context_fields:
                setattr(self, key, copy.deepcopy(value))
        for key, value in context['runtime'].items():
            if key in self._runtime_fields:
                setattr(self.runtime, key, copy.deepcopy(value))

    def _ledger_key(self):
        return f'commitment_workspace:{self.adapter.organization_id}:current'

    def _save_ledger(self):
        if self._ledger_initializing:
            return
        if self.active_commitment_id:
            self._commitments[self.active_commitment_id]['context'] = self._capture_context()
        doc = {
            **make_envelope(self._ledger_key(), organization_id=self.adapter.organization_id),
            'kind': 'CommitmentWorkspace', 'demo_session_id': self.demo_session_id,
            'session_started_at': self.session_started_at,
            'active_commitment_id': self.active_commitment_id,
            'records': copy.deepcopy(self._commitments),
            'current_context': self._capture_context(),
        }
        self.adapter.backend.upsert_by_id('deputy_public_state', doc)
        archive = copy.deepcopy(doc)
        archive['_id'] = f'commitment_workspace:{self.adapter.organization_id}:{self.demo_session_id}'
        self.adapter.backend.upsert_by_id('deputy_public_state', archive)

    def list_commitments(self):
        return sorted([
            {key: copy.deepcopy(value) for key, value in record.items() if key != 'context'}
            for record in self._commitments.values()
        ], key=lambda row: row['created_at'], reverse=True)

    def select_commitment(self, payload):
        cid = payload.get('commitment_id')
        if cid not in self._commitments:
            raise ContractError('commitment_not_found', 'This commitment is not in the current demo session.')
        self._save_ledger()
        self.active_commitment_id = cid
        self._restore_context(self._commitments[cid]['context'])
        self._sync_public_deputy_mirror()
        return self._commitments[cid]['id']

    def new_commitment_draft(self, payload):
        self._save_ledger()
        self.active_commitment_id = None
        self._restore_context(self._draft_context)
        for field, section in [('goal_text', 'intent_and_goal'), ('principle_text', 'governing_principle')]:
            if payload.get(field):
                self.commit_state[section]['proposed_text'] = str(payload[field]).strip()
        self.commit_state['summary_copy']['goal_summary'] = self.commit_state['intent_and_goal']['proposed_text']
        self.commit_state['summary_copy']['principle_summary'] = self.commit_state['governing_principle']['proposed_text']
        self._sync_public_deputy_mirror()

    def _record_commitment(self, payload, actor, now):
        cid = payload.get('commitment_id') or f'commitment-{uuid.uuid4().hex}'
        previous = self._commitments.get(cid)
        c = self.commit_state
        section_values = [
            ('Goal', c['intent_and_goal']['proposed_text']),
            ('Rule / principle', c['governing_principle']['proposed_text']),
            ('Culture', c['culture_to_protect']['protect']),
            ('Monitoring', '; '.join(c['monitoring_mandate']['signals_watched'])),
        ]
        record = {
            'id': cid, 'kind': 'Agreement', 'number': previous['number'] if previous else len(self._commitments) + 1,
            'text': c['intent_and_goal']['proposed_text'], 'status': 'confirmed',
            'version': previous['version'] + 1 if previous else 1,
            'created_at': previous['created_at'] if previous else now,
            'confirmed_at': previous['confirmed_at'] if previous else now,
            'updated_at': now, 'confirmed_by': actor,
            'source_chat_url': payload.get('source_chat_url') or (previous or {}).get('source_chat_url'),
            'scenario_key': payload.get('scenario_key') or (previous or {}).get('scenario_key', 'unconfigured'),
            'sections': [{'kind': kind, 'text': text} for kind, text in section_values],
        }
        self.active_commitment_id = cid
        self._commitments[cid] = {**record, 'context': self._capture_context()}
        self.adapter.backend.insert_one('deputy_public_state', {
            **make_envelope(f'{cid}:revision:{record["version"]}', organization_id=self.adapter.organization_id),
            'kind': 'CommitmentRevision', 'demo_session_id': self.demo_session_id, **record,
        })

    def _require_scenario(self):
        if self.active_commitment_id and self._commitments[self.active_commitment_id]['scenario_key'] != 'discount-demo':
            raise ContractError('implementation_not_configured', 'This commitment has no implementation plan or measured outcomes yet.')
