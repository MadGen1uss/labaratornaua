"""Чистые функции аналитики (лекции 3, 7).

Ни одна функция не меняет входные данные и не обращается к часам:
текущее время `now` всегда передаётся параметром.
"""
from __future__ import annotations

from datetime import datetime
from typing import Mapping, Optional, Sequence

from .models import OPEN_STATUSES, Status, TicketView


def is_open(view: TicketView) -> bool:
    return view.status in OPEN_STATUSES


def is_overdue(view: TicketView, now: datetime) -> bool:
    """Нарушен ли SLA: заявка закончена/ещё идёт позже срока."""
    end = view.finished_at if view.finished_at is not None else now
    return end > view.deadline


def hours_overdue(view: TicketView, now: datetime) -> float:
    end = view.finished_at if view.finished_at is not None else now
    delta = (end - view.deadline).total_seconds() / 3600
    return round(max(0.0, delta), 2)


def queue_key(view: TicketView) -> tuple:
    """Ключ очереди: приоритет, затем срок SLA, затем номер."""
    return (int(view.priority), view.deadline, view.ticket_id)


def open_queue(views: Sequence[TicketView]) -> tuple:
    """Открытые заявки в порядке обработки (исходная коллекция не меняется)."""
    return tuple(sorted((v for v in views if is_open(v)), key=queue_key))


def overdue_views(views: Sequence[TicketView], now: datetime) -> tuple:
    return tuple(v for v in views if is_overdue(v, now))


def resolution_hours(view: TicketView) -> Optional[float]:
    if view.finished_at is None:
        return None
    return round((view.finished_at - view.created_at).total_seconds() / 3600, 2)


def average_resolution_hours(views: Sequence[TicketView]) -> Optional[float]:
    values = [h for h in map(resolution_hours, views) if h is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def sla_compliance(views: Sequence[TicketView], now: datetime) -> float:
    """Доля заявок, уложившихся в SLA, в процентах."""
    if not views:
        return 100.0
    ok = sum(1 for v in views if not is_overdue(v, now))
    return round(100 * ok / len(views), 1)


def reachable(source: Status, target: Status,
              graph: Mapping[Status, frozenset],
              visited: frozenset = frozenset()) -> bool:
    """Можно ли из `source` прийти в `target` по графу переходов (рекурсия).

    Обход графа в глубину естественно записывается рекурсивно; множество
    `visited` неизменяемо и защищает от зацикливания (IN_PROGRESS ⇄ WAITING).
    """
    if source is target:
        return True
    if source in visited:
        return False
    seen = visited | {source}
    return any(reachable(nxt, target, graph, seen) for nxt in graph[source])
