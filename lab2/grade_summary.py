"""Сводка успеваемости (лекция № 2, императивная парадигма).

Базовая функция из лекции расширена подсчётом оценок по диапазонам A-F.
Расчёт отделён от вывода: модуль ничего не печатает.
"""

PASSING_SCORE = 50


def grade_letter(score):
    """Возвращает буквенную оценку для корректного балла 0..100.

    Ветви проверяются сверху вниз от более высокого порога, поэтому
    диапазоны не пересекаются и не оставляют «дыр» (например, 89.5 -> B).
    """
    if score >= 90:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= PASSING_SCORE:
        return "D"
    else:
        return "F"


def _is_valid_score(score):
    """Балл корректен: число (не bool) в диапазоне 0..100 включительно."""
    return (
        not isinstance(score, bool)
        and isinstance(score, (int, float))
        and 0 <= score <= 100
    )


def build_grade_summary(records):
    """Строит сводку по списку записей {"score": ...}.

    Возвращает словарь: valid_count, average, passed_count, best, errors,
    grade_counts (количество оценок A, B, C, D, F).

    Инвариант цикла: после обработки k записей
      1) valid_count + len(errors) == k;
      2) total - сумма баллов корректных записей среди первых k;
      3) passed_count - число корректных записей с баллом >= 50;
      4) best - первая запись с максимальным баллом среди корректных
         (None, если корректных нет);
      5) сумма grade_counts == valid_count, а количество в каждом
         диапазоне равно числу корректных записей этого диапазона;
      6) passed_count == A + B + C + D.
    Завершение: цикл for делает ровно один шаг на каждую из n записей.
    """
    total = 0
    passed_count = 0
    best = None
    valid_count = 0
    errors = []
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}

    for index, record in enumerate(records, start=1):
        score = record.get("score") if isinstance(record, dict) else None
        if not _is_valid_score(score):
            errors.append({"row": index, "record": record})
            continue
        valid_count += 1
        total += score
        if score >= PASSING_SCORE:
            passed_count += 1
        grade_counts[grade_letter(score)] += 1
        if best is None or score > best["score"]:
            best = record

    average = total / valid_count if valid_count else None
    return {
        "valid_count": valid_count,
        "average": average,
        "passed_count": passed_count,
        "best": best,
        "errors": errors,
        "grade_counts": grade_counts,
    }
