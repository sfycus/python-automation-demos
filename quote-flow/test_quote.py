import unittest
from decimal import Decimal

from quote import QuoteError, calculate_quote


class QuoteTests(unittest.TestCase):
    def test_valid_quote(self):
        result = calculate_quote({"customer": "Тестовый клиент", "items": [
            {"sku": "GEN-12", "quantity": 1}, {"sku": "ATS-12", "quantity": 1},
            {"sku": "SERVICE", "quantity": 1}], "discount_percent": 5})
        self.assertEqual(Decimal(result["total"]), Decimal("261250.00"))
        self.assertFalse(result["approved"])

    def test_incompatible_accessory(self):
        with self.assertRaisesRegex(QuoteError, "не совместим"):
            calculate_quote({"customer": "Тест", "items": [
                {"sku": "GEN-12", "quantity": 1}, {"sku": "ATS-20", "quantity": 1}]})

    def test_invalid_discount(self):
        with self.assertRaisesRegex(QuoteError, "Скидка"):
            calculate_quote({"customer": "Тест", "items": [
                {"sku": "GEN-12", "quantity": 1}], "discount_percent": 20})


if __name__ == "__main__":
    unittest.main()
