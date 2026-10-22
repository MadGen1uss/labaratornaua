"""Данные: воспроизводимый генератор, JSON и сборка службы поддержки (лекция 4)."""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .models import CATEGORIES, Status
from .policies import PriorityPolicy
from .service import HelpDesk

# Фиксированный «момент отчёта» — результаты запусков воспроизводимы.
REFERENCE_NOW = datetime(2026, 10, 22, 12, 0)

STUDENTS = (
    "Алиев Т.", "Бекова А.", "Сериков Н.", "Ким Д.", "Омарова Л.",
    "Жумабаев Р.", "Петрова М.", "Касымов Е.", "Нурланова С.", "Иванов А.",
    "Тулеуов Б.", "Ахметова К.", "Смагулов Д.", "Волкова И.", "Абдрахманов Ж.",
)
GROUPS = ("ИС-24-1", "ИС-24-2", "ИС-23-1", "ИС-23-2", "ВТ-24-1")
AGENTS = ("Ахметова А.", "Бектурова Д.", "Серик Н.")

TITLES = {
    "Стипендия": (
        "Не пришла стипендия за октябрь",
        "Срочно: ошибка в сумме стипендии",
        "Как оформить социальную стипендию",
    ),
    "Оценки": (
        "Неверный балл в ведомости",
        "Срочно нужна пересдача — не отображается допуск",
        "Не вижу оценку за рубежный контроль",
    ),
    "Расписание": (
        "Пересечение занятий в четверг",
        "Не отображается новое расписание",
        "Аудитория указана неверно",
    ),
    "Общежитие": (
        "Нет горячей воды в блоке Б",
        "Заявка на переселение",
        "Сломан замок в комнате 412",
    ),
    "Технические": (
        "Не могу войти в личный кабинет",
        "Не открывается электронный журнал",
        "Нет доступа к Wi-Fi в корпусе 2",
    ),
    "Документы": (
        "Справка с места учёбы",
        "Заказать дубликат студенческого билета",
        "Выписка из приказа о зачислении",
    ),
}

# Типовые «жизненные пути» заявок (с повторами — чаще встречаются).
FLOWS = (
    (), (),
    ("IN_PROGRESS",),
    ("IN_PROGRESS", "WAITING"),
    ("IN_PROGRESS", "RESOLVED"),
    ("IN_PROGRESS", "RESOLVED"),
    ("IN_PROGRESS", "RESOLVED", "CLOSED"),
    ("IN_PROGRESS", "WAITING", "IN_PROGRESS", "RESOLVED"),
    ("CLOSED",),
)


def generate_records(n: int = 30, seed: int = 2026,
                     now: datetime = REFERENCE_NOW) -> List[dict]:
    """Воспроизводимый набор заявок: при одинаковом seed результат одинаков."""
    rng = random.Random(seed)
    records: List[dict] = []
    for _ in range(n):
        category = rng.choice(CATEGORIES)
        created = now - timedelta(hours=rng.randint(2, 96),
                                  minutes=rng.choice((0, 15, 30, 45)))
        events: List[dict] = []
        moment = created
        for status in rng.choice(FLOWS):
            moment = moment + timedelta(hours=rng.randint(1, 14))
            if moment > now:
                break
            events.append({"status": status, "at": moment.isoformat(), "note": ""})
        started = any(e["status"] == "IN_PROGRESS" for e in events)
        records.append(
            {
                "student": f"{rng.choice(STUDENTS)} ({rng.choice(GROUPS)})",
                "category": category,
                "title": rng.choice(TITLES[category]),
                "created_at": created.isoformat(),
                "assignee": rng.choice(AGENTS) if started else None,
                "events": events,
            }
        )
    records.sort(key=lambda r: r["created_at"])
    return records


def save_records(path, records: List[dict]) -> None:
    Path(path).write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_records(path) -> List[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_desk(records: List[dict],
               policy: Optional[PriorityPolicy] = None) -> HelpDesk:
    """Создать службу поддержки и воспроизвести по записям всю историю."""
    desk = HelpDesk(policy)
    for rec in records:
        view = desk.register(rec["student"], rec["category"], rec["title"],
                             datetime.fromisoformat(rec["created_at"]))
        if rec.get("assignee"):
            desk.assign(view.ticket_id, rec["assignee"])
        for event in rec.get("events", []):
            desk.change_status(view.ticket_id, Status[event["status"]],
                               datetime.fromisoformat(event["at"]),
                               event.get("note", ""))
    return desk
