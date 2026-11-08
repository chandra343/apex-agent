"""WhatsApp Multi-Device Gateway Adapter (Baileys Bridge Style)."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional
import requests
from apex.agent import default_agent
from apex.config import config
from apex.gateways.queue import conversation_queue
from apex.security.auth import security_auth


class WhatsAppAdapter:
    """Communicates with WhatsApp via local Baileys bridge on bridge_port."""

    def __init__(self) -> None:
        self.bridge_port = config.get("gateways.whatsapp.bridge_port", 3001)
        self.bridge_url = f"http://127.0.0.1:{self.bridge_port}"

    def send_message(self, jid: str, text: str) -> bool:
        try:
            resp = requests.post(f"{self.bridge_url}/send", json={"jid": jid, "text": text}, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def handle_inbound_message(self, jid: str, text: str) -> None:
        """Handle incoming chat frame forwarded by Baileys bridge."""
        if not security_auth.is_authorized(jid):
            pairing_code = config.get("security.pairing_code", "APEX-2026")
            if text.strip() == pairing_code:
                security_auth.try_pairing(jid, text.strip())
                self.send_message(jid, "🎉 Pairing successful! You are now authorized to use Project Apex.")
            else:
                self.send_message(jid, "🔒 Unauthorized. Please provide the secret pairing code.")
            return

        session_id = f"wa_{jid}"
        conversation_queue.enqueue(
            conversation_id=session_id,
            payload=text,
            processor=lambda prompt: self._execute_turn(jid, session_id, prompt)
        )

    def _execute_turn(self, jid: str, session_id: str, prompt: str) -> None:
        try:
            response = default_agent.run(prompt, session_id=session_id, channel="whatsapp")
            self.send_message(jid, response)
        except Exception as e:
            self.send_message(jid, f"❌ Execution error: {e}")


# Global whatsapp adapter
whatsapp_adapter = WhatsAppAdapter()
