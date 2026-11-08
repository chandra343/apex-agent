"""Telegram Gateway Adapter with Inline Keyboard Model Picker & FIFO Queue."""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Dict, List, Optional
import requests

from apex.agent import default_agent
from apex.config import config, DATA_DIR
from apex.gateways.queue import conversation_queue
from apex.router.model_switcher import model_switcher
from apex.security.auth import security_auth
from apex.tools.transcribe import transcribe_audio


class TelegramAdapter:
    """Telegram Bot gateway supporting polling, inline keyboards, voice notes, and FIFO queuing."""

    def __init__(self) -> None:
        self.token = config.get("gateways.telegram.token", "")
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.running = False
        self.last_update_id = 0

    def start_polling(self) -> None:
        """Run long-polling event loop."""
        if not self.token or "YOUR_" in self.token:
            print("Telegram Bot token not configured. Skipping Telegram adapter.")
            return

        self.running = True
        print("✔ Telegram Gateway Adapter started (polling)...")

        while self.running:
            try:
                updates = self._get_updates(offset=self.last_update_id + 1, timeout=20)
                for u in updates:
                    self.last_update_id = u["update_id"]
                    self._process_update(u)
            except Exception as e:
                time.sleep(3.0)

    def stop(self) -> None:
        self.running = False

    def _get_updates(self, offset: int, timeout: int = 20) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/getUpdates"
        try:
            resp = requests.get(url, params={"offset": offset, "timeout": timeout}, timeout=timeout + 5)
            if resp.status_code == 200:
                return resp.json().get("result", [])
        except Exception:
            pass
        return []

    def _send_message(
        self,
        chat_id: int | str,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> None:
        url = f"{self.base_url}/sendMessage"
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text[:4000],
            "parse_mode": "Markdown"
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            requests.post(url, json=payload, timeout=10)
        except Exception:
            # Fallback without markdown if parsing fails
            payload.pop("parse_mode", None)
            try:
                requests.post(url, json=payload, timeout=10)
            except Exception:
                pass

    def _process_update(self, update: Dict[str, Any]) -> None:
        # Handle Callback Queries (Inline Keyboard Buttons)
        if "callback_query" in update:
            cb = update["callback_query"]
            chat_id = cb["message"]["chat"]["id"]
            data = cb.get("data", "")
            if data.startswith("set_model:"):
                target_model = data.split(":", 1)[1]
                model_switcher.switch_model(target_model)
                self._send_message(chat_id, f"✔ *Active model switched to:* `{target_model}`")
            return

        message = update.get("message", {})
        if not message:
            return

        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        voice = message.get("voice")

        # 1. Check Authorization
        if not security_auth.is_authorized(chat_id):
            # Check if user sent the pairing code
            pairing_code = config.get("security.pairing_code", "APEX-2026")
            if text.strip() == pairing_code:
                security_auth.try_pairing(chat_id, text.strip())
                self._send_message(
                    chat_id,
                    "🎉 *Pairing Successful!*\nYour Telegram account is now authorized to operate Project Apex."
                )
            else:
                self._send_message(
                    chat_id,
                    "🔒 *Unauthorized Access*\nThis is a private sovereign AI assistant. "
                    "Please enter the secret pairing code to authorize your account."
                )
            return

        # 2. Handle Voice Notes
        if voice:
            file_id = voice.get("file_id")
            audio_text = self._download_and_transcribe_voice(file_id)
            if audio_text:
                self._send_message(chat_id, f"🎙️ *Voice Note Received:*\n_{audio_text}_\n\nExecuting...")
                text = audio_text
            else:
                self._send_message(chat_id, "⚠️ Failed to transcribe audio voice note.")
                return

        # 3. Handle Commands
        if text.startswith("/model"):
            self._send_model_picker(chat_id)
            return

        if text.startswith("/start") or text.startswith("/help"):
            self._send_message(
                chat_id,
                "🤖 *Project Apex Telegram Gateway*\n\n"
                "• Send any prompt or code instruction to execute.\n"
                "• Send a *Voice Note* to dictate commands.\n"
                "• `/model` - Tap inline buttons to switch AI models.\n"
                "• `/stats` - View token usage and estimated costs."
            )
            return

        # 4. Enqueue into FIFO Queue (OpenClaw style)
        session_id = f"tg_{chat_id}"
        conversation_queue.enqueue(
            conversation_id=session_id,
            payload=text,
            processor=lambda prompt: self._execute_agent_turn(chat_id, session_id, prompt)
        )

    def _execute_agent_turn(self, chat_id: int | str, session_id: str, prompt: str) -> None:
        try:
            response = default_agent.run(prompt, session_id=session_id, channel="telegram")
            self._send_message(chat_id, response)
        except Exception as e:
            self._send_message(chat_id, f"❌ Execution error: {e}")

    def _send_model_picker(self, chat_id: int | str) -> None:
        models = model_switcher.get_available_models()
        keyboard_buttons = []
        for m in models:
            m_id = m["id"]
            btn_text = f"✔ {m_id}" if m_id == config.default_model else m_id
            keyboard_buttons.append([{"text": btn_text, "callback_data": f"set_model:{m_id}"}])

        reply_markup = {"inline_keyboard": keyboard_buttons}
        self._send_message(chat_id, "🎯 *Select an AI Model:*", reply_markup=reply_markup)

    def _download_and_transcribe_voice(self, file_id: str) -> Optional[str]:
        try:
            get_file_url = f"{self.base_url}/getFile?file_id={file_id}"
            resp = requests.get(get_file_url, timeout=10)
            if resp.status_code != 200:
                return None
            file_path = resp.json().get("result", {}).get("file_path")
            if not file_path:
                return None

            download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            audio_bytes = requests.get(download_url, timeout=30).content

            voice_dir = DATA_DIR / "media"
            voice_dir.mkdir(parents=True, exist_ok=True)
            local_audio_file = voice_dir / f"tg_voice_{int(time.time())}.ogg"

            with open(local_audio_file, "wb") as f:
                f.write(audio_bytes)

            ok, transcribed = transcribe_audio(str(local_audio_file))
            return transcribed if ok else None
        except Exception:
            return None


# Global telegram adapter
telegram_adapter = TelegramAdapter()
