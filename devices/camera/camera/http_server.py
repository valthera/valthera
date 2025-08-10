#!/usr/bin/env python3

import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class CameraHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return

        if self.path == "/":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"valthera camera")
            return

        # Basic 404
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"not found")


def run_server():
    port_str = os.environ.get("CAMERA_HTTP_PORT", "8000")
    try:
        port = int(port_str)
    except ValueError:
        port = 8000

    server = HTTPServer(("0.0.0.0", port), CameraHandler)
    server.serve_forever()


if __name__ == "__main__":
    run_server()

