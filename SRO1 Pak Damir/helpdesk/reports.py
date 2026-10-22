"""Текстовые отчёты (лекции 3, 8)."""
from __future__ import annotations

from datetime import datetime
from typing import List

from . import analytics, pipeline
from .data import build_desk
from .models import Priority
from .paradigms import compare
from .policies import DefaultPriority, ExamPeriodPriority
from .service import HelpDesk


def queue_text(desk: HelpDesk, now: datetime, limit: int = 10) -> str:
    lines = pipeline.queue_lines(desk.views(), now, limit)
    if not lines:
        return "Очередь пуста."
    header = f"Очередь обработки (первые {len(lines)}; «!» — SLA нарушен):"
    return "\n".join((header, *lines))


def violations_text(desk: HelpDesk, now: datetime) -> str:
    late = desk.violations(now)
    if not late:
        return "Нарушений SLA нет."
    rows = [
        f"#{v.ticket_id:03d} P{int(v.priority)} {v.status.value:<16} "
        f"просрочка {analytics.hours_overdue(v, now):>6.1f} ч  {v.title}"
        for v in late
    ]
    return "\n".join((f"Нарушения SLA: {len(late)}", *rows))


def stats_text(desk: HelpDesk, now: datetime) -> str:
    views = desk.views()
    statuses = pipeline.count_statuses(views)
    priorities = pipeline.count_priorities(views)
    avg = analytics.average_resolution_hours(views)
    lines = [f"Политика: {desk.policy.name}", f"Всего заявок: {len(views)}", "По статусам:"]
    lines += [f"  {s.value:<18}{n:>3}" for s, n in statuses.items()]
    lines.append("По приоритетам:")
    lines += [f"  P{int(p)} {p.name:<9}{n:>3}" for p, n in priorities.items()]
    lines.append(f"Соблюдение SLA: {analytics.sla_compliance(views, now)} %")
    lines.append("Среднее время решения: "
                 + ("нет данных" if avg is None else f"{avg} ч"))
    overdue = analytics.overdue_views(views, now)
    lines.append(f"Суммарная просрочка: {pipeline.total_overdue_hours(overdue, now)} ч")
    return "\n".join(lines)


def compare_policies(records: List[dict], now: datetime) -> List[dict]:
    """Одни и те же заявки, две политики приоритета."""
    rows = []
    for policy in (DefaultPriority(), ExamPeriodPriority()):
        views = build_desk(records, policy).views()
        late = analytics.overdue_views(views, now)
        rows.append(
            {
                "policy": policy.name,
                "overdue": len(late),
                "compliance": analytics.sla_compliance(views, now),
                "critical": pipeline.count_priorities(views)[Priority.CRITICAL],
                "overdue_hours": pipeline.total_overdue_hours(late, now),
            }
        )
    return rows


def policies_text(records: List[dict], now: datetime) -> str:
    rows = compare_policies(records, now)
    lines = ["Сравнение политик приоритета:",
             f"{'Политика':<26}{'SLA, %':>8}{'Наруш.':>8}{'P1':>5}{'Просрочка, ч':>14}"]
    lines += [
        f"{r['policy']:<26}{r['compliance']:>8}{r['overdue']:>8}"
        f"{r['critical']:>5}{r['overdue_hours']:>14}"
        for r in rows
    ]
    return "\n".join(lines)


def paradigms_text(records: List[dict], now: datetime) -> str:
    results = compare(records, now)
    same = len({tuple(r["ids"]) for r in results.values()}) == 1
    lines = ["Сравнение парадигм (задача: нарушения SLA):"]
    lines += [f"  {name:<18}{len(r['ids']):>3} шт.   {r['ms']:>8.4f} мс"
              for name, r in results.items()]
    lines.append("Результаты совпадают: " + ("да" if same else "НЕТ"))
    return "\n".join(lines)
