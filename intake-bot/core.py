"""Reusable intake logic, independent of Telegram network calls."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class IntakeService:
    def __init__(self, db_path: str | Path = ":memory:"):
        self.db = sqlite3.connect(str(db_path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                chat_id INTEGER PRIMARY KEY, stage TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT '', contact TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL, name TEXT NOT NULL,
                contact TEXT NOT NULL, details TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new', created_at TEXT NOT NULL
            );
        """)

    def close(self):
        self.db.close()

    def handle(self, chat_id: int, text: str, operator_id: int | None = None) -> tuple[str, str | None]:
        """Return (reply_to_sender, optional_message_to_operator)."""
        text = text.strip()
        if not text:
            return "Напишите сообщение текстом.", None
        if len(text) > 1000:
            return "Сообщение слишком длинное: максимум 1000 символов.", None

        if operator_id is not None and chat_id == operator_id:
            if text == "/list":
                rows = self.db.execute("SELECT id,name,status,created_at FROM requests ORDER BY id DESC LIMIT 10").fetchall()
                if not rows:
                    return "Заявок пока нет.", None
                return "Последние заявки:\n" + "\n".join(
                    f"#{r['id']} · {r['name']} · {r['status']} · {r['created_at'][:16]}" for r in rows), None
            if text.startswith("/done "):
                try:
                    request_id = int(text.split()[1])
                except (ValueError, IndexError):
                    return "Формат: /done 1", None
                result = self.db.execute("UPDATE requests SET status='done' WHERE id=?", (request_id,))
                self.db.commit()
                return (f"Заявка #{request_id} закрыта." if result.rowcount else "Такой заявки нет."), None
            return "Команды оператора: /list, /done НОМЕР", None

        if text in ("/start", "/new"):
            self.db.execute("INSERT INTO sessions(chat_id,stage) VALUES(?,'name') "
                            "ON CONFLICT(chat_id) DO UPDATE SET stage='name',name='',contact=''", (chat_id,))
            self.db.commit()
            return "Здравствуйте! Как вас или вашу компанию зовут?", None

        row = self.db.execute("SELECT stage,name,contact FROM sessions WHERE chat_id=?", (chat_id,)).fetchone()
        if row is None:
            return "Чтобы оставить заявку, отправьте /new.", None

        if row["stage"] == "name":
            if len(text) > 100:
                return "Название слишком длинное: максимум 100 символов.", None
            self.db.execute("UPDATE sessions SET name=?,stage='contact' WHERE chat_id=?", (text, chat_id))
            self.db.commit()
            return "Оставьте телефон, email или удобный способ связи.", None
        if row["stage"] == "contact":
            if len(text) > 150:
                return "Контакт слишком длинный: максимум 150 символов.", None
            self.db.execute("UPDATE sessions SET contact=?,stage='details' WHERE chat_id=?", (text, chat_id))
            self.db.commit()
            return "Коротко опишите задачу и срок.", None

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cur = self.db.execute("INSERT INTO requests(chat_id,name,contact,details,created_at) VALUES(?,?,?,?,?)",
                              (chat_id, row["name"], row["contact"], text, now))
        self.db.execute("DELETE FROM sessions WHERE chat_id=?", (chat_id,))
        self.db.commit()
        request_id = cur.lastrowid
        notification = (f"Новая заявка #{request_id}\nКлиент: {row['name']}\n"
                        f"Контакт: {row['contact']}\nЗадача: {text}")
        return f"Готово! Заявка #{request_id} передана менеджеру.", notification
