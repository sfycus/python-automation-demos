import unittest

from core import IntakeService


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.service = IntakeService()

    def tearDown(self):
        self.service.close()

    def test_customer_flow_and_operator(self):
        for text in ["/new", "ООО Тест", "@test", "Нужна интеграция"]:
            reply, notice = self.service.handle(1, text, operator_id=99)
        self.assertIn("#1", reply)
        self.assertIn("Нужна интеграция", notice)
        listing, _ = self.service.handle(99, "/list", operator_id=99)
        self.assertIn("ООО Тест", listing)
        self.assertIn("new", listing)
        done, _ = self.service.handle(99, "/done 1", operator_id=99)
        self.assertIn("закрыта", done)

    def test_customer_cannot_use_operator_command(self):
        reply, _ = self.service.handle(1, "/list", operator_id=99)
        self.assertIn("/new", reply)

    def test_restart_clears_partial_session(self):
        self.service.handle(1, "/new", 99)
        self.service.handle(1, "Старое имя", 99)
        reply, _ = self.service.handle(1, "/new", 99)
        self.assertIn("зовут", reply)
        self.assertEqual(self.service.db.execute("SELECT name FROM sessions WHERE chat_id=1").fetchone()[0], "")


if __name__ == "__main__":
    unittest.main()
