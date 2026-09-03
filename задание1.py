# numbers — исходный список целых чисел
numbers = [4, 7, 2, 9, 12, 5, 8, 3]

# Переменные с изменяемым состоянием
total = 0
even_numbers = []
squares = []  # Для сохранения квадратов выбранных чисел
iterations_count = 0  # Счётчик итераций

for number in numbers:
    iterations_count += 1
    if number % 2 == 0:
        even_numbers.append(number)
        sq = number ** 2
        squares.append(sq)
        total += sq

print("Чётные числа:", even_numbers)
print("Квадраты чётных чисел:", squares)
print("Сумма квадратов:", total)
print("Количество итераций цикла:", iterations_count)
