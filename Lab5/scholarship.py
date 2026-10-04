"""Объектная модель назначения стипендии (лабораторная работа № 5, вариант 5).

Модуль содержит:
    SocialCategory        - допустимые социальные категории;
    ScholarshipDecision   - неизменяемый результат расчёта (сумма + объяснение);
    ScholarshipPolicy     - абстрактная политика расчёта;
    AcademicPolicy        - политика «только успеваемость»;
    SocialAcademicPolicy  - политика «успеваемость + социальная надбавка»;
    ScholarshipApplicant  - претендент: оценки, категория, текущая политика.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class SocialCategory(Enum):
    """Социальная категория претендента."""

    NONE = "нет"
    LOW_INCOME = "малообеспеченная семья"
    ORPHAN = "сирота"
    LARGE_FAMILY = "многодетная семья"


@dataclass(frozen=True)
class ScholarshipDecision:
    """Результат расчёта: сумма в тенге и текстовое объяснение решения."""

    amount: int
    explanation: str


def _check_money(value, label):
    """Проверяет, что значение - неотрицательное целое (не bool)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label}: ожидается целое число")
    if value < 0:
        raise ValueError(f"{label}: значение не может быть отрицательным")


def _check_average_threshold(value, label):
    """Проверяет, что порог среднего балла лежит в диапазоне 0..100."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label}: ожидается число")
    if not 0 <= value <= 100:
        raise ValueError(f"{label}: порог должен быть от 0 до 100")


class ScholarshipPolicy(ABC):
    """Правило расчёта стипендии.

    Политика не хранит изменяемого состояния о претенденте: она получает
    средний балл и категорию и возвращает решение. Поэтому одну политику
    можно безопасно использовать для многих претендентов.
    """

    @abstractmethod
    def decide(self, average, category):
        """Возвращает ScholarshipDecision для среднего балла и категории.

        average - float или None (если оценок нет).
        category - элемент SocialCategory.
        """


class AcademicPolicy(ScholarshipPolicy):
    """Стипендия зависит только от среднего балла (ступенчатая шкала).

    Инварианты: пороги идут по убыванию, суммы не убывают с ростом порога,
    все пороги в диапазоне 0..100, суммы - неотрицательные целые.
    """

    DEFAULT_TIERS = ((90, 60000), (75, 45000), (60, 30000))

    def __init__(self, tiers=DEFAULT_TIERS):
        tiers = tuple(tuple(pair) for pair in tiers)
        if not tiers:
            raise ValueError("Шкала не должна быть пустой")
        previous_threshold = None
        previous_amount = None
        for pair in tiers:
            if len(pair) != 2:
                raise ValueError("Ступень шкалы - пара (порог, сумма)")
            threshold, amount = pair
            _check_average_threshold(threshold, "порог")
            _check_money(amount, "сумма")
            if previous_threshold is not None:
                if threshold >= previous_threshold:
                    raise ValueError("Пороги должны строго убывать")
                if amount > previous_amount:
                    raise ValueError("Сумма не может расти при снижении порога")
            previous_threshold, previous_amount = threshold, amount
        self._tiers = tiers

    @property
    def tiers(self):
        """Неизменяемая копия шкалы."""
        return self._tiers

    def decide(self, average, category):
        """Подбирает ступень по среднему баллу; категория не учитывается."""
        if average is None:
            return ScholarshipDecision(0, "Нет оценок: стипендия не назначена")
        for threshold, amount in self._tiers:
            if average >= threshold:
                return ScholarshipDecision(
                    amount,
                    f"Средний балл {average:.2f} >= {threshold}: "
                    f"академическая стипендия {amount} тг",
                )
        lowest = self._tiers[-1][0]
        return ScholarshipDecision(
            0, f"Средний балл {average:.2f} < {lowest}: стипендия не назначена"
        )


class SocialAcademicPolicy(ScholarshipPolicy):
    """Базовая выплата за допуск + надбавка за категорию + бонус за успеваемость.

    Инварианты: все суммы - неотрицательные целые, пороги в диапазоне 0..100.
    Надбавки заданы неизменяемым набором пар (категория, сумма).
    """

    DEFAULT_SUPPLEMENTS = (
        (SocialCategory.NONE, 0),
        (SocialCategory.LOW_INCOME, 15000),
        (SocialCategory.LARGE_FAMILY, 10000),
        (SocialCategory.ORPHAN, 25000),
    )

    def __init__(self, min_average=50, base=20000, excellence_average=85,
                 excellence_bonus=10000, supplements=DEFAULT_SUPPLEMENTS):
        _check_average_threshold(min_average, "min_average")
        _check_average_threshold(excellence_average, "excellence_average")
        if excellence_average < min_average:
            raise ValueError("Порог бонуса не может быть ниже порога допуска")
        _check_money(base, "base")
        _check_money(excellence_bonus, "excellence_bonus")
        table = {}
        for category, amount in supplements:
            if not isinstance(category, SocialCategory):
                raise TypeError("Ключ надбавки должен быть SocialCategory")
            _check_money(amount, "надбавка")
            table[category] = amount
        for category in SocialCategory:
            table.setdefault(category, 0)
        self._min_average = min_average
        self._base = base
        self._excellence_average = excellence_average
        self._excellence_bonus = excellence_bonus
        self._supplements = table

    def decide(self, average, category):
        """Считает сумму по частям и перечисляет их в объяснении."""
        if average is None:
            return ScholarshipDecision(0, "Нет оценок: стипендия не назначена")
        if average < self._min_average:
            return ScholarshipDecision(
                0,
                f"Средний балл {average:.2f} < {self._min_average}: "
                "нет допуска, надбавки не выплачиваются",
            )
        parts = [("база", self._base)]
        supplement = self._supplements[category]
        if supplement:
            parts.append((f"надбавка «{category.value}»", supplement))
        if average >= self._excellence_average:
            parts.append(("бонус за успеваемость", self._excellence_bonus))
        total = sum(amount for _, amount in parts)
        details = " + ".join(f"{label} {amount}" for label, amount in parts)
        return ScholarshipDecision(total, f"{details} = {total} тг")


class ScholarshipApplicant:
    """Претендент на стипендию: оценки, категория и текущая политика расчёта.

    Инварианты: имя не пусто; каждый балл - число 0..100 (не bool);
    категория - SocialCategory; политика - ScholarshipPolicy.
    Список оценок скрыт, наружу отдаётся только tuple.
    """

    def __init__(self, name, social_category, policy):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Имя не должно быть пустым")
        if not isinstance(social_category, SocialCategory):
            raise TypeError("Категория должна быть элементом SocialCategory")
        if not isinstance(policy, ScholarshipPolicy):
            raise TypeError("Ожидается объект ScholarshipPolicy")
        self.name = name.strip()
        self._social_category = social_category
        self._policy = policy
        self._scores = []

    def add_score(self, score):
        """Добавляет корректный балл (команда, ничего не возвращает)."""
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise TypeError("Балл должен быть числом")
        if not 0 <= score <= 100:
            raise ValueError("Балл должен быть от 0 до 100")
        self._scores.append(float(score))

    def change_policy(self, policy):
        """Заменяет политику расчёта (команда)."""
        if not isinstance(policy, ScholarshipPolicy):
            raise TypeError("Ожидается объект ScholarshipPolicy")
        self._policy = policy

    @property
    def social_category(self):
        """Социальная категория (только чтение)."""
        return self._social_category

    @property
    def scores(self):
        """Неизменяемый снимок оценок."""
        return tuple(self._scores)

    @property
    def average(self):
        """Средний балл или None, если оценок нет."""
        if not self._scores:
            return None
        return sum(self._scores) / len(self._scores)

    @property
    def decision(self):
        """Решение текущей политики (запрос, состояние не меняется)."""
        return self._policy.decide(self.average, self._social_category)

    @property
    def amount(self):
        """Размер стипендии в тенге."""
        return self.decision.amount

    @property
    def explanation(self):
        """Текстовое объяснение решения."""
        return self.decision.explanation

    def __repr__(self):
        return (
            f"ScholarshipApplicant(name={self.name!r}, "
            f"social_category={self._social_category.name})"
        )
