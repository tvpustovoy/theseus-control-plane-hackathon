# Подключение Muse.Hackathon и Argon.Hackathon

## Muse MCP compatibility note — November 7, 2026

The Muse Code session began failing Meta API calls with HTTP 400: `Recursive JSON schemas are not currently supported` after the Ours MCP server advertised 34 tools. An A/B check isolated the connection: the Ours MCP entry was removed from the private `~/.config/muse/settings.json` (exact backup: `~/.config/muse/settings.json.before-ours-mcp-schema-20261107`), and a fresh `muse-wonder-1.0` run with no MCP returned `OK` with exit code 0. This proves a working Muse path without Ours MCP; the specific incompatible tool schema has not been identified. Existing Muse sessions, auth and other settings were preserved.

The configuration example below is a future integration target, **not the active Muse setting**. Do not re-enable it wholesale until the tool schemas have been filtered or adapted and a real Muse/Meta call passes. A running Muse process may keep its old tool inventory; exit it and start a fresh process to pick up the current setting. For now, coordinator communication through Muse's Ours MCP is unavailable; manual status files and user-mediated handoff remain available.

**Инструкции подготовлены; сессии и идентичности ещё не созданы. Не начинать задачи без команды Тараса.** Сначала прочитать AGENTS.md, docs/PLAN.md, docs/COLLABORATION.md, свой пакет роли.

## Два независимых подключения
1. API модели — inference: Meta или Gemini, оплачивается соответствующим аккаунтом.
2. Ours через MCP — идентичность и зашифрованная связь с командой. Наличие API-ключа модели не создаёт Ours-идентичность.

Отдельно от них: [RecPlace MCP](RECPLACE-MCP.md) — чтение исходной базы для Argon. Конфигурация описана, ключи новых клиентов ещё не выданы. Основной вход Muse после переноса — MongoDB.

На текущем компьютере muse, agy и ours-mcp уже установлены. Проверять версии, не переустанавливать весь стек. Общий Ours-сервер не перезапускать и его настройки не менять.

## Ours
MCP-адаптер запускается командой `ours-mcp proxy`. Он использует приватный профиль `~/.ours-client/profile.json`. Не копировать профиль, credentialPath или токены в публичный проект. На другой машине нужен отдельно выданный клиентский профиль и `ours-install client --config /absolute/private-profile.json`; не угадывать адреса и не открывать локальный daemon наружу.

В подключённой сессии:
1. Вызвать list_identities и проверить существование Human identity. На этом хосте родитель проверен: tvp-pg@pg-home. Если инструмент показывает только роли, current_identity раскрывает родителя.
2. Если нужное имя есть — choose_identity. Если нет — create_identity с именем Muse.Hackathon либо Argon.Hackathon и bio из пакета. Создание/привязка только после команды владельца на запуск этой роли.
3. Никогда не брать Viveka.HackatonCoordinator и не использовать force при занятой идентичности.
4. Прочитать current_identity. Существующая persona требует согласия перед принятием. Мантра и пакеты ролей явно запрошены владельцем для этих новых агентов.
5. Отправить координатору HELLO: роль, версия harness, task=none, доступные инструменты, доступность API (без ключей), запрос следующей разрешённой задачи.
6. Запросить отдельное согласие на мониторинг. Само наличие MCP не даёт фонового пробуждения.

## Muse Code
Официальный CLI на этом компьютере: ~/.local/bin/muse. Он читает корневой AGENTS.md после доверия папке; не запускать muse init --force поверх наших правил.

После разрешения на старт:
```sh
cd /Users/taraspustovoy/Projects/theseus-control-plane-hackathon
muse --model muse-wonder-1.0 --contributor-mode off "Read AGENTS.md and docs/agents/muse/START-HERE.md. Prepare to work as Muse.Hackathon. Report your scope, dependencies and access blockers in Russian; wait for my instruction before implementation."
```

В приватных пользовательских настройках Muse объединить, не перезаписывая остальную конфигурацию:
```json
{
  "mcp_servers": {
    "ours": {
      "transport": "stdio",
      "command": "ours-mcp",
      "args": ["proxy"],
      "enabled": true,
      "mode": "required"
    }
  }
}
```
Если executable не виден в PATH, использовать локально проверенный абсолютный путь. Проверить /mcp. Этот фрагмент подготовлен по документации; подключение Muse к Ours ещё не испытано.

Для модели: интерактивный /login либо приватный META_API_KEY для headless CLI. Для собственного приложения Model API использует ключ, который наши адаптеры должны читать из окружения; имена переменных не дают ключу иной scope. Ключей в командной строке/репозитории не должно быть.

Источники: https://dev.meta.ai/docs/muse-code ; https://dev.meta.ai/docs/muse-code/configuration ; https://dev.meta.ai/docs/muse-code/extending .

## Argon: API-аккаунт и CLI — разные маршруты
Выданный на мероприятии временный аккаунт имеет, по сообщению организатора, $25 и доступ только к AI Studio Gemini API. Войти отдельным профилем браузера в https://aistudio.google.com/ и создать ключ выданного проекта. Проверить аккаунт/проект перед созданием. Не включать оплату и не создавать другой платный проект.

Сохранить ключ локально как GEMINI_API_KEY в игнорируемом .env, без пароля аккаунта. Сумма/доступ пока подтверждены письмом, не реальным API-вызовом. Ключ не создан этой подготовкой. Срок жизни аккаунта — день события, не долговременная зависимость продукта.

Для API-агента нужен runner с tool loop: он передаёт ролевой prompt модели, исполняет разрешённые tool calls и подключает локальный ours-mcp как клиент. Сам по себе запрос к Gemini не умеет читать наши файлы или вступать в Ours. Runner ещё предстоит выбрать/реализовать; не обещать готового бота из одного ключа.

Если используется уже установленный Antigravity CLI, справка текущей версии подтверждает подключение MCP:
```sh
agy mcp add ours ours-mcp proxy
```
Это изменение пользовательской конфигурации; выполнить только в рамках разрешённого запуска. Действующая личная подписка и её логин остаются отдельными. Не перелогинивать agy временным аккаунтом: право на Antigravity из письма не следует. Для подписочного запуска сохранять useG1Credits=false, если дополнительные кредиты не разрешены.

Для модели в приложении начать с SDK @google/genai или google-genai и проверить Interactions API/доступную модель по актуальной документации. На этом шаге нет ни модельного вызова, ни установки пакетов. Google guide рекомендует Argon как ведущую модель, Flash как ограниченных исполнителей; фактический доступ проверяется первым малым вызовом.

Проверенный ранее подписочный CLI-маршрут (не расходует выданные $25 API-кредиты):
```sh
cd /Users/taraspustovoy/Projects/theseus-control-plane-hackathon
agy --model gemini-4-argon-medium --settings '{"useG1Credits":false}' -i "Read AGENTS.md and docs/agents/argon/START-HERE.md. Prepare to work as Argon.Hackathon. Report your scope, dependencies and access blockers in Russian; wait for my instruction before implementation."
```

Wonder выбран для разработки, Spark — отдельный возможный runtime для массового извлечения. `--contributor-mode off` не отменяет отдельные условия бесплатных Meta-кредитов; перед клиентским pilot проверить действующие настройки использования данных.

