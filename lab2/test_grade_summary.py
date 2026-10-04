"""Проверки build_grade_summary: пустой ввод, границы, ошибки, трассировка."""

import copy
import unittest

from grade_summary import build_grade_summary, grade_letter


def rec(score, name="S"):
    return {"student": name, "course": "PP 2205", "score": score}


LECTURE_DATA = [rec(88, "Amina"), rec(47, "Dias"),
                rec(93, "Mira"), rec(108, "Arman")]


class EmptyAndLectureTests(unittest.TestCase):
    def test_empty_list(self):
        summary = build_grade_summary([])
        self.assertEqual(summary["valid_count"], 0)
        self.assertIsNone(summary["average"])
        self.assertIsNone(summary["best"])
        self.assertEqual(summary["passed_count"], 0)
        self.assertEqual(summary["errors"], [])
        self.assertEqual(summary["grade_counts"],
                         {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0})

    def test_lecture_example(self):
        summary = build_grade_summary(LECTURE_DATA)
        self.assertEqual(summary["valid_count"], 3)
        self.assertEqual(round(summary["average"], 2), 76.0)
        self.assertEqual(summary["passed_count"], 2)
        self.assertEqual(summary["best"]["student"], "Mira")
        self.assertEqual(len(summary["errors"]), 1)
        self.assertEqual(summary["errors"][0]["row"], 4)

    def test_lecture_example_grade_counts(self):
        counts = build_grade_summary(LECTURE_DATA)["grade_counts"]
        self.assertEqual(counts, {"A": 1, "B": 1, "C": 0, "D": 0, "F": 1})


class BoundaryTests(unittest.TestCase):
    def test_letter_boundaries(self):
        cases = [
            (0, "F"), (49.99, "F"), (50, "D"), (59.99, "D"),
            (60, "C"), (74.99, "C"), (75, "B"), (89.99, "B"),
            (90, "A"), (100, "A"),
        ]
        for score, letter in cases:
            with self.subTest(score=score):
                self.assertEqual(grade_letter(score), letter)

    def test_edge_scores_are_valid(self):
        summary = build_grade_summary([rec(0), rec(100)])
        self.assertEqual(summary["valid_count"], 2)
        self.assertEqual(summary["errors"], [])
        self.assertEqual(summary["grade_counts"]["F"], 1)
        self.assertEqual(summary["grade_counts"]["A"], 1)

    def test_passing_boundary(self):
        summary = build_grade_summary([rec(49.99), rec(50)])
        self.assertEqual(summary["passed_count"], 1)

    def test_out_of_range_scores_are_errors(self):
        summary = build_grade_summary([rec(-0.01), rec(100.01)])
        self.assertEqual(summary["valid_count"], 0)
        self.assertEqual(len(summary["errors"]), 2)
        self.assertIsNone(summary["average"])

    def test_wrong_types_are_errors(self):
        bad = [rec("88"), rec(True), rec(None), rec(float("nan")),
               {"student": "NoScore"}, "not a dict", None]
        summary = build_grade_summary(bad)
        self.assertEqual(summary["valid_count"], 0)
        self.assertEqual([e["row"] for e in summary["errors"]],
                         [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(sum(summary["grade_counts"].values()), 0)

    def test_equal_best_keeps_first(self):
        summary = build_grade_summary([rec(93, "First"), rec(93, "Second")])
        self.assertEqual(summary["best"]["student"], "First")


class InvariantAndTraceTests(unittest.TestCase):
    def test_source_is_not_changed(self):
        records = copy.deepcopy(LECTURE_DATA)
        build_grade_summary(records)
        self.assertEqual(records, LECTURE_DATA)

    def test_counts_invariant_on_mixed_data(self):
        data = [rec(s) for s in (0, 49.99, 50, 60, 75, 90, 100, 101, "x")]
        summary = build_grade_summary(data)
        counts = summary["grade_counts"]
        self.assertEqual(sum(counts.values()), summary["valid_count"])
        self.assertEqual(summary["valid_count"] + len(summary["errors"]),
                         len(data))
        self.assertEqual(summary["passed_count"],
                         counts["A"] + counts["B"] + counts["C"] + counts["D"])

    def test_trace_of_three_records(self):
        """Состояние после k итераций совпадает с таблицей трассировки."""
        records = [rec(88, "Amina"), rec(47, "Dias"), rec(108, "Arman")]
        expected = [
            # k: valid, average, passed, best, counts (A,B,C,D,F), errors
            (0, 0, None, 0, None, (0, 0, 0, 0, 0), 0),
            (1, 1, 88.0, 1, "Amina", (0, 1, 0, 0, 0), 0),
            (2, 2, 67.5, 1, "Amina", (0, 1, 0, 0, 1), 0),
            (3, 2, 67.5, 1, "Amina", (0, 1, 0, 0, 1), 1),
        ]
        for k, valid, average, passed, best, counts, errors in expected:
            with self.subTest(k=k):
                summary = build_grade_summary(records[:k])
                self.assertEqual(summary["valid_count"], valid)
                self.assertEqual(summary["average"], average)
                self.assertEqual(summary["passed_count"], passed)
                name = summary["best"]["student"] if summary["best"] else None
                self.assertEqual(name, best)
                self.assertEqual(tuple(summary["grade_counts"].values()),
                                 counts)
                self.assertEqual(len(summary["errors"]), errors)


if __name__ == "__main__":
    unittest.main()
