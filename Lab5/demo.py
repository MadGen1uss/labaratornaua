"""Демонстрационный запуск: два претендента и две взаимозаменяемые политики."""

from scholarship import (
    AcademicPolicy,
    ScholarshipApplicant,
    SocialAcademicPolicy,
    SocialCategory,
)


def show(applicant):
    average = "-" if applicant.average is None else f"{applicant.average:.2f}"
    print(f"{applicant.name}: средний {average}; {applicant.amount} тг")
    print(f"  {applicant.explanation}")


def main():
    academic = AcademicPolicy()
    social = SocialAcademicPolicy()

    amina = ScholarshipApplicant("Amina", SocialCategory.NONE, academic)
    dias = ScholarshipApplicant("Dias", SocialCategory.LOW_INCOME, academic)
    mira = ScholarshipApplicant("Mira", SocialCategory.ORPHAN, academic)

    for score in (88, 92, 79, 95):
        amina.add_score(score)
    for score in (55, 62, 58):
        dias.add_score(score)

    print("== Политика: только успеваемость ==")
    for applicant in (amina, dias, mira):
        show(applicant)

    print("\n== Политика: успеваемость + социальная надбавка ==")
    for applicant in (amina, dias, mira):
        applicant.change_policy(social)
        show(applicant)

    print("\n== Ошибочный ввод ==")
    try:
        amina.add_score(101)
    except ValueError as error:
        print(f"ValueError: {error}; оценок осталось {len(amina.scores)}")


if __name__ == "__main__":
    main()
