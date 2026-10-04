"""Автоматические тесты (unittest) для варианта 5."""

import unittest

from scholarship import (
    AcademicPolicy,
    ScholarshipApplicant,
    ScholarshipDecision,
    ScholarshipPolicy,
    SocialAcademicPolicy,
    SocialCategory,
)


def make(policy=None, category=SocialCategory.NONE, scores=()):
    applicant = ScholarshipApplicant(
        "Amina", category, policy or AcademicPolicy()
    )
    for score in scores:
        applicant.add_score(score)
    return applicant


class ApplicantTests(unittest.TestCase):
    def test_average_and_scores_snapshot(self):
        applicant = make(scores=(80, 90))
        self.assertEqual(applicant.scores, (80.0, 90.0))
        self.assertEqual(applicant.average, 85)

    def test_average_is_none_without_scores(self):
        self.assertIsNone(make().average)

    def test_scores_snapshot_cannot_change_state(self):
        applicant = make(scores=(70,))
        self.assertIsInstance(applicant.scores, tuple)
        with self.assertRaises(AttributeError):
            applicant.scores = ()
        self.assertEqual(applicant.scores, (70.0,))

    def test_boundary_scores_accepted(self):
        applicant = make(scores=(0, 100))
        self.assertEqual(applicant.average, 50)

    def test_invalid_score_value_keeps_state(self):
        applicant = make(scores=(80,))
        for bad in (-1, 100.5, 101):
            with self.assertRaises(ValueError):
                applicant.add_score(bad)
        self.assertEqual(applicant.scores, (80.0,))

    def test_invalid_score_type_keeps_state(self):
        applicant = make()
        for bad in (True, "90", None):
            with self.assertRaises(TypeError):
                applicant.add_score(bad)
        self.assertEqual(applicant.scores, ())

    def test_constructor_validation(self):
        policy = AcademicPolicy()
        with self.assertRaises(ValueError):
            ScholarshipApplicant("  ", SocialCategory.NONE, policy)
        with self.assertRaises(TypeError):
            ScholarshipApplicant("A", "сирота", policy)
        with self.assertRaises(TypeError):
            ScholarshipApplicant("A", SocialCategory.NONE, object())

    def test_name_is_stripped(self):
        applicant = ScholarshipApplicant(
            "  Amina ", SocialCategory.NONE, AcademicPolicy()
        )
        self.assertEqual(applicant.name, "Amina")

    def test_change_policy_rejects_wrong_type(self):
        applicant = make(scores=(95,))
        with self.assertRaises(TypeError):
            applicant.change_policy("academic")
        self.assertEqual(applicant.amount, 60000)


class AcademicPolicyTests(unittest.TestCase):
    def test_tier_boundaries(self):
        cases = {89.99: 45000, 90: 60000, 75: 45000, 74.9: 30000,
                 60: 30000, 59.99: 0}
        for average, expected in cases.items():
            with self.subTest(average=average):
                self.assertEqual(
                    make(scores=(average,)).amount, expected
                )

    def test_no_scores_means_zero_with_explanation(self):
        applicant = make()
        self.assertEqual(applicant.amount, 0)
        self.assertIn("Нет оценок", applicant.explanation)

    def test_category_is_ignored(self):
        plain = make(category=SocialCategory.NONE, scores=(80,))
        orphan = make(category=SocialCategory.ORPHAN, scores=(80,))
        self.assertEqual(plain.amount, orphan.amount)

    def test_invalid_tiers_rejected(self):
        bad_tiers = [
            (),
            ((60, 30000), (90, 60000)),      # пороги растут
            ((90, 10000), (60, 30000)),      # сумма растёт при снижении порога
            ((101, 100),),                   # порог вне 0..100
            ((90, -5),),                     # отрицательная сумма
        ]
        for tiers in bad_tiers:
            with self.subTest(tiers=tiers):
                with self.assertRaises((ValueError, TypeError)):
                    AcademicPolicy(tiers)

    def test_tiers_property_is_immutable_snapshot(self):
        self.assertIsInstance(AcademicPolicy().tiers, tuple)


class SocialAcademicPolicyTests(unittest.TestCase):
    def test_base_only(self):
        applicant = make(SocialAcademicPolicy(), scores=(60,))
        self.assertEqual(applicant.amount, 20000)

    def test_supplement_added(self):
        applicant = make(SocialAcademicPolicy(), SocialCategory.ORPHAN,
                         scores=(60,))
        self.assertEqual(applicant.amount, 45000)

    def test_excellence_bonus_and_explanation(self):
        applicant = make(SocialAcademicPolicy(), SocialCategory.LOW_INCOME,
                         scores=(90,))
        self.assertEqual(applicant.amount, 20000 + 15000 + 10000)
        self.assertIn("бонус за успеваемость", applicant.explanation)
        self.assertIn("малообеспеченная семья", applicant.explanation)

    def test_below_admission_gets_nothing_even_with_category(self):
        applicant = make(SocialAcademicPolicy(), SocialCategory.ORPHAN,
                         scores=(49.9,))
        self.assertEqual(applicant.amount, 0)

    def test_admission_boundary_inclusive(self):
        self.assertEqual(
            make(SocialAcademicPolicy(), scores=(50,)).amount, 20000
        )

    def test_invalid_configuration_rejected(self):
        with self.assertRaises(ValueError):
            SocialAcademicPolicy(min_average=80, excellence_average=70)
        with self.assertRaises(ValueError):
            SocialAcademicPolicy(base=-1)
        with self.assertRaises(TypeError):
            SocialAcademicPolicy(supplements=(("сирота", 100),))


class InterchangeablePoliciesTests(unittest.TestCase):
    def test_policy_swap_changes_result_without_changing_scores(self):
        applicant = make(category=SocialCategory.ORPHAN, scores=(65,))
        self.assertEqual(applicant.amount, 30000)
        applicant.change_policy(SocialAcademicPolicy())
        self.assertEqual(applicant.amount, 45000)
        self.assertEqual(applicant.scores, (65.0,))

    def test_custom_policy_works_through_interface(self):
        class FixedPolicy(ScholarshipPolicy):
            def decide(self, average, category):
                return ScholarshipDecision(1000, "фиксированная выплата")

        applicant = make(FixedPolicy())
        self.assertEqual(applicant.amount, 1000)

    def test_abstract_policy_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            ScholarshipPolicy()

    def test_query_does_not_mutate(self):
        applicant = make(scores=(70, 80))
        before = applicant.scores
        applicant.amount, applicant.explanation, applicant.average
        self.assertEqual(applicant.scores, before)


if __name__ == "__main__":
    unittest.main()
