"""Deterministic quote rules for a small equipment supplier."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


CATALOG = {
    "GEN-12": {"name": "Генератор 12 кВт", "price": "215000.00", "type": "generator"},
    "GEN-20": {"name": "Генератор 20 кВт", "price": "349000.00", "type": "generator"},
    "ATS-12": {"name": "АВР до 12 кВт", "price": "42000.00", "type": "ats", "fits": ["GEN-12"]},
    "ATS-20": {"name": "АВР до 20 кВт", "price": "57000.00", "type": "ats", "fits": ["GEN-20"]},
    "SERVICE": {"name": "Пусконаладка", "price": "18000.00", "type": "service"},
}


class QuoteError(ValueError):
    pass


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_quote(payload: dict[str, Any]) -> dict[str, Any]:
    customer = str(payload.get("customer", "")).strip()
    if not customer or len(customer) > 120:
        raise QuoteError("Укажите название клиента (до 120 символов).")

    raw_items = payload.get("items")
    if not isinstance(raw_items, list) or not raw_items or len(raw_items) > 20:
        raise QuoteError("Добавьте от 1 до 20 позиций.")

    lines = []
    generator_skus = []
    for entry in raw_items:
        if not isinstance(entry, dict):
            raise QuoteError("Неверный формат позиции.")
        sku = str(entry.get("sku", ""))
        if sku not in CATALOG:
            raise QuoteError(f"Неизвестная позиция: {sku[:30]}")
        try:
            quantity = int(entry.get("quantity", 0))
        except (TypeError, ValueError):
            raise QuoteError(f"Некорректное количество для {sku}.") from None
        if quantity < 1 or quantity > 100:
            raise QuoteError(f"Количество для {sku} должно быть от 1 до 100.")
        product = CATALOG[sku]
        if product["type"] == "generator":
            generator_skus.append(sku)
        unit_price = Decimal(product["price"])
        lines.append({"sku": sku, "name": product["name"], "quantity": quantity,
                      "unit_price": str(money(unit_price)),
                      "line_total": str(money(unit_price * quantity))})

    if len(generator_skus) != 1:
        raise QuoteError("В КП должен быть ровно один тип генератора.")
    generator = generator_skus[0]
    for line in lines:
        product = CATALOG[line["sku"]]
        if product["type"] == "ats" and generator not in product["fits"]:
            raise QuoteError(f"{line['name']} не совместим с {CATALOG[generator]['name']}.")

    try:
        discount = Decimal(str(payload.get("discount_percent", 0)))
    except Exception:
        raise QuoteError("Некорректная скидка.") from None
    if not discount.is_finite() or discount < 0 or discount > 15:
        raise QuoteError("Скидка должна быть от 0 до 15%.")

    subtotal = sum((Decimal(line["line_total"]) for line in lines), Decimal("0"))
    discount_amount = money(subtotal * discount / Decimal("100"))
    total = money(subtotal - discount_amount)
    return {"customer": customer, "items": lines, "subtotal": str(money(subtotal)),
            "discount_percent": str(discount), "discount_amount": str(discount_amount),
            "total": str(total), "currency": "RUB", "approved": False}
