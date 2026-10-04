"""Предметные расчёты: среднее, медиана и статус допуска."""

from statistics import median

PASSING_AVERAGE = 50


def calculate_average(scores):
    """Возвращает среднее или None для пустой последовательности."""
    return sum(scores) / len(scores) if scores else None


def calculate_median(scores):
    """Возвращает медиану или None для пустой последовательности.

    statistics.median на пустых данных выбрасывает StatisticsError,
    поэтому пустой случай обрабатывается явно, как и в calculate_average.
    """
    return median(scores) if scores else None


def determine_status(average):
    """Возвращает статус по среднему баллу."""
    if average is None:
        return "нет данных"
    return "допущен" if average >= PASSING_AVERAGE else "не допущен"
