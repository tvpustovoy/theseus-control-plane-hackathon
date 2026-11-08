# Theseus — общий трекер

Источник: tasks.json. Пересчёт: python3 reports/build.py. Снимок: 2026-11-07

**Входы готовы ≠ разрешено начать.** Назначенные владельцы — предложения, пока Тарас не разрешил запуск. Подтверждение доставки не равно ACK.

- Подготовка: 1/5 завершено
- A: 1/7 завершено
- B: 0/7 завершено
- Интерфейс: 0/4 завершено
- Защита: 0/3 завершено

## Участники

- Viveka.HackatonCoordinator: active_coordination
- Muse.Hackathon: demo_evidence_ready
- Argon.Hackathon: handoff_after_model_limit
- Setu.Hackathon: demo_artifacts_in_progress
- Independent verifier: unassigned

## Задачи

| ID / фаза | Работа / владелец | Готовность | Статус / разрешение / доставка |
|---|---|---|---|
| P00 · Подготовка | План, роли, пакеты и трекер — Viveka.Hackathon | Завершено | done / разрешено / not_sent |
| P01 · Подготовка | Зафиксировать контракты и план независимой оценки — Viveka.HackatonCoordinator | Входы готовы | todo / ждёт Тараса / not_sent |
| P02 · Подготовка | Запустить сессии и связь Ours — Viveka.HackatonCoordinator | Ждёт: Команда Тараса на создание/запуск ролей | todo / ждёт Тараса / not_sent |
| P03 · Подготовка | Проверить ключи Meta, Gemini и SubQ — Viveka.HackatonCoordinator | Ждёт: Получить Gemini API key; определить бюджет теста | todo / ждёт Тараса / not_sent |
| P04 · Подготовка | Подготовить MongoDB и ограниченный доступ — Argon.Hackathon | Ждёт: P01; Разрешить создание базы/доступа | todo / ждёт Тараса / not_sent |
| A01 · A | Выбрать процесс и разрешённые источники — Тарас | Ждёт: Ссылка/набор данных и границы использования | todo / ждёт Тараса / not_sent |
| A02 · A | Приём файлов, типы, хеши и повторная загрузка — Muse.Hackathon | Ждёт: P01; P02 | todo / ждёт Тараса / not_sent |
| A03 · A | Meta: текст/PDF/медиа → claims со свидетельствами — Muse.Hackathon | Ждёт: A02; P03; A01 | todo / ждёт Тараса / not_sent |
| A04 · A | Версионированная модель и запросы — Argon.Hackathon | Ждёт: P01; P02; P04 | todo / ждёт Тараса / not_sent |
| A05 · A | Подбор конфликтов и SubQ-шлюз — Muse.Hackathon | Завершено | done / разрешено / acknowledged |
| A06 · A | Собрать и подтвердить исходную модель v1 — Viveka.HackatonCoordinator | Ждёт: A03; A04; Решение Тараса по существенным конфликтам | todo / ждёт Тараса / not_sent |
| A07 · A | Построить один исполняемый инструмент — Argon.Hackathon | Ждёт: A06 | todo / ждёт Тараса / not_sent |
| B01 · B | Дельта модели и затронутые зависимости — Argon.Hackathon | Ждёт: A06 | todo / ждёт Тараса / not_sent |
| B02 · B | Новый файл/видео → новые свидетельства — Muse.Hackathon | Ждёт: A03; B01; Разрешённый новый материал, например звонок | todo / ждёт Тараса / not_sent |
| B03 · B | Новые противоречия и измерение экономии — Muse.Hackathon | Ждёт: B02; P03 | todo / ждёт Тараса / not_sent |
| B04 · B | Человеческое решение и проверка полномочий — Argon.Hackathon | Ждёт: B01; B03; A07 | todo / ждёт Тараса / not_sent |
| B05 · B | Изменение инструмента и собственного навыка — Argon.Hackathon | Ждёт: B04 | todo / ждёт Тараса / not_sent |
| B06 · B | Независимая held-out оценка — Проверяющий — не назначен | Ждёт: B05; P01; Назначить независимого проверяющего | todo / ждёт Тараса / not_sent |
| B07 · B | Принятие/откат и доказательство поведения — Argon.Hackathon | Ждёт: B06; Разрешение на активацию точной версии | todo / ждёт Тараса / not_sent |
| F01 · Интерфейс | Каркас Deputy CEO и инструменты состояния — Argon.Hackathon | Ждёт: P01; P02 | todo / ждёт Тараса / not_sent |
| F02 · Интерфейс | Fetch Deputy CEO / Agentverse bridge — Viveka.Hackathon | Ждёт: F01; B07; Доступ/регистрация Agentverse | todo / ждёт Тараса / not_sent |
| F03 · Интерфейс | Six Theseus browser UI states on localhost — Argon.Hackathon | Входы готовы | review / разрешено / acknowledged |
| F04 · Интерфейс | Organization Memory opening and grounded source questions — Viveka.Datamaster | Входы готовы | review / разрешено / acknowledged |
| D01 · Защита | Нарратив, презентация, видео и сценарий — Setu.Hackathon | Входы готовы | todo / разрешено / sent_unacknowledged |
| D02 · Защита | Подставить реальные результаты и ссылки — Setu.Hackathon | Ждёт: D01; F03 | todo / ждёт Тараса / not_sent |
| D03 · Защита | Публикация и сдача — Viveka.HackatonCoordinator | Ждёт: D02; Явная команда Тараса на публикацию и отправку | todo / ждёт Тараса / not_sent |

## Критерии и передача

### P00 · План, роли, пакеты и трекер

- Область: docs/
- Готово, когда: Читаемые план/пакеты; пересчёт трекера и его проверки проходят
- Свидетельства: docs/PLAN.md, docs/PHASES.md, docs/COLLABORATION.md, reports/build.py, reports/evidence/tracker-check.md

### P01 · Зафиксировать контракты и план независимой оценки

- Область: docs/CONTRACTS.md; app/evaluation/
- Готово, когда: Согласованы входы/выходы, development/validation/final splits и критерии допуска
- Свидетельства: нет

### P02 · Запустить сессии и связь Ours

- Область: docs/status/
- Готово, когда: У каждой роли отдельная идентичность; HELLO/ACK подтверждены; монитор проверен
- Свидетельства: нет

### P03 · Проверить ключи Meta, Gemini и SubQ

- Область: приватная конфигурация; reports/evidence/
- Готово, когда: Минимальные разрешённые вызовы и доступные модели записаны без секретов
- Свидетельства: нет

### P04 · Подготовить MongoDB и ограниченный доступ

- Область: database/
- Готово, когда: Подключение, запись/чтение синтетической записи, scope организации проверен
- Свидетельства: нет

### A01 · Выбрать процесс и разрешённые источники

- Область: приватный реестр; docs/DECISIONS.md
- Готово, когда: Один процесс, источники, права и критерии результата определены
- Свидетельства: нет

### A02 · Приём файлов, типы, хеши и повторная загрузка

- Область: app/ingestion/
- Готово, когда: SourceRecord/Delta; повтор не дублируется; ошибки типа/доступа видимы
- Свидетельства: нет

### A03 · Meta: текст/PDF/медиа → claims со свидетельствами

- Область: app/extraction/
- Готово, когда: Реальный вызов; проверяемые цитаты/таймкоды; наблюдения отделены от выводов
- Свидетельства: нет

### A04 · Версионированная модель и запросы

- Область: app/model/; database/
- Готово, когда: Сохранены источники/claims, изоляция scope, запрос provenance, версия без перезаписи истории
- Свидетельства: нет

### A05 · Подбор конфликтов и SubQ-шлюз

- Область: app/verification/
- Готово, когда: Нормализация/группировка, uncertainty route, тест межгрупповых пропусков; mock отделён от live
- Свидетельства: database/fixtures/evidence-handoff.json, database/fixtures/review-packet-subq-discount.json, docs/status/Muse.Hackathon.md

### A06 · Собрать и подтвердить исходную модель v1

- Область: интеграция; docs/DECISIONS.md
- Готово, когда: Сквозной Meta→MongoDB→SubQ прогон; утверждённый baseline; открытые вопросы сохранены
- Свидетельства: нет

### A07 · Построить один исполняемый инструмент

- Область: app/runtime/
- Готово, когда: Инструмент исполняет выбранный процесс; границы полномочий и baseline tests
- Свидетельства: нет

### B01 · Дельта модели и затронутые зависимости

- Область: app/model/
- Готово, когда: Diff новой версии, impacted rules/goals/tools, прежняя версия доступна
- Свидетельства: нет

### B02 · Новый файл/видео → новые свидетельства

- Область: app/ingestion/; app/extraction/
- Готово, когда: Обработана только дельта; предложения встречи не превращены в одобренные правила
- Свидетельства: нет

### B03 · Новые противоречия и измерение экономии

- Область: app/verification/
- Готово, когда: Одинаковый набор: direct review против Snap+escalation; расходы и missed conflicts
- Свидетельства: нет

### B04 · Человеческое решение и проверка полномочий

- Область: app/control/
- Готово, когда: Автор/версия/scope решения проверены; без разрешения изменение не активно
- Свидетельства: нет

### B05 · Изменение инструмента и собственного навыка

- Область: app/runtime/
- Готово, когда: Зафиксирована development-ошибка, patch и versioned skill/context/routing change
- Свидетельства: нет

### B06 · Независимая held-out оценка

- Область: app/evaluation/; отдельный закрытый набор
- Готово, когда: Baseline/candidate на unseen cases, sample sizes, regressions, reproducible gate
- Свидетельства: нет

### B07 · Принятие/откат и доказательство поведения

- Область: app/runtime/; app/control/
- Готово, когда: Хорошая версия принята при выполнении критериев; плохая заблокирована; rollback и поведение проверены
- Свидетельства: нет

### F01 · Каркас Deputy CEO и инструменты состояния

- Область: app/deputy/
- Готово, когда: Обзор, предложения и evidence через scoped tools; без произвольного доступа к базе
- Свидетельства: нет

### F02 · Fetch Deputy CEO / Agentverse bridge

- Область: app/deputy/agentverse/
- Готово, когда: Hosted Deputy CEO guides the owner to Theseus views; localhost-only data access is not claimed
- Свидетельства: нет

### F03 · Six Theseus browser UI states on localhost

- Область: app/ui/; app/api/; existing Argon backend areas
- Готово, когда: Six navigable states, evidence drawer, demo CRM validation, honest live/fixture/simulation labels, one start command and exact localhost URL
- Свидетельства: docs/agents/argon/UI-LOCALHOST-BRIEF.md, reports/2-scenarios/DEMO-INTERFACES.md, app/api/test_ui_api.py, docs/status/Viveka.Datamaster.md

### F04 · Organization Memory opening and grounded source questions

- Область: app/ui/; app/api/
- Готово, когда: Verified raw import and partial extraction shown separately; bounded source browsing; grounded question with citations; old six-state demo and reset survive; browser QA
- Свидетельства: docs/status/Viveka.Datamaster.md, app/api/test_organization_memory.py

### D01 · Нарратив, презентация, видео и сценарий

- Область: reports/1-concept/; reports/2-scenarios/; reports/3-artifacts/
- Готово, когда: Черновики 60s/3min/слайдов/Q&A, список недостающих evidence; работа ещё не подтверждена ACK
- Свидетельства: нет

### D02 · Подставить реальные результаты и ссылки

- Область: reports/3-artifacts/
- Готово, когда: Пять partner usage evidence, built-today, финальные ролик и слайды без вымышленных claims
- Свидетельства: нет

### D03 · Публикация и сдача

- Область: публичный GitHub; формы
- Готово, когда: Проверены секреты, запуск, ссылки; GitHub и обе заявки подтверждены
- Свидетельства: нет

