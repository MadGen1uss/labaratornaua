"""Точка входа: консольное меню службы поддержки студентов.

    python main.py            — интерактивное меню
    python main.py --demo     — готовый демонстрационный сценарий
    python main.py --generate — пересоздать data/tickets.json
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from helpdesk import reports
from helpdesk.data import (REFERENCE_NOW, build_desk, generate_records,
                           load_records, save_records)
from helpdesk.models import CATEGORIES, HelpDeskError, Status, TRANSITIONS
from helpdesk.policies import DefaultPriority, ExamPeriodPriority
from helpdesk.service import HelpDesk

DEFAULT_DATA = Path(__file__).parent / "data" / "tickets.json"

MENU = """
=== Служба поддержки студентов ===
1. Очередь заявок            6. История заявки
2. Нарушения SLA             7. Сменить политику приоритета
3. Статистика                8. Сравнить политики
4. Новая заявка              9. Сравнить парадигмы
5. Сменить статус заявки     0. Выход"""


def _ask_int(read, write, prompt: str) -> int:
    raw = read(prompt).strip()
    if not raw.lstrip("-").isdigit():
        raise HelpDeskError("Нужно ввести число")
    return int(raw)


def run_menu(desk: HelpDesk, records: list, now: datetime,
             read=input, write=print) -> None:
    """Цикл меню. `read` и `write` подменяются в тестах."""

    def show_queue():
        write(reports.queue_text(desk, now))

    def show_violations():
        write(reports.violations_text(desk, now))

    def show_stats():
        write(reports.stats_text(desk, now))

    def new_ticket():
        student = read("Студент (ФИО, группа): ")
        for i, name in enumerate(CATEGORIES, 1):
            write(f"  {i}. {name}")
        index = _ask_int(read, write, "Категория №: ")
        if not 1 <= index <= len(CATEGORIES):
            raise HelpDeskError("Нет такой категории")
        title = read("Тема: ")
        view = desk.register(student, CATEGORIES[index - 1], title, now)
        write(f"Создана заявка #{view.ticket_id}, приоритет P{int(view.priority)}, "
              f"срок до {view.deadline:%d.%m %H:%M}")

    def change_status():
        ticket_id = _ask_int(read, write, "Номер заявки: ")
        current = desk.get(ticket_id).status
        options = sorted(TRANSITIONS[current], key=lambda s: s.value)
        if not options:
            raise HelpDeskError(f"Из статуса «{current.value}» переходов нет")
        for i, status in enumerate(options, 1):
            write(f"  {i}. {status.value}")
        choice = _ask_int(read, write, "Новый статус №: ")
        if not 1 <= choice <= len(options):
            raise HelpDeskError("Нет такого пункта")
        view = desk.change_status(ticket_id, options[choice - 1], now)
        write(f"Заявка #{view.ticket_id}: {view.status.value}")

    def show_history():
        ticket_id = _ask_int(read, write, "Номер заявки: ")
        for change in desk.history(ticket_id):
            write(f"  {change.at:%d.%m %H:%M}  {change.status.value:<18}{change.note}")

    def switch_policy():
        write("  1. Обычный период\n  2. Экзаменационная сессия")
        choice = _ask_int(read, write, "Политика №: ")
        if choice not in (1, 2):
            raise HelpDeskError("Нет такой политики")
        desk.switch_policy(DefaultPriority() if choice == 1 else ExamPeriodPriority())
        write(f"Политика: {desk.policy.name}; сроки пересчитаны.")

    handlers = {
        "1": show_queue, "2": show_violations, "3": show_stats,
        "4": new_ticket, "5": change_status, "6": show_history,
        "7": switch_policy,
        "8": lambda: write(reports.policies_text(records, now)),
        "9": lambda: write(reports.paradigms_text(records, now)),
    }
    while True:
        write(MENU)
        choice = read("Выберите пункт: ").strip()
        if choice == "0":
            write("До свидания!")
            return
        handler = handlers.get(choice)
        if handler is None:
            write("Неизвестный пункт меню.")
            continue
        try:
            handler()
        except HelpDeskError as error:
            write(f"Ошибка: {error}")


def run_demo(desk: HelpDesk, records: list, now: datetime, write=print) -> None:
    write(f"Демонстрация на {len(desk)} заявках, момент отчёта {now:%d.%m.%Y %H:%M}\n")
    write(reports.queue_text(desk, now, 8) + "\n")
    write(reports.violations_text(desk, now) + "\n")
    write(reports.stats_text(desk, now) + "\n")
    write(reports.policies_text(records, now) + "\n")
    write(reports.paradigms_text(records, now) + "\n")
    first = desk.views()[0].ticket_id
    write(f"Попытка недопустимого перехода для заявки #{first}:")
    try:
        desk.change_status(first, Status.NEW, now)
    except HelpDeskError as error:
        write(f"  Ошибка: {error}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    parser.add_argument("--now", default=REFERENCE_NOW.isoformat(),
                        help="момент отчёта (ISO), по умолчанию фиксированный")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args(argv)

    path = Path(args.data)
    if args.generate or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        save_records(path, generate_records())
        print(f"Данные записаны в {path}")
    records = load_records(path)
    now = datetime.fromisoformat(args.now)
    desk = build_desk(records)
    if args.demo:
        run_demo(desk, records, now)
    else:
        run_menu(desk, records, now)


if __name__ == "__main__":
    main()
