"""Тесты моделей и политик (лекции 5, 6)."""
import unittest
from datetime import datetime, timedelta

from helpdesk.models import (CATEGORIES, InvalidTransition, Priority, Status,
                             Ticket, ValidationError, raise_priority)
from helpdesk.policies import (DefaultPriority, ExamPeriodPriority,
                               PriorityPolicy)

T0 = datetime(2026, 10, 20, 9, 0)


def make_ticket(category="Оценки", title="Неверный балл"):
    return Ticket(1, "Алиев Т.", category, title, T0)


class TicketTests(unittest.TestCase):
    def test_new_ticket_has_new_status_and_one_history_entry(self):
        ticket = make_ticket()
        self.assertIs(ticket.status, Status.NEW)
        self.assertEqual(len(ticket.history()), 1)

    def test_empty_title_rejected(self):
        with self.assertRaises(ValidationError):
            make_ticket(title="   ")

    def test_unknown_category_rejected(self):
        with self.assertRaises(ValidationError):
            make_ticket(category="Космос")

    def test_valid_transition_is_recorded(self):
        ticket = make_ticket()
        ticket.change_status(Status.IN_PROGRESS, T0 + timedelta(hours=1), "взяли")
        self.assertIs(ticket.status, Status.IN_PROGRESS)
        self.assertEqual(ticket.history()[-1].note, "взяли")

    def test_invalid_transition_rejected(self):
        ticket = make_ticket()
        with self.assertRaises(InvalidTransition):
            ticket.change_status(Status.RESOLVED, T0 + timedelta(hours=1))

    def test_closed_is_terminal(self):
        ticket = make_ticket()
        ticket.change_status(Status.CLOSED, T0 + timedelta(hours=1))
        for status in Status:
            with self.assertRaises(InvalidTransition):
                ticket.change_status(status, T0 + timedelta(hours=2))

    def test_time_must_not_go_backwards(self):
        ticket = make_ticket()
        with self.assertRaises(ValidationError):
            ticket.change_status(Status.IN_PROGRESS, T0 - timedelta(minutes=1))

    def test_history_is_a_copy(self):
        ticket = make_ticket()
        history = ticket.history()
        self.assertIsInstance(history, tuple)
        ticket.change_status(Status.IN_PROGRESS, T0 + timedelta(hours=1))
        self.assertEqual(len(history), 1)  # старая копия не изменилась

    def test_finished_at_and_reopen(self):
        ticket = make_ticket()
        ticket.change_status(Status.IN_PROGRESS, T0 + timedelta(hours=1))
        self.assertIsNone(ticket.finished_at)
        ticket.change_status(Status.RESOLVED, T0 + timedelta(hours=5))
        ticket.change_status(Status.CLOSED, T0 + timedelta(hours=9))
        self.assertEqual(ticket.finished_at, T0 + timedelta(hours=5))

        again = make_ticket()
        again.change_status(Status.IN_PROGRESS, T0 + timedelta(hours=1))
        again.change_status(Status.RESOLVED, T0 + timedelta(hours=2))
        again.change_status(Status.IN_PROGRESS, T0 + timedelta(hours=3))  # переоткрыта
        self.assertIsNone(again.finished_at)

    def test_snapshot_is_immutable(self):
        view = make_ticket().snapshot()
        with self.assertRaises(Exception):
            view.title = "другое"


class RaisePriorityTests(unittest.TestCase):
    def test_one_step(self):
        self.assertIs(raise_priority(Priority.LOW), Priority.NORMAL)

    def test_ceiling_is_critical(self):
        self.assertIs(raise_priority(Priority.CRITICAL), Priority.CRITICAL)
        self.assertIs(raise_priority(Priority.HIGH, 10), Priority.CRITICAL)

    def test_zero_steps_unchanged(self):
        self.assertIs(raise_priority(Priority.NORMAL, 0), Priority.NORMAL)


class PolicyTests(unittest.TestCase):
    def test_default_by_category(self):
        policy = DefaultPriority()
        self.assertIs(policy.priority("Стипендия", "вопрос"), Priority.HIGH)
        self.assertIs(policy.priority("Документы", "справка"), Priority.LOW)

    def test_urgent_keyword_boosts(self):
        policy = DefaultPriority()
        self.assertIs(policy.priority("Документы", "СРОЧНО нужна справка"), Priority.NORMAL)

    def test_exam_policy_boosts_only_exam_categories(self):
        policy = ExamPeriodPriority()
        self.assertIs(policy.priority("Оценки", "балл"), Priority.HIGH)
        self.assertIs(policy.priority("Документы", "справка"), Priority.LOW)

    def test_exam_policy_halves_sla(self):
        base, exam = DefaultPriority(), ExamPeriodPriority()
        self.assertEqual(exam.sla_hours(Priority.NORMAL), base.sla_hours(Priority.NORMAL) // 2)
        self.assertGreaterEqual(exam.sla_hours(Priority.CRITICAL), 1)

    def test_policies_share_interface(self):
        for policy in (DefaultPriority(), ExamPeriodPriority()):
            self.assertIsInstance(policy, PriorityPolicy)
            for category in CATEGORIES:
                self.assertIsInstance(policy.priority(category, "тема"), Priority)

    def test_interface_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            PriorityPolicy()


if __name__ == "__main__":
    unittest.main()
