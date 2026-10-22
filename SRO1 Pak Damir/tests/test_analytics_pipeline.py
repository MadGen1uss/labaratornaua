"""Тесты чистых функций и функционального конвейера (лекции 7, 8)."""
import types
import unittest
from datetime import datetime, timedelta

from helpdesk import analytics, pipeline
from helpdesk.models import Priority, Status, TRANSITIONS, TicketView

T0 = datetime(2026, 10, 20, 9, 0)


def view(ticket_id=1, priority=Priority.NORMAL, status=Status.NEW,
         deadline_h=24, finished_h=None, category="Оценки", assignee=None):
    return TicketView(
        ticket_id=ticket_id, student="Студент", category=category, title="Тема",
        priority=priority, status=status, created_at=T0,
        deadline=T0 + timedelta(hours=deadline_h), assignee=assignee,
        finished_at=None if finished_h is None else T0 + timedelta(hours=finished_h),
    )


class OverdueTests(unittest.TestCase):
    def test_open_ticket_before_deadline_is_ok(self):
        self.assertFalse(analytics.is_overdue(view(), T0 + timedelta(hours=23)))

    def test_open_ticket_after_deadline_is_overdue(self):
        self.assertTrue(analytics.is_overdue(view(), T0 + timedelta(hours=25)))

    def test_boundary_exactly_at_deadline_is_not_overdue(self):
        self.assertFalse(analytics.is_overdue(view(), T0 + timedelta(hours=24)))

    def test_finished_in_time_stays_ok_forever(self):
        v = view(status=Status.RESOLVED, finished_h=10)
        self.assertFalse(analytics.is_overdue(v, T0 + timedelta(days=30)))

    def test_finished_late_is_overdue(self):
        v = view(status=Status.RESOLVED, finished_h=30)
        self.assertTrue(analytics.is_overdue(v, T0 + timedelta(hours=31)))
        self.assertEqual(analytics.hours_overdue(v, T0 + timedelta(hours=31)), 6.0)

    def test_hours_overdue_never_negative(self):
        self.assertEqual(analytics.hours_overdue(view(), T0), 0.0)


class PureFunctionTests(unittest.TestCase):
    def test_open_queue_orders_by_priority_then_deadline(self):
        views = [
            view(1, Priority.NORMAL, deadline_h=10),
            view(2, Priority.HIGH, deadline_h=30),
            view(3, Priority.HIGH, deadline_h=5),
            view(4, Priority.CRITICAL, status=Status.CLOSED, finished_h=1),
        ]
        ids = [v.ticket_id for v in analytics.open_queue(views)]
        self.assertEqual(ids, [3, 2, 1])  # закрытая (4) не попала в очередь

    def test_functions_do_not_mutate_input(self):
        views = [view(2, Priority.LOW), view(1, Priority.HIGH)]
        before = list(views)
        analytics.open_queue(views)
        analytics.overdue_views(views, T0 + timedelta(days=9))
        pipeline.count_statuses(views)
        self.assertEqual(views, before)

    def test_average_resolution_empty_is_none(self):
        self.assertIsNone(analytics.average_resolution_hours([view()]))

    def test_average_resolution_value(self):
        views = [view(1, status=Status.RESOLVED, finished_h=4),
                 view(2, status=Status.RESOLVED, finished_h=8)]
        self.assertEqual(analytics.average_resolution_hours(views), 6.0)

    def test_sla_compliance(self):
        now = T0 + timedelta(hours=30)
        views = [view(1), view(2, deadline_h=48)]
        self.assertEqual(analytics.sla_compliance(views, now), 50.0)
        self.assertEqual(analytics.sla_compliance([], now), 100.0)

    def test_reachable_recursive(self):
        self.assertTrue(analytics.reachable(Status.NEW, Status.CLOSED, TRANSITIONS))
        self.assertTrue(analytics.reachable(Status.WAITING, Status.RESOLVED, TRANSITIONS))
        self.assertFalse(analytics.reachable(Status.CLOSED, Status.NEW, TRANSITIONS))
        self.assertFalse(analytics.reachable(Status.RESOLVED, Status.NEW, TRANSITIONS))

    def test_reachable_survives_cycles(self):
        graph = {Status.NEW: frozenset({Status.WAITING}),
                 Status.WAITING: frozenset({Status.NEW}),
                 Status.CLOSED: frozenset()}
        self.assertFalse(analytics.reachable(Status.NEW, Status.CLOSED, graph))


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.views = [
            view(1, Priority.NORMAL, deadline_h=10, category="Оценки"),
            view(2, Priority.HIGH, deadline_h=20, category="Стипендия", assignee="А"),
            view(3, Priority.CRITICAL, deadline_h=5, category="Стипендия"),
            view(4, Priority.LOW, status=Status.CLOSED, finished_h=2),
        ]

    def test_iter_queue_is_lazy_generator(self):
        gen = pipeline.iter_queue(self.views)
        self.assertIsInstance(gen, types.GeneratorType)
        self.assertEqual(next(gen).ticket_id, 3)
        self.assertEqual(next(gen).ticket_id, 2)

    def test_iter_queue_skips_finished(self):
        self.assertEqual([v.ticket_id for v in pipeline.iter_queue(self.views)], [3, 2, 1])

    def test_closure_predicates(self):
        grants = pipeline.category_is("Стипендия")
        self.assertEqual([v.ticket_id for v in filter(grants, self.views)], [2, 3])
        urgent = pipeline.priority_at_least(Priority.HIGH)
        self.assertEqual([v.ticket_id for v in filter(urgent, self.views)], [2, 3])
        both = pipeline.all_of(grants, pipeline.assigned_to("А"))
        self.assertEqual([v.ticket_id for v in filter(both, self.views)], [2])

    def test_count_statuses_sums_to_total(self):
        counts = pipeline.count_statuses(self.views)
        self.assertEqual(sum(counts.values()), len(self.views))
        self.assertEqual(counts[Status.CLOSED], 1)

    def test_count_priorities_has_all_keys(self):
        counts = pipeline.count_priorities([])
        self.assertEqual(set(counts), set(Priority))

    def test_queue_lines_respects_limit(self):
        now = T0 + timedelta(hours=6)
        self.assertEqual(len(pipeline.queue_lines(self.views, now, limit=2)), 2)
        self.assertEqual(len(pipeline.queue_lines(self.views, now)), 3)

    def test_overdue_marker_in_line(self):
        now = T0 + timedelta(hours=6)
        first = pipeline.queue_lines(self.views, now, limit=1)[0]
        self.assertIn("!", first)  # заявка №3: срок 5 ч, прошло 6 ч

    def test_total_overdue_hours(self):
        now = T0 + timedelta(hours=12)
        self.assertEqual(pipeline.total_overdue_hours(self.views, now), 9.0)  # 7 + 2

    def test_take_more_than_available(self):
        self.assertEqual(pipeline.take(10, iter([1, 2])), (1, 2))


if __name__ == "__main__":
    unittest.main()
