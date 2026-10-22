"""Модели предметной области (лекции 4, 5).

Здесь только данные и правила их целостности:
  * Status, Priority — перечисления;
  * TRANSITIONS — допустимые переходы между статусами;
  * Ticket — изменяемая заявка с защищённым состоянием (инкапсуляция);
  * TicketView — неизменяемый «снимок» заявки для чистых функций (лекция 7).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, IntEnum
from types import MappingProxyType
from typing import Optional


class HelpDeskError(Exception):
    """Базовое исключение службы поддержки."""


class ValidationError(HelpDeskError):
    """Некорректные входные данные."""


class InvalidTransition(HelpDeskError):
    """Недопустимый переход между статусами."""


class TicketNotFound(HelpDeskError):
    """Заявка с таким номером не существует."""


class Status(Enum):
    NEW = "Новая"
    IN_PROGRESS = "В работе"
    WAITING = "Ожидает студента"
    RESOLVED = "Решена"
    CLOSED = "Закрыта"


class Priority(IntEnum):
    """Чем меньше число, тем выше приоритет."""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


CATEGORIES = (
    "Стипендия",
    "Оценки",
    "Расписание",
    "Общежитие",
    "Технические",
    "Документы",
)

OPEN_STATUSES = frozenset({Status.NEW, Status.IN_PROGRESS, Status.WAITING})
FINISHED_STATUSES = frozenset({Status.RESOLVED, Status.CLOSED})

# Граф допустимых переходов (только чтение).
TRANSITIONS = MappingProxyType(
    {
        Status.NEW: frozenset({Status.IN_PROGRESS, Status.CLOSED}),
        Status.IN_PROGRESS: frozenset({Status.WAITING, Status.RESOLVED}),
        Status.WAITING: frozenset({Status.IN_PROGRESS, Status.CLOSED}),
        Status.RESOLVED: frozenset({Status.CLOSED, Status.IN_PROGRESS}),
        Status.CLOSED: frozenset(),
    }
)


def raise_priority(priority: Priority, steps: int = 1) -> Priority:
    """Повысить приоритет на `steps` ступеней (рекурсивно, лекция 7).

    Рекурсия здесь обоснована: операция определяется как «один шаг + то же
    самое для оставшихся шагов», а базовый случай — потолок CRITICAL.
    """
    if steps <= 0 or priority is Priority.CRITICAL:
        return priority
    return raise_priority(Priority(priority - 1), steps - 1)


@dataclass(frozen=True)
class StatusChange:
    """Запись истории статусов."""

    status: Status
    at: datetime
    note: str = ""


@dataclass(frozen=True)
class TicketView:
    """Неизменяемый снимок заявки — вход для чистых функций аналитики."""

    ticket_id: int
    student: str
    category: str
    title: str
    priority: Priority
    status: Status
    created_at: datetime
    deadline: datetime
    assignee: Optional[str]
    finished_at: Optional[datetime]


class Ticket:
    """Заявка студента. Состояние закрыто: меняется только через методы."""

    def __init__(self, ticket_id: int, student: str, category: str,
                 title: str, created_at: datetime) -> None:
        if not isinstance(created_at, datetime):
            raise ValidationError("created_at должен быть datetime")
        if not student or not student.strip():
            raise ValidationError("Не указан студент")
        if not title or not title.strip():
            raise ValidationError("Пустая тема заявки")
        if category not in CATEGORIES:
            raise ValidationError(f"Неизвестная категория: {category!r}")
        self._id = ticket_id
        self._student = student.strip()
        self._category = category
        self._title = title.strip()
        self._created_at = created_at
        self._status = Status.NEW
        self._priority = Priority.NORMAL
        self._deadline = created_at
        self._assignee: Optional[str] = None
        self._history = [StatusChange(Status.NEW, created_at, "Заявка создана")]

    # --- чтение ---------------------------------------------------------
    @property
    def ticket_id(self) -> int:
        return self._id

    @property
    def category(self) -> str:
        return self._category

    @property
    def title(self) -> str:
        return self._title

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def status(self) -> Status:
        return self._status

    @property
    def priority(self) -> Priority:
        return self._priority

    @property
    def deadline(self) -> datetime:
        return self._deadline

    @property
    def assignee(self) -> Optional[str]:
        return self._assignee

    def history(self) -> tuple:
        """Копия истории: внешний код не может её испортить."""
        return tuple(self._history)

    @property
    def finished_at(self) -> Optional[datetime]:
        """Момент последнего перехода в «решена/закрыта» (None, если открыта)."""
        finished: Optional[datetime] = None
        for change in self._history:
            if change.status in OPEN_STATUSES:
                finished = None  # заявку открыли заново
            elif finished is None:
                finished = change.at
        return finished

    # --- изменение ------------------------------------------------------
    def set_priority(self, priority: Priority, deadline: datetime) -> None:
        if deadline < self._created_at:
            raise ValidationError("Срок SLA не может быть раньше создания")
        self._priority = Priority(priority)
        self._deadline = deadline

    def assign(self, agent: str) -> None:
        if not agent or not agent.strip():
            raise ValidationError("Не указан исполнитель")
        self._assignee = agent.strip()

    def change_status(self, new_status: Status, when: datetime, note: str = "") -> None:
        if new_status not in TRANSITIONS[self._status]:
            raise InvalidTransition(
                f"{self._status.value} → {new_status.value} недопустим"
            )
        if when < self._history[-1].at:
            raise ValidationError("Время изменения раньше предыдущей записи")
        self._status = new_status
        self._history.append(StatusChange(new_status, when, note))

    def snapshot(self) -> TicketView:
        return TicketView(
            ticket_id=self._id,
            student=self._student,
            category=self._category,
            title=self._title,
            priority=self._priority,
            status=self._status,
            created_at=self._created_at,
            deadline=self._deadline,
            assignee=self._assignee,
            finished_at=self.finished_at,
        )
