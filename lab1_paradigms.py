"""Лабораторная работа № 1. Сравнение парадигм программирования на Python.

Вариант 5: получить кубы положительных чисел.

Весь код лабораторной находится в этом файле.

Запуск (Python 3.11 или новее, сторонние библиотеки не нужны):
    python lab1_paradigms.py          # все консольные демонстрации
    python lab1_paradigms.py test     # автоматические тесты
    python lab1_paradigms.py gui      # окно tkinter (событийный стиль)

Тесты можно запустить и стандартной командой:
    python -m unittest lab1_paradigms -v

Содержание:
    Часть 1. Сквозная задача: сумма квадратов чётных чисел
        1. императивный стиль
        2. процедурный стиль
        3. объектно-ориентированный стиль
        4. функциональный стиль
        5. событийный стиль (tkinter)
    Часть 2. Индивидуальный вариант 5: кубы положительных чисел
        императивный, процедурный, ООП и функциональный стили
    Часть 3. Демонстрация и тесты
"""

import sys
import unittest

NUMBERS = [4, 7, 2, 9, 12, 5, 8, 3]          # сквозная задача, ответ: 228
VARIANT_NUMBERS = [4, -7, 2, 0, -9, 12, 5, -8, 3]   # вариант 5


# =====================================================================
# ЧАСТЬ 1. СКВОЗНАЯ ЗАДАЧА: сумма квадратов чётных чисел
# =====================================================================

# ---------------------------------------------------------------------
# 1. Императивный стиль: явные команды и изменяемое состояние
# ---------------------------------------------------------------------

def imperative_process(numbers):
    """Возвращает (чётные числа, их квадраты, сумма квадратов, число итераций).

    Изменяемое состояние программы:
      total        - накопитель суммы, меняется на каждом чётном числе;
      even_numbers - список, пополняется методом append;
      squares      - список, пополняется методом append;
      iterations   - счётчик итераций, растёт на каждом шаге цикла;
      number       - переменная цикла, получает новое значение на каждом шаге.
    """
    total = 0
    even_numbers = []
    squares = []
    iterations = 0

    for number in numbers:
        iterations += 1
        if number % 2 == 0:
            squared = number ** 2
            even_numbers.append(number)
            squares.append(squared)
            total += squared

    return even_numbers, squares, total, iterations


# ---------------------------------------------------------------------
# 2. Процедурный стиль: каждая функция решает одну подзадачу
# ---------------------------------------------------------------------

def is_even(number: int) -> bool:
    """Проверяет, чётное ли число."""
    return number % 2 == 0


def square(number: int) -> int:
    """Возвращает квадрат числа."""
    return number ** 2


def get_even_numbers(values: list[int]) -> list[int]:
    """Возвращает новый список чётных чисел, не изменяя исходный."""
    result = []
    for number in values:
        if is_even(number):
            result.append(number)
    return result


def sum_even_squares(values: list[int]) -> int:
    """Возвращает сумму квадратов чётных чисел."""
    total = 0
    for number in get_even_numbers(values):
        total += square(number)
    return total


# ---------------------------------------------------------------------
# 3. Объектно-ориентированный стиль: состояние и поведение в классе
# ---------------------------------------------------------------------

class NumberCollection:
    """Набор целых чисел с операциями над ним.

    Атрибут self._numbers хранит состояние объекта - собственный список чисел
    этого экземпляра. Он создаётся как копия (list(numbers)), поэтому
    изменение исходного списка снаружи не влияет на объект. Подчёркивание
    показывает, что это внутренняя деталь: клиент работает через методы.
    """

    def __init__(self, numbers):
        numbers = list(numbers)
        for number in numbers:
            if isinstance(number, bool) or not isinstance(number, int):
                raise TypeError("Коллекция должна содержать только целые числа")
        self._numbers = numbers

    def get_even_numbers(self):
        """Возвращает список чётных чисел."""
        return [n for n in self._numbers if n % 2 == 0]

    def sum_even_squares(self):
        """Возвращает сумму квадратов чётных чисел."""
        total = 0
        for number in self.get_even_numbers():
            total += number ** 2
        return total

    def count_even_numbers(self):
        """Возвращает количество чётных чисел."""
        return len(self.get_even_numbers())

    def find_maximum(self):
        """Возвращает максимум всей коллекции или None, если она пуста."""
        return max(self._numbers) if self._numbers else None

    def calculate_average(self):
        """Возвращает среднее всей коллекции или None, если она пуста."""
        if not self._numbers:
            return None
        return sum(self._numbers) / len(self._numbers)


# ---------------------------------------------------------------------
# 4. Функциональный стиль: композиция отбора, преобразования, свёртки
# ---------------------------------------------------------------------

def sum_even_squares_map_filter(numbers):
    """filter -> map -> sum, без изменяемых переменных."""
    return sum(
        map(
            lambda number: number ** 2,
            filter(lambda number: number % 2 == 0, numbers),
        )
    )


def sum_even_squares_generator(numbers):
    """То же вычисление генераторным выражением."""
    return sum(number ** 2 for number in numbers if number % 2 == 0)


def even_squares(numbers):
    """Отдельный список квадратов чётных чисел."""
    return [number ** 2 for number in numbers if number % 2 == 0]


# ---------------------------------------------------------------------
# 5. Событийный стиль (tkinter): вычисление запускается нажатием кнопки
# ---------------------------------------------------------------------
# Логика (parse_numbers, sum_even_squares) отделена от окна, поэтому её можно
# проверять тестами без графической среды. tkinter импортируется только
# при создании окна.

DEFAULT_TEXT = "4 7 2 9 12 5 8 3"


def parse_numbers(text):
    """Разбирает строку с целыми числами через пробел; иначе ValueError."""
    tokens = text.split()
    if not tokens:
        raise ValueError("Введите хотя бы одно число")
    numbers = []
    for token in tokens:
        try:
            numbers.append(int(token))
        except ValueError:
            raise ValueError(
                f"Не удаётся преобразовать в целое число: {token!r}"
            ) from None
    return numbers


def create_app():
    """Создаёт окно приложения и возвращает корневой объект Tk."""
    import tkinter as tk

    root = tk.Tk()
    root.title("Парадигмы программирования")

    tk.Label(root, text="Числа через пробел:").pack(padx=20, pady=(10, 0))
    entry = tk.Entry(root, width=30)
    entry.insert(0, DEFAULT_TEXT)
    entry.pack(padx=20, pady=5)

    result_label = tk.Label(root, text="Нажмите кнопку")
    result_label.pack(padx=20, pady=10)

    def calculate():
        """Обработчик события нажатия кнопки «Вычислить»."""
        try:
            numbers = parse_numbers(entry.get())
        except ValueError as error:
            result_label.config(text=f"Ошибка: {error}")
            return
        result_label.config(text=f"Результат: {sum_even_squares(numbers)}")

    def clear():
        """Обработчик события нажатия кнопки «Очистить»."""
        entry.delete(0, tk.END)
        result_label.config(text="Нажмите кнопку")

    tk.Button(root, text="Вычислить", command=calculate).pack(padx=20, pady=5)
    tk.Button(root, text="Очистить", command=clear).pack(padx=20, pady=(0, 10))
    return root


# =====================================================================
# ЧАСТЬ 2. ВАРИАНТ 5: кубы положительных чисел
# Ноль не считается положительным числом.
# =====================================================================

# --- императивный стиль ------------------------------------------------

def variant5_imperative(numbers):
    """Строит список кубов, явно изменяя переменную cubes командами append.

    Изменяемое состояние: cubes (список) и переменная цикла number.
    """
    cubes = []
    for number in numbers:
        if number > 0:
            cubes.append(number ** 3)
    return cubes


# --- процедурный стиль -------------------------------------------------

def is_positive(number: float) -> bool:
    """Проверяет, что число строго больше нуля."""
    return number > 0


def cube(number: float) -> float:
    """Возвращает куб числа."""
    return number ** 3


def get_positive_numbers(values: list[int]) -> list[int]:
    """Выбирает положительные числа (шаг 1)."""
    result = []
    for number in values:
        if is_positive(number):
            result.append(number)
    return result


def get_positive_cubes(values: list[int]) -> list[int]:
    """Возводит выбранные числа в куб (шаг 2)."""
    cubes = []
    for number in get_positive_numbers(values):
        cubes.append(cube(number))
    return cubes


# --- объектно-ориентированный стиль ------------------------------------

class PositiveNumberCollection:
    """Набор чисел; состояние (_numbers) скрыто, поведение - в методах."""

    def __init__(self, numbers):
        numbers = list(numbers)
        for number in numbers:
            if isinstance(number, bool) or not isinstance(number, (int, float)):
                raise TypeError("Коллекция должна содержать только числа")
        self._numbers = numbers

    def positive_numbers(self):
        """Возвращает положительные числа."""
        return [n for n in self._numbers if n > 0]

    def positive_cubes(self):
        """Возвращает кубы положительных чисел."""
        return [n ** 3 for n in self.positive_numbers()]

    def count_positive(self):
        """Возвращает количество положительных чисел."""
        return len(self.positive_numbers())


# --- функциональный стиль ----------------------------------------------

def positive_cubes_functional(numbers):
    """Композиция: отбор положительных, затем возведение в куб."""
    return list(map(cube, filter(is_positive, numbers)))


def positive_cubes_generator(numbers):
    """То же вычисление генераторным выражением."""
    return list(number ** 3 for number in numbers if number > 0)


# =====================================================================
# ЧАСТЬ 3. ДЕМОНСТРАЦИЯ
# =====================================================================

def demo_base_task():
    print("=== Часть 1. Сумма квадратов чётных чисел ===")

    print("\n[1] Императивный стиль")
    evens, squares, total, iterations = imperative_process(NUMBERS)
    print("Чётные числа:", evens)
    print("Квадраты чётных:", squares)
    print("Сумма квадратов:", total)
    print("Итераций цикла:", iterations)

    print("\n[2] Процедурный стиль")
    print("is_even(4) =", is_even(4))
    print("is_even(7) =", is_even(7))
    print("square(5) =", square(5))
    print("Чётные числа:", get_even_numbers(NUMBERS))
    print("Сумма квадратов:", sum_even_squares(NUMBERS))

    print("\n[3] Объектно-ориентированный стиль")
    first = NumberCollection(NUMBERS)
    print("Объект 1")
    print("  Чётные числа:", first.get_even_numbers())
    print("  Сумма квадратов:", first.sum_even_squares())
    print("  Количество чётных:", first.count_even_numbers())
    print("  Максимум:", first.find_maximum())
    print("  Среднее:", first.calculate_average())
    second = NumberCollection([10, 15, 20, 25])
    print("Объект 2")
    print("  Чётные числа:", second.get_even_numbers())
    print("  Сумма квадратов:", second.sum_even_squares())
    print("  Количество чётных:", second.count_even_numbers())
    print("  Максимум:", second.find_maximum())
    print("  Среднее:", second.calculate_average())

    print("\n[4] Функциональный стиль")
    print("map/filter:", sum_even_squares_map_filter(NUMBERS))
    print("Генераторное выражение:", sum_even_squares_generator(NUMBERS))
    print("Квадраты чётных:", even_squares(NUMBERS))
    print("Изменяемых переменных: императивная версия - 4 "
          "(total, even_numbers, squares, iterations), функциональная - 0")


def demo_variant5():
    print("\n=== Часть 2. Вариант 5: кубы положительных чисел ===")
    print("Исходные числа:", VARIANT_NUMBERS)

    print("\n[1] Императивный стиль")
    print("Кубы положительных:", variant5_imperative(VARIANT_NUMBERS))

    print("\n[2] Процедурный стиль")
    print("is_positive(5) =", is_positive(5))
    print("is_positive(0) =", is_positive(0))
    print("cube(3) =", cube(3))
    print("Положительные:", get_positive_numbers(VARIANT_NUMBERS))
    print("Кубы положительных:", get_positive_cubes(VARIANT_NUMBERS))

    print("\n[3] Объектно-ориентированный стиль")
    first = PositiveNumberCollection(VARIANT_NUMBERS)
    print("Объект 1: кубы положительных:", first.positive_cubes())
    second = PositiveNumberCollection([-1, 6, 0, 10])
    print("Объект 2: кубы положительных:", second.positive_cubes())

    print("\n[4] Функциональный стиль")
    print("map/filter:", positive_cubes_functional(VARIANT_NUMBERS))
    print("Генераторное выражение:", positive_cubes_generator(VARIANT_NUMBERS))


def demo():
    demo_base_task()
    demo_variant5()


# =====================================================================
# ТЕСТЫ (unittest)
# =====================================================================

EXPECTED_TOTAL = 228          # 16 + 4 + 144 + 64
EXPECTED_CUBES = [64, 8, 1728, 125, 27]


class ImperativeTests(unittest.TestCase):
    def test_process(self):
        evens, squares, total, iterations = imperative_process(NUMBERS)
        self.assertEqual(evens, [4, 2, 12, 8])
        self.assertEqual(squares, [16, 4, 144, 64])
        self.assertEqual(total, EXPECTED_TOTAL)
        self.assertEqual(iterations, 8)

    def test_empty_and_no_evens(self):
        self.assertEqual(imperative_process([]), ([], [], 0, 0))
        self.assertEqual(imperative_process([1, 3]), ([], [], 0, 2))


class ProceduralTests(unittest.TestCase):
    def test_helpers_separately(self):
        self.assertTrue(is_even(4))
        self.assertFalse(is_even(7))
        self.assertTrue(is_even(0))
        self.assertTrue(is_even(-4))
        self.assertEqual(square(5), 25)
        self.assertEqual(square(-3), 9)

    def test_get_even_numbers_and_sum(self):
        self.assertEqual(get_even_numbers(NUMBERS), [4, 2, 12, 8])
        self.assertEqual(sum_even_squares(NUMBERS), EXPECTED_TOTAL)

    def test_input_is_not_changed(self):
        data = list(NUMBERS)
        get_even_numbers(data)
        sum_even_squares(data)
        self.assertEqual(data, NUMBERS)


class OopTests(unittest.TestCase):
    def test_first_collection(self):
        c = NumberCollection(NUMBERS)
        self.assertEqual(c.get_even_numbers(), [4, 2, 12, 8])
        self.assertEqual(c.sum_even_squares(), EXPECTED_TOTAL)
        self.assertEqual(c.count_even_numbers(), 4)
        self.assertEqual(c.find_maximum(), 12)
        self.assertEqual(c.calculate_average(), 6.25)

    def test_second_object_is_independent(self):
        first = NumberCollection(NUMBERS)
        second = NumberCollection([10, 15, 20, 25])
        self.assertEqual(second.get_even_numbers(), [10, 20])
        self.assertEqual(second.sum_even_squares(), 500)
        self.assertEqual(second.find_maximum(), 25)
        self.assertEqual(second.calculate_average(), 17.5)
        self.assertEqual(first.sum_even_squares(), EXPECTED_TOTAL)

    def test_empty_collection(self):
        c = NumberCollection([])
        self.assertEqual(c.get_even_numbers(), [])
        self.assertEqual(c.sum_even_squares(), 0)
        self.assertEqual(c.count_even_numbers(), 0)
        self.assertIsNone(c.find_maximum())
        self.assertIsNone(c.calculate_average())

    def test_source_list_is_copied(self):
        data = [2, 4]
        c = NumberCollection(data)
        data.append(6)
        self.assertEqual(c.get_even_numbers(), [2, 4])

    def test_invalid_elements(self):
        for bad in ([1, "2"], [True], [1.5], [None]):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    NumberCollection(bad)


class FunctionalTests(unittest.TestCase):
    def test_both_forms(self):
        self.assertEqual(sum_even_squares_map_filter(NUMBERS), EXPECTED_TOTAL)
        self.assertEqual(sum_even_squares_generator(NUMBERS), EXPECTED_TOTAL)

    def test_even_squares_list(self):
        self.assertEqual(even_squares(NUMBERS), [16, 4, 144, 64])

    def test_empty(self):
        self.assertEqual(sum_even_squares_map_filter([]), 0)
        self.assertEqual(even_squares([]), [])

    def test_input_is_not_changed(self):
        data = list(NUMBERS)
        even_squares(data)
        self.assertEqual(data, NUMBERS)


class AllStylesAgreeTests(unittest.TestCase):
    def test_same_result_everywhere(self):
        cases = [NUMBERS, [], [1, 3, 5], [-4, -3, 0, 6], [2]]
        for data in cases:
            with self.subTest(data=data):
                results = {
                    imperative_process(data)[2],
                    sum_even_squares(data),
                    NumberCollection(data).sum_even_squares(),
                    sum_even_squares_map_filter(data),
                    sum_even_squares_generator(data),
                }
                self.assertEqual(len(results), 1)


class EventLogicTests(unittest.TestCase):
    def test_parse_numbers(self):
        self.assertEqual(parse_numbers("4 7  2"), [4, 7, 2])
        self.assertEqual(parse_numbers("-4 3"), [-4, 3])

    def test_default_text_gives_expected_result(self):
        numbers = parse_numbers(DEFAULT_TEXT)
        self.assertEqual(sum_even_squares(numbers), EXPECTED_TOTAL)

    def test_empty_input_is_error(self):
        for text in ("", "   "):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_numbers(text)

    def test_bad_token_is_named_in_error(self):
        with self.assertRaises(ValueError) as context:
            parse_numbers("4 abc 2")
        self.assertIn("abc", str(context.exception))

    def test_float_is_error(self):
        with self.assertRaises(ValueError):
            parse_numbers("4.5")


def all_variant5_styles(data):
    return {
        "imperative": variant5_imperative(data),
        "procedural": get_positive_cubes(data),
        "oop": PositiveNumberCollection(data).positive_cubes(),
        "functional": positive_cubes_functional(data),
        "generator": positive_cubes_generator(data),
    }


class Variant5Tests(unittest.TestCase):
    def test_expected_result_in_every_style(self):
        for style, result in all_variant5_styles(VARIANT_NUMBERS).items():
            with self.subTest(style=style):
                self.assertEqual(result, EXPECTED_CUBES)

    def test_zero_and_negatives_are_excluded(self):
        for style, result in all_variant5_styles([0, -1, -2, -3]).items():
            with self.subTest(style=style):
                self.assertEqual(result, [])

    def test_empty_input(self):
        for style, result in all_variant5_styles([]).items():
            with self.subTest(style=style):
                self.assertEqual(result, [])

    def test_order_is_preserved_and_duplicates_kept(self):
        for style, result in all_variant5_styles([3, 1, 3, -5, 2]).items():
            with self.subTest(style=style):
                self.assertEqual(result, [27, 1, 27, 8])

    def test_smallest_positive_boundary(self):
        for style, result in all_variant5_styles([-1, 0, 1]).items():
            with self.subTest(style=style):
                self.assertEqual(result, [1])

    def test_input_is_not_changed(self):
        for name, func in (
            ("imperative", variant5_imperative),
            ("procedural", get_positive_cubes),
            ("functional", positive_cubes_functional),
        ):
            with self.subTest(style=name):
                data = list(VARIANT_NUMBERS)
                func(data)
                self.assertEqual(data, VARIANT_NUMBERS)

    def test_procedural_helpers(self):
        self.assertTrue(is_positive(1))
        self.assertFalse(is_positive(0))
        self.assertFalse(is_positive(-1))
        self.assertEqual(cube(3), 27)
        self.assertEqual(cube(-2), -8)
        self.assertEqual(get_positive_numbers(VARIANT_NUMBERS),
                         [4, 2, 12, 5, 3])

    def test_oop_second_object_and_count(self):
        first = PositiveNumberCollection(VARIANT_NUMBERS)
        second = PositiveNumberCollection([-1, 6, 0, 10])
        self.assertEqual(second.positive_cubes(), [216, 1000])
        self.assertEqual(second.count_positive(), 2)
        self.assertEqual(first.count_positive(), 5)
        self.assertEqual(first.positive_cubes(), EXPECTED_CUBES)

    def test_oop_rejects_bad_elements(self):
        for bad in ([1, "2"], [True], [None]):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    PositiveNumberCollection(bad)

    def test_oop_copies_source_list(self):
        data = [1, 2]
        collection = PositiveNumberCollection(data)
        data.append(3)
        self.assertEqual(collection.positive_cubes(), [1, 8])

    def test_float_inputs(self):
        self.assertEqual(positive_cubes_functional([0.5, -0.5]), [0.125])


# =====================================================================
# ТОЧКА ВХОДА
# =====================================================================

def main(argv):
    command = argv[1] if len(argv) > 1 else "demo"
    if command == "demo":
        demo()
    elif command == "test":
        unittest.main(argv=[argv[0], "-v"])
    elif command == "gui":
        create_app().mainloop()
    else:
        print("Использование: python lab1_paradigms.py [demo | test | gui]")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
