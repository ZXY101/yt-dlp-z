"""A local stand-in for a bgutil PO token server: answers GET /ping with its version."""

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


@dataclass
class FakePotServer:
    url: str
    version: str
    # Answers /ping with this body instead of the version, to act like some other server.
    body: str | None = None


@contextmanager
def fake_pot_server(version: str = "1.2.3") -> Iterator[FakePotServer]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path != "/ping":
                self.send_response(404)
                self.end_headers()
                return
            body = pot.body or json.dumps({"server_uptime": 1.5, "version": pot.version})
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, *_args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    pot = FakePotServer(url=f"http://127.0.0.1:{server.server_address[1]}", version=version)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield pot
    finally:
        server.shutdown()
        server.server_close()
