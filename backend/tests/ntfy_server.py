"""A local stand-in for an ntfy server that records what it receives."""

import json
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


@dataclass
class FakeNtfy:
    url: str
    received: list[dict[str, Any]] = field(default_factory=list)
    auth: list[str | None] = field(default_factory=list)
    # Status code to answer with.
    status: int = 200

    def wait_for(self, count: int, timeout: float = 10) -> list[dict[str, Any]]:
        deadline = time.monotonic() + timeout
        while len(self.received) < count:
            assert time.monotonic() < deadline, f"got {self.received}"
            time.sleep(0.02)
        return self.received

    def titles(self) -> list[str]:
        return [str(message["title"]) for message in self.received]


@contextmanager
def fake_ntfy() -> Iterator[FakeNtfy]:
    server: ThreadingHTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers["Content-Length"])
            ntfy.received.append(json.loads(self.rfile.read(length)))
            ntfy.auth.append(self.headers.get("Authorization"))
            self.send_response(ntfy.status)
            self.end_headers()

        def log_message(self, *_args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    ntfy = FakeNtfy(url=f"http://127.0.0.1:{server.server_address[1]}")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield ntfy
    finally:
        server.shutdown()
        server.server_close()
