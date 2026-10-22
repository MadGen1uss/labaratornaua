"""Функциональный конвейер (лекция 8): замыкания, map/filter/reduce, генераторы."""
from __future__ import annotations

from datetime import datetime
from functools import partial, reduce
from heapq import heapify, heappop
from itertools import islice
from operator import add
from typing import Callable, Iterable, Iterator, Optional, Sequence

from .analytics import hours_overdue, is_open, is_overdue, queue_key
from .models import Priority, Status, TicketView

Predicate = Callable[[TicketView], bool]


# --- фабрики предикатов (замыкания) -----------------------------------------
def category_is(category: str) -> Predicate:
    def predicate(view: TicketView) -> bool:
        return view.category == category
    return predicate


def priority_at_least(level: Priority) -> Predicate:
    """Приоритет не ниже `level` (CRITICAL — самый высокий)."""
    return lambda view: view.priority <= level


def assigned_to(agent: str) -> Predicate:
    return lambda view: view.assignee == agent


def overdue_at(now: datetime) -> Predicate:
    return lambda view: is_overdue(view, now)


def all_of(*predicates: Predicate) -> Predicate:
    """Композиция предикатов по «И»."""
    return lambda view: all(p(view) for p in predicates)


# --- ленивая очередь -------------------------------------------------------
def iter_queue(views: Iterable[TicketView]) -> Iterator[TicketView]:
    """Генератор очереди: отдаёт заявки по одной, самая срочная первой.

    Куча строится за O(n), каждая выдача стоит O(log n); если нужны только
    первые k заявок, полная сортировка не выполняется.
    """
    heap = [(queue_key(v), v) for v in views if is_open(v)]
    heapify(heap)
    while heap:
        yield heappop(heap)[1]


def take(n: int, iterable: Iterable) -> tuple:
    return tuple(islice(iterable, n))


# --- форматирование и свёртки ---------------------------------------------
def format_view(view: TicketView, now: datetime) -> str:
    mark = "!" if is_overdue(view, now) else " "
    return (
        f"#{view.ticket_id:03d} {mark} P{int(view.priority)} "
        f"{view.status.value:<16} {view.category:<11} "
        f"до {view.deadline:%d.%m %H:%M}  {view.title}"
    )


def queue_lines(views: Sequence[TicketView], now: datetime,
                limit: Optional[int] = None) -> tuple:
    lines = map(partial(format_view, now=now), iter_queue(views))
    return take(limit, lines) if limit else tuple(lines)


def count_statuses(views: Iterable[TicketView]) -> dict:
    """Статистика по статусам через reduce (без изменения аккумулятора)."""
    empty = {status: 0 for status in Status}
    return reduce(
        lambda acc, v: {**acc, v.status: acc[v.status] + 1}, views, empty
    )


def count_priorities(views: Iterable[TicketView]) -> dict:
    empty = {priority: 0 for priority in Priority}
    return reduce(
        lambda acc, v: {**acc, v.priority: acc[v.priority] + 1}, views, empty
    )


def total_overdue_hours(views: Iterable[TicketView], now: datetime) -> float:
    return round(reduce(add, map(partial(hours_overdue, now=now), views), 0.0), 2)
