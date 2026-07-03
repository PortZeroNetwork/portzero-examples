from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = (
            "Hello from the PortZero Python process example.\n"
            f"PZ_TUNNEL={self.server.tunnel}\n"
            f"localhost_port={self.server.server_port}\n"
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
    tunnel = os.environ.get("PZ_TUNNEL", "python-process.portzero.local:80")
    tunnel_host = tunnel.split(":", 1)[0]

    server = Server(("127.0.0.1", 0), Handler)
    server.tunnel = tunnel
    port = server.server_port

    print(
        f"PORTZERO_EXAMPLE_LISTENING language=python variant=process host=127.0.0.1 "
        f"port={port} url=http://127.0.0.1:{port}/ tunnel={tunnel} tunnel_url=http://{tunnel_host}/",
        flush=True,
    )
    print(
        f"This Python process was launched with PZ_TUNNEL={tunnel}. It is now listening on localhost port {port}. "
        "The program asked to listen on port 0, so the OS assigned an available port. Next, portzero-local's local "
        f"daemon will detect PZ_TUNNEL and the listening port, then make it available at http://{tunnel_host}/.",
        flush=True,
    )

    server.serve_forever()


if __name__ == "__main__":
    main()
