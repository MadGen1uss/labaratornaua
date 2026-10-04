"""Преобразование результатов в текст (без печати)."""


def format_average(value):
    """Форматирует средний балл; None выводится как тире."""
    return "—" if value is None else f"{value:.2f}"


def format_median(value):
    """Форматирует медиану; None выводится как тире."""
    return "—" if value is None else f"{value:.2f}"


def format_rating(rows):
    """Строит текст рейтинга по средним баллам."""
    lines = ["Рейтинг группы"]
    for position, row in enumerate(rows, start=1):
        average = format_average(row["average"])
        lines.append(
            f"{position}. {row['name']}: {average} — {row['status']}"
        )
    return "\n".join(lines)


def format_median_report(rows):
    """Строит текст с медианами оценок студентов (индивидуальное задание)."""
    lines = ["Медианы оценок"]
    for row in rows:
        lines.append(f"{row['name']}: {format_median(row['median'])}")
    return "\n".join(lines)
