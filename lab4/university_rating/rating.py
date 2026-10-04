"""Итоговая запись студента и сортировка рейтинга."""

from .calculations import calculate_average, calculate_median, determine_status
from .validation import validate_scores, validate_student


def build_student_result(student):
    """Формирует новую итоговую запись одного студента."""
    validate_student(student)
    scores = validate_scores(student["scores"])
    average = calculate_average(scores)
    return {
        "id": student["id"],
        "name": student["name"],
        "average": average,
        "median": calculate_median(scores),
        "status": determine_status(average),
    }


def _sort_key(item):
    average = item["average"]
    return average is not None, average or 0


def build_rating(students):
    """Возвращает рейтинг, не изменяя исходные записи."""
    results = [build_student_result(item) for item in students]
    return sorted(results, key=_sort_key, reverse=True)
