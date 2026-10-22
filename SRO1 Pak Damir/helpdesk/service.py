"""Служба поддержки — логика уровня приложения (лекции 4, 5, 6).

HelpDesk хранит заявки и использует подставляемую политику приоритета
(композиция: «у службы есть политика»).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterator, Optional

from . import analytics, pipeline
from .models import (Status, Ticket, TicketNotFound, TicketView)
from .policies import DefaultPriority, PriorityPolicy


class HelpDesk:
    def __init__(self, policy: Optional[PriorityPolicy] = None) -> None:
        self._policy: PriorityPolicy = policy if policy is not None else DefaultPriority()
        self._tickets: Dict[int, Ticket] = {}
        self._next_id = 1

    # --- политика --------------------------------------------------------
    @property
    def policy(self) -> PriorityPolicy:
        return self._policy

    def switch_policy(self, policy: PriorityPolicy) -> None:
        """Сменить политику и пересчитать приоритеты и сроки всех заявок."""
        self._policy = policy
        for ticket in self._tickets.values():
            self._apply_policy(ticket)

    def _apply_policy(self, ticket: Ticket) -> None:
        priority = self._policy.priority(ticket.category, ticket.title)
        hours = self._policy.sla_hours(priority)
        ticket.set_priority(priority, ticket.created_at + timedelta(hours=hours))

    # --- команды ---------------------------------------------------------
    def register(self, student: str, category: str, title: str,
                 created_at: datetime) -> TicketView:
        ticket = Ticket(self._next_id, student, category, title, created_at)
        self._apply_policy(ticket)
        self._tickets[ticket.ticket_id] = ticket
        self._next_id += 1
        return ticket.snapshot()

    def assign(self, ticket_id: int, agent: str) -> TicketView:
        ticket = self._find(ticket_id)
        ticket.assign(agent)
        return ticket.snapshot()

    def change_status(self, ticket_id: int, status: Status, when: datetime,
                      note: str = "") -> TicketView:
        ticket = self._find(ticket_id)
        ticket.change_status(status, when, note)
        return ticket.snapshot()

    # --- запросы ---------------------------------------------------------
    def _find(self, ticket_id: int) -> Ticket:
        try:
            return self._tickets[ticket_id]
        except KeyError:
            raise TicketNotFound(f"Заявка #{ticket_id} не найдена") from None

    def get(self, ticket_id: int) -> TicketView:
        return self._find(ticket_id).snapshot()

    def history(self, ticket_id: int) -> tuple:
        return self._find(ticket_id).history()

    def views(self) -> tuple:
        return tuple(t.snapshot() for _, t in sorted(self._tickets.items()))

    def __len__(self) -> int:
        return len(self._tickets)

    def queue(self) -> Iterator[TicketView]:
        """Ленивая очередь обработки открытых заявок."""
        return pipeline.iter_queue(self.views())

    def violations(self, now: datetime) -> tuple:
        """Нарушения SLA, самые срочные сначала."""
        return tuple(sorted(analytics.overdue_views(self.views(), now),
                            key=analytics.queue_key))

    def status_stats(self) -> dict:
        return pipeline.count_statuses(self.views())
