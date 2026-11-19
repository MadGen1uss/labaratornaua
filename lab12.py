"""Лабораторная работа 12. Асинхронный конвейер обработки оценок студентов.

producer -> queue (maxsize) -> N consumer -> result_queue -> saver
Улучшения: asyncio.timeout, повторные попытки, третья очередь,
сравнение 1 и 2 потребителей, рейтинг студентов.
"""
import asyncio
import time
from dataclasses import dataclass, field

SENTINEL = object()

RECORDS = [
    {'student': 'Алия', 'grade': 85},
    {'student': 'Дамир', 'grade': 54},
    {'student': 'Руслан', 'grade': 78},
    {'student': '', 'grade': 91},
    {'student': 'Мадина', 'grade': 105},
]


class TransientError(Exception):
    """Временная ошибка (имитация сбоя сервиса), допускает повтор."""


@dataclass
class Stats:
    results: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    elapsed: float = 0.0
    max_qsize: int = 0

    @property
    def average(self) -> float:
        if not self.results:
            return 0.0
        return sum(r['grade'] for r in self.results) / len(self.results)

    def ranking(self) -> list[dict]:
        return sorted(self.results, key=lambda r: r['grade'], reverse=True)


def validate(record: dict) -> None:
    student = str(record.get('student', '')).strip()
    grade = record.get('grade')
    if not student:
        raise ValueError('Не указано имя')
    if (isinstance(grade, bool) or not isinstance(grade, (int, float))
            or not 0 <= grade <= 100):
        raise ValueError('Оценка должна быть от 0 до 100')


async def process(record: dict, attempt: int, delay: float) -> dict:
    await asyncio.sleep(delay)  # имитация сохранения
    if record.get('flaky', 0) >= attempt:  # временный сбой на первых попытках
        raise TransientError('временный сбой сервиса')
    if record.get('hang'):  # имитация зависшего вызова
        await asyncio.sleep(3600)
    if record.get('crash'):  # неожиданная ошибка
        raise RuntimeError('неожиданный сбой')
    validate(record)
    return {**record, 'status': 'зачет' if record['grade'] >= 60 else 'незачет'}


async def process_with_retry(record: dict, delay: float, timeout: float,
                             retries: int) -> dict:
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            async with asyncio.timeout(timeout):
                return await process(record, attempt, delay)
        except (TransientError, TimeoutError) as error:
            last = error
            await asyncio.sleep(0.01 * attempt)  # небольшая пауза перед повтором
    raise TransientError(f'исчерпаны попытки ({retries}): {last!r}')


async def producer(queue: asyncio.Queue, data: list[dict],
                   consumers: int, delay: float, stats: Stats) -> None:
    for record in data:
        await asyncio.sleep(delay)  # имитация получения из сервиса
        await queue.put(record)  # при полной очереди ждет (обратное давление)
        stats.max_qsize = max(stats.max_qsize, queue.qsize())
    for _ in range(consumers):  # по одному сигналу на каждого потребителя
        await queue.put(SENTINEL)


async def consumer(name: str, queue: asyncio.Queue, out: asyncio.Queue,
                   stats: Stats, delay: float, timeout: float,
                   retries: int, verbose: bool) -> None:
    while True:
        item = await queue.get()
        try:
            if item is SENTINEL:
                if verbose:
                    print(name, 'завершен')
                return
            try:
                result = await process_with_retry(item, delay, timeout, retries)
                await out.put(result)
                if verbose:
                    print(name, 'обработал', result)
            except (ValueError, TransientError) as error:
                stats.errors.append(f'{item}: {error}')
            except Exception as error:  # неожиданная ошибка не роняет работника
                stats.errors.append(f'{item}: {type(error).__name__}: {error}')
        finally:
            queue.task_done()


async def saver(out: asyncio.Queue, stats: Stats) -> None:
    while True:
        item = await out.get()
        try:
            if item is SENTINEL:
                return
            stats.results.append(item)
        finally:
            out.task_done()


async def run_pipeline(data: list[dict], consumers: int = 2, maxsize: int = 3,
                       produce_delay: float = 0.15, process_delay: float = 0.25,
                       timeout: float = 1.0, retries: int = 3,
                       verbose: bool = False) -> Stats:
    queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
    out: asyncio.Queue = asyncio.Queue()
    stats = Stats()
    started = time.perf_counter()
    save_task = asyncio.create_task(saver(out, stats))
    workers = [
        asyncio.create_task(consumer(f'worker-{i}', queue, out, stats,
                                     process_delay, timeout, retries, verbose))
        for i in range(1, consumers + 1)
    ]
    await producer(queue, data, consumers, produce_delay, stats)
    await queue.join()
    await asyncio.gather(*workers)
    await out.put(SENTINEL)
    await out.join()
    await save_task
    stats.elapsed = time.perf_counter() - started
    return stats


def print_report(stats: Stats) -> None:
    print(f'Обработано: {len(stats.results)}')
    print(f'Ошибок: {len(stats.errors)}')
    print(f'Средний балл: {stats.average:.2f}')
    print(f'Время: {stats.elapsed:.2f} с')
    for error in stats.errors:
        print('Ошибка:', error)
    print('Рейтинг:')
    for place, item in enumerate(stats.ranking(), 1):
        print(f"  {place}. {item['student']}: {item['grade']} ({item['status']})")


# ---------------------------- тестирование ----------------------------

async def run_tests() -> None:
    fast = dict(produce_delay=0.01, process_delay=0.02)

    # 1. Все записи корректны
    good = [{'student': f'S{i}', 'grade': 50 + i} for i in range(6)]
    s = await run_pipeline(good, **fast)
    assert len(s.results) == 6 and not s.errors
    print('Тест 1 OK: обработано все, ошибок нет')

    # 2. Пустое имя: ошибка зафиксирована, цикл продолжается
    s = await run_pipeline([{'student': '', 'grade': 90},
                            {'student': 'A', 'grade': 70}], **fast)
    assert len(s.errors) == 1 and len(s.results) == 1
    print('Тест 2 OK: пустое имя отклонено, работа продолжена')

    # 3. Оценка < 0 или > 100
    s = await run_pipeline([{'student': 'A', 'grade': -1},
                            {'student': 'B', 'grade': 101}], **fast)
    assert len(s.errors) == 2 and not s.results
    print('Тест 3 OK: недопустимые оценки отклонены')

    # 4. maxsize = 1: производитель ждет, данные не теряются
    s = await run_pipeline(good * 2, maxsize=1, produce_delay=0.0,
                           process_delay=0.02)
    assert s.max_qsize <= 1 and len(s.results) == 12
    print('Тест 4 OK: maxsize=1, потерь нет')

    # 5. Один и два потребителя
    data = [{'student': f'S{i}', 'grade': 70} for i in range(10)]
    one = await run_pipeline(data, consumers=1, produce_delay=0.0,
                             process_delay=0.05)
    two = await run_pipeline(data, consumers=2, produce_delay=0.0,
                             process_delay=0.05)
    assert two.elapsed < one.elapsed
    print(f'Тест 5 OK: 1 потребитель {one.elapsed:.2f} с, '
          f'2 потребителя {two.elapsed:.2f} с')

    # 6. Исключение в process: task_done вызван, join завершается
    s = await asyncio.wait_for(run_pipeline(
        [{'student': 'A', 'grade': 70, 'crash': True},
         {'student': 'B', 'grade': 80}], **fast), timeout=5)
    assert len(s.errors) == 1 and len(s.results) == 1
    print('Тест 6 OK: исключение не блокирует join')

    # 7. Пустой вход: средний балл 0
    s = await run_pipeline([], **fast)
    assert s.average == 0.0 and not s.results
    print('Тест 7 OK: пустой вход, деления на ноль нет')

    # 8. (доп.) повтор при временной ошибке и таймаут
    s = await run_pipeline([{'student': 'A', 'grade': 70, 'flaky': 2}],
                           retries=3, **fast)
    assert len(s.results) == 1
    s = await run_pipeline([{'student': 'B', 'grade': 70, 'hang': True}],
                           timeout=0.05, retries=2, **fast)
    assert len(s.errors) == 1
    print('Тест 8 OK: retry работает, timeout срабатывает')


async def main() -> None:
    print('=== Базовый запуск ===')
    stats = await run_pipeline(RECORDS, consumers=2, maxsize=3, verbose=True)
    print_report(stats)
    print('\n=== Тесты ===')
    await run_tests()


if __name__ == '__main__':
    asyncio.run(main())
