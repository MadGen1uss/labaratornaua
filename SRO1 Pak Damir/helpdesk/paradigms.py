"""Сравнение парадигм на одной задаче (лекция 1).

Задача: получить номера заявок с нарушением SLA в порядке обработки.
Три решения: императивное (prototype), объектное (HelpDesk) и функциональное.
"""
from __future__ import annotations

import timeit
from datetime import datetime
from typing import List, Sequence

from .analytics import queue_key
from .data import build_desk
from .models import TicketView
from .pipeline import overdue_at
from .prototype import overdue_ids_imperative


def overdue_functional(views: Sequence[TicketView], now: datetime) -> List[int]:
    """Функциональный вариант: фильтр → сортировка → проекция."""
    late = filter(overdue_at(now), views)
    return [v.ticket_id for v in sorted(late, key=queue_key)]


def compare(records: List[dict], now: datetime, repeat: int = 300) -> dict:
    """Запустить три решения, проверить совпадение и замерить время."""
    desk = build_desk(records)
    views = desk.views()
    candidates = {
        "Императивное": lambda: overdue_ids_imperative(records, now),
        "Объектное (ООП)": lambda: [v.ticket_id for v in desk.violations(now)],
        "Функциональное": lambda: overdue_functional(views, now),
    }
    results = {}
    for name, solve in candidates.items():
        ids = solve()
        seconds = timeit.timeit(solve, number=repeat) / repeat
        results[name] = {"ids": ids, "ms": round(seconds * 1000, 4)}
    return results
