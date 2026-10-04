"""Автоматические проверки публичных функций пакета university_rating."""

import importlib
import unittest

from university_rating import build_rating, build_student_result
from university_rating.calculations import (
    calculate_average,
    calculate_median,
    determine_status,
)
from university_rating.report import (
    format_median_report,
    format_rating,
)
from university_rating.validation import validate_scores, validate_student


def student(student_id, name, scores):
    return {"id": student_id, "name": name, "scores": scores}


class RatingTests(unittest.TestCase):
    def test_empty_average(self):
        self.assertIsNone(calculate_average([]))

    def test_status_boundary(self):
        self.assertEqual(determine_status(49.99), "не допущен")
        self.assertEqual(determine_status(50), "допущен")

    def test_invalid_score(self):
        with self.assertRaises(ValueError):
            validate_scores([80, 101])

    def test_source_is_not_changed(self):
        students = [student(1, "Test", [70, 80])]
        before = [student(1, "Test", [70, 80])]
        build_rating(students)
        self.assertEqual(students, before)


class BoundaryCaseTests(unittest.TestCase):
    def test_empty_students_list(self):
        self.assertEqual(build_rating([]), [])

    def test_empty_scores(self):
        result = build_student_result(student(1, "A", []))
        self.assertIsNone(result["average"])
        self.assertEqual(result["status"], "нет данных")

    def test_edge_scores_are_valid(self):
        self.assertEqual(validate_scores([0, 100]), [0.0, 100.0])

    def test_negative_score(self):
        with self.assertRaises(ValueError):
            validate_scores([-0.1])

    def test_wrong_score_types(self):
        for bad in ("80", True, None):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    validate_scores([bad])

    def test_scores_container_type(self):
        with self.assertRaises(TypeError):
            validate_scores("80")

    def test_missing_field_is_named(self):
        with self.assertRaises(ValueError) as context:
            validate_student({"id": 1, "scores": []})
        self.assertIn("name", str(context.exception))

    def test_record_must_be_dict(self):
        with self.assertRaises(TypeError):
            validate_student([1, "A", []])

    def test_validate_scores_returns_copy(self):
        original = [70, 80]
        checked = validate_scores(original)
        checked.append(1.0)
        self.assertEqual(original, [70, 80])

    def test_rating_order_and_none_last(self):
        rating = build_rating([
            student(1, "NoData", []),
            student(2, "Low", [40]),
            student(3, "High", [90]),
        ])
        self.assertEqual([r["name"] for r in rating],
                         ["High", "Low", "NoData"])

    def test_equal_averages_keep_input_order(self):
        students = [student(1, "First", [60]), student(2, "Second", [60]),
                    student(3, "Third", [60])]
        for _ in range(3):
            names = [r["name"] for r in build_rating(students)]
            self.assertEqual(names, ["First", "Second", "Third"])

    def test_report_text(self):
        rating = build_rating([student(1, "Amina", [88, 92, 79]),
                               student(2, "Mira", [])])
        self.assertEqual(
            format_rating(rating),
            "Рейтинг группы\n1. Amina: 86.33 — допущен\n"
            "2. Mira: — — нет данных",
        )

    def test_modules_import_without_cycles(self):
        for name in ("validation", "calculations", "rating", "report",
                     "main"):
            with self.subTest(module=name):
                importlib.import_module(f"university_rating.{name}")


class MedianTests(unittest.TestCase):
    """Индивидуальное задание, вариант 5: медиана оценок."""

    def test_median_odd_count(self):
        self.assertEqual(calculate_median([79, 88, 92]), 88)

    def test_median_even_count(self):
        self.assertEqual(calculate_median([40, 60, 70, 100]), 65)

    def test_median_is_independent_of_input_order(self):
        self.assertEqual(calculate_median([92, 79, 88]), 88)

    def test_median_of_empty_is_none(self):
        self.assertIsNone(calculate_median([]))

    def test_median_differs_from_average(self):
        result = build_student_result(student(1, "A", [0, 100, 100]))
        self.assertEqual(result["median"], 100)
        self.assertAlmostEqual(result["average"], 66.6667, places=3)

    def test_median_in_result_and_empty_scores(self):
        self.assertIsNone(build_student_result(student(1, "A", []))["median"])
        self.assertEqual(
            build_student_result(student(1, "A", [88, 92, 79]))["median"], 88
        )

    def test_median_does_not_change_rating_order(self):
        # у Low выше медиана, но ниже среднее: порядок по среднему
        rating = build_rating([student(1, "Low", [0, 100, 100]),
                               student(2, "High", [90, 90, 90])])
        self.assertEqual([r["name"] for r in rating], ["High", "Low"])

    def test_median_report_text_and_none(self):
        rating = build_rating([student(1, "Amina", [88, 92, 79]),
                               student(2, "Mira", [])])
        self.assertEqual(format_median_report(rating),
                         "Медианы оценок\nAmina: 88.00\nMira: —")

    def test_median_source_is_not_changed(self):
        students = [student(1, "T", [80, 70, 90])]
        build_rating(students)
        self.assertEqual(students, [student(1, "T", [80, 70, 90])])


if __name__ == "__main__":
    unittest.main()
