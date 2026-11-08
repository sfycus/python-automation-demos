"""Offline conversation demo; no Telegram token needed."""

from core import IntakeService


def main():
    service = IntakeService()
    try:
        client = 1001
        operator = 9001
        for user_text in ["/new", "ООО Сигнал", "@signal_manager", "Нужен бот для заявок до пятницы"]:
            reply, notification = service.handle(client, user_text, operator)
            print(f"Клиент: {user_text}\nБот: {reply}\n")
            if notification:
                print(f"Уведомление оператору:\n{notification}\n")
        reply, _ = service.handle(operator, "/list", operator)
        print(f"Оператор: /list\nБот: {reply}\n")
        reply, _ = service.handle(operator, "/done 1", operator)
        print(f"Оператор: /done 1\nБот: {reply}")
    finally:
        service.close()


if __name__ == "__main__":
    main()
