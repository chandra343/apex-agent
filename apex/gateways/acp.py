"""Agent Client Protocol (ACP) Adapter for IDEs (VS Code, Cursor, Zed, Neovim)."""
from __future__ import annotations

import json
import sys
from typing import Any, Dict
from apex.agent import default_agent


class ACPAdapter:
    """Provides standard Agent Client Protocol framing over stdio JSON-RPC."""

    def __init__(self) -> None:
        self.session_id = "ide_acp_session"

    def run_stdio_loop(self) -> None:
        """Listen on stdin for ACP JSON-RPC requests from IDE and reply on stdout."""
        for line in sys.stdin:
            line_str = line.strip()
            if not line_str:
                continue

            try:
                req = json.loads(line_str)
                req_id = req.get("id")
                method = req.get("method")
                params = req.get("params", {})

                if method == "initialize":
                    self._send_reply(req_id, {
                        "protocolVersion": "1.0",
                        "serverInfo": {"name": "apex-acp-server", "version": "1.0.0"}
                    })
                elif method == "session/prompt":
                    prompt_text = params.get("prompt", "")
                    # Execute through agent
                    result_text = default_agent.run(prompt_text, session_id=self.session_id, channel="acp")
                    self._send_reply(req_id, {"response": result_text})
                else:
                    self._send_reply(req_id, {"status": "ok"})
            except Exception as e:
                self._send_error(req.get("id") if "req" in locals() else None, str(e))

    def _send_reply(self, req_id: Any, result: Any) -> None:
        payload = {"jsonrpc": "2.0", "id": req_id, "result": result}
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()

    def _send_error(self, req_id: Any, error_msg: str) -> None:
        payload = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": error_msg}}
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()


def run_acp_server() -> None:
    adapter = ACPAdapter()
    adapter.run_stdio_loop()
