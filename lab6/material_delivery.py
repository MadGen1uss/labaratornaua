"""Вариант 5. Доставка учебных материалов.

MaterialService (клиент) использует контракт DeliveryChannel.
Реализации: EmailDelivery, LinkDelivery, MemoryDelivery.
Повышенная сложность: отправка просроченной ссылки запрещена.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, Protocol


class DeliveryChannel(Protocol):
    """Контракт канала доставки: единственная операция deliver."""

    def deliver(self, recipient: str, message: str) -> None:
        """Доставляет сообщение получателю."""
        ...


@dataclass(frozen=True)
class Material:
    """Учебный материал со ссылкой и необязательным сроком действия."""

    title: str
    url: str
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("Название материала не может быть пустым")
        if not isinstance(self.url, str) or not self.url.startswith(
            ("http://", "https://")
        ):
            raise ValueError("Ссылка должна начинаться с http:// или https://")

    def is_expired(self, now: datetime) -> bool:
        """Возвращает True, если срок действия ссылки истёк."""
        return self.expires_at is not None and now >= self.expires_at


class Student:
    """Студент: идентификатор, имя и адрес для доставки."""

    def __init__(self, student_id, name, email):
        if isinstance(student_id, bool) or not isinstance(student_id, int):
            raise TypeError("Идентификатор должен быть целым числом")
        if student_id <= 0 or not isinstance(name, str) or not name.strip():
            raise ValueError("Некорректные данные студента")
        if not isinstance(email, str) or "@" not in email:
            raise ValueError("Некорректный адрес электронной почты")
        self.student_id = student_id
        self.name = name.strip()
        self.email = email.strip()



class EmailDelivery:
    """Заглушка e-mail: формирует письмо и хранит его в outbox."""

    def __init__(self, sender: str = "no-reply@atu.example", echo: bool = False):
        self.sender = sender
        self.echo = echo
        self.outbox: list[str] = []

    def deliver(self, recipient: str, message: str) -> None:
        letter = f"From: {self.sender}\nTo: {recipient}\n\n{message}"
        self.outbox.append(letter)
        if self.echo:
            print(letter)


class LinkDelivery:
    """Публикует ссылку в личном кабинете (словарь получатель -> записи)."""

    def __init__(self, echo: bool = False):
        self.echo = echo
        self.portal: dict[str, list[str]] = {}

    def deliver(self, recipient: str, message: str) -> None:
        self.portal.setdefault(recipient, []).append(message)
        if self.echo:
            print(f"[кабинет {recipient}] {message}")


class MemoryDelivery:
    """Тестовый дублёр: сохраняет пары (получатель, сообщение)."""

    def __init__(self):
        self.messages: list[tuple[str, str]] = []

    def deliver(self, recipient: str, message: str) -> None:
        self.messages.append((recipient, message))


class MaterialService:
    """Регистрирует студентов и доставляет им материалы через канал."""

    def __init__(
        self,
        channel: DeliveryChannel,
        clock: Callable[[], datetime] = datetime.now,
    ):
        self._channel = channel
        self._clock = clock
        self._students: dict[int, Student] = {}

    def register(self, student: Student) -> None:
        if student.student_id in self._students:
            raise ValueError("Студент уже зарегистрирован")
        self._students[student.student_id] = student

    def deliver_material(self, student_id: int, material: Material) -> None:
        student = self._get_student(student_id)
        if material.is_expired(self._clock()):
            raise ValueError("Срок действия ссылки истёк")
        self._channel.deliver(
            student.email, f"{material.title}: {material.url}"
        )

    def _get_student(self, student_id: int) -> Student:
        try:
            return self._students[student_id]
        except KeyError as error:
            raise KeyError("Студент не найден") from error


if __name__ == "__main__":
    book = Material("Лекция 6", "https://lms.atu.example/pp/lecture6")
    for channel in (EmailDelivery(echo=True), LinkDelivery(echo=True)):
        print(f"--- {type(channel).__name__} ---")
        service = MaterialService(channel)
        service.register(Student(101, "Amina", "amina@atu.example"))
        service.deliver_material(101, book)
