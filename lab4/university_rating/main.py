"""Точка входа: демонстрационные данные и запуск приложения."""

from .rating import build_rating
from .report import format_median_report, format_rating


def load_demo_data():
    """Возвращает демонстрационные записи студентов."""
    return [
        {"id": 101, "name": "Amina", "scores": [88, 92, 79]},
        {"id": 102, "name": "Dias", "scores": [45, 52, 48]},
        {"id": 103, "name": "Mira", "scores": []},
    ]


def main():
    """Формирует рейтинг и печатает отчёты."""
    students = load_demo_data()
    rating = build_rating(students)
    print(format_rating(rating))
    print()
    print(format_median_report(rating))


if __name__ == "__main__":
    main()
