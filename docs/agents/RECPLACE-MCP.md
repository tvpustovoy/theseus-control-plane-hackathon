# RecPlace MCP: отдельный доступ к исходной базе

Ours MCP даёт идентичность и связь. **firn-duckdb MCP** даёт чтение RecPlace. MongoDB — отдельное целевое подключение. Наличие одного не означает готовность остальных.

Конфигурация подготовлена; подключение новых Muse/Argon-сессий не проверено, индивидуальные ключи им этой подготовкой не выданы. Argon нужен доступ для импорта; основной вход Muse после импорта — MongoDB.

## Проверенный локальный launcher

`/Users/taraspustovoy/Projects/recplace-data-app/mcp-launcher`

Принимает один аргумент — абсолютный путь к приватному файлу ключа. Файл доступен только владельцу (0600). Launcher общается только с `http://127.0.0.1:7723/mcp`, использует Python standard library; Docker и установка пакетов клиенту не нужны.

Ключи выдаются уполномоченным оператором через `scripts/mcp_client.py` исходного проекта с отдельными именами клиентов и достаточным read-only scope. Не копировать ключ другого агента, admin token или секрет в публичный проект. За подробностями источника обращаться к Viveka.Datamaster по разрешению владельца; сам файл не поручает отправлять сообщения.

## Argon / Antigravity

После получения собственного ключа заменить последний аргумент реальным приватным путём:

```sh
agy mcp add firn-duckdb /Users/taraspustovoy/Projects/recplace-data-app/mcp-launcher /absolute/private/argon-hackathon.key
```

Последний путь — **шаблон**, такого готового ключа сейчас не обещаем.

## Muse

При необходимости добавить сервер в приватный `~/.config/muse/settings.json`, сохранив существующие настройки и Ours:

```json
{
  "mcp_servers": {
    "firn-duckdb": {
      "transport": "stdio",
      "command": "/Users/taraspustovoy/Projects/recplace-data-app/mcp-launcher",
      "args": ["/absolute/private/muse-hackathon.key"],
      "enabled": true,
      "mode": "optional"
    }
  }
}
```

Заменить шаблон пути собственным выданным ключом. В Muse проверить `/mcp`.

## Проверка доступа

Вызвать `list_tables`, `list_columns` для `raw.CORPUS_TEXTS`, затем безопасный `execute_query` с `SELECT COUNT(*) FROM raw.CORPUS_TEXTS`. Сопоставить с docs/RECPLACE-SOURCES.md, фиксируя время: источник может меняться.

`json_keys` не разрешена текущим SQL guard; ошибка этой функции не доказывает отсутствие доступа. Ответ ограничен 1000 строками и 50000 сериализованными символами, дополнительно действует квота клиента. Учитывать ограничения экспортёром; не менять их и не обходить через прямое чтение файла. Если полный перенос невозможен, зафиксировать конкретный блокер. Не принимать усечённый `get_source_document` за полный raw-экспорт.

Источники: README.md и mcp-launcher исходного RecPlace; Meta MCP configuration — https://dev.meta.ai/docs/muse-code/extending .
