import unittest
from datetime import datetime, timedelta

from material_delivery import (
    EmailDelivery, LinkDelivery, MemoryDelivery,
    Material, MaterialService, Student,
)

NOW = datetime(2026, 10, 8, 12, 0)
URL = "https://lms.atu.example/pp/lecture6"


def make_service(channel):
    service = MaterialService(channel, clock=lambda: NOW)
    service.register(Student(1, "Amina", "amina@atu.example"))
    return service


class MaterialServiceTests(unittest.TestCase):
    def test_link_is_delivered_to_registered_student(self):
        channel = MemoryDelivery()
        make_service(channel).deliver_material(1, Material("Лекция 6", URL))
        self.assertEqual(
            channel.messages, [("amina@atu.example", f"Лекция 6: {URL}")]
        )

    def test_unexpired_link_is_allowed(self):
        channel = MemoryDelivery()
        material = Material("Лекция", URL, NOW + timedelta(days=1))
        make_service(channel).deliver_material(1, material)
        self.assertEqual(len(channel.messages), 1)

    def test_expired_link_is_rejected(self):
        channel = MemoryDelivery()
        material = Material("Лекция", URL, NOW - timedelta(seconds=1))
        with self.assertRaisesRegex(ValueError, "истёк"):
            make_service(channel).deliver_material(1, material)
        self.assertEqual(channel.messages, [])

    def test_unknown_student_is_reported(self):
        with self.assertRaisesRegex(KeyError, "Студент не найден"):
            make_service(MemoryDelivery()).deliver_material(
                999, Material("Лекция", URL)
            )

    def test_duplicate_registration_is_rejected(self):
        service = make_service(MemoryDelivery())
        with self.assertRaisesRegex(ValueError, "уже зарегистрирован"):
            service.register(Student(1, "Other", "o@atu.example"))

    def test_invalid_material_data_is_rejected(self):
        with self.assertRaises(ValueError):
            Material("", URL)
        with self.assertRaises(ValueError):
            Material("Лекция", "ftp://bad")

    def test_invalid_student_data_is_rejected(self):
        with self.assertRaises(TypeError):
            Student(True, "A", "a@b.c")
        with self.assertRaises(ValueError):
            Student(1, "  ", "a@b.c")
        with self.assertRaises(ValueError):
            Student(1, "A", "no-at-sign")

    def test_channels_are_interchangeable(self):
        material = Material("Лекция 6", URL)
        email, portal, memory = EmailDelivery(), LinkDelivery(), MemoryDelivery()
        for channel in (email, portal, memory):
            make_service(channel).deliver_material(1, material)
        self.assertIn(URL, email.outbox[0])
        self.assertIn("To: amina@atu.example", email.outbox[0])
        self.assertEqual(portal.portal["amina@atu.example"], [f"Лекция 6: {URL}"])
        self.assertEqual(memory.messages[0][1], f"Лекция 6: {URL}")


if __name__ == "__main__":
    unittest.main()
