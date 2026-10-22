"""Императивный прототип (лекция 2): состояние, присваивание, условия, циклы.

Работает напрямую со словарями из JSON, без классов и без модулей проекта.
Правила приоритета и SLA здесь намеренно продублированы — это и есть
исходная точка сравнения парадигм.

Запуск:  python -m helpdesk.prototype
"""
from datetime import datetime, timedelta
import json
import sys

BASE_PRIORITY = {"Стипендия": 2, "Оценки": 3, "Расписание": 3,
                 "Общежитие": 3, "Технические": 3, "Документы": 4}
SLA_HOURS = {1: 4, 2: 8, 3: 24, 4: 72}
URGENT = ["срочно", "не могу войти", "блокиров"]
OPEN = ["NEW", "IN_PROGRESS", "WAITING"]


def overdue_ids_imperative(records, now):
    """Номера заявок с нарушением SLA, в порядке обработки."""
    found = []
    number = 0
    for rec in records:
        number = number + 1
        prio = BASE_PRIORITY.get(rec["category"], 3)
        text = rec["title"].lower()
        for word in URGENT:
            if word in text:
                if prio > 1:
                    prio = prio - 1
                break
        created = datetime.fromisoformat(rec["created_at"])
        deadline = created + timedelta(hours=SLA_HOURS[prio])
        finished = None
        for event in rec["events"]:
            if event["status"] in OPEN:
                finished = None
            elif finished is None:
                finished = datetime.fromisoformat(event["at"])
        end = now if finished is None else finished
        if end > deadline:
            found.append((prio, deadline, number))
    found.sort()
    return [item[2] for item in found]


def main(path="data/tickets.json", now=datetime(2026, 10, 22, 12, 0)):
    with open(path, encoding="utf-8") as handle:
        records = json.load(handle)
    total = len(records)
    open_count = 0
    for rec in records:
        status = rec["events"][-1]["status"] if rec["events"] else "NEW"
        if status in OPEN:
            open_count += 1
    late = overdue_ids_imperative(records, now)
    print("Императивный прототип службы поддержки")
    print("Всего заявок:", total)
    print("Открытых:", open_count)
    print("Нарушений SLA:", len(late))
    print("Номера нарушений:", late)


if __name__ == "__main__":
    main(*sys.argv[1:2])
