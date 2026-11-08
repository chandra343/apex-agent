"""Authenticated HTTP REST Webhook Gateway Adapter."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from typing import Any, Dict
from apex.agent import default_agent
from apex.config import config
from apex.security.auth import security_auth


class WebhookRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/v1/chat":
            self.send_response(404)
            self.end_headers()
            return

        # Check Authorization header
        auth_header = self.headers.get("Authorization", "")
        secret = config.get("security.pairing_code", "APEX-2026")
        if not auth_header.endswith(secret):
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"error": "Unauthorized"}\n')
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            payload = json.loads(body.decode("utf-8"))
            prompt = payload.get("prompt", "")
            session_id = payload.get("session_id", "webhook_default")

            answer = default_agent.run(prompt, session_id=session_id, channel="webhook")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"response": answer}).encode("utf-8") + b"\n")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8") + b"\n")

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Suppress default server logs


def start_webhook_server(host: str = "127.0.0.1", port: int = 20129) -> HTTPServer:
    server = HTTPServer((host, port), WebhookRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
