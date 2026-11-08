"""OAuth and Account Authentication Manager for Subscriptions:

Antigravity, GitHub Copilot, Claude Code, OpenAI Codex, Cursor, Kiro AI, and Local Engines.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from apex.config import config


GITHUB_COPILOT_CLIENT_ID = "Iv1.b507a08c87ecfe98"  # Standard VS Code Client ID for Copilot


class OAuthManager:
    """Handles OAuth & Session login for Antigravity, Copilot, Claude, Codex, Cursor, and Local Engines."""

    def __init__(self) -> None:
        pass

    # =========================================================================
    # 1. GOOGLE ANTIGRAVITY OAUTH & SESSION IMPORT
    # =========================================================================
    def import_antigravity(self, console: Optional[Console] = None) -> Tuple[bool, str]:
        """Auto-detect or import Google Antigravity OAuth session from local system."""
        c = console or Console()
        paths_to_check = [
            Path.home() / ".gemini" / "antigravity-cli" / "antigravity-oauth-token",
            Path.home() / ".config" / "antigravity" / "oauth.json",
            Path.home() / ".antigravity" / "oauth.json"
        ]

        found_token = ""
        found_refresh = ""
        found_email = ""
        source_path = ""

        # Check environment first
        env_tok = os.environ.get("ANTIGRAVITY_TOKEN") or os.environ.get("GOOGLE_ANTIGRAVITY_TOKEN")
        if env_tok:
            found_token = env_tok
            source_path = "Environment Variable"

        if not found_token:
            for p in paths_to_check:
                if p.exists():
                    try:
                        content = json.loads(p.read_text(encoding="utf-8"))
                        t_obj = content.get("token")
                        if isinstance(t_obj, dict):
                            found_token = t_obj.get("access_token", "")
                            found_refresh = t_obj.get("refresh_token", "")
                        elif isinstance(t_obj, str):
                            found_token = t_obj

                        found_email = content.get("id_token_email", "")
                        if found_token:
                            source_path = str(p)
                            break
                    except Exception:
                        pass

        if not found_token:
            return False, "Tidak ditemukan session Antigravity aktif di ~/.gemini/antigravity-cli/antigravity-oauth-token."

        # Verify against Google Cloud Code Assist endpoint
        tier_name = "Antigravity"
        project_id = "aicode-consumers"
        try:
            v_url = "https://cloudcode-pa.googleapis.com/v1internal:loadCodeAssist"
            headers = {
                "Authorization": f"Bearer {found_token}",
                "Content-Type": "application/json",
                "User-Agent": "Antigravity/2.0"
            }
            v_resp = requests.post(v_url, headers=headers, json={}, timeout=8)
            if v_resp.status_code == 200:
                v_data = v_resp.json()
                tier_name = v_data.get("currentTier", {}).get("name", "Antigravity")
                project_id = v_data.get("cloudaicompanionProject", "aicode-consumers")
        except Exception:
            pass

        # Save to config
        providers = config.get("providers", {})
        providers["antigravity"] = {
            "api_key": found_token,
            "refresh_token": found_refresh,
            "email": found_email,
            "project": project_id,
            "base_url": "https://cloudcode-pa.googleapis.com/v1internal",
            "models": [
                "gemini-2.0-flash",
                "gemini-2.0-pro-exp",
                "gemini-1.5-pro",
                "gemini-3-flash",
                "claude-3-5-sonnet"
            ]
        }
        config.set("providers", providers, auto_save=True)

        user_info = f" ({found_email})" if found_email else ""
        return True, f"Berhasil mengimpor session Google Antigravity{user_info} [Tier: {tier_name}] dari {source_path}!"

    def get_valid_antigravity_token(self) -> Optional[str]:
        """Get active Antigravity OAuth access token from file or config."""
        token_path = Path.home() / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
        if token_path.exists():
            try:
                content = json.loads(token_path.read_text(encoding="utf-8"))
                t_obj = content.get("token", {})
                if isinstance(t_obj, dict) and t_obj.get("access_token"):
                    return t_obj["access_token"]
            except Exception:
                pass

        providers = config.get("providers", {})
        return providers.get("antigravity", {}).get("api_key")

    # =========================================================================
    # 2. GITHUB COPILOT OAUTH DEVICE CODE FLOW
    # =========================================================================
    def login_github_copilot(self, console: Optional[Console] = None) -> Tuple[bool, str]:
        """Perform OAuth Device Code login for GitHub Copilot."""
        c = console or Console()
        device_code_url = "https://github.com/login/device/code"
        headers = {"Accept": "application/json"}
        payload = {
            "client_id": GITHUB_COPILOT_CLIENT_ID,
            "scope": "read:user"
        }

        try:
            resp = requests.post(device_code_url, data=payload, headers=headers, timeout=10)
            if resp.status_code != 200:
                return False, f"Gagal meminta kode device dari GitHub: {resp.status_code} {resp.text}"

            data = resp.json()
            device_code = data["device_code"]
            user_code = data["user_code"]
            verification_uri = data.get("verification_uri", "https://github.com/login/device")
            interval = max(5, int(data.get("interval", 5)))
            expires_in = int(data.get("expires_in", 900))

            c.print(Panel(
                f"[bold green]AUTENTIKASI AKUN GITHUB COPILOT (OAUTH)[/bold green]\n\n"
                f"1. Buka browser Anda: [bold cyan link={verification_uri}]{verification_uri}[/bold cyan link]\n"
                f"2. Masukkan kode verifikasi: [bold yellow]{user_code}[/bold yellow]\n"
                f"3. Berikan izin otorisasi untuk akun GitHub Anda.\n\n"
                f"[dim]Menunggu konfirmasi dari GitHub (berlaku {expires_in // 60} menit)... Tekan Ctrl+C untuk membatalkan.[/dim]",
                border_style="green",
                expand=True
            ))

            token_url = "https://github.com/login/oauth/access_token"
            token_payload = {
                "client_id": GITHUB_COPILOT_CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            }

            gh_oauth_token = ""
            start_poll = time.time()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=c,
                transient=True
            ) as progress:
                progress.add_task("[cyan]Menunggu otorisasi browser...[/cyan]", total=None)

                while time.time() - start_poll < expires_in:
                    time.sleep(interval)
                    t_resp = requests.post(token_url, data=token_payload, headers=headers, timeout=10)
                    t_data = t_resp.json()

                    if "access_token" in t_data:
                        gh_oauth_token = t_data["access_token"]
                        break

                    err = t_data.get("error")
                    if err == "authorization_pending":
                        continue
                    elif err == "slow_down":
                        interval += 5
                        continue
                    elif err in ["expired_token", "access_denied"]:
                        return False, f"Otorisasi dibatalkan atau waktu habis ({err})."
                    else:
                        if err:
                            return False, f"Error dari GitHub: {err} ({t_data.get('error_description')})"

            if not gh_oauth_token:
                return False, "Waktu tunggu otorisasi habis."

            ok, msg, copilot_token, exp = self._exchange_copilot_token(gh_oauth_token)
            if not ok:
                return False, f"Login GitHub berhasil, namun gagal mengaktifkan Copilot: {msg}"

            providers = config.get("providers", {})
            providers["copilot"] = {
                "api_key": gh_oauth_token,
                "copilot_token": copilot_token,
                "token_expires_at": exp,
                "base_url": "https://api.githubcopilot.com",
                "models": ["claude-3.7-sonnet", "claude-3.5-sonnet", "gpt-4o", "o3-mini", "o1"]
            }
            config.set("providers", providers, auto_save=True)

            return True, "Login Akun GitHub Copilot Berhasil! Kuota Claude 3.7 & GPT-4o siap digunakan."
        except KeyboardInterrupt:
            return False, "Login dibatalkan oleh pengguna."
        except Exception as e:
            return False, f"Terjadi kesalahan saat login GitHub: {str(e)}"

    def _exchange_copilot_token(self, gh_oauth_token: str) -> Tuple[bool, str, str, float]:
        """Exchange GitHub OAuth token for temporary Copilot session token."""
        url = "https://api.github.com/copilot_internal/v2/token"
        headers = {
            "Authorization": f"token {gh_oauth_token}",
            "Editor-Version": "vscode/1.85.1",
            "Editor-Plugin-Version": "copilot/1.144.0",
            "User-Agent": "GithubCopilot/1.144.0",
            "Accept": "application/json"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return False, f"HTTP {resp.status_code}: {resp.text[:150]}", "", 0.0

            data = resp.json()
            token = data.get("token", "")
            expires_at = float(data.get("expires_at", time.time() + 1800))
            if not token:
                return False, "Token Copilot kosong dalam respon GitHub", "", 0.0

            return True, "OK", token, expires_at
        except Exception as e:
            return False, str(e), "", 0.0

    def get_valid_copilot_token(self) -> Optional[str]:
        """Return a valid Copilot session token, refreshing automatically if needed."""
        providers = config.get("providers", {})
        copilot_cfg = providers.get("copilot", {})
        gh_key = copilot_cfg.get("api_key", "")
        if not gh_key or gh_key.startswith("YOUR_"):
            return None

        curr_token = copilot_cfg.get("copilot_token", "")
        expires_at = float(copilot_cfg.get("token_expires_at", 0))

        if curr_token and expires_at > (time.time() + 120):
            return curr_token

        ok, msg, new_tok, new_exp = self._exchange_copilot_token(gh_key)
        if ok and new_tok:
            copilot_cfg["copilot_token"] = new_tok
            copilot_cfg["token_expires_at"] = new_exp
            providers["copilot"] = copilot_cfg
            config.set("providers", providers, auto_save=True)
            return new_tok

        return None

    # =========================================================================
    # 3. CLAUDE CODE SESSION IMPORT
    # =========================================================================
    def import_claude_code(self) -> Tuple[bool, str, Optional[str]]:
        """Look for Claude Code CLI credentials in ~/.claude.json or system environment."""
        paths_to_check = [
            Path.home() / ".claude.json",
            Path.home() / ".claude" / "auth.json",
            Path.home() / ".config" / "claude" / "config.json"
        ]

        found_key = ""
        source_desc = ""

        env_tok = os.environ.get("CLAUDE_CODE_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
        if env_tok and not env_tok.startswith("YOUR_"):
            found_key = env_tok
            source_desc = "Environment Variable"

        if not found_key:
            for p in paths_to_check:
                if p.exists():
                    try:
                        content = json.loads(p.read_text(encoding="utf-8"))
                        tok = (
                            content.get("oauthToken") or
                            content.get("apiKey") or
                            content.get("token") or
                            content.get("session_token")
                        )
                        if tok and isinstance(tok, str) and not tok.startswith("YOUR_"):
                            found_key = tok
                            source_desc = str(p)
                            break
                    except Exception:
                        pass

        if found_key:
            providers = config.get("providers", {})
            providers["claude-code"] = {
                "api_key": found_key,
                "base_url": "https://api.anthropic.com/v1",
                "models": ["claude-3-7-sonnet-latest", "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"]
            }
            config.set("providers", providers, auto_save=True)
            return True, f"Berhasil mengimpor session Claude Code dari {source_desc}!", found_key

        return False, "Tidak ditemukan konfigurasi Claude Code aktif di ~/.claude.json atau Environment.", None

    # =========================================================================
    # 4. OPENAI CODEX & CHATGPT PLUS SESSION IMPORT
    # =========================================================================
    def import_codex(self, manual_token: str = "") -> Tuple[bool, str]:
        """Import OpenAI Codex / ChatGPT Plus session token."""
        found_token = manual_token
        source = "Input Manual"

        if not found_token:
            paths = [
                Path.home() / ".codex" / "auth.json",
                Path.home() / ".config" / "codex" / "config.json",
                Path.home() / ".chatgpt" / "session.json"
            ]
            for p in paths:
                if p.exists():
                    try:
                        content = json.loads(p.read_text(encoding="utf-8"))
                        t = content.get("accessToken") or content.get("session_token")
                        if t:
                            found_token = t
                            source = str(p)
                            break
                    except Exception:
                        pass

        if not found_token:
            return False, "Tidak ditemukan file session Codex / ChatGPT."

        providers = config.get("providers", {})
        providers["codex"] = {
            "api_key": found_token,
            "base_url": "https://chatgpt.com/backend-api",
            "models": ["gpt-4o", "o3-mini", "o1", "gpt-4.5"]
        }
        config.set("providers", providers, auto_save=True)
        return True, f"Berhasil mengimpor session OpenAI Codex dari {source}!"

    # =========================================================================
    # 5. CURSOR SESSION IMPORT
    # =========================================================================
    def import_cursor(self) -> Tuple[bool, str, Optional[str]]:
        """Look for Cursor IDE session token in globalStorage or system."""
        paths_to_check = [
            Path.home() / ".config" / "Cursor" / "User" / "globalStorage" / "storage.json",
            Path.home() / ".cursor" / "auth.json"
        ]

        env_tok = os.environ.get("CURSOR_TOKEN") or os.environ.get("WORKOS_CURSOR_SESSION_TOKEN")
        found_key = env_tok or ""
        source_desc = "Environment Variable" if env_tok else ""

        if not found_key:
            for p in paths_to_check:
                if p.exists():
                    try:
                        content = json.loads(p.read_text(encoding="utf-8"))
                        tok = content.get("workos.sessionToken") or content.get("cursor.auth.token")
                        if tok and isinstance(tok, str):
                            found_key = tok
                            source_desc = str(p)
                            break
                    except Exception:
                        pass

        if found_key:
            providers = config.get("providers", {})
            providers["cursor"] = {
                "api_key": found_key,
                "base_url": "https://api.cursor.com/v1",
                "models": ["cursor-fast", "claude-3.5-sonnet", "gpt-4o"]
            }
            config.set("providers", providers, auto_save=True)
            return True, f"Berhasil mengimpor auth Cursor dari {source_desc}!", found_key

        return False, "Tidak ditemukan kredensial Cursor aktif di sistem.", None

    # =========================================================================
    # 6. KIRO AI FREE TIER
    # =========================================================================
    def import_kiro(self, api_key: str = "") -> Tuple[bool, str]:
        """Configure Kiro AI Free Tier."""
        key = api_key or os.environ.get("KIRO_API_KEY", "")
        if not key:
            key = "kiro-free-tier"

        providers = config.get("providers", {})
        providers["kiro"] = {
            "api_key": key,
            "base_url": "https://api.kiro.ai/v1",
            "models": ["kiro-claude-3.5-sonnet", "kiro-glm-4", "kiro-llama-3.3"]
        }
        config.set("providers", providers, auto_save=True)
        return True, "Kiro AI Platform berhasil dikonfigurasi!"

    # =========================================================================
    # 7. AUTO-SCAN LOCAL AI ENGINES
    # =========================================================================
    def scan_local_services(self) -> Dict[str, Dict[str, Any]]:
        """Probe localhost ports for Ollama (11434), LM Studio (1234), vLLM (8000), llama.cpp (8080)."""
        detected: Dict[str, Dict[str, Any]] = {}

        # 1. Ollama (Port 11434)
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=1.5)
            if r.status_code == 200:
                tags_data = r.json().get("models", [])
                models = [m["name"] for m in tags_data] if tags_data else ["qwen2.5-coder:7b", "llama3.2:3b"]
                detected["ollama"] = {
                    "name": "Ollama (Lokal)",
                    "base_url": "http://localhost:11434/v1",
                    "api_key": "none",
                    "models": models
                }
        except Exception:
            pass

        # 2. LM Studio (Port 1234)
        try:
            r = requests.get("http://localhost:1234/v1/models", timeout=1.5)
            if r.status_code == 200:
                m_data = r.json().get("data", [])
                models = [m["id"] for m in m_data] if m_data else ["local-model"]
                detected["lmstudio"] = {
                    "name": "LM Studio (Lokal)",
                    "base_url": "http://localhost:1234/v1",
                    "api_key": "none",
                    "models": models
                }
        except Exception:
            pass

        # 3. vLLM (Port 8000)
        try:
            r = requests.get("http://localhost:8000/v1/models", timeout=1.5)
            if r.status_code == 200:
                m_data = r.json().get("data", [])
                models = [m["id"] for m in m_data] if m_data else ["vllm-model"]
                detected["vllm"] = {
                    "name": "vLLM Server",
                    "base_url": "http://localhost:8000/v1",
                    "api_key": "none",
                    "models": models
                }
        except Exception:
            pass

        # 4. llama.cpp / llama-server (Port 8080)
        try:
            r = requests.get("http://localhost:8080/v1/models", timeout=1.5)
            if r.status_code == 200:
                m_data = r.json().get("data", [])
                models = [m["id"] for m in m_data] if m_data else ["gguf-model"]
                detected["llamacpp"] = {
                    "name": "llama.cpp (Lokal)",
                    "base_url": "http://localhost:8080/v1",
                    "api_key": "none",
                    "models": models
                }
        except Exception:
            pass

        if detected:
            providers = config.get("providers", {})
            for svc_id, svc_data in detected.items():
                providers[svc_id] = {
                    "api_key": svc_data["api_key"],
                    "base_url": svc_data["base_url"],
                    "models": svc_data["models"]
                }
            config.set("providers", providers, auto_save=True)

        return detected


# Global instance
oauth_manager = OAuthManager()
