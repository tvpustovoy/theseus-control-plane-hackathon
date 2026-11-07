# Общий контракт Argon ↔ Muse · старт v0.1

Приоритет для первичного переноса над общим черновиком SCHEMA.md. Argon реализует физическую структуру и доступ, Muse — семантическое извлечение. Оба начинают с этого контракта; изменение полей согласуют через координатора. Контракт подготовлен, коллекции/функции пока не реализованы.

## Коллекции в базе theseus_recplace
| Коллекция | Кто создаёт / кто наполняет | Содержание |
|---|---|---|
| raw_records | Argon / импортёр Argon | Первичные записи RecPlace без смысловой переработки |
| import_runs | Argon / импортёр | Source snapshot, counts/hashes, errors, completed/incomplete |
| sources | Argon / детерминированный mapping | Документ, полный текст/ссылка на blob, provenance в raw_records, тип источника |
| source_chunks | Argon / Muse | Фрагменты с точными границами и хешем исходного текста |
| claims | Argon / Muse через write_claim_batch | Новые кандидаты фактов, не одобренная истина |
| fact_refs | Argon / Muse | reinforces/contradicts/updates со свидетельством |
| review_signals | Argon / Muse/SubQ | Пробелы, противоречия, неопределённость |
| extraction_runs | Argon / Muse | Model/prompt/schema versions, input hash, usage, ошибки |
| model_versions, decisions | Argon / control layer | Согласованное состояние и решения человека |

Все записи: schema_version, organization_id="recplace", _id, created_at. Права доступа обеспечивает приложение/DB user, не само наличие organization_id.

raw_records: source_table, dump_id, src_file, src_row_decimal (строка), loaded_at_source (строка + source type), v_json (исходное текстовое представление JSON), payload_sha256, record_key, import_run_id. null остаётся null. Поле payload parsed допустимо только как дополнительная проекция; не заменяет lossless v_json. Крупный payload хранить целиком в приватном blob/GridFS со ссылкой и хешем, не обрезать.

record_key строится из полного source identity; Argon сначала проверяет уникальность (table,dump,file,row). Если есть коллизии/дубликаты — хранить occurrence, не upsert-ить разные записи в одну. Версия содержимого хранится отдельно от identity. Повтор одного import run идемпотентен.

sources: source_type (sales_conversation / normative / founder_meeting / crm_record / unknown), raw_record_ids, original_source_metadata, text или text_blob_ref, text_sha256, day nullable, client_ref nullable, truncation_status, mapping_version. Unknown не приравнивать к sales.

source_chunks: source_id, source_version, chunk_id, text, text_sha256, char_start/end, transcript/media locator nullable, chunker_version. Границы ссылаются на конкретную версию текста.

claims: source_id, chunk_id, run_id, claim, fact_type, zone/subzone, speaker_role, knowledge_state, target_q, quote, evidence_locator, business_fields, extraction_status="candidate", quote_gate, model, prompt_version. known означает «так утверждает источник», не одобрение человеком. Не переименовывать автоматически candidate в accepted.

## Интерфейс, который Argon предоставляет Muse
Язык реализации не предписан; операции возвращают JSON, тестовый adapter соответствует тому же формату.
- list_sources(source_type, cursor, limit) → items, next_cursor; чтение после завершённого import run.
- get_source(source_id, version) → полный Source и provenance; явная ошибка вместо обрезки.
- put_chunks(source_id, version, chunks, chunker_version) → chunk_ids; проверяет границы/хеши.
- start_extraction(source_id, source_version, prompt_version, model, input_hash) → run_id.
- write_claim_batch(run_id, chunk_id, asserts, refs, signals) → accepted_candidate_ids, rejected_items; JSON/цитаты/enum валидируются.
- finish_extraction(run_id, usage, status, errors) → receipt.
- get_related_claims(source_id, subject_keys, scope) → ограниченный пакет для следующей сверки.

write_claim_batch создаёт только candidates. Подтверждать факты и правила может только отдельный процесс решения/проверки. Muse не должен сам создавать/изменять MongoDB-коллекции или писать произвольные документы в обход контракта.

## Три сообщения готовности
1. **SCHEMA_READY**: коллекции/индексы и adapter созданы; валидный и ошибочный synthetic batch проверены. Muse может подключать writer.
2. **RAW_IMPORT_VERIFIED**: lossless raw-копия сверена; указаны import_run_id, counts/digests; источники готовы.
3. **EXTRACTION_PILOT_READY**: Muse показал небольшой реальный pilot, цитаты и rejected cases; массовая обработка не запускается автоматически.

