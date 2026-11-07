# Proposed evidence model · v0

All records have `organization_id`, stable `_id`, `created_at` (UTC ISO timestamp), `schema_version`. Every write must be scoped to the authorized organization. Application authorization is required; an organization field alone is not isolation.

| Collection | Fields beyond common envelope | Meaning |
|---|---|---|
| sources | origin, content_hash, content, consent, sensitivity, observed_at | Immutable authorized source snapshots |
| claims | subject, predicate, value, valid_from, valid_to, source_id, quote, span, extraction_run_id, status | Candidate statements; status candidate/accepted/rejected/disputed |
| entities | kind, name, claim_ids, model_version | Proposed organization structure anchored in claims |
| relations | from_id, to_id, type, claim_ids, model_version | Explicit relationships with evidence |
| reviews | claim_ids, method, provider, model, prompt_version, result, uncertainty, run_id | Model review signals; never automatic truth |
| conflicts | claim_ids, reason, status, resolution_decision_id | Possible contradictions, including temporal/scope ambiguity |
| goals | parent_id, description, priority, resource_budget, success_criteria, owner | Human-approved goal tree |
| rules | text, kind, scope, authority, version, decision_id | Explicit rules and permissions; kind explicit |
| culture_hypotheses | description, supporting_event_ids, counterexamples, review_status | Inferred recurring behavior, not approved policy |
| agent_specs | intent, goal_ids, role, model_version, allowed_tools, data_scope, budget, status, approval_decision_id | Draft agent contract; starts proposed |
| decisions | author, subject_id, action, rationale, previous_version, next_version, created_at | Human approval, rejection or correction |
| acknowledgements | agent_id, decision_id, received_at, applied_version | Delivery acknowledgement, distinct from compliance |
| events | run_id, agent_id, type, payload_redacted, goal_id, rule_version, model_version | Auditable actions and observations |
| evaluations | dataset_id, model_version, metric, numerator, denominator, method, limitations | Measured reliability, not a model's self-confidence |

## Invariants to implement

1. A claim's quote must match the referenced source span. Source support does not imply truth.
2. A contradiction compares scope and time as well as values; two different dates may both be correct.
3. Changes create new versions and preserve prior evidence and decisions.
4. Activation requires a current human approval of the exact agent specification version. An acknowledgement alone cannot authorize tools.
5. A culture hypothesis remains separate from explicit policy until deliberately adopted.
6. Track goal delivery and reliability with observed outcomes and sample size. Do not invent a probability of goal achievement.

Validation, access control, transactions and enforcement are future application work. The schema is provisional until the first vertical slice validates it.
