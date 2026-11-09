"""Authenticated HTTP REST Webhook & Event Router Gateway Adapter (OpenBot Style)."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from typing import Any, Dict
from apex.agent import default_agent
from apex.config import config
from apex.security.auth import security_auth
from apex.workflows.engine import workflow_engine


class WebhookRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/v1/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {"status": "healthy", "service": "apex-gateway", "version": "1.0.0"}
            self.wfile.write(json.dumps(resp).encode("utf-8") + b"\n")
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        # Check Authorization header for protected endpoints
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
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = {}

        # 1. Chat endpoint (/v1/chat)
        if self.path == "/v1/chat":
            try:
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
            return

        # 2. Direct Workflow Trigger (/v1/workflows/trigger/<name>)
        if self.path.startswith("/v1/workflows/trigger/"):
            wf_name = self.path[len("/v1/workflows/trigger/"):].strip("/")
            try:
                res = workflow_engine.run_workflow(wf_name, input_params=payload, trigger_source="webhook")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(res).encode("utf-8") + b"\n")
            except Exception as e:
                self.send_response(400 if "not found" in str(e).lower() else 500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8") + b"\n")
            return

        # 3. Generic Event Ingestion (/v1/events/<event_type>)
        if self.path.startswith("/v1/events/"):
            event_type = self.path[len("/v1/events/"):].strip("/")
            try:
                # If a workflow with the event_type name exists, trigger it; otherwise pass to agent
                wf = workflow_engine.get_workflow(event_type)
                if wf:
                    res = workflow_engine.run_workflow(event_type, input_params=payload, trigger_source=f"event:{event_type}")
                    reply = {"triggered_workflow": event_type, "run_id": res["run_id"], "status": res["status"]}
                else:
                    event_prompt = f"Received external webhook event '{event_type}':\n```json\n{json.dumps(payload, indent=2)}\n```\nAnalyze and take necessary actions."
                    agent_reply = default_agent.run(event_prompt, session_id=f"event_{event_type}", channel="webhook_event")
                    reply = {"event_type": event_type, "response": agent_reply}

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(reply).encode("utf-8") + b"\n")
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8") + b"\n")
            return

        # Path not recognized
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Suppress default server logs


def start_webhook_server(host: str = "127.0.0.1", port: int = 20129) -> HTTPServer:
    server = HTTPServer((host, port), WebhookRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
