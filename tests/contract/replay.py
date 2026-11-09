"""A loopback HTTP server that answers from recorded replies and keeps each request.

``Replay(answer)`` calls ``answer(method, path, body)`` for every request and
sends back the ``(status, body bytes)`` it returns. Requests are kept in
``requests`` as dicts with ``method``, ``path``, ``headers`` and ``body``.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"

Answer = Callable[[str, str, bytes], tuple[int, bytes]]


class Replay:
    def __init__(self, answer: Answer) -> None:
        self.answer = answer
        self.requests: list[dict[str, Any]] = []
        replay = self

        class Handler(BaseHTTPRequestHandler):
            def _serve(self) -> None:
                size = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(size) if size else b""
                replay.requests.append(
                    {"method": self.command, "path": self.path, "headers": dict(self.headers), "body": body}
                )
                status, data = replay.answer(self.command, self.path, body)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = _serve
            do_POST = _serve

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}"
        self._thread = threading.Thread(target=self._server.serve_forever, args=(0.05,), daemon=True)

    def __enter__(self) -> Replay:
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join()


def in_order(*replies: tuple[int, bytes]) -> Answer:
    """An answer function giving ``replies`` one per request, in order."""
    queue = list(replies)

    def answer(method: str, path: str, body: bytes) -> tuple[int, bytes]:
        if not queue:
            return 500, b'{"error": {"message": "no recorded reply is left"}}'
        return queue.pop(0)

    return answer
