% =====================================================================
% lab10.pl  (UTF-8)
% Лабораторная работа 10. Логическое программирование в SWI-Prolog.
% Вариант 4: Консультация, основной предикат needs_advice/2.
% Запуск:  swipl lab10.pl     либо   ?- [lab10].
% =====================================================================

% ---------- Исходная база знаний (задания 1-2) ----------

% students and courses
student(aida).
student(miras).
student(dana).
student(timur).
student(aliya).            % добавлено в задании 1

course(programming_1).
course(programming_2).
course(data_structures).
course(databases).
course(artificial_intelligence).
course(machine_learning).

% completed(Student, Course)
completed(aida, programming_1).
completed(aida, programming_2).
completed(aida, data_structures).
completed(aida, databases).
completed(miras, programming_1).
completed(miras, databases).
completed(dana, programming_1).
completed(dana, programming_2).
completed(dana, data_structures).
completed(timur, programming_1).
completed(aliya, programming_1).   % добавлено в задании 1
completed(aliya, programming_2).   % добавлено в задании 1

% requires(Course, Prerequisite)
requires(programming_2, programming_1).
requires(data_structures, programming_2).
requires(artificial_intelligence, data_structures).
requires(artificial_intelligence, databases).
requires(machine_learning, artificial_intelligence).

% wants(Student, Course) -- курсы, на которые студент хочет записаться
% (факты индивидуального варианта 4)
wants(aida, artificial_intelligence).
wants(aida, machine_learning).
wants(miras, artificial_intelligence).
wants(dana, artificial_intelligence).
wants(timur, machine_learning).
wants(aliya, artificial_intelligence).

% ---------- Задание 2: правила и составные цели ----------

ai_candidate(Student) :-
    completed(Student, data_structures),
    completed(Student, databases).

strong_student(Student) :-
    completed(Student, programming_2),
    completed(Student, data_structures).

% ---------- Задание 4: непосредственный допуск ----------

missing_direct(Student, Course, Prerequisite) :-
    student(Student),
    requires(Course, Prerequisite),
    \+ completed(Student, Prerequisite).

immediate_eligible(Student, Course) :-
    student(Student),
    course(Course),
    \+ missing_direct(Student, Course, _).

% ---------- Задание 5: транзитивные пререквизиты ----------

prerequisite(Course, Prerequisite) :-
    requires(Course, Prerequisite).
prerequisite(Course, Prerequisite) :-
    requires(Course, Intermediate),
    prerequisite(Intermediate, Prerequisite).

% ---------- Задание 6: полный допуск ----------
% ВНИМАНИЕ: вариант из методички
%     missing_all(S, C, M) :- setof(...), !.
%     missing_all(_, _, []).
% содержит ошибку: при вызове missing_all(S, C, []) и непустом реальном
% списке первое правило не унифицируется с [], и срабатывает второе
% правило -> eligible/2 возвращает true для любого студента.
% Здесь использован findall/3 + sort/2: список строится ДО унификации
% с выходным аргументом, пустой результат обрабатывается естественно,
% cut не нужен.

missing_all(Student, Course, Missing) :-
    findall(P,
            ( prerequisite(Course, P),
              \+ completed(Student, P) ),   % P уже связана предыдущей целью
            Found),
    sort(Found, Missing).                   % убирает дубликаты, сортирует

eligible(Student, Course) :-
    student(Student),
    course(Course),
    missing_all(Student, Course, []).

% ---------- Задание 7: безопасный обход (защита от циклов) ----------

safe_prerequisite(Course, Prerequisite) :-
    safe_prerequisite(Course, Prerequisite, [Course]).

safe_prerequisite(Course, Prerequisite, _) :-
    requires(Course, Prerequisite).
safe_prerequisite(Course, Prerequisite, Visited) :-
    requires(Course, Next),
    \+ memberchk(Next, Visited),
    safe_prerequisite(Next, Prerequisite, [Next|Visited]).

% Для эксперимента временно раскомментируйте цикл, затем закомментируйте:
% requires(programming_1, machine_learning).

% ---------- Задание 8: интегрированный отчёт ----------
% student/1 и course/1 нужны, чтобы \+ в missing_all не получал
% несвязанную переменную Student (типичная ошибка из методички).

recommendation(Student, Course, eligible, []) :-
    eligible(Student, Course).
recommendation(Student, Course, missing, Missing) :-
    student(Student),
    course(Course),
    missing_all(Student, Course, Missing),
    Missing \= [].

% ---------- Индивидуальный вариант 4: консультация ----------
% needs_advice(Student, Missing): Missing -- отсортированный список всех
% дисциплин (транзитивно), которых студенту не хватает для курсов из wants/2.
% Если недостающих дисциплин нет, предикат ложен (консультация не нужна).

needs_advice(Student, Missing) :-
    student(Student),
    setof(P,
          Course^( wants(Student, Course),
                   prerequisite(Course, P),
                   \+ completed(Student, P) ),
          Missing).

% =====================================================================
% Контрольные запросы (вводить в интерпретаторе):
% ?- completed(aida, databases).
% ?- completed(Student, programming_1).
% ?- ai_candidate(S).
% ?- strong_student(S).
% ?- missing_direct(miras, artificial_intelligence, What).
% ?- immediate_eligible(aida, artificial_intelligence).
% ?- prerequisite(machine_learning, C).
% ?- missing_all(miras, artificial_intelligence, M).
% ?- eligible(miras, artificial_intelligence).
% ?- recommendation(S, artificial_intelligence, Status, Missing).
% ?- needs_advice(S, Missing).
% =====================================================================
