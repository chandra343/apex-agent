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

    def _send_voice(self, chat_id: int | str, audio_file_path: str) -> bool:
        """Send an audio voice note to a Telegram chat."""
        url = f"{self.base_url}/sendVoice"
        try:
            with open(audio_file_path, "rb") as f_voice:
                files = {"voice": f_voice}
                data = {"chat_id": chat_id}
                resp = requests.post(url, data=data, files=files, timeout=20)
                return resp.status_code == 200
        except Exception:
            return False

    def _send_document(self, chat_id: int | str, document_path: str, caption: str = "") -> bool:
        """Send a document or file attachment to a Telegram chat."""
        url = f"{self.base_url}/sendDocument"
        try:
            with open(document_path, "rb") as f_doc:
                files = {"document": f_doc}
                data = {"chat_id": chat_id, "caption": caption[:1024]}
                resp = requests.post(url, data=data, files=files, timeout=30)
                return resp.status_code == 200
        except Exception:
            return False

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
                "🤖 *Project Apex Telegram Gateway* 🚀\n\n"
                "• 💬 *Kirim Perintah*: Kirim prompt, instruksi kode, atau tugas otomatisasi apa pun.\n"
                "• 🎙️ *Voice Note*: Kirim rekaman suara untuk mendiktekan perintah.\n"
                "• ⚙️ `/model` - Ganti model AI aktif secara instan via tombol.\n"
                "• 📊 `/stats` - Pantau penggunaan token dan kalkulasi biaya."
            )
            return

        # 4. Enqueue into FIFO Queue (OpenClaw style)
        session_id = f"tg_{chat_id}"
        is_voice_turn = bool(voice)
        conversation_queue.enqueue(
            conversation_id=session_id,
            payload=text,
            processor=lambda prompt: self._execute_agent_turn(chat_id, session_id, prompt, is_voice=is_voice_turn)
        )

    def _execute_agent_turn(self, chat_id: int | str, session_id: str, prompt: str, is_voice: bool = False) -> None:
        try:
            response = default_agent.run(prompt, session_id=session_id, channel="telegram")
            self._send_message(chat_id, response)

            # If user sent a voice note, reply with voice synthesis as well!
            if is_voice and response:
                try:
                    from apex.tools.speech import synthesize_speech
                    from apex.config import DATA_DIR
                    import re

                    # Clean markdown formatting for clear spoken voice
                    clean_spoken = re.sub(r"[`*_#\[\]\(\)>~]", "", response)[:400]
                    audio_target = str(DATA_DIR / "audio" / f"reply_{chat_id}_{int(time.time())}.mp3")
                    res = synthesize_speech(clean_spoken, output_path=audio_target, language="id")
                    if os.path.exists(audio_target):
                        self._send_voice(chat_id, audio_target)
                except Exception:
                    pass
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
