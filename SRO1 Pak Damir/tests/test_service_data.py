"""Тесты службы, данных, сравнения парадигм и меню (лекции 1, 4, 5)."""
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import main as app
from helpdesk import paradigms, reports
from helpdesk.data import (REFERENCE_NOW, build_desk, generate_records,
                           load_records, save_records)
from helpdesk.models import (InvalidTransition, Priority, Status,
                             TicketNotFound, ValidationError)
from helpdesk.policies import DefaultPriority, ExamPeriodPriority
from helpdesk.service import HelpDesk

T0 = datetime(2026, 10, 20, 9, 0)


class HelpDeskTests(unittest.TestCase):
    def test_register_assigns_sequential_ids(self):
        desk = HelpDesk()
        a = desk.register("А", "Оценки", "тема", T0)
        b = desk.register("Б", "Документы", "справка", T0)
        self.assertEqual((a.ticket_id, b.ticket_id), (1, 2))
        self.assertEqual(len(desk), 2)

    def test_failed_register_does_not_consume_id(self):
        desk = HelpDesk()
        with self.assertRaises(ValidationError):
            desk.register("А", "Оценки", "", T0)
        self.assertEqual(desk.register("А", "Оценки", "тема", T0).ticket_id, 1)

    def test_unknown_ticket(self):
        with self.assertRaises(TicketNotFound):
            HelpDesk().get(42)

    def test_change_status_and_invalid_transition(self):
        desk = HelpDesk()
        tid = desk.register("А", "Оценки", "тема", T0).ticket_id
        view = desk.change_status(tid, Status.IN_PROGRESS, T0 + timedelta(hours=1))
        self.assertIs(view.status, Status.IN_PROGRESS)
        with self.assertRaises(InvalidTransition):
            desk.change_status(tid, Status.NEW, T0 + timedelta(hours=2))

    def test_deadline_follows_policy(self):
        desk = HelpDesk(DefaultPriority())
        view = desk.register("А", "Документы", "справка", T0)
        self.assertEqual(view.deadline, T0 + timedelta(hours=72))

    def test_switch_policy_recalculates(self):
        desk = HelpDesk(DefaultPriority())
        tid = desk.register("А", "Оценки", "балл", T0).ticket_id
        before = desk.get(tid)
        desk.switch_policy(ExamPeriodPriority())
        after = desk.get(tid)
        self.assertLess(after.deadline, before.deadline)
        self.assertLess(after.priority, before.priority)

    def test_views_do_not_expose_internal_state(self):
        desk = HelpDesk()
        desk.register("А", "Оценки", "тема", T0)
        views = desk.views()
        self.assertIsInstance(views, tuple)
        self.assertEqual(len(desk.views()), 1)

    def test_violations_sorted_most_urgent_first(self):
        desk = HelpDesk()
        desk.register("А", "Документы", "справка", T0)       # P4, 72 ч
        desk.register("Б", "Стипендия", "вопрос", T0)        # P2, 8 ч
        late = desk.violations(T0 + timedelta(days=10))
        self.assertEqual([v.ticket_id for v in late], [2, 1])


class DataTests(unittest.TestCase):
    def test_generator_is_reproducible(self):
        self.assertEqual(generate_records(seed=7), generate_records(seed=7))
        self.assertNotEqual(generate_records(seed=7), generate_records(seed=8))

    def test_at_least_twenty_records_and_valid(self):
        records = generate_records()
        self.assertGreaterEqual(len(records), 20)
        self.assertEqual(len(build_desk(records)), len(records))

    def test_shipped_data_file_loads(self):
        path = Path(app.DEFAULT_DATA)
        records = load_records(path)
        self.assertGreaterEqual(len(records), 20)
        self.assertEqual(records, generate_records())  # файл = результат генератора

    def test_json_round_trip(self):
        records = generate_records(10)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.json"
            save_records(path, records)
            self.assertEqual(load_records(path), records)

    def test_no_event_in_the_future(self):
        for rec in generate_records():
            for event in rec["events"]:
                self.assertLessEqual(datetime.fromisoformat(event["at"]), REFERENCE_NOW)


class ComparisonTests(unittest.TestCase):
    def test_three_paradigms_agree(self):
        results = paradigms.compare(generate_records(), REFERENCE_NOW, repeat=3)
        id_sets = {tuple(r["ids"]) for r in results.values()}
        self.assertEqual(len(id_sets), 1)
        self.assertGreater(len(next(iter(id_sets))), 0)

    def test_paradigms_agree_on_other_seeds(self):
        for seed in (1, 2, 3):
            records = generate_records(25, seed=seed)
            results = paradigms.compare(records, REFERENCE_NOW, repeat=1)
            self.assertEqual(len({tuple(r["ids"]) for r in results.values()}), 1)

    def test_exam_policy_is_never_more_lenient(self):
        default, exam = reports.compare_policies(generate_records(), REFERENCE_NOW)
        self.assertGreaterEqual(exam["overdue"], default["overdue"])
        self.assertLessEqual(exam["compliance"], default["compliance"])


class MenuTests(unittest.TestCase):
    def run_menu(self, inputs):
        records = generate_records()
        desk = build_desk(records)
        feed, out = iter(inputs), []
        app.run_menu(desk, records, REFERENCE_NOW, read=lambda _: next(feed),
                     write=out.append)
        return desk, "\n".join(out)

    def test_exit_immediately(self):
        _, output = self.run_menu(["0"])
        self.assertIn("До свидания", output)

    def test_unknown_item_and_queue(self):
        _, output = self.run_menu(["x", "1", "0"])
        self.assertIn("Неизвестный пункт", output)
        self.assertIn("Очередь обработки", output)

    def test_new_ticket_via_menu(self):
        desk, output = self.run_menu(["4", "Тест Т. (ИС-24-1)", "5", "Срочно нужна справка", "0"])
        self.assertIn("Создана заявка #31", output)
        self.assertEqual(desk.get(31).priority, Priority.HIGH)  # «Технические» (NORMAL) + «срочно» → HIGH

    def test_bad_input_is_reported_not_raised(self):
        _, output = self.run_menu(["6", "abc", "6", "999", "0"])
        self.assertIn("Нужно ввести число", output)
        self.assertIn("не найдена", output)


if __name__ == "__main__":
    unittest.main()
