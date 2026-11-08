"""Optional Telegram adapter. Run only after setting BOT_TOKEN and OPERATOR_CHAT_ID."""

import json
import os
import sys
import urllib.parse
import urllib.request

from core import IntakeService


def api(token: str, method: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    request = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=body)
    with urllib.request.urlopen(request, timeout=40) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise RuntimeError(f"Telegram method {method} failed")
    return result


def main():
    token = os.environ.get("BOT_TOKEN", "")
    operator = os.environ.get("OPERATOR_CHAT_ID", "")
    if not token or not operator.isdigit():
        sys.exit("Set BOT_TOKEN and numeric OPERATOR_CHAT_ID in the environment.")
    operator_id = int(operator)
    service = IntakeService("intake.sqlite3")
    offset = 0
    print("Bot is polling. Press Ctrl+C to stop.")
    try:
        while True:
            try:
                updates = api(token, "getUpdates", {"offset": offset, "timeout": 25})["result"]
                for update in updates:
                    offset = update["update_id"] + 1
                    message = update.get("message", {})
                    if "text" not in message or "chat" not in message:
                        continue
                    chat_id = int(message["chat"]["id"])
                    reply, notification = service.handle(chat_id, message["text"], operator_id)
                    api(token, "sendMessage", {"chat_id": chat_id, "text": reply})
                    if notification:
                        api(token, "sendMessage", {"chat_id": operator_id, "text": notification})
            except (OSError, RuntimeError, KeyError) as exc:
                print(f"Temporary Telegram error: {type(exc).__name__}", file=sys.stderr)
    except KeyboardInterrupt:
        pass
    finally:
        service.close()


if __name__ == "__main__":
    main()
