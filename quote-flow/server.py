"""No-dependency local API and UI for the quote demo."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from quote import CATALOG, QuoteError, calculate_quote


STATIC = Path(__file__).parent / "static"


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, data, content_type="application/json; charset=utf-8"):
        body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/catalog":
            self._send(200, CATALOG)
        elif self.path in ("/", "/index.html"):
            self._send(200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
        else:
            self._send(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/api/quote":
            self._send(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 100_000:
                self._send(413, {"error": "Request too large"})
                return
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise QuoteError("Ожидался JSON-объект.")
            self._send(200, calculate_quote(payload))
        except (ValueError, QuoteError) as exc:
            self._send(400, {"error": str(exc)})


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("QuoteFlow: http://127.0.0.1:8765")
    server.serve_forever()
