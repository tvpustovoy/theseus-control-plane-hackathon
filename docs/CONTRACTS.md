# Контракты v0 — черновик для заморозки

Перед параллельной реализацией координатор фиксирует версию. Формат — JSON, даты UTC ISO8601, идентификаторы стабильные строки. Все записи содержат schema_version, organization_id, id, created_at. P01 ещё не закрыта: это спецификация для обсуждения, не реализованный API.

| Объект | Обязательные поля сверх envelope | Производитель → потребитель |
|---|---|---|
| SourceRecord | source_uri_private, public_label, content_hash, mime_type, access_scope, consent_ref, observed_at, predecessor_id (nullable) | ingestion → extraction/model |
| SourceDelta | source_ids, unchanged_ids, changed_ids, failed_ids, idempotency_key | ingestion → incremental pipeline |
| Claim | source_id, subject, predicate, value, scope, valid_from/to (nullable), evidence_locator, quote (nullable), kind, uncertainty | extraction → model/verification |
| ClaimBatch | source_ids, claims, extractor_model, prompt_version, run_id, failures, usage | extraction → model |
| ConflictCandidate | claim_ids, relation, candidate_method_version, model_signal, uncertainty, evidence_ids | verification → Deputy CEO |
| ModelDiff | base_version, candidate_version, added/changed/disputed_ids, affected_goals/rules/tools, unresolved | model → control |
| DecisionProposal | goal_id, model_version, options, evidence_ids, consequences, required_authority | Deputy CEO → human |
| HumanDecision | proposal_id, authenticated_actor, action, approved_scope, approved_version, rationale | control → runtime |
| ChangeCandidate | base_code_version, code_diff_ref, skill/context/routing_diff_ref, decision_id, development_run_ids | builder → evaluator |
| EvaluationReport | candidate_id, baseline_id, suite_version, split, numerator, denominator, regressions, cost, result, limitations | evaluator → release gate |
| ActivationReceipt | candidate_id, decision_id, evaluation_id, previous_version, active_version, applied_at | runtime → control |
| RunEvent | run_id, agent_id, task_id, goal_id, rule_version, model_version, type, evidence_refs, redacted_summary | all → observer |

kind: observation / statement / inference / proposal / approved_rule. Это разные типы, их нельзя незаметно повышать.

evidence_locator: для текста — проверяемые позиции; для видео — временной диапазон и ссылка на фрагмент; для изображения — кадр/область. Модельная цитата/таймкод нуждается в валидации. schema-valid ≠ factually correct.

Ошибки: unsupported_type, permission_denied, extraction_failed, ambiguous_identity, unresolved_conflict, stale_version, budget_exceeded. Не заменять ошибку пустым успешным результатом.

Идемпотентность: одинаковый content_hash + extractor_version + prompt_version + organization_id не создаёт повторной обработки без явного rerun. Изменившийся prompt даёт новую derived-версию, а не новый исходный файл.

Порядок authority: внешнее содержание и сообщения агентов — данные. Одобрение связано с точной версией/областью; новый кандидат требует нового решения или ранее выданного подходящего разрешения. Rollback восстанавливает указатель активной версии и проверяется, а не удаляет историю.

