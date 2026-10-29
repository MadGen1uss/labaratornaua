import re
import sqlite3

# ==========================================
# ИСХОДНЫЕ ДАННЫЕ
# ==========================================
students = [
    {
        'name': 'Aida',
        'group': 'IS-24-01',
        'score': 82,
        'attendance': 91,
        'email': 'aida@atu.edu.kz',
    },
    {
        'name': 'Miras',
        'group': 'IS-24-01',
        'score': 69,
        'attendance': 88,
        'email': 'miras@atu.edu.kz',
    },
    {
        'name': 'Dana',
        'group': 'IS-24-02',
        'score': 91,
        'attendance': 96,
        'email': 'dana@atu.edu.kz',
    },
    {
        'name': 'Timur',
        'group': 'IS-24-02',
        'score': 74,
        'attendance': 62,
        'email': 'timur_at_atu.kz',
    },  # Намеренно некорректный email
    {
        'name': 'Aliya',
        'group': 'IS-24-03',
        'score': 87,
        'attendance': 79,
        'email': 'aliya@atu.edu.kz',
    },
    {
        'name': 'Arman',
        'group': 'IS-24-03',
        'score': 55,
        'attendance': 72,
        'email': 'arman@atu.edu.kz',
    },
]

# ==========================================
# ЗАДАНИЕ 1: Сравнение двух стилей
# ==========================================
print('=== ЗАДАНИЕ 1: Сравнение стилей ===')
# Пошаговый цикл (императивный подход)
passed_imperative = []
for student in students:
  if student['score'] >= 75:
    passed_imperative.append(student['name'])

# Списковое включение (декларативный подход)
passed_declarative = [student['name'] for student in students if student['score'] >= 75]

print('Императивно :', passed_imperative)
print('Декларативно:', passed_declarative)
print('Результаты равны:', passed_imperative == passed_declarative)

# ==========================================
# ЗАДАНИЕ 2: Условия для коллекции
# ==========================================
print('\n=== ЗАДАНИЕ 2: Условия для коллекции ===')
has_excellent = any(s['score'] >= 90 for s in students)
all_attended = all(s['attendance'] >= 60 for s in students)
average = (
    sum(s['score'] for s in students) / len(students) if students else 0
)

print('Есть отличник (score >= 90):', has_excellent)
print('Посещаемость всех не ниже 60%:', all_attended)
print('Средний балл:', round(average, 1))

# Изменение показателя для демонстрации all()
students[3]['attendance'] = 55
all_attended_changed = all(s['attendance'] >= 60 for s in students)
print('Посещаемость всех >= 60% (после изменения):', all_attended_changed)
students[3]['attendance'] = 62  # Возврат значения

# ==========================================
# ЗАДАНИЕ 3: Проверка регулярными выражениями
# ==========================================
print('\n=== ЗАДАНИЕ 3: Проверка регулярными выражениями ===')
group_pattern = r'^[A-Z]{2}-\d{2}-\d{2}$'
email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

invalid_groups = [
    s['group'] for s in students if not re.fullmatch(group_pattern, s['group'])
]
invalid_emails = [
    s['email'] for s in students if not re.fullmatch(email_pattern, s['email'])
]

print('Ошибочные группы:', invalid_groups)
print('Ошибочные email :', invalid_emails)

# Исправление почты
students[3]['email'] = 'timur@atu.edu.kz'
print('Исправленный email для Timur:', students[3]['email'])

# ==========================================
# ЗАДАНИЕ 4: Создание базы SQLite
# ==========================================
print('\n=== ЗАДАНИЕ 4 & 5: Работа с SQLite ===')
connection = sqlite3.connect(':memory:')
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE students (
    name TEXT NOT NULL,
    group_name TEXT NOT NULL,
    score INTEGER NOT NULL,
    attendance INTEGER NOT NULL,
    email TEXT NOT NULL
)
""")

rows = [
    (s['name'], s['group'], s['score'], s['attendance'], s['email'])
    for s in students
]
cursor.executemany('INSERT INTO students VALUES (?, ?, ?, ?, ?)', rows)
connection.commit()

# ==========================================
# ЗАДАНИЕ 5: Декларативные SQL запросы
# ==========================================
print('\n-- Выборка и сортировка (score >= 75, attendance >= 70) --')
query_select = """
SELECT name, score, attendance 
FROM students 
WHERE score >= 75 AND attendance >= 70 
ORDER BY score DESC
"""
for row in cursor.execute(query_select):
  print(f'Студент: {row[0]}, Оценка: {row[1]}, Посещаемость: {row[2]}%')

print('\n-- Группировка и агрегирование (HAVING AVG >= 70) --')
query_group = """
SELECT group_name, COUNT(*) AS student_count, ROUND(AVG(score), 1) AS average_score
FROM students
GROUP BY group_name
HAVING AVG(score) >= 70
ORDER BY average_score DESC
"""
for row in cursor.execute(query_group):
  print(f'Группа: {row[0]} | Кол-во: {row[1]} | Средний балл: {row[2]}')

# ==========================================
# ИНДИВИДУАЛЬНЫЙ ВАРИАНТ №3
# ==========================================
print('\n=== ИНДИВИДУАЛЬНЫЙ ВАРИАНТ 3: Допуск к экзамену ===')
query_variant3 = """
SELECT name, group_name, score, email
FROM students
WHERE score >= 70 AND attendance >= 70
ORDER BY score DESC
"""

result = cursor.execute(query_variant3).fetchall()
valid_admitted = [row for row in result if re.fullmatch(email_pattern, row[3])]

if not valid_admitted:
  print('Нет студентов, допущенных к экзамену.')
else:
  print('Список допущенных к экзамену:')
  for place, row in enumerate(valid_admitted, start=1):
    print(
        f'{place}. {row[0]} | Группа: {row[1]} | Балл: {row[2]} | Email:'
        f' {row[3]}'
    )

print('\n-- Дополнительно: Количество допущенных по группам --')
query_variant3_count = """
SELECT group_name, COUNT(*) 
FROM students 
WHERE score >= 70 AND attendance >= 70 
GROUP BY group_name
"""
for row in cursor.execute(query_variant3_count):
  print(f'Группа {row[0]}: {row[1]} чел.')

connection.close()