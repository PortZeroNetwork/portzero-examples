from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = (
            "Hello from the PortZero Python Docker example.\n"
            f"PZ_TUNNEL={self.server.tunnel}\n"
            "container_port=8080\n"
        ).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class Server(ThreadingHTTPServer):
    tunnel: str


def main() -> None:
    server = Server(("0.0.0.0", 8080), Handler)
    server.tunnel = os.environ.get("PZ_TUNNEL", "python-docker.portzero.local:80")
    server.serve_forever()


if __name__ == "__main__":
    main()
