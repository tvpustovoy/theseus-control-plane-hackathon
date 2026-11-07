#!/usr/bin/env python3
"""Offline readiness tracker. No network, model calls or automatic task dispatch."""
import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"todo", "doing", "review", "done", "blocked"}

def validate(data, root):
    tasks = data["tasks"]
    ids = [t["id"] for t in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate task ID")
    by_id = {t["id"]: t for t in tasks}
    for t in tasks:
        if t["status"] not in STATUSES:
            raise ValueError("Invalid status: " + t["id"])
        if t["approval"] not in {"pending", "user"}:
            raise ValueError("Invalid approval: " + t["id"])
        for dep in t["depends_on"]:
            if dep not in by_id:
                raise ValueError("Unknown dependency: " + dep)
        if t["status"] == "done" and not t["evidence"]:
            raise ValueError("Done without evidence: " + t["id"])
        for item in t["evidence"]:
            path = (root / item).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                raise ValueError("Missing or unsafe evidence: " + item)
        if t["status"] in {"doing", "review", "done"}:
            if t["approval"] != "user":
                raise ValueError("Work started without approval: " + t["id"])
            if t["blockers"] or any(by_id[d]["status"] != "done" for d in t["depends_on"]):
                raise ValueError("Work started with unmet dependency/blocker: " + t["id"])
    seen, active = set(), set()
    def visit(key):
        if key in active:
            raise ValueError("Dependency cycle")
        if key in seen:
            return
        active.add(key)
        for dep in by_id[key]["depends_on"]:
            visit(dep)
        active.remove(key)
        seen.add(key)
    for key in ids:
        visit(key)
    return by_id

def readiness(task, by_id):
    if task["status"] == "done":
        return "Завершено"
    unmet = [d for d in task["depends_on"] if by_id[d]["status"] != "done"]
    if unmet or task["blockers"] or task["status"] == "blocked":
        reasons = unmet + task["blockers"]
        return "Ждёт: " + ("; ".join(reasons) or "явный блокер")
    return "Входы готовы"

def render(data, root):
    by_id = validate(data, root)
    phases = list(dict.fromkeys(t["phase"] for t in data["tasks"]))
    counts = [(p, sum(t["status"] == "done" for t in data["tasks"] if t["phase"] == p),
               sum(t["phase"] == p for t in data["tasks"])) for p in phases]
    summary = "\n".join(f"- {p}: {done}/{total} завершено" for p, done, total in counts)
    out = ["# Theseus — общий трекер", "",
           "Источник: tasks.json. Пересчёт: python3 reports/build.py. Снимок: " + data["as_of"], "",
           "**Входы готовы ≠ разрешено начать.** Назначенные владельцы — предложения, пока Тарас не разрешил запуск. Подтверждение доставки не равно ACK.", "",
           summary, "", "## Участники", ""]
    out += [f"- {a['name']}: {a['state']}" for a in data["actors"]]
    out += ["", "## Задачи", "",
            "| ID / фаза | Работа / владелец | Готовность | Статус / разрешение / доставка |",
            "|---|---|---|---|"]
    html_rows = []
    esc = html.escape
    for t in data["tasks"]:
        ready = readiness(t, by_id)
        permission = "разрешено" if t["approval"] == "user" else "ждёт Тараса"
        out.append(f"| {t['id']} · {t['phase']} | {t['title']} — {t['owner']} | {ready} | {t['status']} / {permission} / {t['dispatch']} |")
        evidence = ", ".join(t["evidence"]) or "ещё нет"
        out += []  # Per-task acceptance follows the compact table.
        html_rows.append("<tr><td>" + esc(t["id"]) + "<br>" + esc(t["phase"]) +
            "</td><td><strong>" + esc(t["title"]) + "</strong><br>" + esc(t["owner"]) +
            "<details><summary>Результат и область</summary><p>" + esc(t["acceptance"]) +
            "</p><p>" + esc(t["scope"]) + "</p><p>Свидетельства: " + esc(evidence) +
            "</p></details></td><td>" + esc(ready) + "</td><td>" + esc(t["status"]) +
            "<br>" + esc(permission) + "<br>" + esc(t["dispatch"]) + "</td></tr>")
    out += ["", "## Критерии и передача", ""]
    for t in data["tasks"]:
        out += [f"### {t['id']} · {t['title']}", "", f"- Область: {t['scope']}",
                f"- Готово, когда: {t['acceptance']}",
                "- Свидетельства: " + (", ".join(t["evidence"]) or "нет"), ""]
    md = "\n".join(out) + "\n"
    cards = "".join("<li>" + esc(p) + ": <b>" + str(done) + "/" + str(total) +
                    "</b> завершено</li>" for p, done, total in counts)
    actors = "".join("<li>" + esc(a["name"] + ": " + a["state"]) + "</li>" for a in data["actors"])
    page = """<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Theseus — общий трекер</title><style>
:root{color-scheme:light;--ink:#1c1c1a;--muted:#545958;--line:#c8d6d3;--jade:#00695e}
*{box-sizing:border-box}body{margin:0 auto;padding:28px 18px 64px;max-width:1300px;
font:16px/1.55 system-ui,sans-serif;color:var(--ink);background:#f3f7f7}
h1{font-size:clamp(28px,5vw,40px);margin:0}h2{margin:32px 0 12px}
p{max-width:75ch}a{color:var(--jade);text-underline-offset:3px}
.table{overflow:auto;background:white;border:1px solid var(--line)}
table{border-collapse:collapse;width:100%;min-width:780px;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:14px;border-bottom:1px solid var(--line)}
th{background:#c7e2d8}td:nth-child(2){min-width:300px}summary{cursor:pointer;color:var(--jade);padding:8px 0}
:focus-visible{outline:3px solid var(--jade);outline-offset:3px}::selection{background:#c7e2d8}
small{color:var(--muted)}ul{padding-left:22px}.counts{display:flex;gap:8px 32px;flex-wrap:wrap}
@media(max-width:600px){body{padding:20px 12px}.counts{display:block}}
</style><main><h1>Theseus Control Plane</h1>
<p>Общий план работы команды. <strong>Входы готовы — ещё не разрешение начать.</strong>
Запуск только по команде Тараса. Агенты работают в одной папке в разных областях.</p>
<small>Статический снимок: """ + esc(data["as_of"]) + """. Пересчёт: python3 reports/build.py.</small>
<h2>Готовность по фазам</h2><ul class="counts">""" + cards + """</ul>
<h2>Сессии</h2><ul>""" + actors + """</ul>
<h2>Задачи и зависимости</h2><p>Открой строку «Результат и область», чтобы увидеть критерий готовности.
Таблица прокручивается горизонтально на узком экране.</p>
<div class="table" tabindex="0" aria-label="Таблица задач с горизонтальной прокруткой"><table>
<thead><tr><th>ID / фаза</th><th>Работа / владелец</th><th>Готовность</th><th>Статус / разрешение / доставка</th></tr></thead>
<tbody>""" + "".join(html_rows) + """</tbody></table></div>
<p><a href="../docs/PLAN.md">План</a> · <a href="../docs/PHASES.md">Две фазы</a> ·
<a href="../docs/COLLABORATION.md">Совместная работа</a> · <a href="../docs/WORKLOG.md">Журнал</a></p>
<p>Завершение задач — счётчик принятых результатов, не вероятность успеха и не оценка качества продукта.
Продуктовые проверки ещё не запускались.</p></main></html>"""
    return md, page

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = json.loads((ROOT / "docs/tasks.json").read_text())
    md, page = render(data, ROOT)
    outputs = {ROOT / "docs/WORKBOARD.md": md, ROOT / "reports/STATUS.html": page}
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit("Stale output: " + str(path))
        else:
            path.write_text(content)
    print("Tracker validated: " + str(len(data["tasks"])) + " tasks; no dispatch performed.")

if __name__ == "__main__":
    main()

