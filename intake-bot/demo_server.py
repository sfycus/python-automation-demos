"""Local browser simulator backed by the same IntakeService as the Telegram bot."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from core import IntakeService


service = IntakeService()
HTML = (Path(__file__).parent / "demo.html").read_bytes()


class Handler(BaseHTTPRequestHandler):
    def send(self, status, value, content_type="application/json; charset=utf-8"):
        body = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self.send(200, HTML, "text/html; charset=utf-8")
        else:
            self.send(404, {"error": "Not found"})

    def do_POST(self):
        global service
        if self.path == "/api/reset":
            service.close()
            service = IntakeService()
            self.send(200, {"ok": True})
            return
        if self.path != "/api/chat":
            self.send(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 5000:
                self.send(413, {"error": "Request too large"})
                return
            data = json.loads(self.rfile.read(length))
            role = data.get("role")
            if role not in ("client", "operator") or not isinstance(data.get("text"), str):
                self.send(400, {"error": "Invalid message"})
                return
            chat_id = 1001 if role == "client" else 9001
            reply, notification = service.handle(chat_id, data["text"], 9001)
            self.send(200, {"reply": reply, "notification": notification})
        except (ValueError, TypeError):
            self.send(400, {"error": "Invalid JSON"})


if __name__ == "__main__":
    print("IntakeBot demo: http://127.0.0.1:8766")
    HTTPServer(("127.0.0.1", 8766), Handler).serve_forever()
