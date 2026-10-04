"""Демонстрационный запуск: пример из лекции + количество оценок A-F."""

from grade_summary import build_grade_summary


def main():
    grades = [
        {"student": "Amina", "course": "PP 2205", "score": 88},
        {"student": "Dias", "course": "PP 2205", "score": 47},
        {"student": "Mira", "course": "PP 2205", "score": 93},
        {"student": "Arman", "course": "PP 2205", "score": 108},
    ]
    summary = build_grade_summary(grades)

    print(summary["valid_count"], round(summary["average"], 2))
    print(summary["passed_count"], summary["best"]["student"])
    print(len(summary["errors"]))

    counts = ", ".join(
        f"{letter}={number}" for letter, number in summary["grade_counts"].items()
    )
    print(f"Оценки по диапазонам: {counts}")

    print("\nПустой список:", build_grade_summary([]))


if __name__ == "__main__":
    main()
