"""Политики приоритета и SLA (лекция 6: интерфейс + две реализации + композиция)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from types import MappingProxyType

from .models import Priority, raise_priority

# Часы на решение по каждому приоритету (базовая таблица SLA).
BASE_SLA_HOURS = MappingProxyType(
    {
        Priority.CRITICAL: 4,
        Priority.HIGH: 8,
        Priority.NORMAL: 24,
        Priority.LOW: 72,
    }
)

CATEGORY_PRIORITY = MappingProxyType(
    {
        "Стипендия": Priority.HIGH,
        "Оценки": Priority.NORMAL,
        "Расписание": Priority.NORMAL,
        "Общежитие": Priority.NORMAL,
        "Технические": Priority.NORMAL,
        "Документы": Priority.LOW,
    }
)

URGENT_KEYWORDS = ("срочно", "не могу войти", "блокиров")

# Категории, которые становятся важнее в экзаменационную сессию.
EXAM_CATEGORIES = frozenset({"Оценки", "Расписание", "Технические"})


class PriorityPolicy(ABC):
    """Общий интерфейс: определить приоритет и норматив SLA."""

    name: str = "abstract"

    @abstractmethod
    def priority(self, category: str, title: str) -> Priority:
        """Приоритет заявки по категории и теме."""

    @abstractmethod
    def sla_hours(self, priority: Priority) -> int:
        """Сколько часов отводится на решение."""


class DefaultPriority(PriorityPolicy):
    """Обычный период: приоритет задаёт категория, «срочно» повышает на 1."""

    name = "Обычный период"

    def priority(self, category: str, title: str) -> Priority:
        base = CATEGORY_PRIORITY.get(category, Priority.NORMAL)
        text = title.lower()
        urgent = any(word in text for word in URGENT_KEYWORDS)
        return raise_priority(base, 1) if urgent else base

    def sla_hours(self, priority: Priority) -> int:
        return BASE_SLA_HOURS[priority]


class ExamPeriodPriority(PriorityPolicy):
    """Сессия: обёртка над базовой политикой (композиция).

    Заявки, связанные с экзаменами, получают приоритет на ступень выше,
    а все нормативы SLA сокращаются вдвое.
    """

    name = "Экзаменационная сессия"

    def __init__(self, base: PriorityPolicy | None = None) -> None:
        self._base = base if base is not None else DefaultPriority()

    def priority(self, category: str, title: str) -> Priority:
        result = self._base.priority(category, title)
        if category in EXAM_CATEGORIES:
            return raise_priority(result, 1)
        return result

    def sla_hours(self, priority: Priority) -> int:
        return max(1, self._base.sla_hours(priority) // 2)
